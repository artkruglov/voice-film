---
name: voice-film
description: Make a voice-led explainer film (1–4 min) from research, a report or a product story — script with voiceover, AI voice (Gemini TTS via OpenRouter), generated background music (Lyria), burned-in captions, 16:9 + 9:16, rendered in Remotion from code with real product screenshots/prototype frames, charts and quotes. Use when the user asks for a film, video, ролик, фильм, «видео с голосом/озвучкой», a product launch/promo film, a video summary of research/decisions for leadership or Telegram, or wants to turn a presentation/report into a video. Russian or English. Not for pure music clips or screen recordings.
---

# Voice film

A film that **tells a story with a voice**: every scene is cut to the voiceover, captions are burned in (Telegram and feeds autoplay muted), music sits quietly under the voice, and every number on screen comes from a data file. Built from code (Remotion) — no video generation, so it is exact, re-renderable and cheap.

Proven on a 3-minute decision film for leadership (Russian) and an 83-second product launch film (English). Arcs for both are in `references/story.md`.

## Tools in this skill

`<skill>` = this skill's directory (`~/.claude/skills/voice-film`). Every script takes the **project directory** as its first argument; nothing is tied to one repo or topic.

| Step | Script |
|---|---|
| New project | `cp -R <skill>/template <project> && cd <project> && npm install` |
| Script check | `python3 <skill>/scripts/script_lint.py <project>/SCRIPT.md` (errors must be fixed before voicing) |
| Script → voice lines | `python3 <skill>/scripts/extract_lines.py <project>/SCRIPT.md <project>` |
| Voice samples | `python3 <skill>/scripts/tts.py --samples "<a real line>" --voices Kore,Aoede,Charon,Orus --out <project>/audio/samples` |
| Voice all lines | `python3 <skill>/scripts/tts.py <project> --voice Kore` (`--only s3b` to redo one; every take is transcribed and retried) |
| Check the voice | `python3 <skill>/scripts/verify_voice.py <project>` (transcribes and compares) |
| Music | `python3 <skill>/scripts/music.py <project> [--prompt "..."]` |
| Timeline + captions | `python3 <skill>/scripts/timing.py <project>` → `src/film/timing.json` |
| Mix | `python3 <skill>/scripts/mix.py <project> [--voice-fx warm]` → `out/mix.wav` (settings saved in `<project>/mix.json`) |
| Review stills | `bash <skill>/scripts/review.sh <project> <project>/out/review/r1 <frame@30fps>...` |
| Vision review | `python3 <skill>/scripts/review_frames.py <project>/out/review/r1/*.png --brief "16:9 film"` (second pair of eyes) |
| Render | `bash <skill>/scripts/render.sh <project> [--fast] [--poster SEC] [--name film]` |
| Verify | `bash <skill>/scripts/check.sh <project> [name]` (render.sh runs it) |
| Web embed | `web_compress.py in.mp4 out.mp4 --max-mb 3.5` → `embed_page.py out.mp4 poster.png page.html --title ...` |

Requirements: node ≥ 20, ffmpeg/ffprobe, python3, bun (for review stills; falls back to `npx tsx`). OpenRouter key for voice/music/verification — see Keys.

## Workflow

