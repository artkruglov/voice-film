#!/usr/bin/env bash
# Review stills of chosen frames (30 fps) in both formats. Usage: review.sh <project> <out dir> <frame>...
# Look at every scene before a full render: overlaps, cut-off text, captions over key visuals.
set -euo pipefail
P="$(cd "$1" && pwd)"; DIR="$(mkdir -p "$2" && cd "$2" && pwd)"; shift 2
cd "$P"; if command -v bun >/dev/null; then RUN=bun; else RUN="npx --yes tsx"; fi
$RUN scripts/stills.ts "$DIR/h" "$@" --composition Film --props '{"fps":30,"vertical":false}' | tail -1
$RUN scripts/stills.ts "$DIR/v" "$@" --composition FilmVertical --props '{"fps":30,"vertical":true}' | tail -1
ls "$DIR/h" "$DIR/v"
