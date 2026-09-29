#!/usr/bin/env python3
"""Second pair of eyes on frames: a vision model reads review stills or contact sheets and lists layout problems.
It catches what a linter can't: clipped or overlapping text, text too small for a phone, empty frames,
captions over the key visual, low contrast, content outside safe margins. It reads timestamps on a grid
imprecisely, so it complements looking at the frames yourself, it doesn't replace it.
(Idea from vakovalskii/nd-video-studio nd_review.py, MIT; here via OpenRouter.)
Usage: review_frames.py <image.png|jpg>... [--brief "vertical 9:16 film for Telegram"] [--model google/gemini-3.8-flash]
Exit code 1 if any image got "VERDICT: fix needed"."""
import argparse, base64, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _or import post

ASK = """You review frames of an explainer film (each image is one still or a grid of timestamped stills). {brief}
The bottom band of each frame holds burned-in captions; nothing important may sit under them.
For every frame with a problem write one line: "<frame or timestamp>: <problem> -> <fix>".
Check: clipped or overlapping text, text too small to read on a phone, empty or confusing frames,
captions covering the key visual, low contrast, elements outside safe margins, numbers without a label.
Skip frames without problems. End with exactly one line: VERDICT: ok | VERDICT: fix needed"""

ap = argparse.ArgumentParser()
ap.add_argument('images', nargs='+'); ap.add_argument('--brief', default=''); ap.add_argument('--model', default='google/gemini-3.8-flash')
a = ap.parse_args()
bad = 0
for path in a.images:
    mime = 'image/png' if path.lower().endswith('.png') else 'image/jpeg'
    b64 = base64.b64encode(open(path, 'rb').read()).decode()
    body = {'model': a.model, 'temperature': 0.2, 'messages': [{'role': 'user', 'content': [
        {'type': 'text', 'text': ASK.format(brief=a.brief)},
        {'type': 'image_url', 'image_url': {'url': f'data:{mime};base64,{b64}'}}]}]}
    r = json.load(post('/chat/completions', body, timeout=180))
    text = (r['choices'][0]['message'].get('content') or '').strip()
    print(f'== {path}\n{text}\n')
    bad += 'fix needed' in text.lower()
sys.exit(1 if bad else 0)
