# Weixin PPTX Delivery Fallback

## Symptom

A direct Weixin `MEDIA:/absolute/path/to/deck.pptx` send can fail during CDN upload with HTTP 500, even when the deck is valid and only about 2 MB.

## Verification

Before assuming the deck is bad, confirm:

```bash
stat -c '%n %s bytes' /absolute/path/to/deck.pptx
file /absolute/path/to/deck.pptx
```

Expected outcome: the file exists, has a plausible size, and `file` reports `Microsoft OOXML`.

## Reliable Fallback

If direct `.pptx` delivery fails:

1. Zip the `.pptx`.
2. Re-send the `.zip` through the same Weixin channel.
3. Prefer the zip deliverable for the rest of that session once the direct path has already failed.

Python fallback when `zip` CLI is unavailable:

```python
from pathlib import Path
import zipfile

src = Path('/absolute/path/to/deck.pptx')
dst = src.with_suffix('.zip')
with zipfile.ZipFile(dst, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
    zf.write(src, arcname=src.name)
print(dst)
```

## Why This Belongs In Hermes-Agent Too

This is partly a presentation-delivery issue, but it is also a Hermes gateway troubleshooting pattern: the deck can be valid, the send can still fail at the platform upload layer, and the right recovery is format repackaging rather than regenerating the artifact.
