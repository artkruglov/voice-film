# voice-film

A Claude Code skill that turns research, a report or a product story into a **voice-led explainer film** (1–4 min): script → AI voiceover → background music → burned-in captions → 16:9 and 9:16 MP4s, rendered from code in [Remotion](https://www.remotion.dev/).

Everything on screen is code: real screenshots under a spring camera, charts that count up, re-typeset quotes, stamps. Scene timing comes from the measured voiceover, so re-voicing a line re-times the whole film. Numbers come from data files and are labelled (model / measured / estimate).

## Install

```bash
git clone https://github.com/artkruglov/voice-film ~/.claude/skills/voice-film
```

Then ask Claude Code for "a film / video with voiceover about …" or run `/voice-film`. The full workflow is in [SKILL.md](SKILL.md).

## Pipeline

| Step | Tool |
|---|---|
| Script → voice lines | `scripts/extract_lines.py` (`## N.` sections, `**Voice:** "…"` paragraphs) |
| Voice | `scripts/tts.py` — Gemini TTS or GPT audio via OpenRouter, voice samples to choose by ear |
| Voice check | `scripts/verify_voice.py` — transcribes each line and compares it with the script |
| Music | `scripts/music.py` — Google Lyria via OpenRouter |
| Timeline + captions | `scripts/timing.py` — silence detection, captions ≤ 42 chars snapped to real pauses |
| Mix | `scripts/mix.py` — voice at −16 LUFS, music ducked under speech, optional voice colour presets |
| Frames | `template/` — Remotion project with scene examples and parts; `scripts/review.sh` stills |
| Frame review | `scripts/review_frames.py` — a vision model as a second pair of eyes |
| Render | `scripts/render.sh` — 120 fps master → motion blur → 30 fps, both formats, contact sheets |
| Check | `scripts/check.sh` — streams, decode, loudness |
| Web copy | `scripts/web_compress.py` + `scripts/embed_page.py` — one self-contained HTML page with the video |

Remotion itself has its own license (free for individuals and small companies; check [remotion.dev/license](https://www.remotion.dev/license) for company use).

Requirements: Node ≥ 20, ffmpeg/ffprobe, Python 3 (standard library only), bun or `npx tsx` for review stills. An [OpenRouter](https://openrouter.ai) key for voice, music and checks, passed only through the environment: `OPENROUTER_API_KEY=…` or `OPENROUTER_KEY_FILE=<path>`. `OPENROUTER_API_BASE` points the scripts at your own egress if OpenRouter is blocked in your region.

Script examples and caption rules are tuned for Russian (numbers spelled out, no breaks after short prepositions); English scripts work with `**Voice:** "…"`.

## Credits

- `template/src/kit/` (camera, cursor, springs, punchlines, dither) — [Rieranthony/product-film-skill](https://github.com/Rieranthony/product-film-skill), MIT.
- Vision frame review, voice colour presets and several pitfalls — ideas from [vakovalskii/nd-video-studio](https://github.com/vakovalskii/nd-video-studio), MIT.

## License

MIT
