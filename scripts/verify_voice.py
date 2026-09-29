#!/usr/bin/env python3
"""Transcribe every audio/vo/<id>.wav with a Gemini text model (audio input) and compare with lines.json.
Prints a word-level similarity per line; anything under 0.93 is shown in full so you can re-voice it (tts.py --only <id>).
Usage: verify_voice.py <project> [--model google/gemini-3.8-flash] [--lang русскую]"""
import argparse, base64, difflib, json, os, re, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _or import post
ap = argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--model', default='google/gemini-3.8-flash'); ap.add_argument('--lang', default='русскую')
a = ap.parse_args()
vo = os.path.join(a.project, 'audio', 'vo'); lines = json.load(open(os.path.join(vo, 'lines.json'), encoding='utf-8'))
norm = lambda s: re.sub(r'[^\w ]', '', s.lower().replace('ё', 'е')).split()
bad = 0
for L in lines:
    with tempfile.NamedTemporaryFile(suffix='.mp3') as tmp:
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', os.path.join(vo, L['id'] + '.wav'), '-b:a', '64k', tmp.name], check=True)
        b = base64.b64encode(open(tmp.name, 'rb').read()).decode()
    body = {'model': a.model, 'messages': [{'role': 'user', 'content': [
        {'type': 'text', 'text': f'Дословно расшифруй эту {a.lang} речь. Верни только текст, числа — словами, как произнесено.'},
        {'type': 'input_audio', 'input_audio': {'data': b, 'format': 'mp3'}}]}]}
    heard = json.load(post('/chat/completions', body, timeout=180))['choices'][0]['message']['content'].strip()
    r = difflib.SequenceMatcher(None, norm(L['text']), norm(heard)).ratio(); L['heard'] = heard; L['match'] = round(r, 3)
    ok = r >= 0.93; bad += not ok
    print(L['id'], round(r, 3), '' if ok else f'\n  WANT : {L["text"]}\n  HEARD: {heard}')
json.dump(lines, open(os.path.join(vo, 'lines.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('all lines match' if not bad else f'{bad} line(s) to check or re-voice')
