#!/usr/bin/env python3
"""Transcribe every audio/vo/<id>.wav with a Gemini text model (audio input) and compare with lines.json.
Prints a word-level similarity per line; anything under 0.93 is shown in full so you can re-voice it (tts.py --only <id>).
Any language: the model transcribes in the language it hears.
Usage: verify_voice.py <project> [--model google/gemini-3.8-flash]"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _vc import transcribe, score
ap = argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--model', default='google/gemini-3.8-flash'); ap.add_argument('--lang', default='')  # kept for old commands; not needed
a = ap.parse_args()
vo = os.path.join(a.project, 'audio', 'vo'); lines = json.load(open(os.path.join(vo, 'lines.json'), encoding='utf-8'))
bad = 0
for L in lines:
    wav = os.path.join(vo, L['id'] + '.wav')
    if not os.path.exists(wav): print(L['id'], 'MISSING — voice it: tts.py --only', L['id']); bad += 1; continue
    heard = transcribe(wav, a.model); r = score(L['text'], heard); L['heard'] = heard; L['match'] = r
    ok = r >= 0.93; bad += not ok
    print(L['id'], r, '' if ok else f'\n  WANT : {L["text"]}\n  HEARD: {heard}')
json.dump(lines, open(os.path.join(vo, 'lines.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('all lines match' if not bad else f'{bad} line(s) to check or re-voice')
