#!/usr/bin/env python3
"""Instrumental background music via Google Lyria on OpenRouter -> <project>/audio/music/bgm.mp3.
Lyria needs stream: true. lyria-3-pro-preview gives ~2.5–3 min; lyria-3-clip-preview gives a short clip.
mix.py loops/crossfades the track if the film is longer, so ~3 min is enough for most films.
Usage: music.py <project> [--prompt "..."] [--model google/lyria-3-pro-preview]"""
import argparse, base64, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _or import post, sse
DEFAULT = ('Instrumental background music, about 3 minutes, calm and confident. Warm minimal electronic with soft piano and a light pulse, '
           '100 BPM, no vocals, steady and unobtrusive under a voiceover, no dramatic drops, gentle ending.')
ap = argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--prompt', default=DEFAULT); ap.add_argument('--model', default='google/lyria-3-pro-preview')
a = ap.parse_args()
body = {'model': a.model, 'stream': True, 'modalities': ['audio', 'text'], 'audio': {'format': 'mp3'}, 'messages': [{'role': 'user', 'content': a.prompt}]}
buf = bytearray()
for ch in sse(post('/chat/completions', body, timeout=900)):
    if 'error' in ch:
        hint = '\nLyria refuses prompts that mention AI, video, a product or a brand: describe only the music (genre, BPM, instruments, mood, "no vocals").' if 'PROHIBITED' in str(ch['error']).upper() else ''
        sys.exit(f"Lyria error: {ch['error']}{hint}")
    for c in ch.get('choices', []):
        au = (c.get('delta') or {}).get('audio') or {}
        if au.get('data'): buf += base64.b64decode(au['data'])
if not buf: sys.exit('no audio returned')
d = os.path.join(a.project, 'audio', 'music'); os.makedirs(d, exist_ok=True); p = os.path.join(d, 'bgm.mp3')
open(p, 'wb').write(buf)
dur = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p], capture_output=True, text=True).stdout.strip()
print(p, dur, 's')
