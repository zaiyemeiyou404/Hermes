# CloakBrowser REST API Server

Camofox-compatible local browser backend using CloakBrowser (stealth Chromium).

## Architecture

```
Browser tools  →  HTTP REST API  →  CloakBrowser  →  Stealth Chromium
(Hermes agent)     (port 9377)       (Playwright)     (58 C++ patches)
```

The server wraps CloakBrowser's `launch_async()` with a Camofox-compatible REST API so Hermes Agent can use it without code changes. Hermes's `tools/browser_camofox.py` module sends HTTP requests to port 9377 exactly the same way it did for Camofox.

## Server File

`~/.hermes/scripts/cloakbrowser-server.py`

Built with:
- **aiohttp** — async HTTP server (Python)
- **playwright.async_api** — async browser control
- **cloakbrowser.launch_async** — stealth Chromium with anti-detection

## API Endpoints

All endpoints match the Camofox REST API schema exactly.

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Server status + version |
| POST | `/tabs` | Create browser tab (`{userId, url, sessionKey}`) |
| GET | `/tabs` | List active tabs |
| DELETE | `/tabs/{tabId}` | Close a tab |
| POST | `/tabs/{tabId}/navigate` | Navigate to URL |
| GET | `/tabs/{tabId}/snapshot` | Get accessibility tree snapshot |
| POST | `/tabs/{tabId}/click` | Click element by ref |
| POST | `/tabs/{tabId}/type` | Type text into element |
| POST | `/tabs/{tabId}/scroll` | Scroll page (up/down) |
| POST | `/tabs/{tabId}/back` | Go back in history |
| POST | `/tabs/{tabId}/press` | Press keyboard key |
| POST | `/tabs/{tabId}/screenshot` | Take page screenshot |
| POST | `/tabs/{tabId}/evaluate` | Evaluate JavaScript |
| GET | `/tabs/{tabId}/images` | Get page images |
| DELETE | `/sessions/{userId}` | Close user session |

## Snapshot Format

The accessibility tree uses the same indented format as Camofox:

```
- heading "Example Domain" [level=1] [e3]
- paragraph: This domain is for use in documentation...
- link "Learn more" [e6]:
  - /url: https://iana.org/domains/example
  - text: Learn more
- button "Submit" [e12]
- textbox "Search" [e15]:
  - : "query text"
```

Element refs (`[e1]`, `[e2]`, ...) are auto-generated from DOM traversal and used by `click`/`type`/`press` endpoints.

## Operational Commands

```bash
# Start (background)
python3 ~/.hermes/scripts/cloakbrowser-server.py &

# Health check
curl -s http://127.0.0.1:9377/health

# Check active tabs
curl -s http://127.0.0.1:9377/tabs

# Stop
pkill -f cloakbrowser-server.py

# Start on custom port
CLOAKBROWSER_PORT=9378 python3 ~/.hermes/scripts/cloakbrowser-server.py &
```

## Hermes Configuration

In `~/.hermes/.env`:
```bash
CAMOFOX_URL=http://127.0.0.1:9377
```

The `CAMOFOX_URL` env var is used even for CloakBrowser — Hermes's `browser_camofox.py` module reads it regardless of what's running on the other end.

## Quick Verification

```bash
# 1. Start server (if not running)
python3 ~/.hermes/scripts/cloakbrowser-server.py &

# 2. Create a tab
curl -s -X POST http://127.0.0.1:9377/tabs \
  -H 'Content-Type: application/json' \
  -d '{"userId":"test","url":"about:blank"}'

# 3. Navigate
curl -s -X POST http://127.0.0.1:9377/tabs/<tabId>/navigate \
  -H 'Content-Type: application/json' \
  -d '{"userId":"test","url":"https://example.com"}'

# 4. Snapshot
curl -s "http://127.0.0.1:9377/tabs/<tabId>/snapshot?userId=test"
```

## CloakBrowser Binary

- First launch downloads stealth Chromium to `~/.cache/cloakbrowser/` (~200MB)
- Auto-update checks run in background
- `navigator.webdriver` returns `false` at the C++ level (58 patches)
- reCAPTCHA v3 score: 0.9 (human-level)

## Comparing CloakBrowser vs Camofox

| Capability | Camofox (old) | CloakBrowser (new) |
|------------|--------------|-------------------|
| Browser engine | Firefox (Camoufox) | Chromium (patched) |
| Anti-detection | JS injection | C++ source patches |
| `navigator.webdriver` | false | false |
| reCAPTCHA v3 | ~0.1 | **0.9** |
| Humanize behavior | Basic | `humanize=True` (Bezier, per-char) |
| Binary management | Manual npm install | Auto-download + auto-update |
| Playwright compat | No (REST only) | Native through launch_async |
| Ecosystem | Proprietary | MIT, 19.6k stars |

## Known Issues

- **WeChat (mp.weixin.qq.com) still shows "环境异常"** — this is IP geolocation detection, not browser fingerprinting. Requires a domestic China proxy.
- **First launch is slow** (~200MB download + binary extraction)
- **Memory:** Each browser context (tab) uses ~100-200MB RAM. Clean up with `DELETE /sessions/{userId}`.
- **Concurrent access:** One shared browser instance. Multiple tabs share the same process. For isolated sessions, use Hermes's managed persistence via `browser.camofox.managed_persistence` in config.yaml.
