#!/usr/bin/env python3
"""Voice every line of <project>/audio/vo/lines.json -> audio/vo/<id>.wav (24 kHz mono).
Engines (OpenRouter):
  gemini  google/gemini-3.8-flash-tts via /audio/speech, pcm only (default; fast, natural Russian). Voices: Kore, Aoede (female), Charon, Orus (male), and other Gemini voice names.
  gpt     openai/gpt-audio via chat completions with audio output (stream). Voices: marin, cedar, ash, alloy, coral, sage, verse…
Usage:
  tts.py <project> --voice Kore [--engine gemini] [--only s2a,s3b]      # voice the film (sequential; parallel requests hang)
  tts.py --samples "<one line of the script>" --voices Kore,Aoede,Charon,Orus [--engine gemini] --out <dir>   # mp3 samples to pick a voice
Every take is transcribed and retried if it drifts (--no-check to skip).
Keep one voice and one engine for the whole film. Write numbers as words in the script if the engine misreads digits."""
import argparse, base64, http.client, json, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _or import post, sse
from _vc import transcribe, score

MODELS = {'gemini': 'google/gemini-3.8-flash-tts', 'gpt': 'openai/gpt-audio'}

# Voice direction per line (lines.json: mood / pace / stress).
# gemini: a short tag in square brackets before the text, e.g. "[slowly, curious] text" — the model follows it and does not
#   read it aloud (a sentence-style prefix IS read aloud; the `instructions` field is ignored). Tags are English for any language.
# gpt: the same notes go into the system prompt.
MOOD_TAG = {'neutral': '', 'intrigue': 'curious, leaning in', 'concern': 'serious, weighty', 'relief': 'relieved, warm smile',
            'confident': 'confident, crisp', 'warm': 'warm, gentle', 'excited': 'excited, bright',
            'интрига': 'curious, leaning in', 'тревога': 'serious, weighty', 'облегчение': 'relieved, warm smile',
            'уверенность': 'confident, crisp', 'тепло': 'warm, gentle', 'нейтрально': ''}
PACE_TAG = {'slow': 'slowly', 'fast': 'energetic, a bit faster', 'normal': '', 'медленно': 'slowly', 'быстро': 'energetic, a bit faster'}

def tags(L):
    t = [x for x in (PACE_TAG.get(L.get('pace', ''), L.get('pace', '')), MOOD_TAG.get(L.get('mood', ''), L.get('mood', ''))) if x]
    return ', '.join(t)

def direction(L, base=''):
    """Human-readable delivery note for the gpt system prompt."""
    parts = [base] if base else []
    if tags(L): parts.append('Delivery: ' + tags(L))
    if L.get('stress'): parts.append(f'Stress the words "{L["stress"]}"')
    return '. '.join(parts)

def pcm(engine, voice, text, style='', tag='', tries=4):
    """One line of audio; the whole request is retried if the connection drops mid-body (IncompleteRead, resets)."""
    for k in range(tries):
        try: return _pcm(engine, voice, text, style, tag)
        except (http.client.HTTPException, OSError) as e:
            if k == tries - 1: raise
            print(f'  retry after {type(e).__name__}', file=sys.stderr); time.sleep(5 * (k + 1))

def _pcm(engine, voice, text, style='', tag=''):
    if engine == 'gemini':
        r = post('/audio/speech', {'model': MODELS[engine], 'input': (f'[{tag}] ' if tag else '') + text, 'voice': voice, 'response_format': 'pcm'}, timeout=180)
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
ap.add_argument('--only'); ap.add_argument('--no-check', action='store_true'); ap.add_argument('--style', default=''); ap.add_argument('--samples'); ap.add_argument('--voices'); ap.add_argument('--out')
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
    st, tg = direction(L, a.style), tags(L)
    out = os.path.join(vo, L['id'] + '.wav')
    # Direction tags sometimes get read aloud or make the model paraphrase: check every take, retry, last try without the tag.
    attempts = [tg, tg, ''] if tg else ['']
    for k, t in enumerate(attempts):
        d = save(pcm(a.engine, a.voice, L['text'], st if t or a.engine != 'gemini' else a.style, t), out)
        if a.no_check: break
        heard = transcribe(out); r = score(L['text'], heard)
        if r >= 0.93: break
        print(f'  {L["id"]} take {k + 1}: {r} «{heard[:70]}» — retry' + (' without the tag' if k + 1 < len(attempts) and not attempts[k + 1] and t else ''))
    total += d
    print(L['id'], round(d, 2), 's', ('· ' + (t if a.engine == 'gemini' else st)) if (t or st) else '', '' if a.no_check else f'· match {r}')
meta = os.path.join(vo, 'voice.json'); json.dump({'engine': a.engine, 'model': MODELS[a.engine], 'voice': a.voice, 'style': a.style}, open(meta, 'w'))
print('total', round(total, 1), 's')
