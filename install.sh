#!/usr/bin/env bash
# Install the yteval skill for Claude Code.
#
# Usage:
#   ./install.sh              # install for your user (~/.claude/skills/yteval)
#   ./install.sh --project    # install into the current project (./.claude/skills/yteval)
#   ./install.sh --uninstall  # remove it again
#
# Copies files only. Never edits settings.json, never installs dependencies.

set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/skills/yteval"
SCOPE=user
ACTION=install

for arg in "$@"; do
  case "$arg" in
    --project)   SCOPE=project ;;
    --uninstall) ACTION=uninstall ;;
    -h|--help)   sed -n '2,10p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *)           echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

if [ "$SCOPE" = project ]; then
  DEST="$PWD/.claude/skills/yteval"
else
  DEST="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/yteval"
fi

if [ "$ACTION" = uninstall ]; then
  if [ -d "$DEST" ]; then
    rm -rf "$DEST"
    echo "removed $DEST"
  else
    echo "nothing installed at $DEST"
  fi
  exit 0
fi

[ -f "$SRC/SKILL.md" ] || { echo "error: $SRC/SKILL.md not found — run this from a clone of the repo" >&2; exit 1; }

mkdir -p "$(dirname "$DEST")"
rm -rf "$DEST"
cp -r "$SRC" "$DEST"
find "$DEST" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
echo "installed to $DEST"

# Dependency report. Missing ones are printed, not installed — this script does not
# reach into your package manager.
echo
missing=0
if command -v yt-dlp >/dev/null; then
  echo "  yt-dlp    $(yt-dlp --version 2>/dev/null || echo present)"
else
  echo "  yt-dlp    MISSING — required. Install with: pipx install yt-dlp"
  missing=1
fi

if command -v python3 >/dev/null; then
  echo "  python3   $(python3 --version 2>&1 | cut -d' ' -f2) (stdlib only, no packages needed)"
else
  echo "  python3   MISSING — required"
  missing=1
fi

if command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then
  echo "  gh        authenticated (optional, only for --issues)"
else
  echo "  gh        not authenticated (optional, only for --issues)"
fi

echo
if [ "$missing" -eq 1 ]; then
  echo "Install the missing required tools, then start Claude Code and run:  /yteval --help"
  exit 1
fi
echo "Start Claude Code in the directory you want reports written to, then run:"
echo "  /yteval --help"
