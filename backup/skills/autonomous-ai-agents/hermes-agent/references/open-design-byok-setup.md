# Open Design BYOK Configuration via localStorage

Open Design (nexu-io/open-design) supports BYOK (Bring Your Own Key) mode with any OpenAI-compatible API provider. When the settings UI is inaccessible via browser automation (React SPA click issues), BYOK can be configured by directly injecting the config into the browser's localStorage.

## When to Use

- Open Design is running (Docker/self-hosted) at a known URL
- The Settings dialog doesn't open or buttons don't respond via `browser_click`
- You have the API key and need to set BYOK mode programmatically

## Procedure

1. **Navigate** to the Open Design instance

2. **Check current config**:
```javascript
localStorage.getItem('open-design:config')
```

3. **Set BYOK mode** (via `browser_console` with JS expression):
```javascript
const config = JSON.parse(localStorage.getItem('open-design:config'));
config.mode = 'byok';
config.apiKey = 'sk-your-key-here';
config.baseUrl = 'https://api.deepseek.com';
config.model = 'deepseek-chat';
config.apiProtocol = 'openai';
config.apiProviderBaseUrl = 'https://api.deepseek.com';
localStorage.setItem('open-design:config', JSON.stringify(config));
```

4. **Refresh** the page to apply. The settings button should show `"OpenAI API · no agent selected"`.

5. **Verify** by creating a test project — the model should respond.

## Key Config Fields

| Field | Example | Notes |
|-------|---------|-------|
| `mode` | `"byok"` | Must be `"byok"`, not `"daemon"` |
| `apiKey` | `"sk-..."` | The raw API key |
| `baseUrl` | `"https://api.deepseek.com"` | Provider endpoint (OpenAI-compatible) |
| `model` | `"deepseek-chat"` | Model name the provider expects |
| `apiProtocol` | `"openai"` | `"openai"` for OpenAI-compatible, `"anthropic"` for Anthropic |
| `apiProviderBaseUrl` | `"https://api.deepseek.com"` | Same as `baseUrl` usually |
| `designSystemId` | `"default"` | Preserves design system selection |
| `onboardingCompleted` | `true` | Suppresses the onboarding dialog |

## Pitfalls

- **Browser tool may not trigger React SPA buttons.** The `browser_click` tool dispatches native DOM events, but React SPAs listen for synthetic events that don't always fire from programmatic clicks. If buttons don't respond, use localStorage injection instead.
- **Next.js SPA `type="submit"` buttons** in forms without `<form>` wrappers may not fire `onClick` handlers via `browser_click`. This is a React 19 / Next.js 16 behavior — buttons default to `type="submit"`, and without a wrapping form, the synthetic event may never dispatch.
- **localStorage is per-origin.** Make sure you're on the correct domain before injecting.
- **Config persists in browser storage** but will be reset if cookies/storage are cleared or on container restart (if running in Docker with ephemeral storage).
- **The `open-design:config` key** stores the full config object including non-BYTK fields (pet preferences, theme, notifications). Don't overwrite fields you don't intend to change — read existing config first, then modify.

## Verification

```bash
# After setting config and refreshing, check the button text
curl -s <open-design-url> | grep -o 'BYOK\|OpenAI API\|no agent selected'

# Or check localStorage via browser_console
localStorage.getItem('open-design:config')
# Should show: {"mode":"byok","apiKey":"sk-...",...}
```
