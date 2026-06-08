# Codex auth + reconnect troubleshooting

## Identify which auth path is failing

Do not blur these together:

1. **Hermes provider auth** — `hermes auth add openai-codex`, stored in `~/.hermes/auth.json`
2. **Standalone Codex CLI auth** — `codex login`, often stored in `~/.codex/auth.json`
3. **Editor/plugin session auth** — may reuse CLI auth but can fail separately due to child-process lifecycle issues

A missing `OPENAI_API_KEY` does **not** prove Codex is unauthenticated if OAuth auth files exist.

## Windows-first checks

Use PowerShell, not Unix process commands.

```powershell
where.exe codex
codex --version
Test-Path "$env:USERPROFILE\.codex\auth.json"
```

If the plugin is wedged or repeatedly reconnecting, clear stale processes and auth state before retrying:

```powershell
taskkill /F /IM codex.exe
taskkill /F /IM node.exe
Remove-Item "$env:USERPROFILE\.codex\auth.json" -Force -ErrorAction SilentlyContinue
codex login
```

## OAuth browser login returns 403

If browser login reaches OpenAI and returns **403**, prioritize **region / exit-IP / proxy reputation** over password debugging.

High-probability causes:
- Current proxy region is not accepted for the login flow
- Exit IP is low-reputation / datacenter / widely shared
- Embedded plugin browser is blocked while a normal system browser may work
- Cookie state is polluted from prior failed attempts

Recommended recovery order:

1. Switch proxy exit away from the failing region; prefer trying **US**, **Japan**, or **Singapore** next.
2. **Verify the actual outbound country before retrying login.** In practice, users often have Clash/TUN enabled while the real egress is still their local ISP country. Check a live IP-echo site such as `https://ipinfo.io`, `https://ifconfig.me`, or `https://ip.sb`, or verify the proxy app's own home/status page. If the detected exit still shows the unsupported country (for example China Unicom / Asia/Shanghai), treat the proxy chain as not actually switched yet.
3. Kill stale Codex / Node processes.
4. Remove CLI auth state (`~/.codex/auth.json` on the local machine).
5. Re-run `codex login`.
6. If a URL is shown, open it in the **system browser** (Chrome/Edge), ideally an incognito window, instead of relying on an embedded editor browser.

Interpretation guideline: for user triage, treat `403` during OAuth login as "current region or exit IP not being accepted" unless stronger evidence points elsewhere.

## When a proxy app looks healthy but OAuth still says region unsupported

Do not assume that "TUN on" or "system proxy on" means Codex is actually exiting through the intended country.

Useful triage sequence:

1. In the proxy app, switch to a **specific node** rather than an auto/fallback group.
2. Prefer a mainstream region first: **US / Japan / Singapore**.
3. Temporarily disable extra routing layers (for example, leave system proxy on but disable TUN) if you suspect split-routing confusion.
4. Re-check the live outbound IP/country.
5. Retry `codex login` only after the exit country is confirmed.

If the proxy app's own status/home page still reports the user's local ISP/country, the Codex 403 is usually downstream of the proxy setup rather than a Codex account problem.

## Plugin/UI repeatedly shows reconnecting + child process timeout

Typical message pattern:
- `Reconnecting... N/5`
- `timeout waiting for child process to exit`

This usually means the UI is trying to relaunch or reconnect to Codex, but the old child process did not exit cleanly. Prioritize local process cleanup over account debugging.

User-facing explanation:
- The login/session failure may be secondary; the immediate problem is a stuck background process.
- The current session is likely unhealthy even if the UI still renders.

First recovery steps:
1. Close the current panel/editor session.
2. Kill residual `codex` / `node` processes.
3. Clear local CLI auth state only if relaunch still fails.
4. Reopen the editor and retry login.

## Use API key as a fallback path

If OAuth is blocked but the user has an API key, test whether Codex can run via environment variable instead of browser login.

Windows PowerShell:

```powershell
setx OPENAI_API_KEY "<key>"
```

Open a fresh shell, then test:

```powershell
codex exec "say hi"
```

Use this as a practical workaround, not proof that the OAuth issue is resolved.
