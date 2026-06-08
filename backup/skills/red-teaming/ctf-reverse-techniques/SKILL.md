---
name: ctf-reverse-techniques
description: "Reverse engineering CTF techniques — UPX malformed stub patching + custom stream cipher VM (GDB hw watchpoints), Android native JNI/so reversal (environment-triggered KDF, FNV-1a 64 hash), VEH-based VM (hundreds of exception handlers as micro-instructions, XXTEA with modified params, XOR from AND/NOT), CodeVirtualizer black-box analysis + White-Box AES-256 DFA, and PyInstaller unpacking + game emulation for key derivation."
---

# CTF Reverse — Engineering Techniques

## Trigger

When a CTF challenge provides:
- A packed/unstripped binary where unpacking reveals custom VM opcodes → UPX malformed stub + stream cipher VM
- An Android `.so` with JNI functions reading `/proc` and system properties → environment-triggered KDF
- A binary registering hundreds of Vectored Exception Handlers (VEH) before `main()` → VEH-based VM
- A virtualized binary with CodeVirtualizer + AES tables → White-Box AES + DFA
- A `.exe` unpacked via PyInstaller tools → game emulation for key derivation

## Workflow

### Phase 1 — UPX Malformed Stub + Custom Stream Cipher VM (GQuuuuuupX)

**Signal**: Binary packed with UPX but unpacking produces code that does NOT look like the original (custom VM interpreter). The UPX stub is intentionally malformed — some patches are applied post-unpack.

**Key Insight**: The challenge forces you to **watch when stub bytes are patched** rather than what the final code looks like. Use GDB hardware watchpoints on the unpacked data region.

#### Step 1 — Identify UPX Stub and Unpacking Entry

```bash
# Check if packed with UPX
upx -t challenge.bin

# If UPX complains "not a valid UPX-packed file" but packsig is visible:
# The stub is intentionally broken — extract unpack stub manually
# Find UPX magic "UPX!" or "UPX0" / "UPX1" sections
readelf -l challenge.bin
objdump -s -j UPX0 challenge.bin
```

#### Step 2 — GDB Hardware Watchpoints for Stub Patching

```bash
# Set a watchpoint on the UPX1 (packed data) section region
# The malformed stub patches key bytes AFTER partial decompression
gdb -q challenge.bin

# In GDB:
# 1. Find the unpack destination address range
info files
# Look for UPX0 (unpacked code section)

# 2. Set hardware watchpoint on a specific byte in unpacked code
#    that you suspect gets patched after initial decompression
watch *0x0804XXXX

# 3. Run — GDB will break when the byte is written
#    The backtrace reveals the patching code
run
bt
```

**Workflow**:
```gdb
# For each key byte of the packed stub that decrypts/decides behavior:
# 1. Hardware watchpoint on 4 bytes at suspected stub offset
# 2. First hit = UPX decompression writing initial code
# 3. Second hit = malformed stub post-patching the key
# 4. Examine the surrounding code that did the patch
#    → Extract the key byte at that moment

# Brute-force approach for byte-by-byte key recovery:
b *0x804XXXX          # breakpoint at the exact post-patch comparison
watch *(int*)0x804YYYY # watch the patched region
commands              # conditional logging of each write
  printf "Patched %x at %x from $pc\n", *(int*)0x804YYYY, $pc
  continue
end
```

#### Step 3 — Recover the Custom Stream Cipher VM

After unpacking reveals a VM interpreter:

```python
# The VM has:
# - opcode (1 byte)
# - operand (variable length depending on opcode)
# - rolling state (position-dependent)
# - opcode map = fn(key, profile) — different per key+profile tuple

# Reverse the VM dispatch:
# 1. Locate the main VM loop (typically while(1) with switch(op))
# 2. Map each opcode handler to its semantic:
#    - 0x01: XOR state with rolling key
#    - 0x02: ADD state
#    - 0x03: ROL state by N
#    - 0x04: output byte = state ^ flag_byte
#    - 0xFF: VM exit / terminate
# 3. The opcode dispatch is NOT a simple switch — it uses
#    an opcode->handler mapping table that gets constructed
#    dynamically from the key+profile pair
# 4. If the binary is UPX-packed and keys are post-patched:
#    dump the packed stub and extract patching offsets

# Rolling state recovery:
state = initial_state
decrypted = []
for byte in ciphertext:
    # Each byte transforms state
    op = get_opcode(byte, state)
    output = execute_op(op, byte, state)
    decrypted.append(output)
    state = update_state(state, output)
```

