import { Easing, Img, Loop, OffthreadVideo, Sequence, staticFile, useVideoConfig } from "remotion";
import type { CSSProperties, ReactNode } from "react";
import { camera as springCamera } from "../kit/camera";
import { clamp01 } from "../kit/time";
import { step } from "../kit/spring";
import { FONT, T } from "./tokens";
import { CAPTIONS } from "./cues";
import type { Fmt } from "./layout";

const landEase = Easing.bezier(0.22, 1, 0.36, 1);

/** Blur-in rise (punchline landing) — 0.3 s. */
export function land(t: number, at: number, rise = 28): CSSProperties {
  const u = landEase(clamp01((t - at) / 0.3));
  return { opacity: u, filter: u < 1 ? `blur(${(1 - u) * 14}px)` : undefined, translate: `0 ${(1 - u) * rise}px` };
}

/** A scene window: blur in 0.3 s, blur out 0.25 s at the end. Returns null style when hidden. */
export function win(t: number, from: number, to: number) {
  if (t < from - 0.01 || t > to + 0.01) return null;
  const v = clamp01((t - from) / 0.3) * (1 - clamp01((t - (to - 0.25)) / 0.25));
  return { opacity: v, filter: v < 1 ? `blur(${(1 - v) * 10}px)` : undefined } as CSSProperties;
}

export const grow = (t: number, at: number) => Math.min(1, step(t - at, { stiffness: 120, damping: 22 }));
export const count = (t: number, at: number, n: number) => Math.round(n * grow(t, at));

export function Box({ x = 0, y = 0, w, h, style, children }: { x?: number; y?: number; w?: number; h?: number; style?: CSSProperties; children?: ReactNode }) {
  return <div style={{ position: "absolute", left: x, top: y, width: w, height: h, fontFamily: FONT, boxSizing: "border-box", ...style }}>{children}</div>;
}

export function Tag({ children, color = T.tx2, bg = "#efeee9", size = 22 }: { children: ReactNode; color?: string; bg?: string; size?: number }) {
  return <span style={{ display: "inline-flex", alignItems: "center", height: size * 1.75, padding: `0 ${size * 0.7}px`, borderRadius: 999, background: bg, color, fontSize: size, fontWeight: 600, whiteSpace: "nowrap" }}>{children}</span>;
}

/** Burned-in captions: one phrase at a time in the fixed band, blur swap, up to 2 lines. */
export function Captions({ t, f, hide }: { t: number; f: Fmt; hide?: (text: string) => boolean }) {
  return (
    <>
      {CAPTIONS.map((c, i) => {
        if (hide?.(c.text)) return null; // a kinetic phrase on screen is the caption for that second
        // sequential swap: out-fade finishes at `end`, the next caption fades in from its `start` — never two at once
        if (t < c.start || t >= c.end) return null;
        const v = clamp01((t - c.start) / 0.1) * (1 - clamp01((t - (c.end - 0.1)) / 0.1));
        return (
          <Box key={i} x={(f.W - f.capW) / 2} y={f.capY} w={f.capW} style={{ translate: "0 -50%", textAlign: "center", fontSize: f.capSize, fontWeight: 600, lineHeight: 1.25, color: T.tx, opacity: v, filter: v < 1 ? `blur(${(1 - v) * 6}px)` : undefined, textWrap: "balance" as CSSProperties["textWrap"] }}>
            {c.text}
          </Box>
        );
      })}
    </>
  );
}

export type CamKey = readonly [t: number, cx: number, cy: number, zoom: number];
export type Frame = { src: string; at: number };

/**
 * A product screenshot under a camera, inside the stage. Camera keys are image pixels
 * (the point at the stage center) and zoom (1 = the image fits the stage with a margin).
 * `overlay` draws in image coordinates, so rings and labels ride with the camera.
 */
export function Shot({ t, f, w, h, frames, keys, overlay, margin = 60, box }: { t: number; f: Fmt; w: number; h: number; frames: Frame[]; keys: CamKey[]; overlay?: (toScreen: (x: number, y: number) => { x: number; y: number }, scale: number) => ReactNode; margin?: number; box?: { x: number; y: number; w: number; h: number } }) {
  const st = box ?? f.stage;
  const base = Math.min((st.w - 2 * margin) / w, (st.h - 2 * margin) / h);
  const cam = springCamera(t, keys);
  const scale = base * cam.zoom;
  const cx = st.x + st.w / 2;
  const cy = st.y + st.h / 2;
  const left = cx - cam.x * scale;
  const top = cy - cam.y * scale;
  const toScreen = (x: number, y: number) => ({ x: left + x * scale, y: top + y * scale });
  return (
    <>
      <div style={{ position: "absolute", left: st.x, top: st.y, width: st.w, height: st.h, overflow: "hidden" }}>
        <div style={{ position: "absolute", left: left - st.x, top: top - st.y, width: w * scale, height: h * scale, borderRadius: 14 * scale, overflow: "hidden", boxShadow: `0 0 0 1px ${T.ring}`, background: T.page }}>
          {frames.map((fr, i) => {
            const next = frames[i + 1]?.at ?? Infinity;
            if (t < fr.at - 0.01 || t > next + 0.3) return null;
            const u = i === 0 ? 1 : clamp01((t - fr.at) / 0.25);
            return <Img key={fr.src} src={staticFile(fr.src)} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", opacity: u }} />;
          })}
        </div>
      </div>
      {overlay ? overlay(toScreen, scale) : null}
    </>
  );
}

