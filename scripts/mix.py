"""Audio mix (ffmpeg, no Remotion <Audio>): voice lines placed from src/film/timing.json + ducked music.
- voice: each audio/vo/<id>.wav delayed to its `audioAt`, summed, gained to -16 LUFS integrated (measured, linear gain), true peak kept <= -1 dBTP
- music: audio/music/bgm.mp3 is extended to the film length, if shorter, with a 4 s crossfade into a second pass (from --loop-from, 30 s by default);
  gain envelope from the speech spans: -18 dB below the voice level under speech, -10 dB in gaps, 0.3 s duck-in / 0.4 s release;
  1 s fade-in, 2 s fade-out at the end
- output: <project>/out/mix.wav (48 kHz stereo) + out/mix-info.json
- no audio/music/bgm.mp3 -> voice only
- --voice-fx: optional narrator processing before loudness (EQ + compression, presets spread far apart because
  small EQ moves are inaudible after normalization; idea from vakovalskii/nd-video-studio voice_fx.py, MIT)
Usage: mix.py <project> [--under -18] [--gap -10] [--lufs -16] [--voice-fx natural|warm|broadcast|radio] [--loop-from 30]"""
import json, os, re, subprocess, sys
if len(sys.argv) < 2: sys.exit('usage: mix.py <project> [--under -18] [--gap -10] [--lufs -16] [--voice-fx natural|warm|broadcast|radio] [--loop-from 30]')
ROOT = os.path.abspath(sys.argv[1])
arg = lambda k, d: float(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
T = json.load(open(os.path.join(ROOT, 'src', 'film', 'timing.json')))
OUT = os.path.join(ROOT, 'out'); os.makedirs(OUT, exist_ok=True)
TMP = os.path.join(OUT, 'tmp'); os.makedirs(TMP, exist_ok=True)
sarg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
FX = {'natural': '',
      'warm': 'highpass=f=70,bass=g=3:f=120:w=0.7,equalizer=f=3000:t=q:w=1.2:g=1.5,acompressor=threshold=0.12:ratio=2.5:attack=8:release=120:makeup=2',
      'broadcast': 'highpass=f=80,bass=g=5:f=110:w=0.7,equalizer=f=3000:t=q:w=1.2:g=2.5,acompressor=threshold=0.1:ratio=4:attack=5:release=90:makeup=3',
      'radio': 'highpass=f=350,lowpass=f=3400,equalizer=f=2000:t=q:w=1:g=4,acompressor=threshold=0.1:ratio=8:attack=3:release=60:makeup=3'}
VFX = sarg('--voice-fx', 'natural')
if VFX not in FX: sys.exit(f'--voice-fx: one of {", ".join(FX)}')
LOOP_FROM = arg('--loop-from', 30.0)
DUR = T['duration']; VOICE_LUFS = arg('--lufs', -16.0); UNDER = arg('--under', -18.0); GAP = arg('--gap', -10.0)
ff = lambda *a: subprocess.run(['ffmpeg', '-v', 'error', '-y', *a], check=True)

def loudness(path):
    err = subprocess.run(['ffmpeg', '-nostats', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    summ = err[err.rfind('Summary:'):]
    return float(re.search(r'I:\s+(-?[\d.]+) LUFS', summ).group(1)), float(re.search(r'Peak:\s+(-?[\d.]+) dBFS', summ).group(1)), float(re.search(r'LRA:\s+(-?[\d.]+) LU', summ).group(1))

# 1. voice
ins, fc = [], ''
for i, l in enumerate(T['lines']):
    ins += ['-i', os.path.join(ROOT, 'audio', 'vo', f"{l['id']}.wav")]
    ms = int(round(l['audioAt'] * 1000))
    fc += f"[{i}]aresample=48000,aformat=channel_layouts=mono,adelay={ms}[v{i}];"
n = len(T['lines'])
fc += ''.join(f'[v{i}]' for i in range(n)) + f'amix=inputs={n}:normalize=0:duration=longest,apad=whole_dur={DUR},atrim=0:{DUR}[vo]'
raw = os.path.join(TMP, 'voice-raw.wav')
ff(*ins, '-filter_complex', fc, '-map', '[vo]', '-c:a', 'pcm_s24le', raw)
I, peak, _ = loudness(raw)
g = VOICE_LUFS - I
voice = os.path.join(TMP, 'voice.wav')
if FX[VFX]:
    fxd = os.path.join(TMP, 'voice-fx.wav'); ff('-i', raw, '-af', FX[VFX], '-c:a', 'pcm_s24le', fxd); raw = fxd
    I, peak, _ = loudness(raw); g = VOICE_LUFS - I
ff('-i', raw, '-af', f'volume={g:.2f}dB,alimiter=limit=0.89:attack=2:release=50:level=disabled', '-c:a', 'pcm_s24le', voice)
vI, vPeak, _ = loudness(voice)

# 2. music: extend, envelope, fades
mus = os.path.join(ROOT, 'audio', 'music', 'bgm.mp3')
if not os.path.exists(mus):
    ff('-i', voice, '-af', 'aformat=channel_layouts=stereo', '-ar', '48000', '-c:a', 'pcm_s24le', os.path.join(OUT, 'mix.wav'))
    print(json.dumps({'voice_I': vI, 'music': None, 'duration': DUR})); sys.exit()
mI, _, _ = loudness(mus)
g_gap = VOICE_LUFS + GAP - mI; g_under = VOICE_LUFS + UNDER - mI
spans = [(l['speechStart'], l['speechEnd']) for l in T['lines']]
w = [f"clip((t-{s - 0.3:.3f})/0.3,0,1)*clip(({e + 0.4:.3f}-t)/0.4,0,1)" for s, e in spans]
duck = w[0]
for x in w[1:]: duck = f"max({duck},{x})"
vol = f"pow(10,({g_gap:.2f}+({g_under - g_gap:.2f})*{duck})/20)"
script = os.path.join(TMP, 'music.fc')
open(script, 'w').write(
    f"[0]aresample=48000,aformat=channel_layouts=stereo[a];[1]aresample=48000,aformat=channel_layouts=stereo,atrim=start={LOOP_FROM},asetpts=PTS-STARTPTS[b];"
    f"[a][b]acrossfade=d=4:c1=tri:c2=tri,atrim=0:{DUR},asetpts=PTS-STARTPTS,volume='{vol}':eval=frame,afade=t=in:d=1,afade=t=out:st={DUR - 2:.3f}:d=2[m]")
music = os.path.join(TMP, 'music.wav')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', mus, '-i', mus, '-filter_complex_script', script, '-map', '[m]', '-c:a', 'pcm_s24le', music], check=True)

# 3. mix
mix = os.path.join(OUT, 'mix.wav')
ff('-i', voice, '-i', music, '-filter_complex', '[0]aformat=channel_layouts=stereo[v];[v][1]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.89:level=disabled[o]', '-map', '[o]', '-ar', '48000', '-c:a', 'pcm_s24le', mix)
xI, xPeak, xLRA = loudness(mix)
info = {'voice_fx': VFX, 'voice_raw_I': I, 'voice_gain_dB': round(g, 2), 'voice_I': vI, 'voice_peak_dBFS': vPeak, 'music_source_I': mI,
        'music_gain_gap_dB': round(g_gap, 2), 'music_gain_under_dB': round(g_under, 2), 'mix_I': xI, 'mix_peak_dBFS': xPeak, 'mix_LRA': xLRA, 'duration': DUR}
json.dump(info, open(os.path.join(OUT, 'mix-info.json'), 'w'), indent=1)
print(json.dumps(info))