#### Step 4 — Byte-by-Byte Brute Force

```python
# When the VM has a comparison at the end (checking output against expected):
# Use breakpoints to brute-force each byte

def brute_force_byte(program, position, max_value=256):
    """At each position, try all 256 values, check comparison result."""
    for candidate in range(max_value):
        # Set up program state with candidate at position
        result = run_until_comparison(program, position, candidate)
        if result == "MATCH":
            return candidate
    return None

# Automation via GDB Python scripting:
#   gdb.execute(f"set variable flag_buf[{pos}] = {candidate}")
#   gdb.execute("continue")
#   if match detected: record candidate
```

**Key**: Each byte check is independent due to the VM's state design — the rolling state depends only on previously confirmed bytes. Once byte[0..i-1] are known, byte[i] can be brute-forced with 256 breakpoint hits.

### Phase 2 — Android Native JNI / Env-Triggered KDF (Schrödinger's Env)

**Signal**: An Android challenge with a native `.so` library loaded via `System.loadLibrary()`. The flag depends on environment state — process name, `/proc` entries, system properties.

#### Step 1 — Extract and Analyze the .so

```bash
# Check architecture
file libchallenge.so
# arm / arm64 / x86 / x86_64

# Disassemble all exported JNI functions
objdump -d libchallenge.so | grep -A 50 "Java_"
# Or use Ghidra/IDA for better visualization

# Look for:
# - Calls to fopen("/proc/self/...")
# - Calls to __system_property_get()
# - String comparisons (strcmp / strncmp)
```

#### Step 2 — Environment-Triggered KDF Structure

```python
# Typical flow:
# 1. JNI function check_env() reads:
#    - /proc/self/cmdline → process name
#    - /proc/self/status → trace status / TracerPid
#    - /proc/self/maps → loaded libraries
#    - getprop("ro.debuggable") → 1 if debuggable
#    - getprop("ro.secure") → 1 on production builds
# 2. Combine values into a maps_token string
# 3. Compute FNV-1a 64-bit hash of maps_token
# 4. Compare against stored ticket value
# 5. If match: derive decryption key via XOR/KDF

# FNV-1a 64 hash in C/asm:
def fnv1a_64(data: bytes) -> int:
    """FNV-1a 64-bit hash."""
    h = 0xCBF29CE484222325  # FNV offset basis (64-bit)
    FNV_PRIME = 0x100000001B3
    for byte in data:
        h ^= byte
        h = (h * FNV_PRIME) & 0xFFFFFFFFFFFFFFFF
    return h
```

#### Step 3 — Dual-Conditional Flag Decryption

```python
# Two conditions must be met:
#   COND_A: env_check() → ticket_hash == stored_ticket
#   COND_B: decrypt_flag() → produces readable output

# Strategy: patch the .so to bypass env check
# Method 1: NOP out the conditional branch after hash comparison
# Method 2: Set ticket_hash = 0 and find env that produces 0
# Method 3: Dynamic analysis with Frida:

# Frida script to bypass env checks:
"""
Interceptor.attach(Module.findExportByName("libc.so", "fopen"), {
    onEnter(args) {
        var path = Memory.readCString(args[0]);
        if (path.indexOf("proc") >= 0) {
            // Return fake file contents
            this.fake = true;
        }
    },
    onLeave(retval) {
        if (this.fake) {
            retval.replace(ptr(0xDEAD));
        }
    }
});
"""
```

#### Step 4 — Recovering the Maps Token

```python
# The maps_token is constructed from environment state:
# Typically: base_addr + library_path + permission_bits
# Use the emulator's /proc/[pid]/maps as a starting point

# Step 1: Run the binary in an emulator
adb shell
cd /data/local/tmp
./challenge

# Step 2: Dump /proc/self/maps from inside the process
adb shell cat /proc/$(adb shell pidof challenge)/maps

# Step 3: Reconstruct the token and compute FNV-1a
maps_token = construct_maps_token(pid_maps)  # exact concatenation
ticket = fnv1a_64(maps_token.encode())

# Step 4: The stored ticket is embedded in the .rodata section
strings -t x libchallenge.so | grep -E "^[0-9a-f]+ [0-9a-f]{16}$"
```

**Key**: The FNV-1a hash is deterministic from the maps token. If you can reproduce the exact maps token from an emulator's `/proc` output, the hash will match the stored ticket. The dual condition means both env check and flag decryption use different parts of the same token.

