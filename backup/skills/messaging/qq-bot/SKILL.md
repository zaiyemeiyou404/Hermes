---
name: qq-bot
description: "Deploy and operate QQ protocol bots using go-cqhttp with unidbg-fetch-qsign signature server. Covers installation, sign server Docker setup, protocol matching, auto-register fix, and captcha handling strategies."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [qq, go-cqhttp, bot, sign-server, captcha, messaging]
    related_skills: [web-service-hosting, agent-task-tracking]
---

# QQ Bot Deployment (go-cqhttp)

## Overview

Deploy a QQ bot using **go-cqhttp** (v1.2.0) with **unidbg-fetch-qsign** (Docker-based signature server). The sign server provides protocol signatures needed to authenticate with Tencent's QQ servers.

## Architecture

```
┌──────────────┐     HTTP/WS      ┌──────────────┐     TCP      ┌──────────────┐
│  Your App    │ ◄──────────────► │  go-cqhttp   │ ◄──────────► │  QQ Servers   │
│  (Hermes)    │    (API port     │  (v1.2.0)    │   (QQ proto) │  (Tencent)    │
└──────────────┘     5700)        └──────┬───────┘              └──────────────┘
                                         │
                                    HTTP │ sign requests
                                         ▼
                               ┌──────────────────┐
                               │  Sign Server      │
                               │  (unidbg-fetch-   │
                               │   qsign, Docker)  │
                               │  port 8800        │
                               └──────────────────┘
```

## Installation

### 1. go-cqhttp binary

Download the latest release:
```bash
mkdir -p /home/ubuntu/gocqhttp && cd /home/ubuntu/gocqhttp
wget https://github.com/Mrs4s/go-cqhttp/releases/download/v1.2.0/go-cqhttp_linux_amd64.tar.gz
tar xzf go-cqhttp_linux_amd64.tar.gz
rm go-cqhttp_linux_amd64.tar.gz
```

### 2. unidbg-fetch-qsign Docker container

```bash
docker run -d --name qsign \
  -p 8800:80 \
  -e COUNT=10 \
  bennettwu/qsign-server:latest
```

The sign server bundles Android protocol versions in `/app/txlib/` (e.g., 8.9.63, 8.9.68, 8.9.71, etc.).

## Configuration

### go-cqhttp config.yml

```yaml
account:
  uin: <YOUR_QQ_NUMBER>     # e.g. 2678646826
  password: '<YOUR_PASSWORD>'
  encrypt: false
  use-sso-address: true
  sign-servers:
    - url: 'http://<SIGN_SERVER_HOST>:8800'
      key: '114514'
      authorization: '-'
    - url: '-'
      key: '114514'
      authorization: '-'
```

