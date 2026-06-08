---
name: ctf-misc-pixel-stego
description: "Pixel-level steganography — discrete color channel analysis, nibble encoding, BMP/PNG pixel inspection, GIF frame extraction and stitching."
---

# CTF Misc — Pixel-Level Steganography

## Trigger

When a CTF challenge provides:
- A BMP/PNG with unusually low color depth or discrete color values (e.g. each channel = `0x08, 0x18, 0x28...`)
- An image + an API that renders text to the same format → encoding oracle
- A multi-frame GIF with odd dimensions (e.g. 58×13) and many frames → frame-by-frame data steganography
- An ELF binary that generates images from input and compares against a reference → image-equivalence challenge

## Workflow

### Phase 1 — Detect Discrete Color Encoding

```python
from pathlib import Path
import struct

data = Path("challenge.bmp").read_bytes()
pixel_offset = struct.unpack_from("<I", data, 10)[0]

# BMP stores pixels BGR (not RGB) and rows bottom-to-top (not top-to-bottom)
# Handle these format specifics:
width = struct.unpack_from("<I", data, 18)[0]
height = struct.unpack_from("<I", data, 22)[0]
row_size = ((width * 3 + 3) // 4) * 4  # BMP rows padded to 4-byte boundary
print(f"Image: {width}×{height}, pixel_offset={pixel_offset}, row_size={row_size}")

pixels = data[pixel_offset:]

# Check if color values are discrete
unique = sorted(set(pixels))
print(f"Unique values: {len(unique)}")
if len(unique) <= 16:
    # Each channel encodes exactly 4 bits (nibble)
    # Map: value = base + nibble * step
    step = unique[1] - unique[0]
    base = unique[0]
    print(f"Likely nibble encoding: value = {base:#04x} + nibble * {step:#04x}")
```

**Signal**: If a 24-bit BMP has only 4-16 unique values per channel, it encodes nibbles, not full bytes.

**BMP-specific footers**: Some challenges append a trailing 4-byte little-endian length field after the pixel data. Always check the last 4 bytes of the file:
```python
trailing_len = struct.unpack_from("<I", data, len(data) - 4)[0]
print(f"Trailing length field: {trailing_len}")
```

### Phase 2 — Nibble Extraction (BMP 4-bit Encoding)

```python
base = 0x08  # or whatever the minimum value is
step = 0x10  # or whatever the gap is

nibbles = [(b - base) // step for b in data[pixel_offset:]]

# Length field is often in the last 2 nibbles
text_len = (nibbles[-8] << 4) | nibbles[-7]

# Each pair of nibbles = 1 byte
plain = bytes(
    (nibbles[i] << 4) | nibbles[i+1]
    for i in range(0, text_len * 2, 2)
)
print(plain.decode(errors='replace'))
```

**Verification**: If you have a render API (`/api/render?text=<input>`), confirm your encoding by feeding a known string and comparing the output.

### Phase 3 — GIF Frame Analysis

```python
from PIL import Image
import os

gif = Image.open("challenge.gif")
frames = []
try:
    while True:
        frame = gif.copy()
        frames.append(frame)
        gif.seek(gif.tell() + 1)
except EOFError:
    pass

print(f"Dimensions: {gif.width}×{gif.height}, Frames: {len(frames)}")

# Save all frames
os.makedirs("frames", exist_ok=True)
for i, frame in enumerate(frames):
    frame.save(f"frames/frame_{i:04d}.png")

# Filter for sparse frames (fewest black/non-white pixels)
# These often contain partial character data
sparse = sorted(
    [(i, sum(1 for p in frame.getdata() if p < 128))
     for i, frame in enumerate(frames)],
    key=lambda x: x[1]
)[:20]  # Top 20 sparsest frames
```

**Key insight**: If the GIF is small (58×13) with many frames (500+), each frame likely carries a partial character slice. Multiple passes of filtering are needed: first pass for sparse frames (character tops), second pass for frames that fill gaps (character bottoms).

