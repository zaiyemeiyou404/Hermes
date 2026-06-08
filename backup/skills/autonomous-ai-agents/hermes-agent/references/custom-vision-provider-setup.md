# Custom Vision Provider Setup

When the main model provider doesn't support image inputs (vision), configure a
separate auxiliary vision model. This covers OpenAI-format proxy services such as
Chinese API aggregators that expose OpenAI-compatible endpoints.

## Probe: Find the Base URL

Given an `sk-...` API key, probe candidate endpoints:

```bash
# Probe candidates
for url in \
  "https://api.4sapi.com/v1/models" \
  "https://4sapi.com/v1/models" \
  "https://api.4s.one/v1/models"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $TOKEN" "$url" --connect-timeout 5)
  echo "$url → $code"
done
```

HTTP 200 = valid. HTTP 000 = unreachable. HTTP 401 = wrong key.

## Check Available Vision Models

```bash
curl -s "https://BASE_URL/v1/models" -H "Authorization: Bearer $TOKEN" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)['data']
for m in data:
    if any(k in m['id'].lower() for k in ['gpt-4o','gpt-4.1','claude-3','gemini','vision']):
        print(f'VISION: {m[\"id\"]}')
    else:
        print(f'  {m[\"id\"]}')
"
```

Recommended: `gpt-4o` or `gpt-4.1` (reliable vision, fast).

## Configure in Hermes

### 1. Add custom provider to `config.yaml`

```yaml
custom_providers:
  - name: 4sapi                    # any identifier
    base_url: https://4sapi.com/v1 # the OpenAI-compatible base
    api_key: sk-xxxxxxxx            # the API key
    model: gpt-4o                   # default model for this provider
```

### 2. Point auxiliary vision to it

```bash
hermes config set auxiliary.vision.provider "custom:4sapi"
hermes config set auxiliary.vision.model gpt-4o
```

Or edit `config.yaml` directly:

```yaml
auxiliary:
  vision:
    provider: custom:4sapi
    model: gpt-4o
```

### 3. Verify

Use `vision_analyze` on an image. If it returns successfully, the
config is correct. Common errors and their meaning:

| Error | Meaning |
|-------|---------|
| `unknown variant 'image_url', expected 'text'` | The provider doesn't support multimodal image inputs at the API level. Choose a different model or provider. |
| `exceeded Ns total timeout` | The request reached the model but response was slow. Model or network latency issue. |
| `401 Unauthorized` | API key invalid or expired. |

## Notes

- **Restart not always needed** — the auxiliary model config is read
  per-request, not cached at process start. Changes may apply without
  a session reset.
- **The key goes in `config.yaml`, not `.env`** — custom provider keys
  are stored in the provider definition block, not as an environment
  variable. This is different from first-party providers.
- **openai-codex / GPT-5.4 does NOT support `image_url`** — Codex OAuth
  only accepts text messages. You must route to a different provider
  for vision.