/** Rounded highlight ring around an image rect, in screen space. */
export function Ring({ a, b, v, color = T.accent }: { a: { x: number; y: number }; b: { x: number; y: number }; v: number; color?: string }) {
  if (v <= 0) return null;
  return <div style={{ position: "absolute", left: a.x - 6, top: a.y - 6, width: b.x - a.x + 12, height: b.y - a.y + 12, borderRadius: 16, boxShadow: `0 0 0 4px ${color}, 0 0 0 12px rgba(42,120,214,0.15)`, opacity: v }} />;
}



/** Horizontal bars that grow in (a count lands with its bar). rows: label, value, color, optional sub-label. */
export function Bars({ t, at, rows, max, x, y, w, f, gap = 22, h = 54 }: { t: number; at: number; rows: { label: string; value: number; color: string; sub?: string }[]; max?: number; x: number; y: number; w: number; f: Fmt; gap?: number; h?: number }) {
  const m = max ?? Math.max(...rows.map((r) => r.value));
  const labelW = f.vertical ? 0 : 360;
  return (
    <>
      {rows.map((r, i) => {
        const g = grow(t, at + i * 0.35);
        const top = y + i * (h + gap + (f.vertical ? 44 : 0));
        return (
          <Box key={i} x={x} y={top} w={w} style={{ opacity: clamp01((t - at - i * 0.35) / 0.2) }}>
            <div style={{ position: "absolute", left: 0, top: f.vertical ? 0 : h / 2, translate: f.vertical ? undefined : "0 -50%", fontSize: 30, fontWeight: 650, color: T.tx }}>
              {r.label}
              {r.sub ? <span style={{ display: "block", fontSize: 20, fontWeight: 500, color: T.mut }}>{r.sub}</span> : null}
            </div>
            <div style={{ position: "absolute", left: labelW, top: f.vertical ? 44 : 0, width: (w - labelW - 150) * (r.value / m) * g, height: h, borderRadius: 6, background: r.color }} />
            <div style={{ position: "absolute", right: 0, top: (f.vertical ? 44 : 0) + h / 2, translate: "0 -50%", fontSize: 40, fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>{Math.round(r.value * g)}</div>
          </Box>
        );
      })}
    </>
  );
}

/** A chat bubble with a re-typeset quote (never a screenshot of someone else's UI text). */
export function Bubble({ t, at, x, y, w, text, who = "agent" }: { t: number; at: number; x: number; y: number; w: number; text: string; who?: "agent" | "user" }) {
  return (
    <Box x={x} y={y} w={w} style={{ ...land(t, at, 16), display: "flex", gap: 16, justifyContent: who === "user" ? "flex-end" : "flex-start" }}>
      {who === "agent" ? <div style={{ width: 44, height: 44, borderRadius: 22, background: T.accent, flex: "none" }} /> : null}
      <div style={{ padding: "14px 20px", borderRadius: 18, background: who === "user" ? T.accentSoft : T.card, boxShadow: `0 0 0 1px ${T.ring}`, fontSize: 30, lineHeight: 1.35 }}>{text}</div>
    </Box>
  );
}

/** A tilted rubber stamp (e.g. a priority + fix name) that slams in. */
export function Stamp({ t, at, x, y, label, tag, color = T.bad }: { t: number; at: number; x: number; y: number; label: string; tag?: string; color?: string }) {
  const u = grow(t, at);
  if (t < at) return null;
  return (
    <Box x={x} y={y} style={{ translate: "-50% -50%", rotate: "-3deg", scale: `${1.6 - 0.6 * u}`, opacity: clamp01((t - at) / 0.12), display: "inline-flex", alignItems: "center", gap: 12, padding: "10px 18px", border: `3px solid ${color}`, borderRadius: 12, color, fontSize: 34, fontWeight: 750, whiteSpace: "nowrap", background: "rgba(255,255,255,0.7)" }}>
      {tag ? <span style={{ background: color, color: "#fff", borderRadius: 6, padding: "0 10px", fontSize: 28 }}>{tag}</span> : null}
      {label}
    </Box>
  );
}

/** A real product clip in a frame: starts playing at `from` (absolute seconds) and loops every `loop` seconds. Muted — audio is the mix. */
export function Clip({ x, y, w, h, src, from, loop = 5, radius = 18, style }: { x: number; y: number; w: number; h: number; src: string; from: number; loop?: number; radius?: number; style?: CSSProperties }) {
  const { fps } = useVideoConfig();
  return (
    <div style={{ position: "absolute", left: x, top: y, width: w, height: h, borderRadius: radius, overflow: "hidden", boxShadow: `0 0 0 1px ${T.ring}`, ...style }}>
      <Sequence from={Math.round(from * fps)} layout="none">
        <Loop durationInFrames={Math.round(loop * fps)} layout="none">
          <OffthreadVideo src={staticFile(src)} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        </Loop>
      </Sequence>
    </div>
  );
}

/** Match move helper: interpolate a rect (the same object travelling between scenes). */
export type Rect = { x: number; y: number; w: number; h: number };
export const lerpRect = (a: Rect, b: Rect, u: number): Rect => ({ x: a.x + (b.x - a.x) * u, y: a.y + (b.y - a.y) * u, w: a.w + (b.w - a.w) * u, h: a.h + (b.h - a.h) * u });
