---
name: ctf-pwn-techniques
description: "PWN CTF techniques — stack overflow via negative index/partial overwrite, stack pivot with 2-byte overwrite, heap UAF → FSOP (glibc 2.32+), shellcode with time side-channel, multi-step exploit chaining."
---

# CTF PWN — Exploit Techniques

## Trigger

When a CTF challenge provides:
- A binary with negative index vulnerability (idx < 0 not checked) → arbitrary stack write
- 2-byte stack overflow → partial overwrite + stack pivot
- Heap UAF with glibc 2.32+ → safe-linking bypass + FSOP
- Sandbox that executes user shellcode with fd restrictions → time side-channel
- Multiple small bugs that chain together → composite exploit

## Workflow

### Phase 1 — Negative Index Exploitation

**Signal**: Input index checked only for upper bound (`idx <= 0x50`) but not lower bound.

```python
# If index is signed int and only checks upper bound:
# idx = -8 means writing 8 * element_size bytes BEFORE the array start

# Check what's at array[-1], array[-2]... in the stack layout:
# - Might be a control variable (stage counter, loop bound)
# - Might be function's saved RBP
# - Might be its own return address

# Key trick: negative idx + current read() = overwrite the read() call's 
# own return address (not main's), enabling ret2syscall directly
```

**Verification**: Disassemble the function to confirm what lies at each negative offset.

### Phase 2 — Partial Overwrite + Stack Pivot (1-byte / 2-byte)

**Signal**: 1 or 2 bytes of overflow on a saved RBP.

```python
# Overwrite lowest 1 or 2 bytes of saved RBP
# This shifts the stack frame to a controlled location
# (requires leaking a stack address first)

# Step 1: Leak stack address (via format string or diagnostic menu)
# Step 2: Leak libc / PIE base
# Step 3: Overwrite saved RBP low bytes → pivot stack to controlled data
# Step 4: Find a `leave; ret` gadget (or a function that ends with it)
# Step 5: First pivot executes `read()` to write longer ROP chain
# Step 6: Second pivot executes ORW (open → read → write) ROP chain
```

**2-byte overwrite**: Shifts the frame to a nearby address (ASLR randomizes bits above low 12, but 2 bytes covers 16 bits, giving ~4K possible positions). Works best when the controlled data lies within 64 KB of the original RBP.

**1-byte overwrite variant**: A single `leave; ret` with a 1-byte RBP overwrite suffices when the target buffer is on an adjacent page. Because the low byte changes by at most 255 within a 256-byte window, this is highly reliable — ASLR does not randomize within a page. The pivot shifts RBP by 0x00–0xFF bytes, landing inside a buffer written by an earlier `read()`. Even a single null byte overflow (off-by-one) on RBP is sufficient for a controlled stack pivot when the leaked stack address places the target buffer within the same page.

**Key**: The pivot function's sole purpose is `leave; ret`. This turns a 1- or 2-byte overflow into full stack control.

### Phase 3 — Heap UAF → FSOP (glibc 2.32+)

**Signal**: Heap challenge with `malloc(0)` → UAF → glibc 2.32+ (safe-linking).

```python
# Step 1: UAF via double reference (two pointers to same chunk)
# Step 2: Leak tcache fd → heap_key for safe-linking
#         heap_key = chunk_addr >> 12
# Step 3: Leak heap_base via tcache chain poison
# Step 4: Tcache poisoning → allocate fake large chunk → unsorted bin → libc leak
# Step 5: FSOP chain:
#         a. Allocate fake _IO_FILE structure on heap
#         b. Set _IO_buf_base = "/bin/sh\x00"
#         c. Set vtable pointer to controlled area
#         d. Set wide_data → fake _IO_wide_data → fake wide vtable
#         e. The wide vtable's __overflow calls system()
# Step 6: Overwrite _IO_list_all → point to our fake FILE
# Step 7: Trigger exit() → FSOP → system("/bin/sh")
```

**Key**: glibc 2.32+ safe-linking XORs tcache fd with `(chunk_addr >> 12)`. The heap_key must be leaked first.

### Phase 4 — Time Side-Channel via Sandbox Shellcode

**Signal**: Binary executes user shellcode in a sandbox with seccomp allowing only `open`, `read`, `nanosleep`, `exit`.

