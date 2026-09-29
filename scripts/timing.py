"""Timeline and captions from the voice files (voice-led cut: scenes follow the voice, not a beat grid).
- measures each line (audio/vo/<id>.wav): speech start/end and internal pauses (ffmpeg silencedetect, -40 dB, 0.18 s)
- places lines back to back: each line starts at its paragraph's visual beat (PRE), trailing air (AIR) after the speech
- captions: text from lines.json, split into phrases <= 42 chars; timed by character count inside the line's speech,
  with sentence ends snapped to the nearest measured pause (so captions change where the voice actually breathes)
Per-line lead-in/air come from lines.json fields `pre`/`air` (defaults 0.5 / 0.6).
Usage: timing.py <project> [--maxc 42]  -> <project>/src/film/timing.json"""
import json, os, re, subprocess, sys
ROOT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else sys.exit('usage: timing.py <project> [--maxc 42]')
VO = os.path.join(ROOT, 'audio', 'vo')
lines = json.load(open(os.path.join(VO, 'lines.json')))
MAXC = int(sys.argv[sys.argv.index('--maxc') + 1]) if '--maxc' in sys.argv else 42
PRE = {L['id']: L.get('pre', 0.5) for L in lines}
AIR = {L['id']: L.get('air', 0.6) for L in lines}
# Russian number words: a caption never breaks between two of them (extend for other languages)
NUM = set('один одна одну два две три четыре пять пяти шесть семь восемь девять десять одиннадцать двенадцать тринадцать четырнадцать двадцать двадцати тридцать тридцати сорок пятьдесят сто двести триста шестьсот шестисот'.split())

def probe(path):
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path], capture_output=True, text=True).stdout)
    err = subprocess.run(['ffmpeg', '-i', path, '-af', 'silencedetect=noise=-40dB:d=0.18', '-f', 'null', '-'], capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', err)]
    en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', err)]
    sil = list(zip(st, en + [dur] * (len(st) - len(en))))
    s0 = sil[0][1] if sil and sil[0][0] < 0.02 else 0.0
    s1 = sil[-1][0] if sil and sil[-1][1] > dur - 0.02 else dur
    pauses = [(a, b) for a, b in sil if a > s0 + 0.05 and b < s1 - 0.05]
    return dur, s0, s1, pauses

def phrases(text):
    """Sentences; a long sentence is cut into balanced phrases <= MAXC chars by a small DP:
    breaks after , : ; or before a dash are cheap, breaks after a short word (и, а, в, на, те...) or before «же» are expensive."""
    out = []
    for sent in re.split(r'(?<=[.!?…»“])\s+(?=[А-ЯЁA-Z«„])', text.strip()):
        w = sent.split()
        if len(sent) <= MAXC:
            out.append((sent, True)); continue
        n = len(w); INF = 1e18; target = len(sent) / -(-len(sent) // MAXC)
        best = [INF] * (n + 1); prev = [0] * (n + 1); best[0] = 0
        for j in range(1, n + 1):
            for i in range(j):
                chunk = ' '.join(w[i:j]); L = len(chunk)
                if L > MAXC: continue
                cost = (L - target) ** 2 * 0.3
                if L < 14: cost += 400
                if j < n:
                    last, nxt = w[j - 1], w[j]
                    if last[-1] in ',:;': cost -= 250
                    elif nxt == '—': cost -= 120
                    if len(last.strip(',:;')) <= 3 and last[-1] not in ',:;': cost += 900
                    if nxt in ('же', 'ли', 'бы'): cost += 900
                    if last.lower().strip(',:;') in NUM and nxt.lower().strip(',:;') in NUM: cost += 600  # keep spoken numbers whole
                if best[i] + cost < best[j]: best[j] = best[i] + cost; prev[j] = i
        cuts = []; j = n
        while j > 0: cuts.append((prev[j], j)); j = prev[j]
        for i, j in reversed(cuts): out.append((' '.join(w[i:j]), j == n))
    return out

def cap_times(text, s0, s1, pauses):
    ph = phrases(text)
    total = sum(len(p) for p, _ in ph)
    speech = (s1 - s0) - sum(b - a for a, b in pauses)
    def est(c):  # char offset -> time, proportional over speech with pauses removed
        t = s0 + speech * c / total
        for a, b in pauses:
            if t > a: t += b - a
        return t
    anchors = [(0, s0)]; c = 0; used = set()
    for i, (p, end) in enumerate(ph):
        c += len(p)
        if end and i < len(ph) - 1:
            e = est(c); best = min(((abs((a + b) / 2 - e), k) for k, (a, b) in enumerate(pauses) if k not in used), default=None)
            if best and best[0] < 1.2 and pauses[best[1]][0] > anchors[-1][1]:
                a, b = pauses[best[1]]; used.add(best[1]); anchors += [(c, a), (c + 0.001, b)]
    anchors.append((total, s1))
    def at(c):
        for (c0, t0), (c1, t1) in zip(anchors, anchors[1:]):
            if c0 <= c <= c1: return t0 + (t1 - t0) * (c - c0) / max(c1 - c0, 1e-9)
        return s1
    res = []; c = 0
    for p, _ in ph:
        res.append([p, at(c + 0.002), at(c + len(p))]); c += len(p)
    return res

t = 0.0; out = {'lines': [], 'captions': []}
for L in lines:
    i = L['id']; dur, s0, s1, pauses = probe(os.path.join(VO, f'{i}.wav'))
    start = t + PRE[i]                       # the visual beat of this paragraph
    at = start - s0                          # audio file offset so speech begins exactly at `start`
    end = start + (s1 - s0)
    out['lines'].append({'id': i, 'beat': round(t, 3), 'audioAt': round(at, 3), 'speechStart': round(start, 3), 'speechEnd': round(end, 3), 'trimStart': round(s0, 3), 'fileDur': dur, 'next': round(end + AIR[i], 3)})
    for p, a, b in cap_times(L['text'], s0, s1, pauses):
        out['captions'].append({'line': i, 'text': p, 'start': round(at + a, 3), 'end': round(at + b, 3)})
    t = end + AIR[i]
# captions hold until the next one starts if the gap is short
C = out['captions']
for x, y in zip(C, C[1:]):
    if 0 < y['start'] - x['end'] < 0.6: x['end'] = y['start']
out['duration'] = round(t, 3)
json.dump(out, open(os.path.join(ROOT, 'src', 'film', 'timing.json'), 'w'), ensure_ascii=False, indent=1)
print('duration', out['duration'], 'captions', len(C), 'max chars', max(len(c['text']) for c in C))
for l in out['lines']: print(l['id'], l['beat'], l['speechStart'], l['speechEnd'], l['next'])