### Phase 3 — VEH (Vectored Exception Handler) VM (VectorizedMirage)

**Signal**: Hundreds of `AddVectoredExceptionHandler()` calls registered before `main()`. Each handler is a tiny function (micro-instruction) — `push`, `pop`, `add`, `xor`, `shift`. Triggered by repeated `__debugbreak()` / `int3` instructions.

**Key Insight**: The VEH handlers collectively form a stack-based VM. Each `int3` (or `__debugbreak()`) triggers the next handler in sequence. The handlers are NOT real exception handlers — they're micro-opcodes of a custom VM.

#### Step 1 — Detect VEH VM

```bash
# Check for VEH registration calls
objdump -d challenge.bin | grep -B5 "AddVectoredExceptionHandler"

# Count the number of handlers
# Each call registers a separate handler function
# Hundreds of handlers = VM, not debugging

# If no imports visible (obfuscated):
# Look for direct syscalls: NtQueryInformationProcess / ZwQueryInformationProcess
# Or look for calls that use the VEH registration via kernel32!AddVectoredExceptionHandler
```

#### Step 2 — Extract All VEH Handlers

```python
# Approach: Dump all handler addresses, then read each handler's assembly

# Manual extraction:
# 1. Find all RtlAddVectoredExceptionHandler / AddVectoredExceptionHandler calls
# 2. The second argument is the handler address
# 3. Disassemble each handler — they're typically very short (3-10 instructions)

# Automated extraction via Ghidra/IDAPython:
"""
# IDAPython script to extract VEH handlers
import idautils
import idc

veh_handlers = []
for seg_ea in idautils.Segments():
    for head in idautils.Heads(seg_ea, idc.get_segm_end(seg_ea)):
        if idc.print_insn_mnem(head) == "call":
            called = idc.get_operand_value(head, 0)
            name = idc.get_func_name(called)
            if "AddVectoredExceptionHandler" in name or "RtlAddVectoredExceptionHandler" in name:
                handler = idc.get_operand_value(head, 1)  # 2nd operand
                veh_handlers.append(handler)
                print(f"Handler at {hex(handler)}")
"""
```

#### Step 3 — Map Handlers to VM Opcodes

```python
# Typical micro-instruction handlers:

# Handler 0x00: NOP
# Handler 0x01: PUSH immediate (value embedded in handler)
# Handler 0x02: POP
# Handler 0x03: ADD top two stack values
# Handler 0x04: XOR top two stack values
# Handler 0x05: SHL (shift left)
# Handler 0x06: SHR (shift right)
# Handler 0x07: ROL (rotate left)
# Handler 0x08: DUP (duplicate top of stack)
# Handler 0x09: SWAP (exchange top two)
# Handler 0xFF: VM_EXIT / output

# Each handler typically:
push ebp
mov ebp, esp
; ... 1-3 instructions specific to opcode ...
pop ebp
retn

# Some handlers embed immediate values:
#  mov eax, 0x12345678  ; immediate
#  push eax

# The VM executes by:
# 1. Calling __debugbreak() (int3)
# 2. OS dispatches to next registered VEH
# 3. Handler runs its micro-instruction
# 4. Returns EXCEPTION_CONTINUE_EXECUTION
# 5. Resume at next instruction → next __debugbreak()
```

#### Step 4 — Extract VM Program and Emulate

```python
# After extracting all handlers in order:
vm_program = [
    ("PUSH", 0x1234),
    ("PUSH", 0x5678),
    ("XOR",),
    ("PUSH", 0x9ABC),
    ("ADD",),
    ("DUP",),
    ("XOR",),
    # ... hundreds of instructions
]

# Emulate the VM:
class VEHVM:
    def __init__(self):
        self.stack = []
        self.ip = 0

    def execute(self, program):
        while self.ip < len(program):
            op = program[self.ip]
            self.ip += 1
            if op[0] == "PUSH":
                self.stack.append(op[1])
            elif op[0] == "POP":
                self.stack.pop()
            elif op[0] == "XOR":
                a, b = self.stack.pop(), self.stack.pop()
                self.stack.append(a ^ b)
            elif op[0] == "ADD":
                a, b = self.stack.pop(), self.stack.pop()
                self.stack.append((a + b) & 0xFFFFFFFF)
            elif op[0] == "SHL":
                a = self.stack.pop()
                b = self.stack.pop()
                self.stack.append((a << b) & 0xFFFFFFFF)
            # ... etc
        return self.stack
```

#### Step 5 — XXTEA with Modified Parameters