```python
# Shellcode pattern:
# 1. open("flag") 
# 2. read(fd, buf, 64)
# 3. Compare flag[idx] > mid
#    - If TRUE: jmp $ (infinite loop → killed by alarm(1))
#    - If FALSE: ud2 (immediate SIGILL)
# 4. Parent process detects child exit reason:
#    - SIGALRM (killed) → bit = 1
#    - SIGILL (ud2) → bit = 0

# Avoid noisy operations (rdtsc is blocked)
# Network latency handling: send multiple samples per character
# Use majority vote across 3-5 probes per bit
```

**Anti-noise technique**: 
- For each bit, send 5 probes and take the majority
- The time gap between "alarm kills" (1 second) vs "ud2" (~10ms) is easy to distinguish
- Include a calibration phase with known chars

### Phase 5 — Multi-Bug Chaining

**Signal**: A binary with no single obvious vulnerability, but multiple small issues.

```python
# Common chain pattern:
# Bug A: Array OOB read → leak addresses (heap, libc, PIE, stack, canary)
# Bug B: Negative index write → overwrite control variable
# Bug C: Control variable changes behavior of a different function
# Bug D: Stack overflow (now possible due to changed control flow) → ROP

# Chain strategy:
# 1. Find ALL bugs first (don't try to exploit one in isolation)
# 2. Determine the dependency order (which bug enables which)
# 3. Test each link in the chain individually
# 4. Only assemble the full exploit when each link is confirmed
```

### Phase 6 — Race Condition / TOCTOU (Time-of-Check-Time-of-Use)

**Signal**: Multi-threaded code with shared global state and no locks. A worker thread modifies a counter while the main thread reads it without synchronization.

```python
# Classic pattern — bag exchange with shared state:
#   Thread A (main):  bag_count = read_int(),  item = items[bag_count]
#   Thread B (worker): while(running) { bag_count--, sleep(work), bag_count++ }
#
# The TOCTOU window: Thread B decrements bag_count, sleeps (work period),
# then increments. If Thread A reads bag_count during the sleep window,
# it gets a negative value → negative index into items[].
#
# Negative index write lands bytes BEFORE items[] in memory.
# Position items[] so items[-N] overlaps a function pointer / return address.

# Exploit structure:
# 1. Identify the shared counter variable and the two threads
# 2. Calculate window size: sleep(work) duration in Thread B
# 3. Send enough simultaneous requests to hit the race window
#    - On each attempt, set bag_count via Thread A's read_int()
#    - Race with Thread B's decrement/sleep/increment cycle
# 4. When bag_count goes negative, items[negative_idx] writes
#    at a controlled out-of-bounds address
# 5. Overwrite a return address or function pointer with a ROP gadget
```

**Reliability improvement**: Spray many connections/requests to increase the probability of hitting the small race window. A 1ms window with 100 attempts/sec gives roughly 10% success rate. Use 1000+ attempts for reliable exploitation.

**Key**: The race window opens when `bag_count` is negative (decremented but not yet re-incremented). Any read of `bag_count` during the `sleep(work)` interval yields a negative index, causing an out-of-bounds write.

### Phase 7 — realloc(ptr, 0) Edge Case

**Signal**: The program calls `realloc(ptr, 0)` on a live pointer, or calls `realloc(NULL, 0)` and uses the return value incorrectly.

```python
# realloc(ptr, 0) has surprising behavior:
#
# Case A — realloc(NULL, 0):
#   Allocates a tiny 0x20 chunk (minimum allocation in glibc).
#   Returns a valid pointer — NOT NULL. If the code treats NULL as
#   "allocation failed" it will use the returned non-NULL pointer
#   incorrectly.
#
# Case B — realloc(valid_ptr, 0):
#   Equivalent to free(ptr), BUT with one critical semantic difference.
#   In glibc, realloc tries to extend in-place or move the allocation.
#   The move path: allocates new chunk, memcpy, frees old chunk.
#   With size=0, the new allocation is a 0x20 chunk (same as Case A).
#   The old pointer is freed but the SOURCE POINTER IS NOT CLEARED
#   by the caller → double reference / dangling pointer (UAF).
#
# UAF exploitation:
# 1. realloc(ptr, 0) → old chunk freed, new tiny chunk returned
# 2. Old pointer still held by another variable → UAF reference
# 3. Reallocate the old chunk's size class → overlap with UAF reference
# 4. Modify contents through old pointer → corrupt new allocation
```