### 1. Brief (ask little, decide defaults)
Collect: audience and the **one decision/idea** the film must land; source materials (reports, data JSON, screenshots, prototype); length (default 1:30–2:30); language (default Russian; English works the same); where it plays (Telegram/meeting/feeds → both 16:9 and 9:16). Read the sources yourself — the story comes from them, not from the user retelling it.
**For a product film, read the product, not just its marketing**: code, docs, user stories, the changelog/journal. Build a fact sheet: what is shipped vs early access vs planned, exact offers and limits, what must NOT be claimed (unverified metrics, planned features, testimonials you don't have), and which real media exist (outputs, screenshots, clips). Delegating this sweep to a subagent works well. Marketing copy is often ahead of (or different from) what the code does — the film follows the code.

### 1.5 Story frame — approved before the script
A `## STORY` block at the top of `SCRIPT.md`: logline, **the one sentence the viewer repeats**, hero, stakes, turn, the main number, what we must not claim. Arcs for decision / launch / research / tutorial films, the hook and ending rules and a golden template are in [`references/story.md`](references/story.md).

### 2. Script — `SCRIPT.md`, approved before any audio
Sections `## N. Title · 0:00–0:10`, each with **Кадр:** (what we see), **Титр:** (on-screen text) and one or more voice paragraphs (`**Голос:** «…»` or `**Voice:** "…"`) with per-line direction:
```
**Голос:** «Одна-две фразы, разговорные, как человек рассказывает.» {pre=0.6 air=1.0 mood=intrigue pace=slow hold=1.2}
```
`mood`/`pace` become a delivery tag for the voice, `hold` is a mute beat (picture + music) after the line — see `references/story.md`.
Rules:
- ~15 characters per second of voice (Gemini). 1:30 ≈ 1 000–1 200 characters, 2:30 ≈ 1 800–2 200.
- Hook ≤ 60 chars; one hero through the film; ≤ 8 spoken numbers (≤ 1 per line, each with a comparison); lines ≤ 200 chars; lists ≤ 3 items; the last line is meaning, not logistics. `script_lint.py` checks all of this.
- Spoken style: short sentences, one idea per sentence. **Numbers as words** in the voice («сто двадцать пять»), digits on screen.
- Every number traces to a data file; label it on screen: «модель», «замер 12.03», «оценка». Never round up claims.
- Decision films: problem today → what we tried and why it fails (with numbers) → the solution → proof on the real thing → what must be fixed, **each fix shown on a concrete example** → the decisions asked → where the materials are.
- Quotes from a product/agent are **re-typeset** into bubbles, not screenshots of chats.
- Real product screenshots only from sanitized/blurred copies (no personal data, emails, balances). Prototype frames and synthetic data are fine.

Run `script_lint.py` until there are no errors (and every warning is fixed or deliberately kept). Show the story + script to the user and wait for approval. Then `extract_lines.py`.

### 3. Voice
- Run `tts.py --samples` with one real line on 3–4 voices; let the user pick (they listen, you can't). Default if they don't care: **Kore** (female, calm) on `gemini`; alternative engine `gpt` (voices marin/cedar/ash).
- Voice all lines **sequentially** (parallel requests to Gemini TTS hang). One voice + one engine for the whole film.
- Direction: on Gemini, `mood`/`pace` go in as a short bracket tag (`[slowly, curious] text`) — a sentence-style prefix is read aloud and the `instructions` field is ignored. Tags sometimes get read aloud anyway or make the model paraphrase, so `tts.py` transcribes every take, retries twice and falls back to no tag. Expect this on 1–2 lines per film.
- `verify_voice.py` for the whole film at the end: anything < 0.93 → rephrase the text (spell numbers, drop abbreviations the model misreads) and re-voice that line only.

### 4. Music
`music.py` — Lyria (`google/lyria-3-pro-preview`, stream) gives ~3 min of instrumental. Prompt: calm, no vocals, no drops, unobtrusive under voice. `mix.py` ducks it (−18 dB under speech, −10 dB in gaps, fades) and loops it if the film is longer (`--loop-from` sets where the second pass starts). No music file → voice-only mix.
Lyria refuses prompts that mention AI, video, a product or a brand (`PROHIBITED_CONTENT`, no charge): describe only the music — genre, BPM, instruments, mood, "no vocals".
Voice colour: `--voice-fx natural` (default) / `warm` / `broadcast` / `radio`. Presets are deliberately far apart — small EQ moves vanish after loudness normalization. Let the user pick by ear on a short draft.

### 5. Timeline
`timing.py` measures each voice file (silence detection), places lines back to back (`pre` lead-in, `air` after), splits captions into ≤ 42-char phrases (never inside a spoken number or after a short preposition) and snaps sentence ends to real pauses. Scenes read it through `src/film/cues.ts`:
- `scene("s2")` → the section's window; `para("s2b")` → one paragraph's window;
- `C("s4b", "Итоги квартала")` → the second the voice says it — **use this for every sub-moment** (counter lands, screenshot swaps, stamp slams). No literal times in scene code, so re-voicing re-times the whole film.

### 6. Build scenes (`<project>/src/film/scenes/*.tsx`)
Start from `template/src/film/scenes/example.tsx` and `parts.tsx`:
- `win(t, a, b)` blur-in/out window; `land(t, at)` punchline landing; `grow/count` for numbers;
- `Shot` — a screenshot under a spring camera with `Ring` highlights (put images in `public/shots/`, crop tool/debug bars off);
- `Bars` (animated horizontal bars), `Bubble` (re-typeset quote), `Stamp` (e.g. «P0 · Fix name»), `Tag`, `Box`;
- `kit/` — camera, springs, cursor + cursor paths, punchlines, dither.
- Real clips: `OffthreadVideo` (muted) inside `Sequence from` + `Loop` plays product videos in their frames; Chrome renders them fine at the 120 fps master.
Layout: `layout.ts` gives a **stage** and a **caption band**; nothing important goes in the band. Design both formats from the start (`f.vertical`): 9:16 is its own layout (stack comparisons, zoom screenshots ≥ 2×), not a squeezed 16:9. Tokens and the type scale (`TYPE`, three levels, minimum sizes) in `tokens.ts` — replace colours and fonts with the product's own.
Rules for composition, motion, match moves, screenshots, captions and safe zones: [`references/visual-grammar.md`](references/visual-grammar.md). Read it before writing scenes.

### 7. Review before the full render
`review.sh` stills at 2–3 frames per scene in both formats (frame = seconds × 30; in zsh pass frames as an array: `F=(60 240 …); review.sh … "${F[@]}"`). Look for: text cut off, overlaps, captions over key visuals, empty frames, wrong numbers. Then run `review_frames.py` on the same stills (a vision model lists problems per frame; exit code 1 on "fix needed") — it catches small text and overlaps you skimmed past, but misreads grid timestamps, so it never replaces your own look. Fix, re-check. Then `render.sh --fast` for a full draft and look at `out/film-contact.png` and the vertical contact sheet.

### 8. Final render and verification
`render.sh` (120 fps master → motion blur → 30 fps, ~7 min render per minute of film per format). `check.sh` must show: video + audio streams, equal durations, `decode ok`, ≈ −16 LUFS, peak ≤ −1 dBFS. Look at a few frames of the finished mp4s yourself (ffmpeg `-ss`) before reporting.

### 9. Deliver
Send both mp4s (16:9 and 9:16) and the poster. For a web page that accepts one HTML file only (an internal wiki or artifact host, ≤ 5 MB): `web_compress.py … --max-mb 3.5` then `embed_page.py`, publish the page, open the link and check that the player loads. Record paths, voice, engine, music source and loudness in the project `README.md`.

## Keys
- Voice, music and verification use OpenRouter. The key goes **only into the environment of the command**: `OPENROUTER_API_KEY=… python3 …` or `OPENROUTER_KEY_FILE=<path>`. Never print it, write it into the project, a commit or a message.
- If the user points you to where a key lives, check it with `GET https://openrouter.ai/api/v1/key` (HTTP 200) and show at most a masked prefix; pass it via a temporary file in `OPENROUTER_KEY_FILE` and delete that file when done.
- OpenRouter answers 403 from some regions. Run from another network or set `OPENROUTER_API_BASE` to your own egress/proxy with the same API. Scripts retry 429/5xx (honouring `Retry-After`).
- Model notes (check `GET /api/v1/models` — TTS models may be missing from the list but still work on `/audio/speech`): `google/gemini-3.8-flash-tts` (pcm only), `openai/gpt-audio(-mini)` (stream, pcm16), `google/lyria-3-pro-preview` / `lyria-3-clip-preview` (stream).

## Traps
- A background agent building the film may stall on long renders — check `out/` yourself and finish verification rather than restarting.
- Don't re-encode a file another process is still writing (partial mp4 → "Invalid NAL unit size").
- Script edits → re-run `extract_lines.py` (ids shift if you add paragraphs), re-voice changed lines, then `timing.py`.
- Remotion Studio is silent: audio is muxed by ffmpeg after rendering.
- ffmpeg `loudnorm` resamples to 192 kHz and can eat the tail — `mix.py` measures and applies linear gain instead; if you add `loudnorm` anywhere, follow it with `aresample=48000` and pad to length.
- TTS swallows or swaps words in ways that are easy to miss by ear. When `verify_voice.py` flags a line, rephrase it rather than re-voicing the same text.
- Web copies: `web_compress.py` uses `-tune animation`, which keeps flat UI and small text sharp at high crf.
- `render.sh` re-runs `timing.py` and `mix.py`; mix options persist in `<project>/mix.json`, so a chosen `--voice-fx` survives the render.
- Captions: breaks go after a dash, never before it; if a caption starts with "—", re-run `timing.py` after updating the skill.

## Credits
- `template/src/kit/` — from [Rieranthony/product-film-skill](https://github.com/Rieranthony/product-film-skill) (MIT, see `template/src/kit/LICENSE`).
- Frame review by a vision model, voice-colour presets and several traps — ideas from [vakovalskii/nd-video-studio](https://github.com/vakovalskii/nd-video-studio) (MIT).
