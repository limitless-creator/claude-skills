// The reel: camera picture framed per beat, then each beat's elements, then optional captions.
// Everything is read from beats.json, brand.json and words.json (a copy of work/words_tl.json).
// For a look beats.json can't express, add a component in kit.tsx and a new element type below.
import React from "react";
import { AbsoluteFill, OffthreadVideo, staticFile, useCurrentFrame } from "remotion";
import beatsJson from "./beats.json";
import wordsJson from "./words.json";
import { Beat, cameraAt, FPS, freeSide, H, W } from "./camera";
import { brand, Card, FONT, List, Num, Picture, Text } from "./kit";

export const data = beatsJson as { duration: number; video?: string; beats: Beat[] };
const beats = data.beats;
const words = wordsJson as { w: string; s: number | null; e: number | null }[];

// where graphics go for each free side (x, width), and the slots they stack into from the top
const COL = { left: { x: 40, w: 430 }, right: { x: 610, w: 430 }, full: { x: 90, w: 900 } };
const SLOT_Y = { top: 170, upper: 330, middle: 760, chest: 1100, bottom: 1450 };

const Element: React.FC<{ el: any; t: number; end: number; side: "left" | "right" | "full"; k: number }> = ({ el, t, end, side, k }) => {
  const col = COL[side];
  const box = { x: el.x ?? col.x, w: el.w ?? col.w, y: el.y ?? SLOT_Y[(el.pos as keyof typeof SLOT_Y) ?? (k === 0 ? "upper" : "middle")] };
  const live = { t, at: el.at, end: el.end ?? end, ...box };
  switch (el.type) {
    case "text": return <Text {...live} lead={el.lead} keyText={el.key} size={el.size ?? (side === "full" ? 120 : 88)} align={el.align} />;
    case "card": return <Card {...live} title={el.title} body={el.body} img={el.img} />;
    case "image": case "logo": return <Picture {...live} img={el.src} frame={el.type === "image" && el.frame !== false} grey={el.grey} credit={el.credit} />;
    case "number": return <Num {...live} value={el.value} prefix={el.prefix} suffix={el.suffix} label={el.label} size={el.size} />;
    case "list": return <List {...live} items={el.items} gap={el.gap} />;
    default: return null;
  }
};

const Captions: React.FC<{ t: number }> = ({ t }) => {
  if (brand.captions.style !== "words") return null;
  const said = words.filter((w) => w.s !== null && w.e !== null);
  const i = said.findIndex((w) => t >= (w.s as number) && t < (w.e as number) + 0.25);
  if (i < 0) return null;
  // groups of up to 3 words that never run across a sentence end
  let start = 0;
  for (let k = 0, n = 0; k <= i; k++, n++) { if (n === 3 || (k > 0 && /[.!?]$/.test(said[k - 1].w))) { start = k; n = 0; } }
  let stop = start;
  while (stop < said.length && stop - start < 3 && (stop === start || !/[.!?]$/.test(said[stop - 1].w))) stop++;
  const chunk = said.slice(start, stop);
  return (
    <div style={{ position: "absolute", left: 60, width: W - 120, top: SLOT_Y[brand.captions.position as keyof typeof SLOT_Y] ?? SLOT_Y.bottom, textAlign: "center",
      fontFamily: FONT.heading, fontWeight: 800, fontSize: brand.captions.size, color: brand.colors.text, textShadow: "0 4px 24px rgba(0,0,0,.6)" }}>
      {chunk.map((w, k) => <span key={k} style={{ color: start + k === i ? brand.colors.accent : undefined }}>{w.w} </span>)}
    </div>
  );
};

export const Reel: React.FC = () => {
  const t = useCurrentFrame() / FPS;
  const cam = cameraAt(t, beats);
  return (
    <AbsoluteFill style={{ background: brand.colors.bg, overflow: "hidden" }}>
      <AbsoluteFill style={{ transform: `translate(${cam.tx}px, ${cam.ty}px) scale(${cam.s})`, transformOrigin: "50% 50%",
        borderRadius: cam.s < 1 ? brand.card.radius / cam.s : 0, overflow: "hidden" }}>
        <OffthreadVideo src={staticFile(data.video ?? "camera_1x.mp4")} style={{ width: W, height: H }} />
      </AbsoluteFill>
      {beats.map((b, i) => {
        const end = i + 1 < beats.length ? beats[i + 1].t0 : data.duration;
        return b.elements.map((el, k) => <Element key={`${b.id}-${k}`} el={el} t={t} end={end} side={freeSide(b)} k={k} />);
      })}
      <Captions t={t} />
    </AbsoluteFill>
  );
};
