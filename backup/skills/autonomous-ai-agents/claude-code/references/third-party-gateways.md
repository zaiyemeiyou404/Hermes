# Third-party gateways and provider compatibility

Use this when Claude Code needs to talk to a non-Anthropic backend.

## Durable facts

- Claude Code supports third-party / gateway deployments via `ANTHROPIC_BASE_URL`.
- Recent upstream changelog notes show the CLI can:
  - read model choices from the gateway's `/v1/models` endpoint
  - honor custom provider model naming / overrides
  - run against Bedrock, Vertex, Foundry, and Anthropic-compatible gateways
- `ANTHROPIC_API_KEY` is the simplest auth path for scripted / bare usage.
- `apiKeyHelper` is also supported and can refresh dynamic keys.

## Important compatibility rule

Claude Code expects an **Anthropic-compatible** API surface when using `ANTHROPIC_BASE_URL`.

That means a provider that is only **OpenAI-compatible** is not a drop-in target. If the desired backend is DeepSeek's native API, connect Claude Code through a translation proxy / gateway that presents Anthropic-compatible endpoints to Claude Code and forwards to the real backend.

## Practical implication

- Direct: `Claude Code -> Anthropic-compatible gateway` ✅
- Direct: `Claude Code -> DeepSeek native API` ❌
- Via adapter: `Claude Code -> Anthropic-compatible proxy -> DeepSeek/OpenAI-style backend` ✅

## Good verification checks

1. `claude --version`
2. `claude auth status --text` or provide `ANTHROPIC_API_KEY`
3. Ensure the gateway exposes `/v1/models`
4. Start with a simple print-mode probe in a safe directory

## Why this matters

When a user asks to "connect DeepSeek to Claude Code", first determine whether they mean:
- use DeepSeek directly (not compatible as-is), or
- use DeepSeek behind a gateway / adapter (compatible if the adapter speaks Anthropic format).
