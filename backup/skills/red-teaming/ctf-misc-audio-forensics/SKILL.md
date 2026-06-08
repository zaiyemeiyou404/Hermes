---
name: ctf-misc-audio-forensics
description: "Audio forensic analysis — event segmentation via RMS, Morse/Wabun code decoding, FFT spectrogram inspection, encrypted audio container recovery."
---

# CTF Misc — Audio Forensics

## Trigger

When a CTF challenge provides:
- An audio file with short repeating "chirps" or "bird-like" sounds → Morse or Wabun code
- An audio file with unusual lyrics or background noise → FFT spectrogram hidden message
- An encrypted audio file (`.enc`) + encryptor binary → custom audio container reversing
- An audio file with metadata saying "Do you know FFT?" → spectrogram analysis

## Workflow

### Phase 1 — Audio Event Segmentation

```python
from scipy.io import wavfile
from scipy.ndimage import binary_closing, binary_opening
import numpy as np

fs, x = wavfile.read("challenge.wav")
if x.ndim == 2:
    x = x.mean(axis=1)
x = x.astype(np.float32) / (np.max(np.abs(x)) + 1e-9)

# Frame-based RMS
frame_len = int(fs * 0.01)
n = len(x) // frame_len
frames = x[:n * frame_len].reshape(n, frame_len)
rms = np.sqrt(np.mean(frames ** 2, axis=1))

# Threshold to find active segments
active = rms > 0.01
active = binary_closing(active, structure=np.ones(5))   # merge nearby events
active = binary_opening(active, structure=np.ones(2))   # remove noise

# Find event boundaries
edge = np.diff(np.r_[False, active, False].astype(int))
starts = np.where(edge == 1)[0] * 0.01
ends = np.where(edge == -1)[0] * 0.01

events = [(s, e, e - s) for s, e in zip(starts, ends)]
print(f"Event count: {len(events)}")
```

**Verification**: Plot the events over the waveform to confirm segmentation is correct. Each event should correspond to one audible "chirp."

### Phase 2 — Morse / Wabun Code Detection

Classify events by duration into 3 categories:
- **Short tone** → dot (`.`)  
- **Long tone** → dash (`-`)  
- **Very long / gap** → character separator or word separator

#### 3-Tone Labeling Technique

When you see three distinct tone durations but the naive split leads to consecutive "22" (invalid in Morse), tone 2 is likely a **delimiter**, not a dot or dash:

```python
# Categorize durations into exactly 3 groups
durations = sorted([e[2] for e in events])
# Use k-means (k=3) or percentile-based thresholding
q33 = np.percentile(durations, 33)
q66 = np.percentile(durations, 66)

tone_labels = []
for d in durations:
    if d <= q33:
        tone_labels.append(1)  # dot
    elif d <= q66:
        tone_labels.append(2)  # delimiter (not dot, not dash)
    else:
        tone_labels.append(3)  # dash

# Check: if no consecutive "22" exists, tone 2 IS a delimiter
# A delimiter means "end of character" — split on tone 2
has_consecutive_22 = any(
    tone_labels[i] == 2 and tone_labels[i+1] == 2
    for i in range(len(tone_labels)-1)
)
if not has_consecutive_22:
    print("Tone 2 is a delimiter, not a dot/dash — splitting on tone 2")
```

**When tone 2 = delimiter**: Instead of mapping all 3 tones to `.`/`-`/` `, treat tone 2 as an implicit character separator. Reclassify tone 2 events as gaps in the sequence, using only tones 1 and 3 for `.` and `-`.

#### Greedy Duration Matching

When tone durations vary widely (e.g. each dot is slightly different), use greedy matching by known duration ratios:

```python
# Reference: Morse timing assumes dot=1 unit, dash=3 units, intra-char gap=1 unit
# If the audio uses fixed tone lengths (not proportional), measure directly:
dot_duration = min(durations)  # shortest tone = dot
dash_duration = max(durations) # longest tone = dash

# For each event, assign the closest match
morse_chars = []
for d in durations:
    dist_to_dot = abs(d - dot_duration)
    dist_to_dash = abs(d - dash_duration)
    if dist_to_dot < dist_to_dash:
        morse_chars.append(".")
    elif dist_to_dash < dist_to_dot:
        morse_chars.append("-")
    else:
        morse_chars.append(" ")

# If tone 2 is delimiter, insert gaps:
if not has_consecutive_22:
    # Rebuild: for each event, use its tone label
    # tone 1 = ".", tone 3 = "-", tone 2 = break between characters
    morse_chars = []
    for label in tone_labels:
        if label == 1:
            morse_chars.append(".")
        elif label == 3:
            morse_chars.append("-")
        # label == 2 = delimiter = implicit break (no character added)
    # Insert word separators where gaps between events are extra large
```

```python
# Categorize durations
durations = [e[2] for e in events]
median = np.median(durations)
short_threshold = median * 1.5
long_threshold = median * 3

morse_chars = []
for d in durations:
    if d < short_threshold:
        morse_chars.append(".")
    elif d < long_threshold:
        morse_chars.append("-")
    else:
        morse_chars.append(" ")  # character separator

morse_string = "".join(morse_chars)
print(f"Morse: {morse_string[:200]}")
```

