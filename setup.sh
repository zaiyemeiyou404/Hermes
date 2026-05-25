#!/usr/bin/env bash
set -euo pipefail

echo "=== Hermes Agent Restore Script ==="

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
BACKUP_DIR="$HOME/Hermes/backup"

# 1. Ensure Hermes config directory exists
mkdir -p "$HERMES_HOME/memories" "$HERMES_HOME/scripts" "$HERMES_HOME/hermes-agent"

# 2. Restore memory
if [ -f "$BACKUP_DIR/memories/MEMORY.md" ]; then
  cp "$BACKUP_DIR/memories/MEMORY.md" "$HERMES_HOME/memories/"
  echo "✅ Memory restored"
fi
if [ -f "$BACKUP_DIR/memories/USER.md" ]; then
  cp "$BACKUP_DIR/memories/USER.md" "$HERMES_HOME/memories/"
  echo "✅ User profile restored"
fi

# 3. Restore scripts
if [ -f "$BACKUP_DIR/scripts/cloakbrowser-server.py" ]; then
  cp "$BACKUP_DIR/scripts/cloakbrowser-server.py" "$HERMES_HOME/scripts/"
  chmod +x "$HERMES_HOME/scripts/cloakbrowser-server.py"
  echo "✅ CloakBrowser script restored"
fi

# 4. Restore persona
if [ -f "$BACKUP_DIR/persona/AGENTS.md" ]; then
  # Persona typically goes in the project root or agent config
  cp "$BACKUP_DIR/persona/AGENTS.md" "$HERMES_HOME/hermes-agent/AGENTS.md" 2>/dev/null || true
  echo "✅ Persona restored"
fi

# 5. Config example hint
if [ -f "$HOME/Hermes/config/config.yaml.example" ]; then
  echo ""
  echo "⚠️  Config template available at: ~/Hermes/config/config.yaml.example"
  echo "   Copy to $HERMES_HOME/config.yaml and fill in your API keys"
fi

echo ""
echo "=== Restore complete ==="
echo "Run 'hermes gateway restart' to apply changes."
