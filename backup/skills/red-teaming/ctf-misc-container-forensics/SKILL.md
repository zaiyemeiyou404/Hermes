---
name: ctf-misc-container-forensics
description: "Container/image forensic analysis — OCI layer extraction, PyTorch checkpoint inspection, TLS key log recovery, custom encrypted container reversing."
---

# CTF Misc — Container & Image Forensics

## Trigger

When a CTF challenge provides:
- A directory with `blobs/`, `index.json`, `oci-layout` → OCI image
- A `.bin` / `.pth` / PyTorch checkpoint with suspicious size → PyTorch model forensics
- A `.pcapng` + key material → TLS-decrypt-and-analyze workflow
- A binary that wraps audio/image/data into a custom format + `.enc` file → custom container reversing

## Workflow

### Phase 1 — Identify Container Type

| Signal | Likely type | Action |
|--------|------------|--------|
| `index.json` + `oci-layout` | OCI image | Read `index.json` → `manifest.json` → config blob → list layers |
| `data.pkl` + `data/` + `byteorder` | PyTorch checkpoint | Rename to `.zip`, extract, inspect `data.pkl` for hidden tensor names |
| Custom magic bytes (e.g. `MINILCTF`) | Custom encrypted container | Hex dump header, map field lengths, identify crypto primitives |
| `.pcapng` + `sslkeylog.log` (or recoverable key material) | TLS-decrypt challenge | Load keylog in Wireshark, export HTTP objects |

### Phase 2 — OCI Image Layer Extraction

```bash
# Read index
cat index.json | python3 -m json.tool

# Get manifest digest, then read config
# Check Cmd, WorkingDir, and especially history entries
# History might reveal deleted files: "COPY x.py /opt/" then "RUN rm /opt/x.py"

# List all layer blobs
# Extract each layer tar to find whiteout files (.wh.<name>)
for blob in blobs/sha256/*; do
  mkdir -p layer_$(basename $blob)
  tar -xzf "$blob" -C layer_$(basename $blob) 2>/dev/null
done

# Look for .wh.* files — these indicate deleted content in previous layers
find . -name '.wh.*'
```

**Verification**: After extracting all layers, you should have a complete filesystem including deleted files from earlier layers.

### Phase 3 — Embedded Resource Extraction from Layer Binaries

When a container layer binary contains embedded resources (PNG images, gesture data, etc.):

```bash
# Binwalk to find embedded PNG/JPEG inside ELF binaries
binwalk -Me challenge_binary
# Look for PNG magic bytes (\\x89PNG\\r\\n\\x1a\\n) in output
# Extract with --dd option for specific types:
binwalk -D 'png:image/png:png' challenge_binary
```

#### llvm-jutsu Hand-Gesture PNG Decoding

The llvm-jutsu challenge embeds 5-finger hand-gesture bitmaps where each pixel's color channel encodes a finger state:

```
Bit assignments per byte:
  bit 7 (MSB) = thumb      (1 = extended, 0 = bent)
  bits 6-0    = fingers 1-5 (pinky→index, each 1 bit + 3 padding bits)
               F5 F4 F3 F2 F1 *PP*  where PP = 2 padding bits
```

**Key decoding rules**:
- **thumb** = bit 7 (extended=1, bent=0)
- **fingers** = bits 6–0, right-to-left byte order (not left-to-right)
- Each byte encodes all 5 fingers for one position/pixel
- **Extended = 1**, **Bent = 0**
- Mapping from rightmost bit inward: finger1, finger2, finger3, finger4, finger5, then thumb

```python
def decode_gesture_pixel(byte_val: int) -> str:
    \"\"\"Decode a single gesture byte into finger states.\"\"\"
    thumb = (byte_val >> 7) & 1           # bit 7
    # Bits 6-0, right-to-left: finger1 (pinky), finger2, ...
    fingers = []
    for i in range(5):  # 5 fingers
        # Right-to-left: shift by i, mask bit 0
        bit = (byte_val >> i) & 1
        fingers.append(bit)
    # fingers[0] = pinky, fingers[4] = thumb-side finger
    return f"T:{'E' if thumb else 'B'} " + " ".join(
        f"F{j+1}:{'E' if f else 'B'}" for j, f in enumerate(fingers)
    )

# For a PNG extracted by binwalk:
from PIL import Image
import numpy as np
img = Image.open("extracted.png")
arr = np.array(img)
# Each pixel's R channel (or whichever channel) contains the gesture byte
for y in range(arr.shape[0]):
    for x in range(arr.shape[1]):
        byte_val = arr[y, x, 0]  # R channel
        state = decode_gesture_pixel(byte_val)
        print(f"({x},{y}): {state}")
```

