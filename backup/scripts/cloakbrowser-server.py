#!/usr/bin/env python3
"""CloakBrowser REST API server — fully async, Camofox-compatible backend."""
import asyncio
import base64
import json
import logging
import os
import re
import sys
import time
import traceback
import uuid

try:
    from aiohttp import web
except ImportError:
    print("aiohttp required: pip install aiohttp", flush=True)
    sys.exit(1)

from cloakbrowser import launch_async

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("cloakbrowser-server")

BROWSER = None
_tabs = {}
_tabs_lock = asyncio.Lock()
DEFAULT_TIMEOUT = 30000


async def get_browser():
    global BROWSER
    if BROWSER is None:
        logger.info("Launching CloakBrowser (async, headless)...")
        BROWSER = await launch_async(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
        )
        logger.info("CloakBrowser launched successfully")
    return BROWSER


# ---------------------------------------------------------------------------
# Accessibility tree generation
# ---------------------------------------------------------------------------

async def _build_accessibility_tree(page) -> str:
    snapshot = await page.evaluate("""() => {
        const lines = [];
        let refCounter = 0;
        function getRole(el) {
            const r = el.getAttribute('role');
            if (r) return r;
            const t = el.tagName.toLowerCase();
            const roles = {
                'a':'link','button':'button','input':'textbox',
                'textarea':'textbox','select':'combobox','img':'img',
                'h1':'heading','h2':'heading','h3':'heading','h4':'heading',
                'h5':'heading','h6':'heading','nav':'navigation',
                'main':'main','header':'banner','footer':'contentinfo',
                'aside':'complementary','form':'form','table':'table',
                'ul':'list','ol':'list','li':'listitem','dialog':'dialog',
                'label':'text','p':'paragraph','span':'text','div':'text',
                'section':'region','code':'code','pre':'text',
                'strong':'strong','em':'emphasis',
            };
            return roles[t] || 'text';
        }
        function getLabel(el) {
            return el.getAttribute('aria-label') || el.getAttribute('alt') ||
                   el.getAttribute('title') || el.getAttribute('placeholder') ||
                   (el.textContent||'').trim().substring(0,100) || el.tagName.toLowerCase();
        }
        function getRef() { refCounter++; return 'e'+refCounter; }
        function getLevel(el) {
            const m = el.tagName.match(/^H([1-6])$/i);
            if (m) return parseInt(m[1]);
            const a = el.getAttribute('aria-level');
            return a ? parseInt(a) : null;
        }
        function getState(el) {
            const s = [];
            if (el.disabled) s.push('disabled');
            if (el.getAttribute('aria-selected')==='true') s.push('selected');
            if (el.getAttribute('aria-pressed')==='true') s.push('pressed');
            if (el.getAttribute('aria-expanded')==='true') s.push('expanded');
            if (el.getAttribute('aria-expanded')==='false') s.push('collapsed');
            if (el.getAttribute('aria-checked')==='true') s.push('checked');
            if (el.getAttribute('aria-current')==='page') s.push('current');
            return s.length ? ' ['+s.join('], [')+']' : '';
        }
        function getUrl(el) {
            if (el.tagName==='A' && el.href) return el.href;
            if (el.tagName==='IMG' && el.src) return el.src;
            return null;
        }
        function walk(node, depth) {
            if (!node || node.nodeType!==1) return;
            const style = window.getComputedStyle(node);
            if (style.display==='none'||style.visibility==='hidden') return;
            const tag = node.tagName.toLowerCase();
            const role = getRole(node);
            const label = getLabel(node);
            const ref = getRef();
            const level = getLevel(node);
            const state = getState(node);
            const url = getUrl(node);
            const indent = '  '.repeat(depth);
            const refStr = ' ['+ref+']';
            const levelStr = level ? ' [level='+level+']' : '';
            const isInteract = ['a','button','input','textarea','select','img','nav','dialog','form'].includes(tag)
                || node.getAttribute('role') || node.getAttribute('onclick') || node.tabIndex>=0;
            if (isInteract && role!=='text' && role!=='region') {
                if (role==='link') {
                    lines.push(indent+'- link "'+label+'"'+state+refStr+':');
                    if (url) lines.push(indent+'  - /url: '+url);
                    const t = (node.textContent||'').trim();
                    if (t&&t!==label) lines.push(indent+'  - text: '+t.substring(0,100));
                } else if (role==='button') {
                    lines.push(indent+'- button "'+label+'"'+state+refStr);
                } else if (role==='textbox') {
                    lines.push(indent+'- textbox "'+label+'"'+state+refStr);
                    const v = node.value;
                    if (v) {
                        const d = v.includes('"')?"'":'"';
                        lines.push(indent+': '+d+v.substring(0,100)+d);
                    }
                } else if (role==='combobox') {
                    lines.push(indent+'- combobox "'+label+'"'+state+refStr);
                } else if (role==='heading') {
                    lines.push(indent+'- heading "'+label+'"'+levelStr+refStr);
                } else if (role==='img') {
                    lines.push(indent+'- img "'+label+'"'+state+refStr);
                    if (url) lines.push(indent+'  - /url: '+url);
                } else if (role==='dialog') {
                    lines.push(indent+'- dialog "'+label+'"'+state+refStr);
                } else if (role==='navigation') {
                    lines.push(indent+'- navigation "'+label+'"'+refStr);
                } else {
                    lines.push(indent+'- '+role+' "'+label+'"'+state+refStr);
                }
            } else if (role==='paragraph') {
                const t = (node.textContent||'').trim();
                if (t) lines.push(indent+'- paragraph: '+t.substring(0,200));
            } else if (role==='heading') {
                lines.push(indent+'- heading "'+label+'"'+levelStr+refStr);
            } else if (role==='list') {
                lines.push(indent+'- list'+refStr);
            } else if (role==='listitem') {
                lines.push(indent+'  - listitem'+refStr);
            } else if (role==='complementary') {
                lines.push(indent+'- complementary "'+label+'"'+refStr);
            } else if (role==='form') {
                lines.push(indent+'- form "'+label+'"'+refStr);
            }
            for (const c of node.children) walk(c, depth+1);
        }
        walk(document.body, 0);
        return lines.join('\\n');
    }""")
    return snapshot or ""


