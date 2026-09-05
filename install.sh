#!/bin/bash
# Jarvis installer.
#
#   ./install.sh           install for Claude Code
#   ./install.sh codex     install for Codex CLI
#   ./install.sh both      install for both
#
# Your data in ~/.jarvis is never overwritten.
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
DATA="$HOME/.jarvis"
TARGET="${1:-claude}"

if [[ "$(uname)" != "Darwin" ]]; then
  echo "Jarvis is macOS only - it reads your tabs through AppleScript."
  echo "Nothing here will work on $(uname). Sorry."
  exit 1
fi

command -v python3 >/dev/null || { echo "python3 not found. Install it and retry."; exit 1; }

install_skill() {
  local dest="$1" label="$2"
  mkdir -p "$dest/scripts"
  cp "$SRC/skills/jarvis/SKILL.md" "$SRC/skills/jarvis/onboarding.md" "$dest/"
  mkdir -p "$dest/agents" && cp "$SRC/skills/jarvis/agents/openai.yaml" "$dest/agents/"
  cp "$SRC/skills/jarvis/scripts/"*.py "$dest/scripts/"
  chmod +x "$dest/scripts/"*.py
  echo "  $label -> $dest"
}

mkdir -p "$DATA"
case "$TARGET" in
  claude) install_skill "$HOME/.claude/skills/jarvis" "Claude Code" ;;
  codex)  install_skill "$HOME/.agents/skills/jarvis" "Codex CLI" ;;
  both)   install_skill "$HOME/.claude/skills/jarvis" "Claude Code"
          install_skill "$HOME/.agents/skills/jarvis" "Codex CLI" ;;
  *) echo "Usage: ./install.sh [claude|codex|both]"; exit 1 ;;
esac

# Never clobber existing data.
for f in profile.md config.json jarvis.json; do
  if [ -f "$DATA/$f" ]; then
    echo "  kept your existing $f"
  else
    cp "$SRC/templates/$f" "$DATA/"
  fi
done

echo
echo "Installed. Your data lives in $DATA and survives reinstalls."
echo
echo "Next: open your agent and run /jarvis  (Codex: \$jarvis)"
echo "First run will ask you a couple of questions, then never again."
echo
echo "Heads up: macOS will ask permission for your terminal to control your"
echo "browser the first time. Without it, Jarvis can't see any tabs."
