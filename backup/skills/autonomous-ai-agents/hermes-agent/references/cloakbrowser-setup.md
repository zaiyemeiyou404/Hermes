# CloakBrowser as Camofox Replacement

## Overview

[CloakBrowser](https://github.com/CloakHQ/CloakBrowser) is a stealth Chromium that patches **58 C++ source-level fingerprints** (canvas, WebGL, audio, fonts, GPU, screen, WebRTC, network timing, automation signals). It passes 30+ detection tests — reCAPTCHA 0.9, Cloudflare Turnstile, FingerprintJS. Unlike Camofox (Firefox-based, JS-injection patching), CloakBrowser modifies the Chromium binary itself.

Hermes Agent uses the `CAMOFOX_URL` env var to route browser operations through a REST API. CloakBrowser can **replace Camofox transparently** by providing a Camofox-compatible REST API server on the same port (9377).

## Install

```bash
pip install cloakbrowser playwright
python3 -m playwright install chromium
```

The stealth Chromium binary (~200MB) auto-downloads on first `launch()` / `launch_async()` call.

## Camofox-Compatible REST API Server

Script: `~/.hermes/scripts/cloakbrowser-server.py`

### Start

```bash
python3 ~/.hermes/scripts/cloakbrowser-server.py
```

Background:

```bash
python3 ~/.hermes/scripts/cloakbrowser-server.py &
```

### Architecture

```
Hermes browser_* tools
    → browser_camofox.py (checks CAMOFOX_URL)
    → HTTP POST/GET/DELETE to 127.0.0.1:9377
    → cloakbrowser-server.py (aiohttp)
        → cloakbrowser.launch_async() → stealth Chromium
        → generates accessibility tree snapshots via JS evaluation
```

### API Endpoints (Camofox-compatible)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/tabs` | POST | Create a new tab (returns `tabId`) |
| `/tabs/{id}` | DELETE | Close tab |
| `/tabs/{id}/navigate` | POST | Navigate to URL |
| `/tabs/{id}/snapshot` | GET | Accessibility tree snapshot |
| `/tabs/{id}/click` | POST | Click element by ref |
| `/tabs/{id}/type` | POST | Type text into element |
| `/tabs/{id}/scroll` | POST | Scroll page |
| `/tabs/{id}/back` | POST | Navigate back |
| `/tabs/{id}/press` | POST | Press keyboard key |
| `/tabs/{id}/screenshot` | POST | Take screenshot (base64) |
| `/tabs/{id}/evaluate` | POST | Execute JS in page context |
| `/tabs/{id}/images` | GET | Get image URLs on page |
| `/sessions/{userId}` | DELETE | Close all tabs for user |

### Configuration

Hermes picks up CloakBrowser automatically if you set `CAMOFOX_URL` in `~/.hermes/.env`:

```bash
echo 'CAMOFOX_URL=http://127.0.0.1:9377' >> ~/.hermes/.env
```

## Usage Patterns

### Python (sync - separate thread)

```python
from cloakbrowser import launch
browser = launch(headless=True)
page = browser.new_page()
page.goto("https://example.com")
print(page.evaluate("navigator.webdriver"))  # False
browser.close()
```

### Python (async - for aiohttp/asyncio servers)

```python
from cloakbrowser import launch_async
browser = await launch_async(headless=True)
page = await browser.new_page()
await page.goto("https://example.com")
wd = await page.evaluate("navigator.webdriver")  # False
await browser.close()
```

### JS / Node

```javascript
import { launch } from 'cloakbrowser';
const browser = await launch();
const page = await browser.newPage();
await page.goto('https://example.com');
await browser.close();
```

## Anti-Detection Verification

```bash
python3 -c "
from cloakbrowser import launch
browser = launch(headless=True)
page = browser.new_page()
page.goto('https://httpbin.org/headers')
print('webdriver:', page.evaluate('navigator.webdriver'))
browser.close()
"
# Expected: webdriver: False
```

## Known Limitations

- **WeChat mp.weixin.qq.com**: Shows "环境异常" even with CloakBrowser — this is an **IP geolocation issue** (Singapore VPS), not a browser fingerprint issue. CloakBrowser passes all standard detection tests (reCAPTCHA 0.9, Cloudflare Turnstile).
- **No VNC support**: Unlike Camofox, the CloakBrowser REST API server doesn't expose a VNC URL for live viewing.
- **Memory**: Each `new_context()` creates a persistent browser context. Close tabs when done to avoid accumulating contexts.
