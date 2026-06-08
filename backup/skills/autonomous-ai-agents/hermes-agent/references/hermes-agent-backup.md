# Hermes Agent Backup & Migration Guide

When you need to replicate a Hermes agent's identity (persona, memories, skills, custom scripts) to another machine, maintain a structured backup repo.

## Repository Structure

```
Hermes/
├── README.md                       # Migration guide
├── setup.sh                        # One-click restore script
├── backup/
│   ├── memories/                   # MEMORY.md + USER.md (the agent's identity)
│   ├── persona/                    # SOUL.md (persona configuration)
│   ├── scripts/                    # Custom scripts (cloakbrowser-server, etc.)
│   └── skills/                     # Custom user-created skills (SKILL.md + references)
├── config/
│   └── config.yaml.example         # Config template (secrets redacted)
└── references/                     # External project setup docs
    ├── task-pulse.md
    ├── ppt-master.md
    └── external-tools.md
```

## What to Back Up

| Item | Path | Why |
|------|------|-----|
| Memory | `~/.hermes/memories/MEMORY.md` | Environment notes, project conventions, tool quirks |
| User profile | `~/.hermes/memories/USER.md` | Communication style, preferences, pet peeves |
| Persona | `~/.hermes/SOUL.md` | Agent's personality/tone definition |
| Custom scripts | `~/.hermes/scripts/` | CloakBrowser server, etc. |
| Custom skills | `~/.hermes/skills/<name>/SKILL.md` | Skills created/modified by the agent |

## What NOT to Back Up (secrets stay local)

- `config.yaml` with real API keys — use `config.yaml.example` instead
- `~/.hermes/.env` — environment variables with tokens
- `~/.hermes/auth.json` — OAuth credentials
- Session files (`~/.hermes/sessions/`)
- Logs (`~/.hermes/logs/`)
- Large binaries (node_modules, venv, browser binaries)

## One-Click Restore

```bash
git clone <backup-repo-url> ~/Hermes
cd ~/Hermes && bash setup.sh
# Then: edit ~/.hermes/config.yaml with your API keys
# Then: hermes gateway restart
```

## Verification

After pushing, verify all files are accessible and correct:

```python
import urllib.request, json

token = "your_github_pat"
base = "https://raw.githubusercontent.com/<user>/Hermes/main"

files_to_check = [
    "README.md",
    "setup.sh",
    "backup/memories/MEMORY.md",
    "backup/memories/USER.md",
    "backup/persona/SOUL.md",
    "backup/scripts/cloakbrowser-server.py",
    "config/config.yaml.example",
]

for path in files_to_check:
    req = urllib.request.Request(
        f"{base}/{path}",
        headers={"Authorization": f"Bearer {token}"}
    )
    resp = urllib.request.urlopen(req, timeout=10)
    content = resp.read()
    print(f"  ✅ {path} ({len(content)} bytes)")
```

Also verify `setup.sh` syntax:
```bash
bash -n /path/to/Hermes/setup.sh
```

Simulate a restore to verify file structure:
```python
import os, shutil, tempfile

backup_dir = "/path/to/Hermes"
restore_dir = tempfile.mkdtemp()
hermes_home = f"{restore_dir}/.hermes"
os.makedirs(f"{hermes_home}/memories")
os.makedirs(f"{hermes_home}/scripts")

shutil.copy(f"{backup_dir}/backup/memories/MEMORY.md", f"{hermes_home}/memories/")
shutil.copy(f"{backup_dir}/backup/memories/USER.md", f"{hermes_home}/memories/")
shutil.copy(f"{backup_dir}/backup/scripts/cloakbrowser-server.py", f"{hermes_home}/scripts/")

restored = os.listdir(f"{hermes_home}/memories") + os.listdir(f"{hermes_home}/scripts")
print(f"  ✅ Restored: {restored}")
assert "MEMORY.md" in str(restored) and "USER.md" in str(restored)
shutil.rmtree(restore_dir)
```

## Keeping It Current

After significant memory updates or new skills:
```bash
cd ~/Hermes
git add -A && git commit -m "update: ..." && git push
```

## Gotchas

- **CDN cache** — `raw.githubusercontent.com` CDN may lag behind the latest commit by 1-5 minutes. Verify via the GitHub API (`GET /repos/<user>/<repo>/contents/`) instead of the raw CDN for authoritative content checking.
- **Secrets are NOT in the repo** — the user must manually set `GITHUB_TOKEN`, `DEEPSEEK_API_KEY`, etc. in `~/.bashrc` or `~/.hermes/.env` on the new machine. The token should NOT be embedded in commit history or README.
- **Full Hermes source code** (`~/.hermes/hermes-agent/`) is the upstream NousResearch repo — do NOT back it up here, just reinstall via `curl -fsSL https://hermes-agent.nousresearch.com/install.sh | sh`.
- **External tools** (CloakBrowser, OpenCode, PPT Master, Task Pulse) are documented in `references/` but must be installed separately from their original sources. Back up their **setup docs and project outputs** (e.g., PPT exports), not the full project binaries.
- **External tools** (CloakBrowser, OpenCode, PPT Master, Task Pulse) are documented in `references/` but must be installed separately.
