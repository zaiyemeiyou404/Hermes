# Weixin `/model` behavior

Use this when a user says `/model` worked before in Weixin, used to "pop up" model choices, or now does nothing.

## Durable findings

- In the gateway core, `/model` is a real gateway-dispatchable slash command.
  - `hermes_cli/commands.py`: `CommandDef("model", ...)` is not `cli_only`.
  - `gateway/run.py`: dispatches `canonical == "model"` to `_handle_model_command()`.
- `_handle_model_command()` supports two UX paths:
  1. Interactive picker if the current adapter implements `send_model_picker`
  2. Text fallback otherwise
- In the current main-tree code inspected during this session:
  - `gateway/platforms/telegram.py` implements `send_model_picker`
  - `gateway/platforms/discord.py` implements `send_model_picker`
  - `gateway/platforms/weixin.py` does **not** implement `send_model_picker`
- Therefore, current Weixin behavior should be text fallback, not an actual interactive picker.

## Diagnostic recipe

1. Confirm the slash command still exists in the registry and gateway dispatcher:
```bash
python3 - <<'PY'
from hermes_cli.commands import resolve_command
print(resolve_command('model'))
PY
rg -n 'canonical == "model"|def _handle_model_command' ~/.hermes/hermes-agent/gateway/run.py
```

2. Check whether the active platform adapter implements model-picker UI:
```bash
python3 - <<'PY'
from pathlib import Path
for rel in [
    'gateway/platforms/telegram.py',
    'gateway/platforms/discord.py',
    'gateway/platforms/weixin.py',
]:
    p = Path('/home/ubuntu/.hermes/hermes-agent') / rel
    text = p.read_text(encoding='utf-8', errors='ignore')
    print(rel, 'send_model_picker' in text)
PY
```

3. Check whether Hermes actually received the user's `/model` message:
```bash
grep -nE "inbound message: platform=weixin|Unrecognized slash command /model|/model" ~/.hermes/logs/gateway.log | tail -n 120
```

## Interpretation

- If logs show the `/model` inbound message and Weixin has no `send_model_picker`, expect a text list response, not a picker.
- If logs do **not** show the `/model` inbound message at all, the likely problem is upstream of Hermes:
  - Weixin/iLink swallowed or rewrote the slash-prefixed message
  - the user may have used another client/platform previously
- Do not claim `/model` is unsupported globally; the issue is platform UX and/or delivery path.

## Practical workaround for Weixin

Use natural-language commands instead of relying on slash UX:
- "切到 gpt-5.4"
- "切到 deepseek-chat"
- "默认模型改成 gpt-5.4"

If the user wants a stable Weixin-native flow, implement a numbered text menu (`模型` -> reply with options -> user sends `1/2/3`) instead of depending on slash-command picker behavior.