The VM implements a custom XXTEA (Corrected Block TEA) cipher with modified shift parameters and delta:

```python
# Standard XXTEA:
# DELTA = 0x9E3779B9
# SHIFT_MIX = (z>>5 ^ y<<2) + (y>>3 ^ z<<4)
# ROUNDS = 6 + 52 // n

# Modified XXTEA from VectorizedMirage:
DELTA_MOD = 0xDEADBEEF  # or other non-standard value
SHIFT_PARAM1 = 3        # instead of 5
SHIFT_PARAM2 = 2        # instead of 2
SHIFT_PARAM3 = 1        # instead of 3
SHIFT_PARAM4 = 5        # instead of 4
ROUNDS_MOD = 32          # fixed or computed differently

def xxtea_decrypt(v, n, key):
    """Decrypt n 32-bit words with modified XXTEA."""
    rounds = 6 + 52 // n if n > 1 else ROUNDS_MOD
    sum_val = (rounds * DELTA_MOD) & 0xFFFFFFFF
    z = v[n - 1]
    while sum_val != 0:
        e = (sum_val >> 2) & 3
        for p in range(n - 1, 0, -1):
            y = v[p - 1]
            v[p] = (v[p] - (((z >> SHIFT_PARAM1 ^ y << SHIFT_PARAM2) +
                            (y >> SHIFT_PARAM3 ^ z << SHIFT_PARAM4)) ^
                           (sum_val ^ y) + (key[(p ^ e) & 3] ^ z))) & 0xFFFFFFFF
            z = v[p]
        y = v[n - 1]
        p = 0
        v[0] = (v[0] - (((z >> SHIFT_PARAM1 ^ y << SHIFT_PARAM2) +
                        (y >> SHIFT_PARAM3 ^ z << SHIFT_PARAM4)) ^
                       (sum_val ^ y) + (key[(0 ^ e) & 3] ^ z))) & 0xFFFFFFFF
        z = v[0]
        sum_val = (sum_val - DELTA_MOD) & 0xFFFFFFFF
    return v
```

**Key**: The shift parameters and delta are NOT the standard XXTEA values. They must be extracted from the VEH handlers. Look for the `shr` and `shl` immediate values in the shift-related handlers.

#### Step 6 — XOR Synthesized from AND/NOT Gates

```python
# The VM does NOT have a native XOR instruction.
# Instead, XOR is synthesized from AND + NOT gates:
# a XOR b = (a AND NOT b) OR (NOT a AND b)

# In the VEH handlers, this appears as:
# 1. NOT a → stack.push(~stack.pop())
# 2. AND a, b → stack.push(stack.pop() & stack.pop())
# 3. OR a, b → stack.push(stack.pop() | stack.pop())
# 4. Combined: XOR = NOT(a AND NOT(b)) AND NOT(NOT(a) AND b)

# OR equivalently (fewer operations with NAND):
# XOR = (a NAND (a NAND b)) NAND (b NAND (a NAND b))
# where NAND(x, y) = NOT(x AND y)

# To recognize XOR in emulation:
# 1. Trace register/stack dependencies
# 2. Look for the pattern: NOT → AND → NOT → AND → OR
# 3. Deduplicate to the underlying XOR operation
# 4. Annotate the VM program with "XOR_EMULATED" for clarity
```

**Key**: The XOR-on-NAND pattern is common in obfuscated VMs. If you see `AND` + `NOT` combinations without a native `XOR`, the VM is synthesizing XOR bitwise. Emulate faithfully — don't simplify during trace, but annotate for human readability.

#### Step 7 — Full VM Emulation Strategy

```bash
# Recommended approach:
# 1. Extract all 300+ VEH handler addresses
# 2. Statically analyze each handler → classify opcode
# 3. Build a program listing (sequence of opcodes + immediates)
# 4. Write a Python emulator
# 5. Single-step through the VM, tracking stack + register state
# 6. Dump intermediate values to identify the XXTEA key schedule
# 7. Once XXTEA key is known, decrypt the flag from embedded ciphertext
```

### Phase 4 — CodeVirtualizer Black-Box + White-Box AES-256 DFA (VectorizedMirage-revenge)

**Signal**: Binary protected with CodeVirtualizer (Oreans). Some functions are virtualized, some are not. The non-virtualized handler boundaries reveal White-Box AES-256 table lookups.

**Key Insight**: Rather than de-virtualizing CodeVirtualizer, extract the White-Box AES tables from the non-virtualized handlers. Then use DFA (Differential Fault Analysis) on the penultimate AES round to recover the last round key.