Key points:
- Two sign-server entries: one real, one fallback with `url: '-'`
- `172.17.0.1:8800` works if sign server is on Docker bridge (host network from container's perspective)
- `127.0.0.1:8800` works if go-cqhttp runs on host

### device.json

Generated automatically on first run, but must be configured for protocol version:

```json
{
  "protocol": 6,
  "display": "MIRAI.204477.001",
  ...
}
```

## Protocol Matching (Critical)

**The sign server and go-cqhttp MUST use matching protocols.**

- Check sign server's available protocols: `docker exec <container> ls /app/txlib/`
- Check sign server's current config: `docker exec <container> cat /app/txlib/config.json`
- Set `device.json` protocol field to match:
  - `6` → Android Pad (matches 8.9.x sign server versions) — **most compatible with unidbg-fetch-qsign**
  - `1` → Android Phone (old)
  - `2` → Android Watch
  - `3` → MacOS
  - `5` → iPad

Protocol 6 (Android Pad 8.9.63) works with the default bundled sign server.

**Don't use protocol 3 (MacOS) with an Android-only sign server** — T544 sign requests will fail with garbage output.

## The auto_register Fix

**This is the #1 gotcha.** If go-cqhttp logs show:
```
获取T544 sign时出现错误: encoding/hex: invalid byte: U+002F '/'
```

The root cause is usually **"Uin is not registered"** — the sign server rejects unknown UINs because `auto_register: false` by default.

**Fix:**
```bash
docker exec <container> sed -i 's/"auto_register": false/"auto_register": true/' /app/txlib/config.json
docker restart <container>
```

Verify the fix took effect by checking go-cqhttp logs for `token 已更新` (successful token means signature works).

## Running go-cqhttp

### First run — test connectivity
```bash
cd /home/ubuntu/gocqhttp && timeout 40 ./go-cqhttp 2>&1
```

### Background process
```bash
cd /home/ubuntu/gocqhttp && ./go-cqhttp &
```

### Clear stale locks (prevent "cache image db failed" errors)
```bash
rm -f data/leveldb-v3/LOCK data/images/LOCK data/videos/LOCK
```

## Captcha Handling

After signature works, go-cqhttp will request **slider captcha verification** (腾讯滑块验证码).

### Critical: captcha page behavior

The captcha page at `ti.qq.com/safe/tools/captcha/sms-verify-login` uses the **mqq JS bridge** — it only renders properly in QQ's built-in browser. Behavior by environment:

| Browser | Behavior |
|---------|----------|
| QQ in-app browser (click link in chat) | Page exits/crashes back to QQ — ticket is consumed by native QQ app, NOT returned to browser |
| WeChat in-app browser | White screen after slider — WeChat blocks QQ's JS bridge |
| Phone Chrome/Safari | White screen — Tencent blocks external browsers |
| Desktop Chrome/Edge | White screen — detected as non-QQ environment |
| Headless (Playwright/Camofox) | Stuck at "安全检测中" — detected as automated browser |

**Bottom line: The captcha URL cannot be solved by the user through any browser interface.** The ticket is consumed by QQ's native app and never reaches the browser URL bar.

### Strategy 1: go-cqhttp + password + captcha (low success rate)
1. Start go-cqhttp, it prints a captcha URL
2. Ask user to open the URL — explain that most browsers will show white
3. If it somehow works, paste the `ticket=xxxxx` value

### Strategy 2: go-cqhttp auto-submit (headless only)
Select option `1` when prompted. Works on a non-headless system with a real display.

### Strategy 3: SMS verification (rarely available)
Some QQ accounts allow SMS code instead of slider. Check the captcha page for "发送短信验证码" option, but note this also requires the captcha page to render, which it won't in external browsers.

### Strategy 5: Automated captcha solving via undetected_chromedriver ⭐ MOST PROMISING

Unlike headless Playwright/Camofox, **undetected_chromedriver** can render the Tencent captcha page (using `--headless=new` + `--disable-blink-features=AutomationControlled`). The captcha appears as a **"Select the matching image"** challenge (not a slider), with 6 images in a 2×3 grid.

**Prerequisites:**
```bash
pip install undetected-chromedriver
```

**Setup:**
```python
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

options = uc.ChromeOptions()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1920,1080')
options.add_argument('--disable-blink-features=AutomationControlled')
options.binary_location = '/home/ubuntu/.cloakbrowser/chromium-146.0.7680.177.5/chrome'

driver = uc.Chrome(options=options, version_main=146, driver_executable_path=None)
driver.get(CAPTCHA_URL)

# Switch to captcha iframe
iframe = driver.find_element(By.CSS_SELECTOR, 'iframe[src*="captcha"]')
driver.switch_to.frame(iframe)
```

**Captcha characteristics:**
- Shows "选择最符合描述的图片" with a target word in quotes (e.g., "一只孔雀", "黑色杯子", "一束向日葵")
- 6 images in a 2×3 grid rendered on `<canvas>` elements
- Images are AI-generated (Hunyuan) — realistic objects like flowers, animals, vases
- "确定" (OK) button at bottom-right
- "换一组" (Refresh) and "我不会" (I can't solve) buttons available

**Solving flow:**
1. Get fresh captcha URL from go-cqhttp (each run generates a unique one)
2. Open in undetected_chromedriver
3. Take screenshot and analyze with vision model to identify target & image position
4. Click the matching image using ActionChains or JavaScript
5. Click "确定" button
6. Wait for page redirect — ticket may come via:
   - URL parameter `ticket=xxxxx`
   - `window.__CAPTCHA_TICKET` JS variable (injected via postMessage listener)
   - Page source text matching `ticket["']?\s*[:=]\s*["']([^"']+)["'}]`
7. Feed ticket back to go-cqhttp via stdin

**Critical timing:** The captcha URL expires in ~2 minutes. The ENTIRE flow (get URL → open browser → screenshot → analyze → click → OK → capture ticket) must complete within this window.

**Manually estimating click positions (per-viewport, within iframe):**
- Image grid: 3 columns × 2 rows
- Each image ~80×80px
- R0C0 (top-left) ≈ (860, 80)
- R0C1 ≈ (945, 80)
- R0C2 ≈ (1030, 80)
- R1C0 ≈ (860, 170)
- R1C1 ≈ (945, 170)
- R1C2 ≈ (1030, 170)
- "确定" button ≈ (1048, 272)
- **Best practice:** Use `driver.find_elements(By.TAG_NAME, 'canvas')` to get exact positions, then calculate centers for clicking.

**Troubleshooting:**
- If `actions.move_by_offset().click()` doesn't select the right image, the coordinates are relative to the iframe viewport — adjust by checking the canvas positions.
- After clicking, verify a blue checkmark appears on the selected image.
- If clicking OK results in a blank page, the captcha likely expired — restart with a fresh URL.
- `options.binary_location` must point to an actual Chrome/Chromium binary. The cloakbrowser chromium works (`/home/ubuntu/.cloakbrowser/chromium-*/chrome`).
go-cqhttp v1.2.0 removed QR login for all protocols. **Use icqq instead** — it supports QR via MacOS/Watch protocol:

```bash
mkdir -p /home/ubuntu/qqbot && cd /home/ubuntu/qqbot
npm init -y && npm install icqq
```

Create `login_qr.js`:
```js
const { Client } = require('icqq');
const client = new Client({
  platform: 3,  // 3=MacOS/Watch — supports QR login
  log_level: 'info',
  sign_api: 'http://127.0.0.1:8800',
  data_dir: './data',
});
client.on('system.login.qrcode', function (e) {
  require('fs').writeFileSync('qrcode.png', e.image);
  console.log('二维码已保存到 qrcode.png, 大小:', e.image.length);
});
client.on('system.online', () => { console.log('登录成功！'); process.exit(0); });
client.login(<QQ_NUMBER>);  // no password → forces QR mode
```

Run:
```bash
node login_qr.js
```

This prints a text QR to terminal AND saves `data/qrcode.png`. Send the image to the user via WeChat with:
```
MEDIA:/path/to/qqbot/data/qrcode.png
```

User scans with **手机QQ → 扫一扫**.

### Fresh ticket per attempt
Each go-cqhttp/icqq run generates a new captcha URL with unique `cap_cd` and `sid` parameters. If a URL expires, restart to get a fresh one.

## QR Code Delivery via WeChat

When a QR code PNG is generated (by icqq or any tool):
1. The file is at `data/qrcode.png` in the bot working directory
2. Send it via WeChat with `MEDIA:/absolute/path/to/qrcode.png`
3. The image arrives as a native photo in the chat — user can long-press → scan
4. The user's phone QQ scan reads the QR and completes login

The QR code has a ~120 second timeout. If it expires, restart the script to generate a new one.

## Verification

**Check sign server is healthy:**
```bash
curl -s http://127.0.0.1:8800/  # Should return {"code": 0, "msg": "IAA ..."}
```

**Check go-cqhttp logs for:**
- ✅ `token 已更新` — signature working
- ✅ `使用协议: Android Pad 8.9.63.11390` — protocol matched
- ❌ `获取T544 sign时出现错误` — sign server issue (usually auto_register)
- ❌ `当前协议不支持二维码登录` — QR login removed from modern go-cqhttp

## Pitfalls

1. **Sign server with auto_register=false by default** — must be set to true or UIN registration fails silently.
2. **Protocol mismatch** — sign server only has Android txlib; go-cqhttp must use an Android protocol.
3. **No QR code login** — go-cqhttp v1.2.0 removed QR login for most protocols. Password + captcha is the only path.
4. **WeChat in-app browser blocks captcha** — the captcha page shows white after slider. Use QQ app or system browser instead.
5. **Stale LOCK files** after previous crash — remove `data/*/LOCK` before restart.
6. **172.17.0.1 vs 127.0.0.1** — if go-cqhttp runs on host, use `127.0.0.1:8800`. If inside a container, use the Docker gateway IP.
7. **captcha.gtimg.com renders in iframe** — the actual captcha element is in an iframe, making browser automation more complex.
8. **captcha URL cannot return ticket to external browser** — the `sms-verify-login` page calls native QQ `mqq.invoke('CAPTCHA', 'onVerifyCAPTCHA')` which only works in QQ's in-app WebView. The ticket never appears in the URL bar.
9. **go-cqhttp lacks QR login** — all protocols in v1.2.0 reject QR login. Use icqq (Node.js) for QR login instead.
10. **icqq sign_api config** — icqq supports the same unidbg-fetch-qsign server via `sign_api: 'http://127.0.0.1:8800'` in client config. Works with auto_register=true on the sign server.

## Linked Files

- `references/sign-server-config.md` — full sign server config.json with explanations
