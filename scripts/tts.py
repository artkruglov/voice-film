#!/usr/bin/env python3
"""Voice every line of <project>/audio/vo/lines.json -> audio/vo/<id>.wav (24 kHz mono).
Engines (OpenRouter):
  gemini  google/gemini-3.8-flash-tts via /audio/speech, pcm only (default; fast, natural Russian). Voices: Kore, Aoede (female), Charon, Orus (male), and other Gemini voice names.
  gpt     openai/gpt-audio via chat completions with audio output (stream). Voices: marin, cedar, ash, alloy, coral, sage, verse…
Usage:
  tts.py <project> --voice Kore [--engine gemini] [--only s2a,s3b]      # voice the film (sequential; parallel requests hang)
  tts.py --samples "<one line of the script>" --voices Kore,Aoede,Charon,Orus [--engine gemini] --out <dir>   # mp3 samples to pick a voice
Keep one voice and one engine for the whole film. Write numbers as words in the script if the engine misreads digits."""
import argparse, base64, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _or import post, sse

MODELS = {'gemini': 'google/gemini-3.8-flash-tts', 'gpt': 'openai/gpt-audio'}

def pcm(engine, voice, text, style=''):
    if engine == 'gemini':
        r = post('/audio/speech', {'model': MODELS[engine], 'input': text, 'voice': voice, 'response_format': 'pcm'}, timeout=180)
        return r.read()
    body = {'model': MODELS[engine], 'stream': True, 'modalities': ['text', 'audio'], 'audio': {'voice': voice, 'format': 'pcm16'},
            'messages': [{'role': 'system', 'content': 'Ты диктор. Произнеси вслух ровно тот текст, который дал пользователь, слово в слово, без добавлений. ' + (style or 'Спокойный уверенный голос, естественные паузы.')},
                         {'role': 'user', 'content': text}]}
    buf = bytearray()
    for ch in sse(post('/chat/completions', body, timeout=300)):
        for c in ch.get('choices', []):
            a = (c.get('delta') or {}).get('audio') or {}
            if a.get('data'): buf += base64.b64decode(a['data'])
    return bytes(buf)

def save(raw, out):
    if not raw: sys.exit(f'empty audio for {out}')
    fmt = ['-c:a', 'libmp3lame', '-b:a', '96k'] if out.endswith('.mp3') else []
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-f', 's16le', '-ar', '24000', '-ac', '1', '-i', 'pipe:0', *fmt, out], input=raw, check=True)
    d = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', out], capture_output=True, text=True).stdout.strip()
    return float(d)

ap = argparse.ArgumentParser()
ap.add_argument('project', nargs='?'); ap.add_argument('--voice'); ap.add_argument('--engine', default='gemini', choices=MODELS)
ap.add_argument('--only'); ap.add_argument('--style', default=''); ap.add_argument('--samples'); ap.add_argument('--voices'); ap.add_argument('--out')
a = ap.parse_args()
if a.samples:
    os.makedirs(a.out or '.', exist_ok=True)
    for v in (a.voices or 'Kore,Aoede,Charon,Orus').split(','):
        p = os.path.join(a.out or '.', f'{a.engine}-{v}.mp3'); print(p, round(save(pcm(a.engine, v, a.samples, a.style), p), 1), 's')
    sys.exit()
if not a.project or not a.voice: ap.error('project and --voice are required (or use --samples)')
vo = os.path.join(a.project, 'audio', 'vo'); lines = json.load(open(os.path.join(vo, 'lines.json'), encoding='utf-8'))
only = set(a.only.split(',')) if a.only else None
total = 0
for L in lines:
    if only and L['id'] not in only: continue
    d = save(pcm(a.engine, a.voice, L['text'], a.style), os.path.join(vo, L['id'] + '.wav')); total += d
    print(L['id'], round(d, 2), 's')
meta = os.path.join(vo, 'voice.json'); json.dump({'engine': a.engine, 'model': MODELS[a.engine], 'voice': a.voice}, open(meta, 'w'))
print('total', round(total, 1), 's')