# ---------------------------------------------------------------------------
# Tab management
# ---------------------------------------------------------------------------

async def _create_page(user_id: str, url: str = "about:blank"):
    browser = await get_browser()
    context = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 720},
        locale="zh-CN",
    )
    page = await context.new_page()
    tab_id = str(uuid.uuid4())[:8]
    async with _tabs_lock:
        _tabs[tab_id] = {"page": page, "context": context, "user_id": user_id}
    if url and url != "about:blank":
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT)
        except Exception as e:
            logger.warning(f"Initial goto {url} failed: {e}")
    return tab_id


async def _get_page(tab_id: str, user_id: str = None):
    async with _tabs_lock:
        tab = _tabs.get(tab_id)
        if not tab: return None
        if user_id and tab["user_id"] != user_id: return None
        return tab["page"]


async def _close_tab(tab_id: str):
    async with _tabs_lock:
        tab = _tabs.pop(tab_id, None)
    if tab:
        try: await tab["context"].close()
        except: pass


async def _close_all_for_user(user_id: str):
    to_close = []
    async with _tabs_lock:
        to_close = [(tid, t) for tid, t in _tabs.items() if t["user_id"] == user_id]
        for tid, _ in to_close: del _tabs[tid]
    for _, tab in to_close:
        try: await tab["context"].close()
        except: pass


# ---------------------------------------------------------------------------
# HTTP Handlers
# ---------------------------------------------------------------------------

async def handle_health(request):
    return web.json_response({
        "ok": True, "running": True,
        "engine": "cloakbrowser", "version": "0.3.30",
        "browserConnected": BROWSER is not None,
        "poolSize": len(_tabs),
    })


