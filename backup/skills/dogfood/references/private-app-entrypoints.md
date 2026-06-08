# Private / Self-hosted App Entrypoint Discovery

Use this when the user asks you to operate a locally hosted or self-hosted web app and the browser target is not obvious.

## Goal
Find the **real UI URL** and **authentication path** before doing browser automation.

## Checklist
1. Confirm the process exists (`ps`, service manager, or Docker).
2. Check listening ports on the host.
3. If Docker is involved, inspect:
   - published ports
   - `HOST` / `PORT` / `PROTOCOL` / `WEBHOOK_URL`-style env vars
   - mounts containing persistent state
4. Prefer the app's declared external URL/domain when reverse proxy or HTTPS is configured.
5. Only after entrypoint discovery, open the UI and inspect whether you're at:
   - login page
   - SSO redirect
   - authenticated dashboard
   - setup / onboarding page

## Example: n8n
A useful pattern for n8n:
```bash
ps -ef | grep -i '[n]8n'
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}' | (head -n 1; grep -i n8n || true)
docker inspect n8n --format '{{range .Config.Env}}{{println .}}{{end}}' | grep -Ei '^(N8N_|WEBHOOK_|GENERIC_)'
docker inspect n8n --format '{{json .Mounts}}'
```

Interpretation pattern:
- If Docker shows `5678/tcp` with **no host mapping**, `http://127.0.0.1:5678` may not be reachable from the host browser.
- If env vars declare `N8N_HOST`, `N8N_PROTOCOL`, and `WEBHOOK_URL`, use that canonical URL first.
- Persistent state commonly lives under `/home/node/.n8n` inside the container; inspect mounts if you need to reason about where credentials or DB files live.

## Browser backend recovery
If browser automation says it cannot connect to its backend:
1. Start the browser server.
2. Run its health check.
3. Retry navigation.

Do not turn a transient backend-startup issue into a durable belief that browser tools are broken.