**Verification**: The gesture states should form a consistent pattern across the image — each pixel's finger states represent a position on a 2D gesture surface. Reconstruct the flag by sequencing the finger states across the grid.

**Signal**: When an LLVM/JIT-based binary is found in a container layer and contains PNG resources, check for 5-finger gesture encoding schemes. The PNG dimensions often map to a gesture matrix.

### Phase 4 — PyTorch Checkpoint Analysis

```bash
# PyTorch .bin files are valid zip archives
cp model.bin model.zip
unzip -l model.zip
# Look for data.pkl, data/ directory, byteorder file

# Inspect data.pkl for hidden tensor/attribute names
python3 -c "
import pickle, zipfile
with zipfile.ZipFile('model.zip') as z:
    with z.open('data.pkl') as f:
        obj = pickle.load(f)
# Search for suspicious field names
import re
dump = str(obj)
for match in re.finditer(r'[\"\\']([\w]+secret\w+|[\w]*flag[\w]*|hidden|key)[\"\\']', dump, re.I):
    print(f'Potential hidden field: {match.group(1)}')
"
```

**Signal**: Look for field names containing `secret`, `key`, `flag`, `hidden`, or unusually long string literals in `data.pkl`.

**Verification**: If you find a suspicious tensor, read its storage file and decode with the correct dtype (from data.pkl).

### Phase 5 — Custom Encrypted Container Reversing

1. Hex dump the first 128-256 bytes of the `.enc` file
2. Identify magic bytes, length fields (usually 4-byte LE), and encrypted blocks
3. Reverse engineer the encryptor binary:
   - `strings` → look for salt strings, algorithm names (`AES`, `RC4`, `XOR`, `FFT`)
   - `readelf -s` / `nm` → look for crypto library symbols
   - Trace timestamp usage (time-based key derivation is common)
4. For time-based AES:
   ```python
   # Brute-force timestamp near file mtime
   import hashlib, struct
   from Crypto.Cipher import AES
   SALT = b"found_salt_string"
   def try_ts(ts, enc_block):
       key = hashlib.sha256(SALT + str(ts).encode()).digest()[:16]
       try:
           cipher = AES.new(key, AES.MODE_ECB)
           plain = cipher.decrypt(enc_block)
           if all(b == 0 for b in plain[-plain[-1]:]):  # PKCS7 valid
               return plain
       except: pass
       return None
   ```
5. For RC4-like stream cipher: identify KSA/PRGA pattern in the binary, replicate in Python

**Verification**: Decrypted output should match a known file header (MP3 `ID3`, PNG `\x89PNG`, etc.)

### Phase 6 — TLS Key Log Recovery + pcap Analysis

If you have a pcap + key material:
```bash
# In Wireshark: Edit → Preferences → Protocols → TLS → (Pre)-Master-Secret log filename
# Or via tshark:
tshark -r capture.pcapng -o tls.keylog_file:sslkeylog.log -Y http -T fields -e http.request.uri -e http.file_data
```

**Verification**: After loading the keylog, HTTP objects should be decrypted and exportable via `File → Export Objects → HTTP`.

## Pitfalls

1. **OCI images with multiple manifests** — always read `index.json` first, not just the first `manifest.json`
2. **PyTorch pickle is unsafe** — `pickle.load()` executes arbitrary code. Use a sandbox or inspect strings/repr first
3. **Timestamp drift** — AES timestamp derivation may use `mtime`, `ctime`, or a fixed offset. Search ±10000 around the estimate
4. **Whiteout is layer-relative** — `.wh.xxx` in layer N means xxx existed in layer N-1. Find the right parent layer
5. **RC4-like ≠ RC4** — challenge implementations often tweak KSA/PRGA. Replicate from binary, don't assume standard RC4
6. **SSL keylog format** — NSS key log format (`CLIENT_RANDOM ...`, `RSA Session-ID:...`) not Wireshark's internal format. Check line prefixes
