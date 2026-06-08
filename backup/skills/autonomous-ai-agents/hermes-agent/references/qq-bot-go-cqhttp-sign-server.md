# go-cqhttp + unidbg-fetch-qsign Sign Server Setup

QQ bot integration for Hermes environments using go-cqhttp with a signature server.

## Architecture

```
go-cqhttp (host)  ──sign request──>  unidbg-fetch-qsign (Docker, port 8800)
    │                                      │
    └──> QQ server (Tencent backend)       └── txlib protocol files
```

## Components

| Component | Role | Port |
|-----------|------|------|
| **go-cqhttp** v1.2.0 | QQ bot client (Android Pad/MacOS protocol) | HTTP 5700 (API) |
| **unidbg-fetch-qsign** 1.1.9 | ARM emulator for QQ protocol signing | 8800 (host) → 80 (container) |
| **txlib** | Protocol version files inside sign server container | — |

## Setup Steps

### 1. Install go-cqhttp

```bash
mkdir -p /home/ubuntu/gocqhttp && cd /home/ubuntu/gocqhttp
wget https://github.com/Mrs4s/go-cqhttp/releases/download/v1.2.0/go-cqhttp_1.2.0_linux_amd64.deb
# Or download binary directly
chmod +x go-cqhttp
```

### 2. Configure go-cqhttp (`config.yml`)

Key sections:

```yaml
account:
  uin: <QQ_NUMBER>
  password: '<PASSWORD>'
  encrypt: false
  sign-servers:
    - url: 'http://172.17.0.1:8800'  # Docker bridge -> qsign container
      key: '114514'
      authorization: '-'
  auto-register: true                 # When sign server config has auto_register: false, you can set this...

servers:
  - http:
      host: 0.0.0.0
      port: 5700
```

### 3. Configure device protocol (`device.json`)

The `protocol` field in `device.json` **must match** available txlib versions in the sign server.

| device.json protocol | go-cqhttp shows | Works with qsign 8.9.x? |
|---------------------|-----------------|------------------------|
| `6` | Android Pad 8.9.63.11390 | ✅ (if 8.9.x txlib present) |
| `2` | Android Watch | ❌ (needs different txlib) |
| `3` | MacOS 5.8.9 | ❌ (qsign has only Android) |

Check available protocols in the sign server container:
```bash
docker exec <container-id> ls /app/txlib/
# e.g. 3.5.1  3.5.2  8.9.63  8.9.68  8.9.71  8.9.73  8.9.80  config.json
```

### 4. Start sign server (Docker)

```bash
docker run -d --name qsign \
  -p 8800:80 \
  -v /path/to/txlib:/app/txlib \
  bennettwu/qsign-server:latest
```

## Common Pitfalls

### "encoding/hex: invalid byte: U+002F '/'"

**Root cause:** Sign server returns `"Uin is not registered."` — the QQ number hasn't registered itself with the sign server.

**Fix:** Set `auto_register: true` in the sign server's `config.json` and restart:

```bash
docker exec <container-id> sed -i 's/"auto_register": false/"auto_register": true/' /app/txlib/config.json
docker restart <container-id>
```

Or verify: `curl http://127.0.0.1:8800/custom_energy?data=...` returns `"Uin is not registered."`.

### Protocol version mismatch

If the sign server only has Android txlib (8.9.63) but go-cqhttp uses MacOS protocol (3), signing fails silently. Match the device.json protocol to what's available in the container.

### Captcha / Slider Verification

Even with correct signing, the QQ account may still require captcha. The go-cqhttp output shows:

```
[WARNING]: 登录需要滑条验证码, 请验证后重试.
[WARNING]: 请前往该地址验证 -> https://ti.qq.com/safe/tools/captcha/sms-verify-login?...
```

**Headless browser limitation:** Tencent's captcha detects headless browsers (Playwright/Chrome) and stays stuck at "安全检测中". Workarounds:

1. **User provides ticket** — send the captcha URL to the user. After they complete the slider on their phone/PC, have them check the URL bar for `ticket=xxxxx` parameter and paste it back. Go-cqhttp asks to choose between:
   - `1` — auto-submit (waits for ticket via some mechanism)
   - `2` — manual submit (user pastes the ticket)

2. **SMS verification** — some QQ accounts support SMS code instead.

### Lock files from crashed runs

If go-cqhttp crashed, stale LOCK files block restart:

```bash
rm -f data/leveldb-v3/LOCK data/images/LOCK data/videos/LOCK
```

## Verification

After successful setup, check:

1. **Sign server healthy:** `curl http://127.0.0.1:8800/` → `"code": 0`
2. **Token updated:** go-cqhttp logs show `"token 已更新"` (means auto_register works)
3. **go-cqhttp API:** `curl http://127.0.0.1:5700/` → should respond

## Useful Commands

```bash
# Check sign server status
curl -s http://127.0.0.1:8800/ | python3 -m json.tool

# Check available protocols inside container
docker exec <qsign-container> ls /app/txlib/

# Check sign server config
docker exec <qsign-container> cat /app/txlib/config.json

# Kill stale go-cqhttp lock files
rm -f /home/ubuntu/gocqhttp/data/leveldb-v3/LOCK /home/ubuntu/gocqhttp/data/images/LOCK /home/ubuntu/gocqhttp/data/videos/LOCK

# Run go-cqhttp with auto-submit captcha (sends "1")
echo -e "1" | cd /home/ubuntu/gocqhttp && ./go-cqhttp

# Check listening ports
ss -tlnp | grep -E '8800|5700'
```
