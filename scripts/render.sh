#!/usr/bin/env bash
# Render both formats and mux the mix. Usage: render.sh <project> [--fast] [--poster SECONDS] [--name film]
#   default: 120 fps master -> 4:1 motion blur -> 30 fps BT.709 H.264 (slow, ~7 min per minute of film per format)
#   --fast : 30 fps straight, no blur (drafts)
# Runs timing.py and mix.py first. Output: <project>/out/<name>.mp4, <name>-vertical.mp4, posters, contact sheets.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; P="$(cd "$1" && pwd)"; shift
FAST=0; POSTER=""; NAME=film
while [ $# -gt 0 ]; do case "$1" in --fast) FAST=1;; --poster) POSTER=$2; shift;; --name) NAME=$2; shift;; esac; shift; done
python3 "$HERE/timing.py" "$P" | head -1
python3 "$HERE/mix.py" "$P" >/dev/null
cd "$P"; OUT=out; mkdir -p $OUT/tmp
DUR=$(python3 -c "import json; print(json.load(open('src/film/timing.json'))['duration'])")
[ -z "$POSTER" ] && POSTER=$(python3 -c "print(round($DUR*0.55,2))")
X264=(-c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -x264-params colorprim=bt709:transfer=bt709:colormatrix=bt709 -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv)
if [ $FAST = 1 ]; then FPS=30; VF="scale=in_color_matrix=bt601:in_range=tv:out_range=pc,format=gbrp,scale=out_color_matrix=bt709:in_range=pc:out_range=tv,format=yuv420p"
else FPS=120; VF="tmix=frames=4:weights='1 1 1 1',select='not(mod(n+1\,4))',setpts=N/(30*TB),scale=in_color_matrix=bt601:in_range=tv:out_range=pc,format=gbrp,scale=out_color_matrix=bt709:in_range=pc:out_range=tv,format=yuv420p"; fi
render() { # composition file vertical
  npx remotion render src/index.ts $1 $OUT/tmp/$2-m.mp4 --props "{\"fps\":$FPS,\"vertical\":$3}" --codec h264 --crf 8 --pixel-format yuv444p --image-format png --muted --concurrency 8 --log error
  ffmpeg -v error -y -i $OUT/tmp/$2-m.mp4 -i $OUT/mix.wav -filter_complex "[0:v]$VF[v]" -map "[v]" -map 1:a -r 30 "${X264[@]}" -c:a aac -b:a 192k -ar 48000 -t $DUR -movflags +faststart $OUT/$2.mp4
  ffmpeg -v error -y -ss $POSTER -i $OUT/$2.mp4 -frames:v 1 $OUT/$2-poster.png
}
render Film $NAME false
render FilmVertical $NAME-vertical true
ROWS=$(python3 -c "import math; print(max(1, math.ceil($DUR/2/8)))" 2>/dev/null || echo 12); VR=$(python3 -c "import math; print(max(1, math.ceil($DUR/3/11)))" 2>/dev/null || echo 6)
ffmpeg -v error -y -i $OUT/$NAME.mp4 -vf "select='not(mod(n\,60))',scale=384:216,tile=8x$ROWS:padding=6:color=0xdddddd" -frames:v 1 -fps_mode vfr $OUT/$NAME-contact.png
ffmpeg -v error -y -i $OUT/$NAME-vertical.mp4 -vf "select='not(mod(n\,90))',scale=216:384,tile=11x$VR:padding=6:color=0xdddddd" -frames:v 1 -fps_mode vfr $OUT/$NAME-vertical-contact.png
rm -rf $OUT/tmp
bash "$HERE/check.sh" "$P" $NAME
