#!/usr/bin/env python3
"""Fit a film under a size budget for embedding in one web page (e.g. a host that accepts one HTML file ≤ 5 MB -> base64 budget ≈ 3.6 MB of video).
Tries a ladder of (height, crf, audio kbps) and keeps the best that fits. Mono AAC for speech films; -tune animation keeps flat UI/text sharp at high crf.
Usage: web_compress.py <in.mp4> <out.mp4> [--max-mb 3.5]"""
import os, subprocess, sys
src, dst = sys.argv[1], sys.argv[2]
lim = float(sys.argv[sys.argv.index('--max-mb') + 1]) if '--max-mb' in sys.argv else 3.5
ladder = [(1080, 28, 64), (1080, 31, 48), (720, 30, 48), (720, 32, 40), (720, 34, 40), (540, 33, 32), (540, 36, 32)]
for h, crf, ab in ladder:
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', src, '-vf', f'scale=-2:{h}', '-c:v', 'libx264', '-preset', 'slow', '-crf', str(crf), '-tune', 'animation', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', f'{ab}k', '-ac', '1', '-movflags', '+faststart', dst], check=True)
    mb = os.path.getsize(dst) / 1e6; print(f'{h}p crf{crf} {ab}k -> {mb:.2f} MB')
    if mb <= lim: print('ok', dst); break
else: print('still over budget: shorten the film or lower the ladder')
