# Hermes webhook automation with n8n

Use this when an external automation system (especially n8n) needs to notify Hermes and let Hermes participate in human-in-the-loop approval.

## What worked

1. Check Hermes state first:
   ```bash
   hermes status --all
   hermes gateway status
   hermes webhook list
   ```
2. Confirm the gateway is actually listening before blaming n8n:
   ```bash
   ss -ltnp | grep 8644 || true
   ps -ef | grep 'hermes.*gateway' | grep -v grep
   ```
3. Create a webhook route and test it locally:
   ```bash
   hermes webhook subscribe codex-triage
   hermes webhook test codex-triage
   hermes webhook list
   ```
4. When n8n runs in Docker and Hermes runs on the host, target Hermes from n8n with:
   ```text
   http://host.docker.internal:8644/webhooks/<name>
   ```
   Do not assume `localhost` from the container reaches the host process.
5. If you changed gateway/platform config and `hermes gateway restart` hangs or times out, verify the live process instead of assuming the restart failed:
   ```bash
   hermes gateway status
   ss -ltnp | grep 8644 || true
   tail -n 50 ~/.hermes/logs/gateway.log
   ```

## n8n-specific pitfall

If a workflow imported through the n8n CLI shows as published/active but `POST /webhook/<path>` returns `404 The requested webhook ... is not registered`, regenerate the workflow/webhook IDs and re-import, then activate/publish again. In this session, recreating the workflow with fresh webhook IDs fixed production registration.

## Verification sequence

1. `curl` the n8n production webhook and confirm HTTP 200/expected status.
2. Check n8n logs for activation or unknown-webhook errors.
3. Trigger `hermes webhook test <name>`.
4. Send a real POST from n8n to Hermes and confirm delivery in the live chat before building approval logic on top.

## Scope note

This pattern is good for human-in-the-loop triage: n8n preprocesses, Hermes/WeChat approves, and a separate worker later pulls approved work for execution.