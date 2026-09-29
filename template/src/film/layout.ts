/** Two formats from one timeline. Stage = where scenes draw; the caption band sits below it and nothing else goes there. */
export type Fmt = {
  vertical: boolean;
  W: number;
  H: number;
  stage: { x: number; y: number; w: number; h: number };
  capY: number; // caption band center
  capW: number;
  capSize: number;
  s: number; // type scale for scene text
};

export const HORIZONTAL: Fmt = { vertical: false, W: 1920, H: 1080, stage: { x: 0, y: 0, w: 1920, h: 905 }, capY: 990, capW: 1560, capSize: 44, s: 1 };
export const VERTICAL: Fmt = { vertical: true, W: 1080, H: 1920, stage: { x: 0, y: 110, w: 1080, h: 1440 }, capY: 1700, capW: 960, capSize: 52, s: 1 };
