# Hermes Auxiliary Vision Setup

When `vision_analyze` fails with `unknown variant 'image_url', expected 'text'` or `Codex auxiliary Responses stream exceeded timeout`, the auxiliary vision model is not configured for the current provider.

## Root Cause

`vision_analyze` uses an **auxiliary model** (`auxiliary.vision`) for image analysis, separate from the main conversation model. If unconfigured, it falls back to the main model/provider — but many providers (openai-codex, DeepSeek) don't support `image_url` content type in their API.

## Solution: Custom Vision Provider

### 1. Add a custom provider entry in `~/.hermes/config.yaml`

The format is a YAML list under `custom_providers:`:

```yaml
custom_providers:
- name: 4sapi
  base_url: https://4sapi.com/v1
  api_key: sk-xxxxxxxxxxxxxxxxxxx
  model: gpt-4o
```

The provider name (`4sapi` here) can be anything. `base_url` must be an OpenAI-compatible API endpoint.

### 2. Configure auxiliary vision to use it

```bash
hermes config set auxiliary.vision.provider "custom:4sapi"
hermes config set auxiliary.vision.model gpt-4o
```

The provider prefix `custom:` tells Hermes to look it up in the `custom_providers` list.

### 3. Verify

Run `vision_analyze(image_url="/path/to/image.jpg")`. If it returns analysis text, vision is working.

## Alternative Providers

| Provider | Auth | Free? | Config |
|----------|------|-------|--------|
| OpenRouter | `OPENROUTER_API_KEY` | Trial | `auxiliary.vision.provider: openrouter`, model: `gpt-4o` |
| Google Gemini | `GOOGLE_API_KEY` | ✅ Free (1500/d) | `auxiliary.vision.provider: google`, model: `gemini-2.0-flash` |
| OpenAI direct | `OPENAI_API_KEY` | Paid | `auxiliary.vision.provider: openai`, model: `gpt-4o` |
| Custom (like 4sapi) | API key | Varies | `auxiliary.vision.provider: custom:<name>` |

## Pitfalls

- **Codex OAuth (openai-codex) does NOT work for vision** — its API doesn't accept `image_url` content type, even with gpt-4o or gpt-5.4. Requests go through but timeout at 120s.
- **Key in `.env` must be set BEFORE the process starts** — Hermes snapshots env at launch. If you add a key to `.env` while Hermes is running, restart it.
- **`custom_providers` is a YAML list of objects** — each entry has `name`, `base_url`, `api_key`, `model`. Indentation matters (two-space indent after the hyphen).
- **YAML syntax errors in config.yaml break tool loading** — common culprit is `platform_toolsets` section: nested list items must be under the correct platform key, not at the parent indentation level.

## Discovery Method — Finding a Custom Provider's Base URL

```bash
for url in "https://4sapi.com/v1/models" "https://api.4sapi.com/v1/models"; do
  curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $KEY" "$url" --connect-timeout 5
done
# HTTP 200 = found
```

Then list available models:
```bash
curl -s "$FOUND_URL" -H "Authorization: Bearer $KEY" | python3 -c "
import sys,json; d=json.load(sys.stdin)
for m in d.get('data',[]):
    if any(k in m['id'].lower() for k in ['vision','gpt-4o','gpt-4.1','gemini','claude-3','gpt-4-v']):
        print(m['id'])
"