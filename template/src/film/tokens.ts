/** Design tokens. Replace with the product's own (colors from its CSS / design system; hex only). Keep a light, calm base for voice-led films. */
export const T = {
  bg: "#f9f9f7",
  card: "#fcfcfb",
  page: "#edeff0",
  ring: "rgba(11,11,11,0.10)",
  line: "#e1e0d9",
  tx: "#0b0b0b",
  tx2: "#52514e",
  mut: "#898781",
  accent: "#2a78d6", // "with the product / agent"
  warn: "#eb6834", // "by hand / problem"
  neutral: "#b9b7ad",
  accentSoft: "#eaf2fc",
  bad: "#d03b3b",
  good: "#0bb552",
} as const;

export const FONT = '-apple-system, "SF Pro Display", system-ui, "Segoe UI", Roboto, sans-serif';
export const SERIF = '"Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif';
export const MONO = '"SF Mono", ui-monospace, "JetBrains Mono", Menlo, monospace';

/** Type scale: three levels per frame at most. [horizontal, vertical] px; nothing smaller than `label`. */
export const TYPE = { display: [92, 84], headline: [56, 52], body: [34, 36], label: [24, 28] } as const;
export const ts = (k: keyof typeof TYPE, vertical: boolean) => TYPE[k][vertical ? 1 : 0];
