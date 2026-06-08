# Homer Dashboard Deployment

[Homer](https://github.com/bastienwirtz/homer) is a static homepage/dashboard for server services. Single YAML config file.

## Quick Deploy

```bash
docker run -d \
  --name homer \
  --restart unless-stopped \
  -p 9098:8080 \
  b4bz/homer:latest
```

## Config File

Homer reads `/www/assets/config.yml` inside the container. Write it fresh each time since the container runs as `lighttpd` (uid 1000) but `/www/assets/` is root-owned:

```bash
# Write to temp, then docker cp
cat > /tmp/homer-config.yml << 'EOF'
---
title: "My Dashboard"
subtitle: "Services"
columns: "3"

services:
  - name: "Core"
    icon: "fas fa-server"
    items:
      - name: "Service Name"
        logo: "fas fa-globe"
        subtitle: "description"
        url: "https://example.com"
        target: "_blank"
EOF

# Copy into container
docker cp /tmp/homer-config.yml homer:/www/assets/config.yml

# Fix permissions (container runs as lighttpd, not root)
docker exec homer chown lighttpd:lighttpd /www/assets/config.yml
docker exec homer chmod 644 /www/assets/config.yml
```

## Caddy Integration

```caddyfile
home.zaiyemeiyou.com {
    tls internal
    reverse_proxy 172.17.0.1:9098
}
```

## Service Worker Cache

Homer uses a Vite PWA service worker that caches the page aggressively. After updating config.yml, the browser may still show the OLD page from cache. Solutions:
- Open in incognito/private window
- Or clear site data for the domain in browser DevTools → Application → Clear site data
- Or use Ctrl+Shift+R (hard refresh)
- On the server side, `docker restart homer` clears the in-memory cache but not the browser's service worker cache

## Common Config Issues

- The `logo` field in service items expects either a Font Awesome class (e.g. `"fas fa-chart-bar"`) or an image URL. If using Font Awesome class names, Homer renders them as `<img>` tags pointing to relative paths, which may produce broken images. Omitting `logo` entirely is safest for a clean layout.
- The `icon` field is for service group headers, not individual items.
- Service item best: just `name`, `subtitle`, `url`, `target` — omit `logo` if icons aren't critical.

## Pitfalls

- Container runs as `lighttpd:lighttpd` (uid 1000), not root. Volume-mounting the config directory leads to permission errors. Always use `docker cp` instead of bind mounts.
- Static assets (logos, custom CSS) must also be `docker cp`'d or managed through a copy step.
- The default `logo` URL in config can use the Homer GitHub raw logo or any public image URL.
