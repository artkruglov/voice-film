#!/usr/bin/env bash
# Verify the deliverables: both streams, durations, full decode, loudness. Usage: check.sh <project> [name=film]
set -uo pipefail
P="$1"; NAME=${2:-film}; cd "$P/out"
for f in $NAME.mp4 $NAME-vertical.mp4; do
  [ -f "$f" ] || { echo "MISSING $f"; continue; }
  echo "== $f"; ffprobe -v error -show_entries stream=codec_type,codec_name,width,height:format=duration -of compact=p=0 "$f"
  ffmpeg -v error -i "$f" -f null - && echo "decode ok" || echo "DECODE ERRORS"
  ffmpeg -nostats -i "$f" -af ebur128=peak=true -f null - 2>&1 | awk '/Summary:/{s=1} s&&/I:|LRA:|Peak:/{print "  "$0}'
done
echo "target: ≈ -16 LUFS integrated, peak ≤ -1 dBFS"
