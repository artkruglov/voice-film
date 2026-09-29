"""Voice check helpers shared by tts.py and verify_voice.py: transcribe a line with a Gemini text model and score it."""
import base64, difflib, json, os, re, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _or import post
MODEL = 'google/gemini-3.8-flash'
UK_US = {'colour': 'color', 'colours': 'colors', 'favourite': 'favorite', 'centre': 'center', 'organise': 'organize', 'realise': 'realize'}

def norm(s):
    w = re.sub(r'[^\w ]', '', re.sub(r'[-–—]', ' ', s.lower().replace('ё', 'е'))).split()
    return [UK_US.get(x, x) for x in w]

def transcribe(wav, model=MODEL):
    with tempfile.NamedTemporaryFile(suffix='.mp3') as tmp:
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', wav, '-b:a', '64k', tmp.name], check=True)
        b = base64.b64encode(open(tmp.name, 'rb').read()).decode()
    body = {'model': model, 'messages': [{'role': 'user', 'content': [
        {'type': 'text', 'text': 'Transcribe this speech verbatim, in the language it is spoken. Return only the text; write numbers as words, exactly as pronounced.'},
        {'type': 'input_audio', 'input_audio': {'data': b, 'format': 'mp3'}}]}]}
    return json.load(post('/chat/completions', body, timeout=180))['choices'][0]['message']['content'].strip()

def score(want, heard):
    # compact spellings ("YouTube" / "You Tube") compare equal
    a, b = ''.join(norm(want)), ''.join(norm(heard))
    return round(max(difflib.SequenceMatcher(None, norm(want), norm(heard)).ratio(), difflib.SequenceMatcher(None, a, b).ratio()), 3)
