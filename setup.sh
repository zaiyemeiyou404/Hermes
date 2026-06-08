#!/usr/bin/env bash
set -euo pipefail

echo "=== Hermes Agent Restore Script ==="

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
BACKUP_DIR="$HOME/Hermes/backup"

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
for script in cloakbrowser-server.py task-pulse-cleanup.py; do
  if [ -f "$BACKUP_DIR/scripts/$script" ]; then
    cp "$BACKUP_DIR/scripts/$script" "$HERMES_HOME/scripts/"
    chmod +x "$HERMES_HOME/scripts/$script"
    echo "✅ $script restored"
  fi
done

# 5. Restore persona (AGENTS.md — Hermes Agent development guide)
if [ -f "$BACKUP_DIR/persona/AGENTS.md" ]; then
  cp "$BACKUP_DIR/persona/AGENTS.md" "$HERMES_HOME/hermes-agent/AGENTS.md"
  echo "✅ Persona (AGENTS.md) restored"
fi

# 6. Config example hint
if [ -f "$HOME/Hermes/config/config.yaml.example" ]; then
  echo ""
  echo "⚠️  Config template available at: ~/Hermes/config/config.yaml.example"
  echo "   Copy to $HERMES_HOME/config.yaml and fill in your API keys"
fi

echo ""
# 7. Restore Task Pulse runtime data
if [ -d "$BACKUP_DIR/task-pulse-data" ]; then
  mkdir -p "$HOME/task-pulse"
  cp -r "$BACKUP_DIR/task-pulse-data" "$HOME/task-pulse/.task-pulse-data"
  echo "✅ Task Pulse runtime data restored to ~/task-pulse/.task-pulse-data"
fi

echo ""
echo "=== Restore complete ==="
echo "Run 'hermes gateway restart' to apply changes."