**Key**: `realloc(ptr, 0)` is NOT equivalent to `free(ptr)` in practice. The move-operation failure path leaves the source pointer alive while freeing the underlying chunk. glibc's minimum chunk size (0x20) means `realloc(NULL, 0)` returns a valid heap address, not NULL — code that checks `if (!ptr) fail()` will miss this.

### Phase 8 — strcspn OOB / Packet Length Corruption

**Signal**: Custom protocol parser uses `strcspn()` on attacker-controlled input without checking if the delimiter exists. If no delimiter is found, `strcspn()` returns the full buffer length, which can exceed the actual packet bounds and corrupt adjacent fields.

```python
# Pattern — length field followed by payload:
#   struct packet {
#       uint16_t len;           // length of payload
#       char payload[];         // payload bytes (may lack delimiter)
#   };
#
# The vulnerable logic:
#   pkt = recv_packet(sock)
#   delim_len = strcspn(pkt.payload, "|")   # find delimiter
#   # If no '|' found, strcspn returns strlen(payload) = entire payload
#   # If payload has no delimiter AND no null terminator within bounds,
#   # strcspn walks past the buffer into adjacent memory
#   
#   process(pkt.payload, delim_len)          # OOB read/write

# Exploitation:
# 1. Send a packet whose payload lacks the delimiter character
# 2. strcspn reads past the payload into adjacent protocol fields
#    - Reads into the NEXT packet's length field
#    - Returns a corrupted (larger) length
# 3. The corrupted length causes `process()` to:
#    a. Read beyond the current packet into kernel/process memory
#    b. Write forged data into adjacent packet buffers
# 4. Chain: forged length → forged next-packet content → arbitrary write
```

**Key**: `strcspn()` only stops at a null byte OR the delimiter. If neither appears within the packet bounds, it scans into adjacent memory, reading whatever follows. This corrupts the length calculation and can forge the next packet's metadata, enabling arbitrary read/write on subsequent iterations.

### Phase 9 — Flag Residue Manipulation

**Signal**: A flag/privilege check uses unsigned integers where overflow can flip the result, and the flag bits are not fully cleared on function exit.

```python
# Pattern — unsigned overflow + stale flag bits:
#
#   uint32_t auth_level = read_user_input();
#   uint32_t required = 5;
#   
#   // auth_level is unsigned — overflow is defined behavior
#   if (auth_level > required) {
#       grant_admin = 1;   // This flag is not reset on exit
#   }
#
#   // If auth_level = UINT32_MAX, then auth_level > required is TRUE
#   // because UINT32_MAX (4294967295) > 5
#   // This may seem correct, but the flag bits bleed:
#
#   process_request();
#   // grant_admin was set — but the function may also set other flags
#   // If grant_admin is NOT explicitly cleared on every exit path,
#   // a previous invocation's stale value persists

# Partial flag leak:
# 1. Call with auth_level = UINT32_MAX → passes the > check
# 2. grant_admin bit is set to 1
# 3. Exit the function WITHOUT clearing grant_admin
# 4. Call again with auth_level = 0 → should fail check
# 5. BUT grant_admin was NOT RE-INITIALIZED (it's static/global)
#    → stale admin privileges carry over
#
# Privilege escalation:
#   The unsigned overflow + stale flag combination means:
#   auth_level = UINT32_MAX → set flag
#   auth_level = 0 → flag survives (not cleared)
#   admin-only operations become accessible
```

**Key**: Two conditions must align: (1) unsigned integer overflow allows passing the check with extreme values, and (2) the privilege flag is not zeroed on every function entry/exit. The stale residue from a previous call persists, granting elevated access. Fix is to explicitly initialize (or clear) privilege flags on every entry path.

## Pitfalls

1. **Safe-linking XOR** — glibc 2.32+ tcache fd is `ptr >> 12 XOR next`. You MUST leak the heap address first
2. **FSOP vtable check** — glibc 2.35+ validates vtable pointers. Use `_IO_wchar_t` wide_data path instead
3. **Partial overwrite randomization** — low 12 bits of heap/stack are fixed; upper bits vary with ASLR. Partial overwrite works when ASLR only randomizes bits above the overwritten range
4. **Stack pivot alignment** — pivoted stack must be 16-byte aligned for SSE/movaps instructions. Adjust with padding
5. **Side-channel noise** — network jitter can make time measurements unreliable. Use majority voting across multiple probes
6. **glibc version specific** — FSOP structures change between glibc versions. Always check the remote libc version
7. **seccomp bypass** — if `openat` is allowed instead of `open`, use that instead. Check the seccomp filter first