#### Step 1 — Identify Non-Virtualized Handlers

```bash
# CodeVirtualizer has characteristic markers:
# - Entry: push 0; push 0; push address; call VIRTUALIZER_START
# - Exit: VIRTUALIZER_END markers
# Non-virtualized handlers are code that exists BETWEEN virtualized chunks

# Find all functions that are NOT virtualized:
# - Look for standard function prologues (push ebp; mov ebp, esp)
# - NOT preceded by the CodeVirtualizer entry marker

objdump -d challenge.exe | grep -B5 "push.*ebp.*mov.*ebp.*esp" | head -100
```

#### Step 2 — Extract White-Box AES Tables

The non-virtualized handlers contain White-Box AES T-type tables:

```python
# White-Box AES-256 table structure:
# kInit[16][256]  — 16 input XOR tables (first AddRoundKey + SubBytes)
# kMid[13][4][4][4][256] — 13 middle round tables (ShiftRows + MixColumns + AddRoundKey)
# kFinal[16][256] — 16 output XOR tables (final AddRoundKey)

# Table extraction approach:
# 1. Locate large lookup tables (.rdata section, typically 16-256 KB each)
# 2. Verify AES structure:
#    - kInit[i][j] = SBox[j XOR key[i]] XOR something
#    - kFinal[i][j] = SBox[j XOR key[i]] XOR key_out[i]
#    - kMid tables: 4 tables per round × 4 bytes per word = complexity

# Dump table regions:
import struct

def dump_table(data, offset, size_bytes):
    """Dump a table starting at offset for size_bytes."""
    return data[offset:offset+size_bytes]

# For kInit: 16 entries × 256 entries × 4 bytes = 16 KB
# For kMid: 13 rounds × 4 rows × 4 cols × 4 positions × 256 × 1 byte = variable
# For kFinal: 16 entries × 256 entries × 4 bytes = 16 KB

# Verify a candidate kInit table:
def verify_kinit(table_4byte, expected_key_xor=None):
    """Check if a 16×256×4-byte table is a valid kInit."""
    for i in range(16):
        for j in range(256):
            val = struct.unpack('<I', table_4byte[i*256*4 + j*4:(i+1)*256*4 - (255-j)*4])[0]
            # kInit[i][j] should equal T-box output
            # If we know the key, verify: val == AES_round(0, key, j)
            pass
    return True  # heuristic: all entries are non-zero and within byte ranges
```

#### Step 3 — DFA (Differential Fault Analysis) on Penultimate Round

```python
# DFA on AES-256 recovers the last round key by injecting faults
# into the penultimate (14th → 13th) round's MixColumns output.

# Key insight:
# AES-256 has 14 rounds. The penultimate round is round 13.
# After SubBytes + ShiftRows + MixColumns of round 13, the state
# feeds into AddRoundKey (round 13 key) and then round 14.
# A fault in one byte of the round 13 MixColumns output affects
# exactly 4 bytes of the round 14 input (after ShiftRows inverse).

# DFA attack steps:
# 1. Collect correct ciphertext(s)
# 2. Inject fault at penultimate round → collect faulty ciphertext
# 3. XOR correct/faulty → differential, which constrains the last round key

def dfa_aes256(correct_ct, faulty_cts, round=14):
    """
    Recover last round key from correct + faulty ciphertexts.
    Requires ~50-200 faulty ciphertexts targeting the penultimate round.
    """
    # For each byte position of the last round key (16 bytes total):
    # 1. The differential in the faulty CT constrains the key byte
    # 2. Each fault gives ~8-16 candidate values per key byte
    # 3. Intersect candidates across multiple faults until unique

    last_round_key = [None] * 16

    for byte_pos in range(16):
        candidates = set(range(256))

        for faulty_ct in faulty_cts:
            diff = correct_ct ^ faulty_ct
            # The differential pattern reveals the fault column
            # From the diff, narrow down candidates for this key byte
            new_candidates = dfa_constrain(byte_pos, correct_ct, faulty_ct)
            candidates &= new_candidates
            if len(candidates) <= 1:
                break

        last_round_key[byte_pos] = candidates.pop() if candidates else None

    return bytes(last_round_key)
```

#### Step 4 — Practical DFA Injection

