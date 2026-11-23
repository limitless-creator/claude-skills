// Framing of the camera picture per beat. The person moves; the free side holds the graphics.
// tx moves the picture: negative = person goes left. At scale s the most tx can be is (s-1)*W/2 before an edge shows.
import { Easing } from "remotion";

export const W = 1080, H = 1920, FPS = 30;
export type Framing = { s: number; tx: number; ty: number };
export type FramingName = "wide" | "left" | "right" | "tight" | "shrink";
export type Beat = { id: string; t0: number; framing: FramingName | Framing; cut?: "hard" | "ease"; elements: any[] };

const maxTx = (s: number) => Math.max(0, ((s - 1) * W) / 2);
export const NAMED: Record<FramingName, Framing> = {
  wide: { s: 1, tx: 0, ty: 0 },
  left: { s: 1.35, tx: -maxTx(1.35), ty: 0 },   // person left, free side right
  right: { s: 1.35, tx: maxTx(1.35), ty: 0 },   // person right, free side left
  tight: { s: 1.3, tx: 0, ty: 0 },
  shrink: { s: 0.72, tx: 0, ty: 120 },          // picture smaller, inside the brand background
};

export const framingOf = (b: Beat): Framing => {
  const f = typeof b.framing === "string" ? NAMED[b.framing] : b.framing;
  // never let a zoom show the picture's edge
  return f.s >= 1 ? { ...f, tx: Math.max(-maxTx(f.s), Math.min(maxTx(f.s), f.tx)) } : f;
};

/** Which side holds graphics for a beat: the side the person is NOT on. */
export const freeSide = (b: Beat): "left" | "right" | "full" => {
  const f = framingOf(b);
  return f.s > 1 && f.tx < -20 ? "right" : f.s > 1 && f.tx > 20 ? "left" : "full";
};

const ease = Easing.bezier(0.22, 1, 0.36, 1);
/** Camera at time t: hard cut on the beat's first frame, or a 6-frame ease from the previous framing. */
export const cameraAt = (t: number, beats: Beat[]): Framing => {
  let i = 0;
  beats.forEach((b, k) => { if (t >= b.t0) i = k; });
  const cur = framingOf(beats[i]);
  if (i === 0 || beats[i].cut !== "ease") return cur;
  const prev = framingOf(beats[i - 1]);
  const x = ease(Math.min(1, (t - beats[i].t0) / (6 / FPS)));
  return { s: prev.s + (cur.s - prev.s) * x, tx: prev.tx + (cur.tx - prev.tx) * x, ty: prev.ty + (cur.ty - prev.ty) * x };
};
