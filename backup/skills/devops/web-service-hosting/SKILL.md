---
name: web-service-hosting
description: "Deploy, expose, operate, and debug web services on a Hermes-managed server. Covers static sites, Dockerized apps, reverse proxies (especially Caddy), TLS/DNS issues, backend health isolation, and service-specific bring-up patterns."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [deployment, hosting, caddy, reverse-proxy, tls, diagnostics, docker, static-sites]
    related_skills: [server-diagnostics, static-site-deployment, design-ai-deployment]
---

# Web Service Hosting

## Overview

Use this skill for the whole class of work around **putting a web service online and keeping it healthy** on a Hermes-managed Linux host.

This umbrella absorbs narrower siblings that separately covered:
- general server and reverse-proxy diagnostics,
- static HTML hosting behind Caddy, and
- deployment of a specific Dockerized design app.

A maintainer should treat these as one class-level skill: **web service hosting** with labeled subsections for deployment style, proxy/TLS, and diagnostics.

## When to Use

Use this skill when the user asks to:
- host a static page or small web app on a port and expose it via a domain
- deploy a Dockerized web tool behind Caddy or nginx
- diagnose 502/504, TLS failures, timeouts, or "it works from localhost but not the domain"
- determine whether the failure is DNS, listener, TLS, reverse proxy, backend, or upstream dependency
- verify a rebuild/restart actually replaced the old process

## Class-Level Diagnostic Order

Always isolate layers in order:
1. process exists
2. port is listening
3. localhost HTTP works
4. TLS handshake works
5. full HTTPS request works
6. reverse-proxy target is correct and reachable
7. upstream dependencies are reachable if the backend depends on them

Do not restart blindly before identifying the broken layer.

## Section A — Hosting Patterns

### Pattern 1: Static content
For static HTML/CSS/JS:
- clean and verify the content first
- pick a free port deliberately
- serve locally with a simple file server only for temporary preview, or use native Caddy `file_server` for durable hosting
- for long-lived domains, prefer removing the extra `python -m http.server` hop entirely and let Caddy serve the directory directly
- if Caddy itself runs in Docker, bind-mount the host static directory into the container (read-only) and point `root *` at the in-container path
- put the public domain in front via Caddy

Example durable Caddy block for a static site:

```caddyfile
example.zaiyemeiyou.com {
    tls internal
    root * /srv/example-site
    file_server
}
```

### Pattern 2: Dockerized applications
For containerized apps:
- clone or fetch the app
- inspect the container's port binding; many templates default to loopback-only bindings
- bring the container up
- verify health locally before touching DNS or TLS
- add a reverse-proxy block only after the backend is healthy

### Pattern 2b: Host-run app behind a Dockerized reverse proxy
A common compromise is: app runs on the host (systemd / native process), but Caddy runs in Docker.

Use this when the app is already stable on the host and you just need proper service management.

Steps:
1. Create a durable service unit (usually `systemd`) for the app instead of a hand-run shell.
2. Make the app listen on `0.0.0.0` if the Dockerized proxy reaches it via the host bridge IP (`172.17.0.1`, `172.18.0.1`, etc.). A listener bound only to `127.0.0.1` will work from the host but fail from the proxy container.
3. Verify from the host first (`curl http://127.0.0.1:PORT` or service health route).
4. Then verify from inside the proxy container to the chosen host bridge IP.
5. Only after both pass, validate the public HTTPS domain.

Typical example:
- Next.js app managed by `systemd`, listening on `0.0.0.0:3000`
- Caddy container reverse-proxying to `172.17.0.1:3000`

See also `templates/nextjs-systemd.service` for a minimal host-run Next.js service unit.

### Pattern 3: App-specific BYOK / UI setup
Some apps have a healthy backend but still need post-deploy product configuration (API keys, BYOK mode, initial setup, localStorage-driven SPAs, etc.). Treat this as part of deployment, not as a separate skill class.

## Section B — Reverse Proxy, DNS, and TLS

### Caddy-centric rules
- confirm the backend is reachable from the proxy's network namespace
- when Caddy is containerized, host services are often reached via the Docker bridge gateway rather than `localhost`
- reload after config edits, then validate again
- DNS must exist before certificate issuance can succeed

### Editing Caddyfile inside a Docker container
When Caddy runs in Docker without a bind-mounted config file:

