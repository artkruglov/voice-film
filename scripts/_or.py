"""OpenRouter helpers. The key comes from $OPENROUTER_API_KEY or from the file in $OPENROUTER_KEY_FILE.
Never print it, never write it into the project, never put it on a command line."""
import json, os, sys, time, urllib.request, urllib.error
# OPENROUTER_API_BASE: your own egress/proxy with the same API (OpenRouter answers 403 from some regions)
BASE = os.environ.get('OPENROUTER_API_BASE', 'https://openrouter.ai/api/v1').rstrip('/')

def key():
    k = os.environ.get('OPENROUTER_API_KEY')
    if not k and os.environ.get('OPENROUTER_KEY_FILE'): k = open(os.environ['OPENROUTER_KEY_FILE']).read().strip()
    if not k: sys.exit('set OPENROUTER_API_KEY (or OPENROUTER_KEY_FILE=<path>) in the environment of this command')
    return k

def post(path, body, timeout=300, stream=False, retries=3):
    data = json.dumps(body).encode()
    for attempt in range(retries):
        req = urllib.request.Request(BASE + path, data=data, headers={'Authorization': 'Bearer ' + key(), 'Content-Type': 'application/json'})
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.HTTPError as e:
            msg = e.read()[:400].decode(errors='replace')
            if e.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                ra = e.headers.get('Retry-After') if e.headers else None
                time.sleep(float(ra) if ra and ra.replace('.', '', 1).isdigit() else 3 * (attempt + 1)); continue
            if e.code == 403: msg += '  (403 can mean the region is blocked: run from another network or set OPENROUTER_API_BASE)'
            sys.exit(f'OpenRouter {e.code}: {msg}')
        except Exception as e:  # timeouts, DNS
            if attempt < retries - 1: time.sleep(3 * (attempt + 1)); continue
            sys.exit(f'OpenRouter request failed: {e}')

def sse(resp):
    for line in resp:
        line = line.decode().strip()
        if not line.startswith('data:') or line == 'data: [DONE]': continue
        try: yield json.loads(line[5:])
        except Exception: continue
