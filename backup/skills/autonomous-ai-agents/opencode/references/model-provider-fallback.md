# OpenCode Model & Provider Fallback Patterns

## Free Models (No Auth Required)

When no provider credentials are configured (`opencode providers list` shows 0 credentials), use OpenCode-hosted free models:

```
opencode/deepseek-v4-flash-free
opencode/mimo-v2.5-free
opencode/minimax-m3-free
opencode/nemotron-3-super-free
opencode/big-pickle
```

List: `opencode models`

These work immediately without any API key setup. Suitable for testing, small code tasks, and smoke checks. May be slower than direct provider models.

## Provider Auth via CLI (Fails — Use Env Var Instead)

`opencode providers login <provider>` may fail with "fetch() URL is invalid" — this command expects a login URL, not a provider name.

**Working auth methods:**
1. **Environment variables** — export `DEEPSEEK_API_KEY=sk-...` in the shell before running `opencode run`. OpenCode auto-detects common provider env vars.
2. **Browser login** — run `opencode` (TUI), then use command palette to log in interactively.

## Model Name Issues

| What you write | What happens |
|---|---|
| `--model deepseek` | "Invalid model format" — falls back to auto-detect |
| `--model deepseek/deepseek-chat` | Works only if DeepSeek provider is configured |
| `--model opencode/deepseek-v4-flash-free` | Works without auth (free model) |

**Key failure pattern**: `--model deepseek/deepseek-chat` fails with "Model not found: deepseek/deepseek-chat" even when `DEEPSEEK_API_KEY` is exported. This means the provider is not registered in OpenCode's auth store. The env var must be discoverable during TUI login OR the provider must be configured in `~/.config/opencode/opencode.jsonc`.

## Git Push After OpenCode Commits

OpenCode commits locally but push fails when the remote is HTTPS and no credentials are configured. Common scenario:

```
$ git commit -m 'fix: ...'
[opencode/hermes-improvements e7acc20] fix: ...
$ git push
fatal: could not read Username for 'https://github.com': No such device or address
```

**Solutions (ordered by preference):**
1. Convert remote to SSH — only if SSH key is configured for GitHub
2. Use `git remote set-url origin https://<token>@github.com/user/repo.git` — requires a GitHub personal access token
3. Ask the user for credentials — they may have a token saved elsewhere

## Prompt File Pattern (`.opencode-instructions.md`)

For complex tasks, write instructions to a file in the repo and reference them from the opencode run command:

```bash
# File: .opencode-instructions.md (checked into repo root)
# Contains: detailed technical steps, code snippets, API references
opencode run "按 .opencode-instructions.md 修改 classtable_server.py，只改这一个文件，改完提交推送"
```

Benefits:
- Instructions survive across sessions
- Can be committed alongside the code changes
- Avoids shell escaping issues with backticks/special chars
- Easy to iterate and refine
