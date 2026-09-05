#!/bin/bash
# One-time: stamp your name and GitHub handle into the placeholders,
# then delete this script.
#
#   ./setup-repo.sh <github-username> "<Your Name>"
set -euo pipefail

USER_NAME="${1:-}"
REAL_NAME="${2:-}"

if [ -z "$USER_NAME" ] || [ -z "$REAL_NAME" ]; then
  echo 'Usage: ./setup-repo.sh <github-username> "Your Name"'
  exit 1
fi

cd "$(dirname "$0")"

FILES=$(grep -rl "YOUR_GITHUB_USERNAME\|YOUR_NAME" . \
  --exclude-dir=.git --exclude=setup-repo.sh 2>/dev/null || true)

if [ -z "$FILES" ]; then
  echo "No placeholders left - already done."
  exit 0
fi

for f in $FILES; do
  # macOS and GNU sed disagree about -i; write via a temp file instead.
  sed -e "s|YOUR_GITHUB_USERNAME|$USER_NAME|g" \
      -e "s|YOUR_NAME|$REAL_NAME|g" "$f" > "$f.tmp" && mv "$f.tmp" "$f"
  echo "  updated $f"
done

echo
echo "Done. Now:"
echo "  rm setup-repo.sh"
echo "  git init && git add -A && git commit -m 'Jarvis 1.0.0'"
echo "  git remote add origin git@github.com:$USER_NAME/jarvis.git"
echo "  git push -u origin main"
