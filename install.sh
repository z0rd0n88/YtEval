#!/usr/bin/env bash
# Install the yteval skill for Claude Code, Google Antigravity / Gemini, and OpenAI Codex.
#
# Usage:
#   ./install.sh              # install for all detected platforms (user global)
#   ./install.sh --claude     # install for Claude Code only
#   ./install.sh --gemini     # install for Google Antigravity / Gemini only
#   ./install.sh --codex      # install for OpenAI Codex only
#   ./install.sh --project    # install into the current project (.claude and .agents)
#   ./install.sh --uninstall  # remove installed copies
#
# Copies files only. Never edits configuration files, never modifies packages.

set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/skills/yteval"
SCOPE=user
ACTION=install

TARGET_CLAUDE=0
TARGET_GEMINI=0
TARGET_CODEX=0
SPECIFIC_TARGET=0

# Parse options; stop parsing options on --
while [ $# -gt 0 ]; do
  case "$1" in
    --project)
      SCOPE=project
      ;;
    --uninstall)
      ACTION=uninstall
      ;;
    --claude)
      TARGET_CLAUDE=1
      SPECIFIC_TARGET=1
      ;;
    --gemini|--antigravity)
      TARGET_GEMINI=1
      SPECIFIC_TARGET=1
      ;;
    --codex)
      TARGET_CODEX=1
      SPECIFIC_TARGET=1
      ;;
    --all)
      TARGET_CLAUDE=1
      TARGET_GEMINI=1
      TARGET_CODEX=1
      SPECIFIC_TARGET=1
      ;;
    -h|--help)
      sed -n '2,12p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "unknown option: $1" >&2
      exit 2
      ;;
    *)
      # Stop parsing options if we hit a positional arg
      break
      ;;
  esac
  shift
done

# If no specific target was given, default to all supported platforms
if [ "$SPECIFIC_TARGET" -eq 0 ]; then
  TARGET_CLAUDE=1
  TARGET_GEMINI=1
  TARGET_CODEX=1
fi

DESTINATIONS=()

if [ "$SCOPE" = project ]; then
  if [ "$TARGET_CLAUDE" -eq 1 ]; then
    DESTINATIONS+=("$PWD/.claude/skills/yteval")
  fi
  if [ "$TARGET_GEMINI" -eq 1 ] || [ "$TARGET_CODEX" -eq 1 ]; then
    DESTINATIONS+=("$PWD/.agents/skills/yteval")
  fi
else
  # Use ${HOME:-} to avoid unbound variable errors if HOME is unset
  HOME_DIR="${HOME:-}"
  if [ -z "$HOME_DIR" ]; then
    echo "error: \$HOME is not set" >&2
    exit 1
  fi
  
  if [ "$TARGET_CLAUDE" -eq 1 ]; then
    DESTINATIONS+=("${CLAUDE_CONFIG_DIR:-$HOME_DIR/.claude}/skills/yteval")
  fi
  if [ "$TARGET_CODEX" -eq 1 ]; then
    DESTINATIONS+=("$HOME_DIR/.agents/skills/yteval")
  fi
  if [ "$TARGET_GEMINI" -eq 1 ]; then
    DESTINATIONS+=("$HOME_DIR/.gemini/config/skills/yteval")
    if [ -d "$HOME_DIR/.gemini/antigravity-cli" ]; then
      DESTINATIONS+=("$HOME_DIR/.gemini/antigravity-cli/skills/yteval")
    fi
  fi
fi

# Deduplicate destinations to avoid symlink overlap clobbering
DEDUPED_DESTS=()
for dest in "${DESTINATIONS[@]}"; do
  skip=0
  for d in "${DEDUPED_DESTS[@]}"; do
    if [ "$dest" = "$d" ]; then
      skip=1
      break
    elif [ -e "$dest" ] && [ -e "$d" ] && [ "$dest" -ef "$d" ]; then
      skip=1
      break
    fi
  done
  if [ "$skip" -eq 0 ]; then
    DEDUPED_DESTS+=("$dest")
  fi
done
DESTINATIONS=("${DEDUPED_DESTS[@]}")

if [ "$ACTION" = uninstall ]; then
  echo "Uninstalling yteval skill..."
  for dest in "${DESTINATIONS[@]}"; do
    if [ -e "$dest" ] && [ "$dest" -ef "$SRC" ]; then
      echo "  $dest points to source, skipping to avoid deletion"
      continue
    fi
    if [ -d "$dest" ] || [ -h "$dest" ]; then
      rm -rf "$dest"
      echo "  removed $dest"
    else
      echo "  not found at $dest"
    fi
  done
  exit 0
fi

[ -f "$SRC/SKILL.md" ] || { echo "error: $SRC/SKILL.md not found — run this from a clone of the repo" >&2; exit 1; }

echo "Installing yteval skill..."
for dest in "${DESTINATIONS[@]}"; do
  # Prevent self-clobbering symlinks
  if [ -e "$dest" ] && [ "$dest" -ef "$SRC" ]; then
    echo "  $dest points to source, skipping to avoid deletion"
    continue
  fi
  
  mkdir -p "$(dirname "$dest")"
  rm -rf "$dest"
  cp -r "$SRC" "$dest"
  find "$dest" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
  echo "  installed to $dest"
done

# Dependency report. Missing ones are printed, not installed.
echo
echo "Checking dependencies:"
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
  echo "Install the missing required tools, then start your agent and run: /yteval --help"
  exit 1
fi

echo "Installation complete. Ready for use with:"
if [ "$TARGET_CLAUDE" -eq 1 ]; then
  echo "  - Claude Code: run '/yteval --help' in chat"
fi
if [ "$TARGET_GEMINI" -eq 1 ]; then
  echo "  - Google Antigravity / Gemini: run '/yteval' or paste YouTube URL to evaluate"
fi
if [ "$TARGET_CODEX" -eq 1 ]; then
  echo "  - OpenAI Codex: activate the yteval skill"
fi
