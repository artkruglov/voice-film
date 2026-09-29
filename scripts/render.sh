#!/usr/bin/env bash
# Render both formats and mux the mix. Usage: render.sh <project> [--fast] [--poster SECONDS] [--name film] [--only h|v]
#   default: 120 fps master -> motion blur -> 30 fps (or 24 fps, see --fps) BT.709 H.264 (slow, ~7 min per minute of film per format)
#   --fps 24|30 : output frame rate. Default: 24 if the film embeds 24 fps clips (public/**/*.mp4), else 30 —
#                 24 fps clips in a 30 fps film judder (every 4th frame repeats), so the film follows its footage.
#   --fast : 30 fps straight, no blur (drafts)
#   --only : re-render one format (h = 16:9, v = 9:16), e.g. after a failed run
# Runs timing.py and mix.py first. Output: <project>/out/<name>.mp4, <name>-vertical.mp4, posters, contact sheets.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; P="$(cd "$1" && pwd)"; shift
FAST=0; POSTER=""; NAME=film; ONLY=""; OFPS=""
while [ $# -gt 0 ]; do case "$1" in --fast) FAST=1;; --poster) POSTER=$2; shift;; --name) NAME=$2; shift;; --only) ONLY=$2; shift;; --fps) OFPS=$2; shift;; esac; shift; done
python3 "$HERE/timing.py" "$P" | head -1
python3 "$HERE/mix.py" "$P" >/dev/null
cd "$P"; OUT=out; mkdir -p $OUT/tmp
DUR=$(python3 -c "import json; print(json.load(open('src/film/timing.json'))['duration'])")
if [ -z "$OFPS" ]; then
  OFPS=30
  CLIPFPS=$(find public -name '*.mp4' -exec ffprobe -v error -select_streams v -show_entries stream=r_frame_rate -of csv=p=0 {} \; 2>/dev/null | sort -u | tr '\n' ' ')
  case " $CLIPFPS " in *" 24/1 "*|*" 24000/1001 "*) OFPS=24; echo "embedded clips at 24 fps -> rendering at 24 fps (use --fps 30 to override)";; esac
fi
BLEND=$((120 / OFPS))
[ -z "$POSTER" ] && POSTER=$(python3 -c "print(round($DUR*0.55,2))")
X264=(-c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -x264-params colorprim=bt709:transfer=bt709:colormatrix=bt709 -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv)
if [ $FAST = 1 ]; then FPS=$OFPS; VF="scale=in_color_matrix=bt601:in_range=tv:out_range=pc,format=gbrp,scale=out_color_matrix=bt709:in_range=pc:out_range=tv,format=yuv420p"
else FPS=120; W=$(printf '1 %.0s' $(seq $BLEND)); VF="tmix=frames=$BLEND:weights='${W% }',select='not(mod(n+1\,$BLEND))',setpts=N/($OFPS*TB),scale=in_color_matrix=bt601:in_range=tv:out_range=pc,format=gbrp,scale=out_color_matrix=bt709:in_range=pc:out_range=tv,format=yuv420p"; fi
render() { # composition file vertical
  npx remotion render src/index.ts $1 $OUT/tmp/$2-m.mp4 --props "{\"fps\":$FPS,\"vertical\":$3}" --codec h264 --crf 8 --pixel-format yuv444p --image-format png --muted --concurrency 8 --log error
  ffmpeg -v error -y -i $OUT/tmp/$2-m.mp4 -i $OUT/mix.wav -filter_complex "[0:v]$VF[v]" -map "[v]" -map 1:a -r $OFPS "${X264[@]}" -c:a aac -b:a 192k -ar 48000 -t $DUR -movflags +faststart $OUT/$2.mp4
  ffmpeg -v error -y -ss $POSTER -i $OUT/$2.mp4 -frames:v 1 $OUT/$2-poster.png
}
if [ "$ONLY" != v ]; then render Film $NAME false; fi   # plain if: a failed render must stop the script (set -e)
if [ "$ONLY" != h ]; then render FilmVertical $NAME-vertical true; fi
[ -f $OUT/$NAME.mp4 ] && [ -f $OUT/$NAME-vertical.mp4 ] || { echo "one format missing: re-run with --only"; exit 1; }
ROWS=$(python3 -c "import math; print(max(1, math.ceil($DUR/2/8)))" 2>/dev/null || echo 12); VR=$(python3 -c "import math; print(max(1, math.ceil($DUR/3/11)))" 2>/dev/null || echo 6)
ffmpeg -v error -y -i $OUT/$NAME.mp4 -vf "select='not(mod(n\,$((OFPS*2))))',scale=384:216,tile=8x$ROWS:padding=6:color=0xdddddd" -frames:v 1 -fps_mode vfr $OUT/$NAME-contact.png
ffmpeg -v error -y -i $OUT/$NAME-vertical.mp4 -vf "select='not(mod(n\,$((OFPS*3))))',scale=216:384,tile=11x$VR:padding=6:color=0xdddddd" -frames:v 1 -fps_mode vfr $OUT/$NAME-vertical-contact.png
rm -rf $OUT/tmp
bash "$HERE/check.sh" "$P" $NAME
