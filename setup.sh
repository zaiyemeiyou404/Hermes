#!/usr/bin/env bash
set -euo pipefail

echo "=== Hermes Agent — Full Restore Script ==="
echo "Restores memories, skills, persona, scripts, Task Pulse data, and clones Task Pulse project."
echo ""

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
BACKUP_DIR="$REPO_ROOT/backup"
TASK_PULSE_DIR="$HOME/task-pulse"
TASK_PULSE_REPO="https://github.com/zaiyemeiyou404/task-Pluse.git"

# --- Preflight: check for required commands ---
MISSING=""
for cmd in git cp mkdir chmod; do
  if ! command -v "$cmd" &>/dev/null 2>&1; then
    MISSING="$MISSING $cmd"
  fi
done
if [ -n "$MISSING" ]; then
  echo "ERROR: missing required commands:$MISSING"
  echo "Please install the packages that provide them and re-run."
  exit 1
fi

# 1. Ensure Hermes config directory exists
mkdir -p "$HERMES_HOME/memories" "$HERMES_HOME/scripts" "$HERMES_HOME/hermes-agent" "$HERMES_HOME/skills"

# 2. Restore memory
if [ -f "$BACKUP_DIR/memories/MEMORY.md" ]; then
  cp "$BACKUP_DIR/memories/MEMORY.md" "$HERMES_HOME/memories/"
  echo "✅ Memory restored"
fi
if [ -f "$BACKUP_DIR/memories/USER.md" ]; then
  cp "$BACKUP_DIR/memories/USER.md" "$HERMES_HOME/memories/"
  echo "✅ User profile restored"
fi

# 3. Restore active skills
if [ -d "$BACKUP_DIR/skills" ]; then
  cp -r "$BACKUP_DIR/skills/." "$HERMES_HOME/skills/"
  echo "✅ Skills restored"
fi

# 4. Restore scripts
if [ -d "$BACKUP_DIR/scripts" ]; then
  cp -r "$BACKUP_DIR/scripts/." "$HERMES_HOME/scripts/"
  find "$HERMES_HOME/scripts" -name '*.py' -exec chmod +x {} +
  echo "✅ Scripts restored from backup/scripts"
fi

# 5. Restore persona (AGENTS.md — Hermes Agent development guide)
if [ -f "$BACKUP_DIR/persona/AGENTS.md" ]; then
  cp "$BACKUP_DIR/persona/AGENTS.md" "$HERMES_HOME/hermes-agent/AGENTS.md"
  echo "✅ Persona (AGENTS.md) restored"
fi

# 6. Config example hint
if [ -f "$REPO_ROOT/config/config.yaml.example" ]; then
  echo ""
  echo "⚠️  Config template available at: $REPO_ROOT/config/config.yaml.example"
  echo "   Copy to $HERMES_HOME/config.yaml and fill in your API keys"
fi

# 7. Clone / update Task Pulse project
echo ""
echo "--- Task Pulse ---"
if [ -d "$TASK_PULSE_DIR/.git" ]; then
  echo "Updating existing Task Pulse repository..."
  git -C "$TASK_PULSE_DIR" pull --ff-only
else
  echo "Cloning Task Pulse repository..."
  git clone "$TASK_PULSE_REPO" "$TASK_PULSE_DIR"
fi

# 8. Restore Task Pulse runtime data
if [ -d "$BACKUP_DIR/task-pulse-data" ]; then
  mkdir -p "$TASK_PULSE_DIR"
  rm -rf "$TASK_PULSE_DIR/.task-pulse-data"
  cp -r "$BACKUP_DIR/task-pulse-data" "$TASK_PULSE_DIR/.task-pulse-data"
  echo "✅ Task Pulse runtime data restored to $TASK_PULSE_DIR/.task-pulse-data"
fi

# 9. npm install (if npm is available)
if command -v npm &>/dev/null 2>&1; then
  echo ""
  echo "Running npm install in $TASK_PULSE_DIR..."
  npm --prefix "$TASK_PULSE_DIR" install
  echo "✅ npm install completed"
else
  echo ""
  echo "⚠️  npm not found — skipped npm install in $TASK_PULSE_DIR"
  echo "   Install Node.js manually, then run: cd $TASK_PULSE_DIR && npm install"
fi

echo ""
echo "=== Restore complete ==="
echo "Run 'hermes gateway restart' to apply changes."
