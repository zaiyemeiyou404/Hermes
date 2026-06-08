# Weixin media download troubleshooting

Use this when a Weixin/WeChat user sends an image/voice/video and Hermes logs a download failure before the model ever sees the attachment.

## Symptom pattern

Gateway log contains something like:

```text
WARNING gateway.platforms.weixin: [Weixin] image download failed:
```

with **nothing after the colon**.

## What that usually means

In `gateway/platforms/weixin.py`, `_download_image()` catches any exception from `_download_and_decrypt_media()` and logs `str(exc)`. Some exception types — especially `asyncio.TimeoutError` / `TimeoutError` — stringify to an empty string. So an empty-suffix log line is a strong clue that the failure was a **timeout while fetching media**, not necessarily a decrypt error.

Relevant chain:

- `_download_image()`
- `_download_and_decrypt_media()`
- `_download_bytes()`
- `asyncio.wait_for(..., timeout=30)` for images

## Quick diagnosis steps

1. Confirm the failure happened before normal media handling:
   - Look for `image download failed` in `~/.hermes/logs/gateway.log`.
   - If the message was image-only and download failed, you may **not** see a later `inbound ... media=1` line because the attachment never made it into `media_paths`.
2. Confirm network/DNS to Weixin media hosts is generally alive:
   - `ilinkai.weixin.qq.com`
   - `mmbiz.qpic.cn`
   - `novac2c.cdn.weixin.qq.com`
3. Ask the user to retry with a small **original** image (not a forwarded image) and ideally include a short text caption so the event still reaches the agent even if media download fails again.
4. If you need definitive root cause, patch the logger to include `exc_info=True` or explicit exception-class logging around `_download_image()` / `_download_video()`.

## Likely causes (highest signal first)

1. Fetch timeout on the iLink/Weixin media URL.
2. Expired or slow media URL from the upstream bridge.
3. Large image or slow CDN response.
4. Forwarded/referenced media object with incompatible fetch parameters.
5. AES/decrypt mismatch (usually produces a non-empty error message, so less likely when the suffix is blank).

## Operator guidance

This issue is **not** evidence that Hermes vision is broken. The model never received the image; the failure happened in the Weixin adapter's media-fetch stage.