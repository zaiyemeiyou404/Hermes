# Stale Dev Server Diagnostics

When a Next.js (or other) dev server is behind a reverse proxy and code changes don't appear on the user's domain, use this diagnostic path.

## Quick Command Reference

```bash
# Show all listening dev servers
ss -ltnp | grep -E ':(3000|3001|3002)\\b'

# Find reverse proxy config
grep -r 'proxy_pass\\|reverse_proxy' /etc/nginx/sites-enabled/ /etc/caddy/ /etc/nginx/conf.d/ 2>/dev/null

# Identify which repo a server PID is rooted in
readlink -f /proc/<PID>/cwd

# Confirm which server has the latest code
curl -s http://127.0.0.1:3000/tasks | grep -o '<your-new-button-text>' | head -1
curl -s http://127.0.0.1:3002/tasks | grep -o '<your-new-button-text>' | head -1

# Restart the correct port
kill <old-pid>
cd <repo> && PORT=3000 npm run dev

# Verify the new server is serving updated content
curl -s http://127.0.0.1:3000/tasks | grep -o '<your-new-button-text>'
```

## Common Patterns

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Code compiles, browser shows old UI | Server on proxied port is stale | Kill old PID, restart on proxy port |
| `next dev` says "another server already running" | Duplicate dev servers in same dir | Use `ss -ltnp` to find PIDs, kill one |
| Changes visible on :3002 but not on domain | Caddy/nginx proxies to :3000 | Restart :3000 server with latest code |
| Dev mode works on localhost but not via domain | Next.js 16 blocks cross-origin HMR / WebSocket connections through Caddy (Docker) | Switch to production mode |

## Production Mode as the Fix for Caddy/Docker Proxy

When the site is served through Caddy (Docker container) → `172.17.0.1:PORT`, `next dev` mode has a known issue: Next.js 16's `allowedDevOrigins` gate blocks HMR WebSocket connections from the proxy hostname, logging `Blocked cross-origin request to /_next/webpack-hmr from "domain.com"`.

The reliable fix is to switch to **production mode**:

```bash
cd <repo>

# 1. Build
npx next build

# 2. Kill ALL old next processes
pkill -f "next start" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true
pkill -f "next-server" 2>/dev/null || true
sleep 2
ps aux | grep -i "[n]ext"  # confirm none remain

# 3. Start production server
npx next start --port 3000 &
sleep 2

# 4. Verify through Caddy
curl -sk https://domain.com/tasks -o /dev/null -w "%{http_code}"
```

Production mode eliminates HMR entirely, avoids CORS/WebSocket edge cases, and loads pages faster over the proxy.
