---
name: ctf-misc-git-forensics
description: "Git object extraction from restricted/limited shell environments — stash forensics, notes forensics, raw Git object decoding via base64+zlib."
---

# CTF Misc — Git Forensics

## Trigger

When a CTF challenge provides:
- A restricted shell with limited commands (`cat`, `gitcat`, `help`, `quit`)
- A `.git` directory accessible but no shell access
- A Git repository with suspicious stashes or notes
- A challenge where the flag is hidden in Git history/deleted objects

## Workflow

### Phase 1 — Enumerate Git Metadata

In a restricted shell, start by reading `.git` metadata:

```
cat .git/HEAD
cat .git/logs/HEAD
cat .git/config
cat .git/description
```

**Reflog enumeration** — `.git/logs/HEAD` records every ref update with timestamps and SHAs:

```
# Sample .git/logs/HEAD entries:
# 000000...abc123 ... <timestamp> <timezone>\tcommit (initial): first commit
# abc123...def456 ... <timestamp> <timezone>\tcommit: second commit
# def456...789abc ... <timestamp> <timezone>\tstash: WIP on main
```

```python
# Parse reflog for SHA1s, stash operations, and timestamps
import re
reflog = open(".git/logs/HEAD").read()
# Extract all SHA1 pairs (prev_sha → new_sha) and commit messages
entries = re.findall(
    r'([0-9a-f]{40}) ([0-9a-f]{40}) .+?\t(.+)',
    reflog
)
for prev, cur, msg in entries:
    print(f"  {prev[:8]}..{cur[:8]}  {msg}")
```

**Key signals from reflog**:
- `stash:` entries → stash operations performed
- `commit (initial):` → first commit SHA
- Multiple SHAs for a single branch → history of HEAD movement
- Reflog often contains SHAs for commits that were later reset or amended

```
cat .git/refs/stash
cat .git/refs/notes/commits
```

**Signals**:
- `refs/stash` exists → there are stashed changes (likely contains hidden data)
- `refs/notes/commits` exists → Git notes attached to commits (hide metadata)
- Multiple branches (`refs/heads/*`) → check each branch's tip

### Phase 2 — Decode Git Objects via Raw SHA

When `git cat-file` isn't available but a `gitcat <sha1>` tool exists that returns encoded Git objects:

**Two common encoding variants:**
1. **base64 → zlib** (most common): `gitcat` returns base64 of zlib-compressed Git object — decode base64 first, then zlib-decompress
2. **zlib only** (raw bytes): `gitcat` returns raw zlib-compressed data (no base64 wrapper)

Detect which variant by examining the first byte of the output:
- If it's printable ASCII (`A-Za-z0-9+/=`) → base64-encoded
- If it starts with `\x78` (zlib magic) → raw zlib

```python
import base64, zlib, struct

def decode_git_object(raw_data: str) -> tuple:
    """Decode a Git object. Handles both base64+zlib and raw-zlib variants."""
    raw_bytes = raw_data.encode('ascii') if isinstance(raw_data, str) else raw_data
    # Detect encoding: base64 starts with ASCII printable
    if raw_bytes[0] in range(0x2B, 0x7E):
        # base64-encoded → decode first, then decompress
        raw = zlib.decompress(base64.b64decode(raw_bytes))
    else:
        # already raw zlib-compressed data
        raw = zlib.decompress(raw_bytes)
    header, body = raw.split(b"\x00", 1)
    kind = header.split(b" ")[0].decode()
    return kind, body

def parse_tree(body: bytes) -> list:
    """Parse a Git tree object into (mode, name, sha1) entries."""
    entries = []
    pos = 0
    while pos < len(body):
        # Format: <mode> <name>\x00<20-byte SHA>
        null = body.index(b"\x00", pos)
        mode, name = body[pos:null].split(b" ", 1)
        pos = null + 1
        sha1 = body[pos:pos+20].hex()
        pos += 20
        entries.append((mode.decode(), name.decode(), sha1))
    return entries
```

### Phase 3 — Recover Commit/Tree/Blob Chain