```python
# Fault injection methods for CodeVirtualized binaries:

# Method 1 — Rowhammer (memory bit flips)
# Target: the AES state buffer during execution
# Use: memory pressure + repeated access to adjacent rows

# Method 2 — Voltage glitching (hardware)
# Drop Vcc momentarily during penultimate round
# Requires oscilloscope + glitcher (ChipWhisperer, etc.)

# Method 3 — Software-based fault injection (most practical)
# Use a debugger to modify a single byte at the right moment:
"""
# GDB script for software fault injection:
set $round = 0
b *0xADDRESS_OF_PENULTIMATE_ROUND
commands
    # Flip one byte in the state at random position
    set $pos = $random % 16
    set *(unsigned char*)($state_ptr + $pos) ^= 0x01
    continue
end
run
"""

# Method 4 — Binary instrumentation (Intel PIN / DynamoRIO)
# Inject faults via pintool at specific instruction count:
"""
// PIN tool pseudo-code
if (instruction_count == target_count) {
    // Flip a byte in AES state
    *(state + pos) ^= fault_mask;
}
"""
```

#### Step 5 — Recover Full AES-256 Key from Last Round Key

```python
# AES-256 key schedule is invertible:
# Given the last round key (round 14), compute backwards to round 0 key.

# For AES-256:
# - Key size: 32 bytes (8 words: w[0]..w[7])
# - Round keys: w[0..7] = user key
# - w[i] = w[i-8] XOR SubWord(RotWord(w[i-1])) XOR RCON[i/8]
# - ... for i >= 8

def aes256_invert_key_schedule(last_round_key_14):
    """
    Recover the original AES-256 key from the last round key.
    last_round_key_14 = bytes 60*4 to 67*4 of expanded key = w[60..67]
    """
    # AES-256 has 15 round keys (0-14), each 128 bits
    # Last round key is rk[14] = w[56..59] (or w[60..63] depending on impl)
    # Work backwards through the key schedule

    # The full expanded key is 15 × 4 × 4 = 240 bytes
    # Last 16 bytes (rk[14]) = w[56], w[57], w[58], w[59]
    # w[i] = w[i-8] XOR SubWord(RotWord(w[i-1])) XOR RCON[i/8]

    # Key schedule inversion:
    # Given w[59], w[58], w[57], w[56]:
    # w[51] = w[59] XOR SubWord(RotWord(w[58])) XOR RCON...?
    # No — the AES-256 schedule alternates between simple XOR
    # and SubWord transformations.

    # Simplified: iterate backwards from w[59] to w[0]
    expanded_key = bytearray(240)
    # Fill last 16 bytes
    expanded_key[224:240] = last_round_key_14
    # ... (invert key schedule)
    return bytes(expanded_key[0:32])
```

**Key**: DFA on AES-256 requires faults in the penultimate (13th) round, not the last round. Faults in the last round only affect the last SubBytes, which is trivially detectable but doesn't help recover the key. The penultimate round MixColumns output spreads one faulty byte across 4 bytes after ShiftRows, giving enough constraints to solve for the last round key.

### Phase 5 — PyInstaller Unpacking + Game Emulation (ezbox)

**Signal**: A `.exe` with PyInstaller signature. The unpacked Python code reveals a game where valid moves derive an AES decryption key.

#### Step 1 — Unpack PyInstaller Archive

```bash
# Identify PyInstaller:
# - Contains PK (ZIP) header near end of file
# - Has _MEIPASS2 or PyInstaller strings
python3 -c "
import struct
with open('challenge.exe', 'rb') as f:
    data = f.read()
    idx = data.find(b'PK\\x03\\x04')
    print(f'ZIP header at offset {hex(idx)}')
"

# Extract using pyinstxtractor:
# https://github.com/extremecoders-re/pyinstxtractor
python3 pyinstxtractor.py challenge.exe

# Extracts to challenge.exe_extracted/
ls challenge.exe_extracted/
```

#### Step 2 — Decompile .pyc Files

```bash
# Use uncompyle6 or decompyle3 for Python 3.8 and below:
uncompyle6 challenge.exe_extracted/challenge.pyc > challenge_decomp.py

# For Python 3.9+ use pycdc or unpyc3:
# pycdc from: https://github.com/zrax/pycdc
pycdc challenge.exe_extracted/challenge.pyc > challenge_decomp.py

# If pycdc fails, try:
# - Decompyle++ (https://github.com/zrax/pycdc)
# - python-uncompyle6 with magic number patching
```

#### Step 3 — Analyze Game Logic