### Phase 4 — ELF Embedded Image Extraction

When an ELF binary generates an image from input and compares against a built-in reference:

```bash
# Extract embedded PNG from ELF
# Find the symbol name (check strings/nm for "png", "hand", "image")
readelf -s check_binary | grep -i "png\|image\|hand\|pic"

# If symbol found, extract its data
python3 -c "
import struct, sys
elf = open('check_binary', 'rb').read()

# The target symbol's address and size from readelf output
sym_addr = 0xXXXXX  # from readelf
sym_size = 0xXXXXX  # from readelf

# Convert virtual address to file offset
# (check ELF program headers for mapping)
for i in range(0, len(elf), 0x1000):
    chunk = elf[i:i+sym_size]
    if chunk[:8] == b'\x89PNG\r\n\x1a\n':  # PNG magic
        open('extracted.png', 'wb').write(chunk)
        print(f'PNG found at offset {i:#x}')
        break
"
```

**Key insight**: The program generates an image based on input bits → compares pixel-by-pixel with the embedded reference → accept/reject. Read the bits from the reference image to reconstruct the valid input.

### Phase 5 — Oracle Probing (Single-Character API Inputs)

When an API renders text to a pixel format and you can control the input, use single-character probes to deduce the encoding:

```python
import requests

def probe_character(char: str) -> bytes:
    \"\"\"Render one character and return its raw pixel data.\"\"\"
    r = requests.get(f"http://challenge/api/render?text={char}")
    return r.content  # raw BMP/PNG bytes

# Probe all printable ASCII characters
encodings = {}
for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789{}_!@#$%":
    raw = probe_character(c)
    # Extract pixel bytes (skip BMP header, handle BGR/bottom-to-top)
    pixel_offset = struct.unpack_from("<I", raw, 10)[0]
    pixels = raw[pixel_offset:]
    encodings[c] = pixels

# Compare encoding of unknown chunks against known probes
def match_encoding(chunk: bytes, encodings: dict) -> str:
    \"\"\"Match a pixel chunk to the closest probe character.\"\"\"
    for char, probe_pixels in encodings.items():
        if chunk == probe_pixels[:len(chunk)]:
            return char
        # Also try reverse byte order (BGR inversion, left-to-right toggle)
        if chunk == bytes(reversed(probe_pixels[:len(chunk)])):
            return f"{char}(reversed)"
    return "?"

# Decode the full challenge image by sliding-window matching
challenge_raw = Path("challenge.bmp").read_bytes()
challenge_pixels = challenge_raw[pixel_offset:]
# Scan for known character-sized blocks
```

**Key technique**: By single-character probing, you can:
- Deduce the exact nibble-to-character mapping without reverse-engineering the renderer
- Detect bit order (left-to-right vs right-to-left) by comparing reversed probes
- Identify BGR vs RGB by swapping channels in the probe
- Confirm trailing length field encoding

**Verification**: If your decoded characters form a valid flag prefix (e.g. `MiniLCTF{`), the oracle encoding is correct. If they're garbage, swap byte order or channel order and retry.

## Pitfalls

1. **Don't assume bit order** — "thumb first" vs "pinky first" changes the decoded byte. Always verify with an oracle endpoint or by enumerating permutations
2. **GIF frames are not always ordered chronologically** — some frames compensate for previous rendering artifacts. Try multiple frame orderings
3. **BMP padding** — BMP rows are padded to 4-byte boundaries. Skip padding bytes when reading nibbles
4. **GIF palette tricks** — palette-based GIFs may encode data in palette indices, not pixel values. Check the palette table
5. **Color channel order** — BMP stores BGR (not RGB). PNG stores RGBA. Adjust per format
6. **ELF symbol size** — the symbol's `st_size` field in `.symtab` is your exact extraction length. Don't guess