**Decode standard Morse**:
```python
MORSE = {
    ".-": "A", "-...": "B", "-.-.": "C", "-..": "D",
    ".": "E", "..-.": "F", "--.": "G", "....": "H",
    "..": "I", ".---": "J", "-.-": "K", ".-..": "L",
    "--": "M", "-.": "N", "---": "O", ".--.": "P",
    "--.-": "Q", ".-.": "R", "...": "S", "-": "T",
    "..-": "U", "...-": "V", ".--": "W", "-..-": "X",
    "-.--": "Y", "--..": "Z",
}

words = morse_string.split("  ")  # double space = word separator
decoded = []
for word in words:
    chars = [MORSE.get(c, "?") for c in word.split()]
    decoded.append("".join(chars))
print(" ".join(decoded))
```

**Detect Wabun code**: If decoded Morse contains `DO` and `SN` markers, these are Wabun code control sequences:
- `DO` → switch from international Morse to Wabun (Japanese kana)
- `SN` → switch back from Wabun to international Morse

This means the challenge mixes international Morse and Wabun code within one audio stream. Recover Wabun segments separately.

#### Leetspeak Post-Processing

After decoding Morse, the plaintext may be leetspeak-encoded. Apply common substitutions to recover the flag:

| Leet | Plain | Example |
|------|-------|---------|
| `@` | `A` | `M1N1LCTF` → `MINILCTF` |
| `0` | `O` | `C0NT41N3R` → `CONTAINER` |
| `3` | `E` | `M0RS3` → `MORSE` |
| `1` | `I` | `F0R3NS1CS` → `FORENSICS` |
| `4` | `A` | `H4ND` → `HAND` |
| `5` | `S` | `G3STUR35` → `GESTURES` |
| `7` | `T` | `B17` → `BIT` |

```python
def leet_to_plain(text: str) -> str:
    \"\"\"Convert common leetspeak back to plain letters.\"\"\"
    leet_map = {
        '@': 'A', '0': 'O', '3': 'E', '1': 'I', '4': 'A',
        '5': 'S', '7': 'T', '2': 'Z',
    }
    return ''.join(leet_map.get(c, c) for c in text)

# Post-process if plaintext looks like leet (has digits/@ in flag-like context)
decoded_text = " ".join(decoded)
if any(c in decoded_text for c in "@013457"):
    plain = leet_to_plain(decoded_text)
    print(f"Leet-decoded: {plain}")
```

**Verification**: After leet decoding, the result should form a recognizable flag pattern (e.g. `MINILCTF{...}`) with proper ASCII letters.

### Phase 3 — FFT Spectrogram Analysis

```bash
# Full spectrogram
ffmpeg -y -i audio.mp3 -lavfi showspectrumpic=s=4096x2048:mode=separate:scale=log:legend=disabled spectrogram.png

# If metadata hints at specific time range, zoom in
ffmpeg -y -ss 200 -t 45 -i audio.mp3 \
  -lavfi showspectrumpic=s=4096x2048:mode=separate:scale=log:legend=disabled spectrogram_zoom.png
```

**Signals to look for**:
- Text hidden in frequency bands (letters/numbers at specific kHz)
- QR code or barcode in the time-frequency plane
- Repeated patterns that suggest encoded data
- Metadata containing "FFT", "spectrum", "frequency" hints

**Verification**: The hidden message should be human-readable when you view the spectrogram at the correct resolution and time range.

### Phase 4 — Encrypted Audio Container Recovery

When given an encryptor (`wyy`) + encrypted audio (`flag.enc`):

1. **Reverse the container format**:
   ```python
   # Typical custom audio container:
   # Magic (8 bytes) + length fields + encrypted key block + encrypted metadata + audio data
   data = open("flag.enc", "rb").read()
   assert data[:8] == magic_bytes
   # Map the field structure by hex-dump and cross-reference with the encoder binary
   ```

2. **Find the key derivation**:
   - `strings wyy | grep -i key\|secret\|salt\|pass`
   - Look for timestamp usage (common pattern: `SHA256(salt + str(timestamp))`)
   - Brute-force timestamp near file mtime with AES padding validation

3. **Recover the stream cipher**:
   - Most custom audio encryptors use RC4-like KSA/PRGA pattern
   - Replicate in Python:
   ```python
   def make_keybox(key):
       box = list(range(256))
       c = last = 0
       for i in range(256):
           c = (box[i] + last + key[i % len(key)]) & 0xff
           box[i], box[c] = box[c], box[i]
           last = c
       return box
   
   def stream_xor(data, key):
       box = make_keybox(key)
       out = bytearray(data)
       for i in range(len(out)):
           j = (i + 1) & 0xff
           out[i] ^= box[(box[j] + box[(box[j] + j) & 0xff]) & 0xff]
       return bytes(out)
   ```

4. **Generate spectrogram of recovered audio** to read hidden message.

## Pitfalls

1. **Dot vs dash ambiguity** — don't assume "short = dot". Verify by checking if decoded output forms recognizable words (e.g. "DO", "MINIL")
2. **Word boundaries** — triple gaps between events may indicate word separators, not character separators
3. **FFT parameters** — default `showspectrumpic` may not reveal the message. Try different `scale` values (`lin`, `log`, `sqrt`) and resolutions
4. **Timestamp brute-force range** — the encryptor may use `timestamp + offset`. Search ±10000 hours around the file's mtime
5. **Non-standard Morse** — some challenges swap dot/dash or use a 4th tone type for control characters. Always check the raw event classification map
6. **AES vs XOR** — custom containers often use AES for the key/metadata block and XOR/stream cipher for the bulk audio. Don't try to AES-decode the audio data directly
7. **Wabun code lookup** — Wabun maps Roman Morse sequences to Japanese kana. If `DO` and `SN` markers are found, you need a Wabun lookup table to decode the Japanese characters
