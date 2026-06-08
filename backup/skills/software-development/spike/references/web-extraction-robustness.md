# Robust web extraction pattern for throwaway spikes

Use this when the user wants a quick script to fetch/extract content from a third-party page, but wants it to be *stable enough to diagnose failures* rather than crash on the first mismatch.

## Pattern

1. Keep the script to one file with a direct CLI entrypoint.
2. Prefer minimal dependencies. For Python, `requests` plus stdlib HTML parsing/regex is often enough for a spike.
3. Set browser-like headers (`User-Agent`, `Accept`, `Accept-Language`) to reduce low-value blocks.
4. Do not assume the fetched page is the target page. Always classify the response into a small set of page types.
5. Return structured JSON so both success and failure are actionable.

Suggested result shape:

```json
{
  "ok": true,
  "title": "...",
  "text_content": "...",
  "html_content": "...",
  "final_url": "...",
  "status_code": 200,
  "page_type": "article",
  "error": null
}
```

## WeChat-specific notes from session

Observed useful detection signals for WeChat anti-bot / verification pages:

- `环境异常`
- `完成验证后即可继续访问`
- `wappoc_appmsgcaptcha`
- `去验证`
- `secitptpage/verify`

Observed article container IDs worth trying in order:

- `js_content`
- `img-content`
- `activity-detail`

Useful title fallbacks:

- `<h1>`
- `meta[property="og:title"]`
- `meta[name="twitter:title"]`
- `<title>`

## Failure mode to avoid

The naive version was:

```python
title = soup.find('h1').text.strip()
content = soup.find('div', {'id': 'js_content'}).decode_contents()
```

This crashes when the response is a verification page or the expected DOM nodes are missing.

## Better behavior

- Detect verification pages explicitly.
- If content container is missing, return `page_type="unknown_page"` with an explanatory `error`.
- If the request fails, return `page_type="request_error"`.
- Offer `--text-only` for direct terminal use when extraction succeeds.

## Why this belongs in a spike

This pattern is ideal for quick feasibility work: it gives the user a useful answer even when extraction fails, and it avoids turning a disposable script into a dependency-management project.
