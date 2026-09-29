import timing from "./timing.json";

/**
 * The film is cut to the voice: every paragraph starts at its line's beat (scripts/timing.py measures
 * the voice files) and sub-moments land on caption starts, which are snapped to the voice's real pauses.
 * Never put literal times in scene code — use L(id).beat, C(id, "prefix"), scene(id).
 */
export type Line = { id: string; beat: number; audioAt: number; speechStart: number; speechEnd: number; next: number };
export type Caption = { line: string; text: string; start: number; end: number };
const T = timing as unknown as { lines: Line[]; captions: Caption[]; duration: number };
export const LINES = T.lines;
export const DURATION = T.duration;
export const CAPTIONS = T.captions;

export function L(id: string): Line {
  const line = LINES.find((l) => l.id === id);
  if (!line) throw new Error(`no line ${id} — re-run timing.py after changing the script`);
  return line;
}

/** Start of the first caption of line `id` that begins with `prefix` (the moment the voice says it). */
export function C(id: string, prefix: string): number {
  const cap = CAPTIONS.find((c) => c.line === id && c.text.startsWith(prefix));
  if (!cap) throw new Error(`no caption «${prefix}» in ${id}`);
  return cap.start;
}

/** Window of a script section: from its first line's beat to the next section's first beat (e.g. scene("s2") covers s2a, s2b…). */
export function scene(section: string): [number, number] {
  const idx = LINES.findIndex((l) => l.id.replace(/[a-z]$/, "") === section);
  if (idx < 0) throw new Error(`no section ${section}`);
  const next = LINES.findIndex((l, i) => i > idx && l.id.replace(/[a-z]$/, "") !== section);
  return [LINES[idx].beat, next < 0 ? DURATION : LINES[next].beat];
}

/** Window of one line (paragraph): its beat to the next line's beat. */
export function para(id: string): [number, number] {
  const i = LINES.findIndex((l) => l.id === id);
  return [LINES[i].beat, LINES[i + 1]?.beat ?? DURATION];
}