```
HEAD commit → tree → subtree → blob (the hidden file)
                     ↓                   
              (alternate trees from          
               stashes and notes)          
```

For each interesting SHA1 (stash, notes ref):
1. `gitcat <sha1>` → decode as commit object → get tree SHA
2. `gitcat <tree_sha>` → decode as tree → list contents
3. `gitcat <blob_sha>` → decode as blob → read the actual data

#### 🔥 Stash — Always Check the 3rd Parent (Untracked Files)

A stash commit in Git has **3 parents** — most players only check the first two:

| Parent | Represents | Likely to contain flag? |
|--------|-----------|------------------------|
| Parent 1 | Working tree baseline (HEAD at stash time) | Not directly |
| Parent 2 | Index/staging area state | Possible, but uncommon |
| **Parent 3** | **Untracked files** (`git stash -u` or `-a`) | **Most likely** |

```python
# After decoding a stash commit:
stash_raw = decode_git_object(gitcat_output)
# stash_raw[1] is the commit body — extract parents from commit headers
# Git commit format:
#   tree <sha>
#   parent <sha1>
#   parent <sha2>
#   parent <sha3>    ← THIS IS THE UNTRACKED FILES PARENT
#   author ...
#   committer ...
#   \ncommit message

import re
commit_body = stash_raw[1].decode()
parents = re.findall(r'^parent ([0-9a-f]{40})', commit_body, re.MULTILINE)
print(f"Parents found: {len(parents)}")
if len(parents) >= 3:
    print(f"Parent 3 (untracked): {parents[2]}")
    # Decode parent 3's tree:
    parent3_raw = decode_git_object(gitcat(parents[2]))
    if parent3_raw[0] == 'commit':
        tree_sha = re.search(r'^tree ([0-9a-f]{40})', parent3_raw[1].decode(), re.M).group(1)
        # List all files in the untracked tree
        tree_body = decode_git_object(gitcat(tree_sha))
        entries = parse_tree(tree_body[1])
        for mode, name, sha in entries:
            print(f"  UNTRACKED: {name} ({sha})")
            blob = decode_git_object(gitcat(sha))
            print(f"    Content: {blob[1][:200]}")
```

**Why Parent 3 matters**: Most CTF players check only the stash tree (which shows changed files) and the index (Parent 2), but completely overlook untracked files. The flag is frequently hidden as an untracked file because `git stash -u` (stash including untracked) or `git stash -a` (all files) captures them. These files are invisible in `git status` at the time of stashing.

**Verification**: If stash has 3+ parents, always decode the third parent's tree. If no tree/blob entries appear in the output, decode the third parent directly as a tree object (it may be a root tree if no files were staged).

#### Git Notes Structure
- Each entry's name is a commit SHA
- Each entry's blob content is the note for that commit

Check if there's a note for the current HEAD commit — it may contain decryption keys.

### Phase 4 — XOR/Recovery

If the hidden data uses XOR encryption with a key from Git notes:

```python
key = b"recovered_key_string"  # from git notes
cipher_b64 = "base64_encoded_ciphertext"  # from stash blob

cipher = base64.b64decode(cipher_b64)
plain = bytes(cipher[i] ^ key[i % len(key)] for i in range(len(cipher)))
print(plain.decode())
```

## Pitfalls

1. **Stash without pop** — never `git stash pop` in a CTF environment. Read the raw object instead; popping modifies state
2. **Notes aren't fetched by default** — `git fetch --all` may not fetch notes. Check `refs/notes/*` explicitly
3. **Base64 encoding** — some restricted tools return base64, not raw. Always check by decoding a known object (e.g. HEAD commit)
4. **Git object types** — commits, trees, and blobs all look different when serialized. Use the header byte (`commit`, `tree`, `blob`) to determine how to parse
5. **Orphaned objects** — objects not reachable from any ref (e.g. `git stash` after `git stash drop`) may still exist. Try `git fsck` or enumerate via `cat .git/objects/??/`
6. **Timestamp sensitivity** — if the key depends on commit timestamps, the timestamp may be off by the committer's timezone
