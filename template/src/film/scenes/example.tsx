import { scene, C, L, LINES } from "../cues";
import { Box, Bars, land, win } from "../parts";
import type { Fmt } from "../layout";
import { T } from "../tokens";

/**
 * Example scenes. Pattern for every scene:
 *   const w = win(t, ...scene("s1")); if (!w) return null;       // visible only in its window, blur in/out
 *   moments come from the voice: C("s1a", "Сто двадцать")        // the caption that says it
 * Numbers on screen must come from data files (import a JSON the project generates), not typed by hand.
 */
export function Title({ t, f }: { t: number; f: Fmt }) {
  const w = win(t, ...scene("s1"));
  if (!w) return null;
  const at = L("s1a").beat;
  return (
    <Box x={0} y={f.stage.y} w={f.W} h={f.stage.h} style={{ ...w, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 18 }}>
      <div style={{ ...land(t, at + 0.2), fontSize: f.vertical ? 72 : 88, fontWeight: 750, letterSpacing: "-0.02em", textAlign: "center", padding: "0 60px" }}>Заголовок фильма</div>
      <div style={{ ...land(t, at + 0.6), fontSize: 30, color: T.tx2 }}>подзаголовок · дата · источник</div>
    </Box>
  );
}

export function Numbers({ t, f }: { t: number; f: Fmt }) {
  if (!LINES.some((l) => l.id.startsWith("s2"))) return null;
  const w = win(t, ...scene("s2"));
  if (!w) return null;
  const at = L("s2a").beat + 0.3;
  return (
    <Box style={w}>
      <Bars t={t} at={at} f={f} x={f.vertical ? 80 : 160} y={f.stage.y + (f.vertical ? 300 : 260)} w={f.vertical ? 920 : 1600}
        rows={[{ label: "Было", value: 120, color: T.warn, sub: "пример" }, { label: "Стало", value: 45, color: T.accent, sub: "пример" }]} />
    </Box>
  );
}

export function End({ t, f }: { t: number; f: Fmt }) {
  const last = LINES[LINES.length - 1];
  if (!last || LINES.length < 3) return null;
  const w = win(t, last.beat, 1e9);
  if (!w) return null;
  return (
    <Box x={0} y={f.stage.y} w={f.W} h={f.stage.h} style={{ ...w, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 20 }}>
      <div style={{ ...land(t, last.beat + 0.2), fontSize: 64, fontWeight: 750 }}>Финальная мысль</div>
      <div style={{ ...land(t, last.beat + 0.6), fontSize: 28, color: T.accent }}>ссылка на материалы</div>
    </Box>
  );
}
// Unused helper kept for reference: C("s2a", "Стало") returns the second the voice says «Стало…».
void C;
