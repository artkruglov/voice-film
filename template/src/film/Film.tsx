import { AbsoluteFill } from "remotion";
import { useTime } from "../kit/time";
import { FONT, T } from "./tokens";
import { HORIZONTAL, VERTICAL } from "./layout";
import { Captions } from "./parts";
import { Title, Numbers, End } from "./scenes/example";

/**
 * The film: one component per script section, each draws only inside its own window (scene("sN")).
 * Replace the example scenes with the film's own (src/film/scenes/*.tsx). Captions always last.
 */
export function Film({ vertical }: { fps: number; vertical: boolean }) {
  const t = useTime();
  const f = vertical ? VERTICAL : HORIZONTAL;
  return (
    <AbsoluteFill style={{ background: T.bg, fontFamily: FONT, color: T.tx, WebkitFontSmoothing: "antialiased", overflow: "hidden" }}>
      <Title t={t} f={f} />
      <Numbers t={t} f={f} />
      <End t={t} f={f} />
      <Captions t={t} f={f} />
    </AbsoluteFill>
  );
}