```bash
# Append a new domain block
docker exec caddy sh -c "cat >> /etc/caddy/Caddyfile << 'EOF'

mysite.zaiyemeiyou.com {
    reverse_proxy 172.17.0.1:9099
}
EOF"

# Reload
docker exec caddy caddy reload --config /etc/caddy/Caddyfile
### Editing Caddyfile inside a Docker container

### Pitfall — `docker cp` fails on bind-mounted config files. If Caddy's config is bind-mounted from the host (e.g. `./Caddyfile:/etc/caddy/Caddyfile` in docker-compose), `docker cp` returns `device or resource busy`. Use `docker exec caddy sh -c "cat >> ..."` to append, or edit the host-side file directly (e.g. `write_file` to the docker-compose dir's Caddyfile) and then `docker exec caddy caddy reload`. The latter is more reliable for multi-line edits since `cat >>` in the container can timeout on longer heredocs.

### Cloudflare proxy mode (orange vs gray cloud)
When the domain is managed by Cloudflare DNS, two modes affect TLS:

| Icon | Mode | Effect |
|------|------|--------|
| 🟠 Orange (Proxied) | Cloudflare terminates TLS at edge, connects to origin over HTTP or HTTPS. **Recommended** — hides real IP, DDoS protection, auto TLS. |
| ⚪ Gray (DNS only) | DNS resolves directly to server IP. Caddy handles TLS via Let's Encrypt. IP is exposed. |

**If using orange cloud (Proxied):**
- Caddy does NOT need a valid public TLS cert — Cloudflare provides it to browsers
- Each domain block in Caddyfile needs `tls internal` to generate a self-signed cert for the CF→origin HTTPS connection:

```caddyfile
example.zaiyemeiyou.com {
    tls internal
    reverse_proxy 172.17.0.1:3000
}
```

- After adding `tls internal` to all blocks, reload Caddy: `docker exec caddy caddy reload --config /etc/caddy/Caddyfile`
- In Cloudflare dashboard → SSL/TLS → set encryption mode to **"Full"** (accepts self-signed origin certs)
- User must change each DNS A record from ⚪ gray to 🟠 orange in Cloudflare dashboard

**If using gray cloud (DNS only):**
- Caddy must obtain a Let's Encrypt certificate via ACME (http-01 or tls-alpn-01 challenge)
- DNS must propagate to Let's Encrypt's resolvers (not just `dig @8.8.8.8`)
- First issuance can fail with NXDOMAIN if DNS hasn't propagated; Caddy retries with exponential backoff (120s, 300s, 600s)
- A `caddy reload` can trigger a fresh issuance attempt
### TLS failure patterns

Typical causes:
- no DNS / wrong DNS
- cert not issued yet
- wrong SNI/domain block
- backend timeout misread as TLS failure
- stale Caddy cert cache after early failed issuance

When debugging cert issues, check both resolver-side DNS and proxy logs; don't infer from the browser alone.

**Caddy cert issuance in Docker:**
- Caddy may use the **Let's Encrypt staging** environment (`acme-staging-v02.api.letsencrypt.org`) after repeated failures, producing untrusted certs. Check `docker logs caddy` for the CA endpoint in cert requests.
- DNS must propagate to Let's Encrypt's resolvers, not just `dig @8.8.8.8` or `@1.1.1.1`. Test with the same CA's resolver if possible.
- Caddy retries with exponential backoff (120s, 300s, 600s). A `caddy reload` can trigger a fresh attempt, but `docker exec caddy caddy renew --force` or cert-specific commands may hang. Reload is safer.
- The `/data/caddy/certificates/acme-v02.api.letsencrypt.org-directory/` directory inside the Caddy container shows which certs are cached. If the domain is missing there, issuance is still failing.

## Section C — Health and Failure Isolation

### Listener health
A live process is not enough. Confirm the listener and inspect backlog indicators where available. If connections are piling up, the process may be alive but hung.

### Proxy vs backend distinction
- localhost backend OK, HTTPS broken → proxy/TLS layer
- TLS handshake OK, HTTP hangs → backend or proxy-to-backend path
- connection refused → wrong port or dead process
- old behavior after deploy → stale process still serving or stale build not restarted

### Upstream dependency checks
If the app depends on external services, test those endpoints independently. DNS resolution alone is not proof of reachability. Distinguish auth-gateway reachability from target-service reachability.

## Section D — Practical Service Bring-Up Recipe

1. verify free/expected port
2. start backend
3. verify localhost HTTP/health endpoint
4. add or confirm proxy config
5. reload proxy
6. verify domain over HTTPS
7. only then debug product-level setup (BYOK, onboarding, SPA settings)

## Product-Specific Subsection — Design/Prototype Apps

AI design apps like Open Design are just one instance of this larger class. Special concerns often include:
- Docker bind address changes for reverse-proxy visibility
- BYOK provider config instead of local CLI integration
- JS-heavy settings UIs that may need localStorage or direct state injection when browser automation cannot click through reliably

These are not sufficient reason for a standalone top-level skill; they belong under this umbrella.

## Common Pitfalls

1. **Treating static hosting, Docker web-app deploys, and reverse-proxy debugging as separate skill classes.** They are all web-service hosting.
2. **Using domain/TLS tests before localhost health checks.** This hides the broken layer.
3. **Assuming a running PID means the server is healthy.** Listener state matters.
4. **Forgetting that containerized proxies often need the host bridge IP, not `localhost`.**
5. **Binding a host-run backend to `127.0.0.1` while a Dockerized proxy targets the host bridge IP.** This causes the classic pattern: localhost health checks pass, public domain returns 502/connection refused.
6. **Using an extra long-lived `python -m http.server` process for a static site that Caddy could serve directly.**
7. **Leaving deployment guidance tied to one app name.** App-specific quirks belong in subsections or references.
8. **Serving temporary Python http.server setups as if they were durable production hosting.**
9. **Ignoring stale-process and stale-build traps after redeploy.**

## Support files

Absorbed narrower historical notes are preserved in:
- `references/server-diagnostics.md`
- `references/static-site-deployment.md`
- `references/design-ai-deployment.md`
- `references/homer-deployment.md` — Homer dashboard config, service-worker cache, icon issues
- `references/gocqhttp-qsign-setup.md` — go-cqhttp + qsign sign server deployment

## Verification Checklist

- [ ] Backend is healthy on localhost before proxy work begins
- [ ] Proxy target and network path are confirmed
- [ ] DNS resolves correctly for the domain
- [ ] HTTPS succeeds end to end
- [ ] Post-deploy app setup (if any) is completed and verified
- [ ] Old processes/builds are ruled out when behavior looks stale