```python
# After decompilation, look for:
# - Level data (grid sizes, box positions, goal positions, wall positions)
# - Input parsing (WASD / arrow keys / move sequences)
# - Win condition checking
# - Flag decryption function

# Typical structure:
"""
# Game: box-pushing puzzle (sokoban variant)
levels = [
    {
        'grid': [[...]],  # 2D grid
        'walls': set(),
        'boxes': set(),
        'goals': set(),
        'player': (x, y),
    },
    # ... multiple levels
]

def check_win(level_idx, boxes):
    \"\"\"Check if all goals reached.\"\"\"
    return boxes == levels[level_idx]['goals']

def decrypt_flag(hashes):
    \"\"\"Derive AES key from all level context hashes.\"\"\"
    # key = SHA256(all_hashes)[:16]
    pass

context_hashes = []
for each level:
    # Compute context hash on level completion
    ctx_hash = SHA256(f\"{level_path}|{goal_positions}\")
    context_hashes.append(ctx_hash)
```

#### Step 4 — Direct Key Derivation (Skip Emulation)

```python
import hashlib

# The AES key is SHA256(all context hashes)[:16]
# Each context hash = SHA256("context_path|goal_positions")
# This is FULLY DETERMINISTIC from level data alone!

def compute_key_from_levels(levels):
    """Compute AES key directly without playing the game."""
    hashes = []
    for level in levels:
        # Construct context string exactly as the game does
        context_str = f"{level['path']}|{sorted(level['goals'])}"
        ctx_hash = hashlib.sha256(context_str.encode()).digest()
        hashes.append(ctx_hash)

    # Concatenate all 1024 hashes... check exact format:
    # Is it SHA256(all concatenated) or SHA256 of hash list?

    # Typically: SHA256(concat(hashes)) or SHA256(b''.join(hashes))
    combined = b''.join(hashes)
    aes_key = hashlib.sha256(combined).digest()[:16]
    return aes_key
```

#### Step 5 — Verify Key and Decrypt Flag

```python
from Crypto.Cipher import AES

def decrypt_flag_with_key(key, ciphertext):
    """
    Decrypt the embedded ciphertext using the derived key.
    Check encryption mode: likely ECB or CBC (if IV present).
    """
    # Try common modes:
    for mode_name, mode in [("ECB", AES.MODE_ECB),
                            ("CBC", AES.MODE_CBC)]:
        try:
            if mode == AES.MODE_CBC:
                # For CBC, IV may be embedded in ciphertext or separate
                iv = ciphertext[:16]
                ct = ciphertext[16:]
                cipher = AES.new(key, mode, iv=iv)
            else:
                cipher = AES.new(key, mode)
            plaintext = cipher.decrypt(ct if mode == AES.MODE_CBC else ciphertext)
            if plaintext.startswith(b"flag{") or all(32 <= b <= 126 for b in plaintext):
                return plaintext
        except Exception:
            continue
    return None

# Full pipeline:
levels = extract_levels_from_decompiled()
aes_key = compute_key_from_levels(levels)
flag = decrypt_flag_with_key(aes_key, embedded_ciphertext)
print(f"Flag: {flag}")
```

#### Step 6 — Game Emulation (Fallback)

```python
# If the key derivation includes runtime state (move count, score, etc.):
# You MUST emulate the game properly.

# Methods:
# 1. Brute-force via BFS on the game state space
# 2. Use an existing sokoban solver (e.g., Sokoban YASC, JSoko)
# 3. Patch the binary to skip game rendering and auto-solve

# Sokoban BFS solver:
from collections import deque

def solve_level(grid, player_start, boxes_start, goals, walls):
    """BFS to find any valid solution for a sokoban level."""
    start_state = (player_start, frozenset(boxes_start))
    q = deque([(start_state, [])])
    visited = {start_state}

    while q:
        (player, boxes), moves = q.popleft()
        if boxes == goals:
            return moves

        for direction in [(0,1), (0,-1), (1,0), (-1,0)]:
            new_player = (player[0] + direction[0], player[1] + direction[1])
            if new_player in walls:
                continue
            new_boxes = set(boxes)
            if new_player in new_boxes:
                # Push the box
                new_box_pos = (new_player[0] + direction[0],
                              new_player[1] + direction[1])
                if new_box_pos in walls or new_box_pos in new_boxes:
                    continue
                new_boxes.remove(new_player)
                new_boxes.add(new_box_pos)
            new_state = (new_player, frozenset(new_boxes))
            if new_state not in visited:
                visited.add(new_state)
                q.append((new_state, moves + [direction]))
    return None
```