async def handle_create_tab(request):
    try:
        body = await request.json()
        user_id = body.get("userId", f"anon_{uuid.uuid4().hex[:8]}")
        url = body.get("url", "about:blank")
        session_key = body.get("sessionKey", "")
        tab_id = await _create_page(user_id, url)
        return web.json_response({"tabId": tab_id, "userId": user_id, "url": url, "sessionKey": session_key})
    except Exception as e:
        logger.error(f"create_tab: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_navigate(request):
    tab_id = request.match_info["tab_id"]
    try:
        body = await request.json()
        url = body.get("url", "")
        user_id = body.get("userId", "")
        page = await _get_page(tab_id, user_id)
        if not page:
            return web.json_response({"error": f"Tab {tab_id} not found"}, status=404)
        await page.goto(url, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT)
        return web.json_response({"url": page.url, "title": await page.title()})
    except Exception as e:
        logger.error(f"navigate: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_snapshot(request):
    tab_id = request.match_info["tab_id"]
    user_id = request.query.get("userId", "")
    try:
        page = await _get_page(tab_id, user_id)
        if not page:
            return web.json_response({"error": f"Tab {tab_id} not found"}, status=404)
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=5000)
        except: pass
        snapshot_text = await _build_accessibility_tree(page)
        refs = re.findall(r'\[(e\d+)\]', snapshot_text)
        return web.json_response({"snapshot": snapshot_text, "refsCount": len(set(refs))})
    except Exception as e:
        logger.error(f"snapshot: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_click(request):
    tab_id = request.match_info["tab_id"]
    try:
        body = await request.json()
        ref = body.get("ref", "").lstrip("@")
        user_id = body.get("userId", "")
        page = await _get_page(tab_id, user_id)
        if not page:
            return web.json_response({"error": f"Tab {tab_id} not found"}, status=404)
        await page.evaluate(f"""() => {{
            const el = document.querySelector('[data-ref="{ref}"]');
            if (el) {{ el.click(); return; }}
            const all = document.querySelectorAll('button, a, input, [role="button"], [tabindex]');
            for (const e of all) {{
                if (e.textContent.includes("{ref}") || e.getAttribute('aria-label')?.includes("{ref}")) {{
                    e.click(); return;
                }}
            }}
        }}""")
        return web.json_response({"url": page.url})
    except Exception as e:
        logger.error(f"click: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_type(request):
    tab_id = request.match_info["tab_id"]
    try:
        body = await request.json()
        ref = body.get("ref", "").lstrip("@")
        text = body.get("text", "")
        user_id = body.get("userId", "")
        page = await _get_page(tab_id, user_id)
        if not page:
            return web.json_response({"error": f"Tab {tab_id} not found"}, status=404)
        await page.evaluate(f"""() => {{
            const el = document.querySelector('[data-ref="{ref}"]');
            if (el) {{ el.focus(); el.value = ''; return; }}
        }}""")
        await page.keyboard.type(text, delay=5)
        return web.json_response({"success": True})
    except Exception as e:
        logger.error(f"type: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_scroll(request):
    tab_id = request.match_info["tab_id"]
    try:
        body = await request.json()
        direction = body.get("direction", "down")
        user_id = body.get("userId", "")
        page = await _get_page(tab_id, user_id)
        if not page:
            return web.json_response({"error": f"Tab {tab_id} not found"}, status=404)
        delta = 500 if direction == "down" else -500
        await page.evaluate(f"window.scrollBy(0, {delta})")
        return web.json_response({"success": True, "scrolled": direction})
    except Exception as e:
        logger.error(f"scroll: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_back(request):
    tab_id = request.match_info["tab_id"]
    try:
        body = await request.json()
        user_id = body.get("userId", "")
        page = await _get_page(tab_id, user_id)
        if not page:
            return web.json_response({"error": f"Tab {tab_id} not found"}, status=404)
        await page.go_back(wait_until="domcontentloaded")
        return web.json_response({"url": page.url})
    except Exception as e:
        logger.error(f"back: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_press(request):
    tab_id = request.match_info["tab_id"]
    try:
        body = await request.json()
        key = body.get("key", "")
        user_id = body.get("userId", "")
        page = await _get_page(tab_id, user_id)
        if not page:
            return web.json_response({"error": f"Tab {tab_id} not found"}, status=404)
        await page.keyboard.press(key)
        return web.json_response({"success": True, "pressed": key})
    except Exception as e:
        logger.error(f"press: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_screenshot(request):
    tab_id = request.match_info["tab_id"]
    try:
        body = await request.json()
        user_id = body.get("userId", "")
        page = await _get_page(tab_id, user_id)
        if not page:
            return web.json_response({"error": f"Tab {tab_id} not found"}, status=404)
        screenshot_bytes = await page.screenshot(type="png", full_page=False)
        b64 = base64.b64encode(screenshot_bytes).decode("ascii")
        ts = str(int(time.time()))
        screenshot_path = f"/tmp/cloakbrowser_screenshot_{tab_id}_{ts}.png"
        with open(screenshot_path, "wb") as f:
            f.write(screenshot_bytes)
        return web.json_response({"screenshot": b64, "screenshot_path": screenshot_path})
    except Exception as e:
        logger.error(f"screenshot: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_close_session(request):
    user_id = request.match_info["user_id"]
    try:
        await _close_all_for_user(user_id)
        return web.json_response({"success": True, "closed": True})
    except Exception:
        return web.json_response({"success": True, "closed": True})


async def handle_list_tabs(request):
    async with _tabs_lock:
        tabs_info = [{"tabId": tid, "userId": t["user_id"]} for tid, t in _tabs.items()]
    return web.json_response({"tabs": tabs_info, "count": len(tabs_info)})


async def handle_close_tab(request):
    tab_id = request.match_info["tab_id"]
    await _close_tab(tab_id)
    return web.json_response({"success": True})


async def handle_evaluate(request):
    tab_id = request.match_info["tab_id"]
    try:
        body = await request.json()
        user_id = body.get("userId", "")
        expression = body.get("expression", "")
        page = await _get_page(tab_id, user_id)
        if not page:
            return web.json_response({"error": f"Tab {tab_id} not found"}, status=404)
        result = await page.evaluate(expression)
        try:
            return web.json_response({"result": result})
        except:
            return web.json_response({"result": str(result)})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def handle_get_images(request):
    tab_id = request.match_info["tab_id"]
    user_id = request.query.get("userId", "")
    try:
        page = await _get_page(tab_id, user_id)
        if not page:
            return web.json_response({"error": f"Tab {tab_id} not found"}, status=404)
        images = await page.evaluate("""() => 
            Array.from(document.querySelectorAll('img'))
                .map(img => ({src: img.src||'', alt: img.alt||''}))
                .filter(i => i.src)
        """)
        return web.json_response({"success": True, "images": images, "count": len(images)})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


def create_app():
    app = web.Application()
    app.router.add_get("/health", handle_health)
    app.router.add_post("/tabs", handle_create_tab)
    app.router.add_get("/tabs", handle_list_tabs)
    app.router.add_delete("/tabs/{tab_id}", handle_close_tab)
    app.router.add_post("/tabs/{tab_id}/navigate", handle_navigate)
    app.router.add_get("/tabs/{tab_id}/snapshot", handle_snapshot)
    app.router.add_post("/tabs/{tab_id}/click", handle_click)
    app.router.add_post("/tabs/{tab_id}/type", handle_type)
    app.router.add_post("/tabs/{tab_id}/scroll", handle_scroll)
    app.router.add_post("/tabs/{tab_id}/back", handle_back)
    app.router.add_post("/tabs/{tab_id}/press", handle_press)
    app.router.add_post("/tabs/{tab_id}/screenshot", handle_screenshot)
    app.router.add_post("/tabs/{tab_id}/evaluate", handle_evaluate)
    app.router.add_get("/tabs/{tab_id}/images", handle_get_images)
    app.router.add_delete("/sessions/{user_id}", handle_close_session)
    return app


async def main():
    port = int(os.environ.get("CLOAKBROWSER_PORT", "9377"))
    host = os.environ.get("CLOAKBROWSER_HOST", "127.0.0.1")
    
    print(f"Starting CloakBrowser server...", flush=True)
    
    # Pre-launch
    try:
        await get_browser()
    except Exception as e:
        print(f"Failed to launch CloakBrowser: {e}", flush=True)
        traceback.print_exc()
        sys.exit(1)
    
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    
    print(f"CloakBrowser server running on http://{host}:{port}", flush=True)
    print(f"__READY__", flush=True)
    
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
