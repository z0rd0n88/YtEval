#!/usr/bin/env bash
# Fetch YouTube captions + metadata for a batch of videos.
#
# Usage:
#   fetch_captions.sh <outdir> <cap> <url-or-id>...
#
# Writes into <outdir>: <ID>.en.vtt (or .en-orig.vtt), <ID>.info.json,
# and <ID>.fetch.log (stderr, used to classify failures).
#
# Prints one classification line per video to stdout:
#   ok <ID> <chosen-vtt-filename>
#   fail <ID> <reason>
# where reason is one of: no-captions | unavailable | rate-limited | timeout | error
#
# Never downloads video or audio (--skip-download). --no-playlist keeps a
# watch?v=X&list=Y URL to video X alone: YouTube appends &list= whenever you
# click through from a playlist, so without it one pasted link becomes a
# forty-video run. --no-playlist does NOT cover a bare playlist?list= URL --
# yt-dlp still expands that to every entry (measured: 12/12) -- so this script
# rejects those outright. Expanding a playlist is the caller's decision, and
# SKILL.md makes it a blocking confirmation.
#
# Exit status is 0 even when individual videos fail — the caller decides.
# Exit 2 means bad arguments.

set -uo pipefail

OUTDIR=${1:-}
CAP=${2:-4}
shift 2 || { echo "usage: fetch_captions.sh <outdir> <cap> <url>..." >&2; exit 2; }
[ -n "$OUTDIR" ] && [ $# -gt 0 ] || { echo "usage: fetch_captions.sh <outdir> <cap> <url>..." >&2; exit 2; }

command -v yt-dlp >/dev/null || { echo "fail - missing-yt-dlp"; exit 2; }

for u in "$@"; do
  case "$u" in
    *playlist\?list=*) echo "usage: refusing playlist URL $u -- pass explicit video URLs" >&2; exit 2 ;;
  esac
done
mkdir -p -- "$OUTDIR"

video_id() {
  # Accept a bare 11-char ID, a watch URL, or a youtu.be short link.
  # Sanitize against path traversal by only keeping valid characters.
  case "$1" in
    *watch\?v=*) printf '%s' "${1#*watch?v=}" | tr -cd 'A-Za-z0-9_-' | cut -c1-11 ;;
    *youtu.be/*) printf '%s' "${1##*youtu.be/}" | tr -cd 'A-Za-z0-9_-' | cut -c1-11 ;;
    *)           printf '%s' "$1" | tr -cd 'A-Za-z0-9_-' | cut -c1-11 ;;
  esac
}

fetch_one() {
  local url=$1 id=$2
  # -- before $url: a bare ID starting with - (e.g. -IozMG9x0dI) is otherwise
  # parsed as a flag by yt-dlp's own argparse, not just the shell.
  timeout 180 yt-dlp \
    --skip-download --write-auto-sub --write-sub --sub-lang "en.*" \
    --sub-format vtt --write-info-json --no-playlist \
    -o "%(id)s.%(ext)s" -- "$url" \
    >>"$OUTDIR/$id.fetch.log" 2>&1
  local rc=$?

  # Classify from the log, not the exit code — yt-dlp's status does not
  # distinguish "no subtitles" from "video unavailable" from a bot challenge,
  # and those three want three different responses from the caller.
  if [ $rc -eq 124 ]; then
    echo "fail $id timeout"; return
  fi
  # Rate limiting arrives in two shapes: the bot challenge, and a plain HTTP 429
  # on the subtitle fetch. The 429 is the common one on a large batch, and it is
  # the dangerous one to miss — without this line it falls through to the
  # file-existence check below and gets reported as "no-captions", which means
  # "this video genuinely has none" and would be written into the report as a
  # truthful coverage note. Observed live: 16 of 46 videos in one batch.
  if grep -qiE "sign in to confirm|HTTP Error 429|too many requests" \
       "$OUTDIR/$id.fetch.log"; then
    echo "fail $id rate-limited"; return
  fi
  if grep -qiE "video unavailable|private video|has been removed|does not exist" \
       "$OUTDIR/$id.fetch.log"; then
    echo "fail $id unavailable"; return
  fi

  # Prefer .en.vtt; fall back to .en-orig.vtt when it is the only one present.
  # The auto-translate variant naming is a real case — hardcoding .en.vtt turns
  # it into a crash with no matching failure reason.
  local chosen=""
  if [ -f "$OUTDIR/$id.en.vtt" ]; then
    chosen="$id.en.vtt"
    rm -f "$OUTDIR/$id.en-orig.vtt"
  elif [ -f "$OUTDIR/$id.en-orig.vtt" ]; then
    chosen="$id.en-orig.vtt"
  fi

  # "no-captions" is a claim about the video, not about this run — it ends up in
  # the report as coverage. Only say it when yt-dlp actually said so, or when the
  # run succeeded and simply produced no subtitle file. Anything else is "error",
  # which is honest about not knowing.
  if [ -z "$chosen" ]; then
    if grep -qi "no subtitles" "$OUTDIR/$id.fetch.log" || [ $rc -eq 0 ]; then
      echo "fail $id no-captions"
    else
      echo "fail $id error"
    fi
    return
  fi
  if [ $rc -ne 0 ]; then
    echo "fail $id error"; return
  fi
  echo "ok $id $chosen"
}

cd -- "$OUTDIR" || exit 2
OUTDIR=.

running=0
for url in "$@"; do
  id=$(video_id "$url")
  fetch_one "$url" "$id" &
  running=$((running + 1))
  if [ "$running" -ge "$CAP" ]; then
    wait -n 2>/dev/null || wait
    running=$((running - 1))
  fi
  sleep 2
done
wait