**Key**: Try the pure deterministic approach FIRST — if the key depends only on level data (context paths + goal positions), you can compute it directly without game emulation. This is the intended shortcut. Only fall back to game emulation if the key derivation incorporates runtime state.

## Pitfalls

1. **VEH handler order** — The order of `AddVectoredExceptionHandler()` calls MATTERS. They are processed in LIST order (first registered = last called in VectoredHandler chain). The VM program order is the REVERSE of registration order unless handlers explicitly chain.

2. **UPX malformed stubs** — Don't assume standard `upx -d` will work. The malformed stub may skip decompression steps. Manual analysis of the stub code is required. Hardware watchpoints are vastly more reliable than software breakpoints for catching stub patching — software breakpoints modify code bytes and interfere with the patching process.

3. **Android env checks** — `/proc` entries differ across emulators and physical devices. The `maps_token` must match EXACTLY what the binary expects. Use the same emulator image/ROM that the challenge author used. Try multiple emulator configurations (API level, architecture, debuggable flag).

4. **FNV-1a collisions** — FN V-1a is not cryptographically secure. If you can't match the exact env, consider hash preimaging as a last resort.

5. **XXTEA parameter identification** — The shift params and delta in the VEH VM may use non-obvious immediate values. Look for `shr`/`shl` with immediates that don't match standard XXTEA (5, 2, 3, 4). The delta may be any 32-bit constant.

6. **XOR from AND/NOT** — If the VM synthesizes XOR, trace the AND/NOT sequence faithfully during emulation. Do NOT optimize by replacing with XOR unless you're absolutely certain no side effects exist (the AND/NOT approach may affect flags or carry bits that downstream operations depend on).

7. **CodeVirtualizer table integrity** — White-Box AES tables may be XOR-encrypted or encoded. The non-virtualized handlers may have a decoding loop that transforms the tables before use. Trace execution from the table loader to see if decoding occurs.

8. **DFA fault target precision** — Injecting a fault at the WRONG round (e.g., last round instead of penultimate) produces unusable differentials. Confirm the round count by tracing the AES round counter or counting SubBytes calls. AES-256 = 14 rounds, so penultimate = round 13.

9. **PyInstaller version mismatch** — `pyinstxtractor.py` may fail on newer PyInstaller versions (5.x+). Try alternative extractors: `pyinstxtractor-ng`, `unpyc3`, or manual ZIP extraction with `python3 -c "import zipfile; z = zipfile.ZipFile('exe'); z.extractall('extracted')"`.

10. **.pyc magic number** — Python version-specific magic numbers must match. Use `struct` to check the first 2 bytes of the .pyc file (e.g., Python 3.9 = 0x610D, Python 3.10 = 0x6F0D). If mismatched, the decompiler may fail or produce incorrect output.

11. **DFA ciphertext requirements** — DFA requires the correct ciphertext AND at least one faulty ciphertext from the same plaintext. If the binary uses randomized nonces/IVs, collect multiple encryptions of the same (or known) plaintext. Faults injected across different IVs are incomparable.

12. **Game emulation state explosion** — Sokoban state space can be exponential. For levels with many boxes, BFS may be infeasible. Use heuristics (Manhattan distance, deadlock detection) or try a specialized solver. Better yet — focus on the deterministic key derivation path first.

13. **VEH handler count** — Hundreds of handlers may be difficult to reverse statically. Consider dynamic extraction: set a breakpoint on every VEH entry, dump the instruction bytes, continue. Use a script to automate.

## Verification

1. **GQuuuuuupX**: Set hardware watchpoint at the suspected patch offset. Confirm two write events (decompression + patching). Extract the patch value. Verify the patched stub now produces correct VM bytecode.

2. **Schrödinger's Env**: Run the patched `.so` on an emulator with the correct `/proc` state. Verify FNV-1a hash of the reconstructed maps_token matches the embedded ticket. Decrypt the flag with the KDF-derived key.

3. **VectorizedMirage**: Dump all VEH handler addresses and classify each handler. Run the reconstructed VM program in your emulator. Verify the XXTEA decryption produces readable text (starts with known prefix or flag format).

4. **VectorizedMirage-revenge**: Extract White-Box AES tables from non-virtualized handlers. Run DFA with at least 50 faulty ciphertexts from the penultimate round. Verify the recovered last round key inverts to a valid AES-256 key. Decrypt the flag.

5. **ezbox**: Run `compute_key_from_levels()` and verify the AES key decrypts the embedded ciphertext to a valid flag. Confirm the key is deterministic (same output on multiple runs).
