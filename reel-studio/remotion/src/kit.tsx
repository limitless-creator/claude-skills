// Building blocks for reel graphics. Every look comes from brand.json; nothing here is anyone's personal style.
// Claude may add new components per reel; keep them driven by brand.json the same way.
import React from "react";
import { continueRender, delayRender, Easing, Img, staticFile } from "remotion";
import { getAvailableFonts } from "@remotion/google-fonts";
import brandJson from "./brand.json";

export type Brand = typeof brandJson;
export const brand: Brand = brandJson;

// ---------- fonts: any Google Fonts family named in brand.json ----------
const families = Array.from(new Set(Object.values(brand.fonts).filter(Boolean) as string[]));
const fontHandle = delayRender("fonts");
Promise.all(families.map(async (fam) => {
  const f = getAvailableFonts().find((x) => x.fontFamily.toLowerCase() === fam.toLowerCase());
  if (!f) { console.warn(`Font "${fam}" is not on Google Fonts; using a system font`); return; }
  const mod = await f.load();
  const info = mod.getInfo();
  for (const style of ["normal", "italic"] as const) {
    const weights = Object.keys((info.fonts as any)[style] ?? {}).filter((w) => ["400", "500", "600", "700", "800"].includes(w));
    if (weights.length) mod.loadFont(style, { weights, subsets: ["latin"] });
  }
})).finally(() => continueRender(fontHandle));
const ff = (fam?: string) => (fam ? `"${fam}", ` : "") + "system-ui, -apple-system, 'Segoe UI', sans-serif";
export const FONT = { heading: ff(brand.fonts.heading), body: ff(brand.fonts.body), accent: ff((brand.fonts as any).accent || brand.fonts.heading) };

// ---------- motion helpers ----------
const ease = Easing.bezier(0.22, 1, 0.36, 1);
export const clamp = (x: number) => Math.min(1, Math.max(0, x));
export const p = (t: number, at: number, d = 0.3) => ease(clamp((t - at) / d));
const pop = (t: number, at: number, d = 0.3) => { const x = clamp((t - at) / d); return x === 0 ? 0 : ease(x) + Math.sin(x * Math.PI) * 0.1 * (1 - x * 0.5); };
const alive = (t: number, end: number, d = 0.1) => 1 - clamp((t - end) / d);

const SHADOW = brand.card.shadow === "soft" ? "0 24px 60px rgba(0,0,0,0.35), 0 6px 16px rgba(0,0,0,0.22)" : "none";
const TEXT_SHADOW = "0 4px 30px rgba(0,0,0,0.45), 0 2px 6px rgba(0,0,0,0.35)";
const upper = (s: string) => (brand.text.case === "upper" ? s.toUpperCase() : s);
export const cardStyle = (): React.CSSProperties => brand.card.style === "none"
  ? { color: brand.colors.text, textShadow: TEXT_SHADOW }
  : brand.card.style === "glass"
  ? { background: "rgba(14,13,12,0.55)", border: "1.5px solid rgba(255,255,255,0.14)", backdropFilter: "blur(18px)", color: brand.colors.text, borderRadius: brand.card.radius, boxShadow: SHADOW }
  : { background: brand.colors.card, color: brand.colors.cardText, borderRadius: brand.card.radius, boxShadow: SHADOW };

export type Box = { x: number; y: number; w: number };
export type Live = { t: number; at: number; end: number };

/** Pops its children in at `at` and fades them out at `end`. */
export const Pop: React.FC<Live & Box & { children: React.ReactNode; style?: React.CSSProperties }> = ({ t, at, end, x, y, w, children, style }) => {
  const k = pop(t, at), o = clamp((t - at) / 0.08) * alive(t, end);
  if (k <= 0 || o <= 0) return null;
  return <div style={{ position: "absolute", left: x, top: y, width: w, opacity: o, transform: `scale(${k})`, transformOrigin: "50% 50%", ...style }}>{children}</div>;
};

/** Small lead-in words + big key words. lead is optional. */
export const Text: React.FC<Live & Box & { lead?: string; keyText: string; size?: number; align?: "left" | "center" }> =
  ({ t, at, end, x, y, w, lead, keyText, size = 104, align = "center" }) => {
    const o = alive(t, end);
    if (t < at || o <= 0) return null;
    const a = p(t, at), b = p(t, lead ? at + 0.35 : at);
    const leadStyle: React.CSSProperties = brand.text.lead === "accent-italic"
      ? { fontFamily: FONT.accent, fontStyle: "italic", fontWeight: 500 } : { fontFamily: FONT.body, fontWeight: 500 };
    return (
      <div style={{ position: "absolute", left: x, top: y, width: w, textAlign: align, opacity: o, textShadow: TEXT_SHADOW, color: brand.colors.text }}>
        {lead && <div style={{ ...leadStyle, fontSize: size * 0.5, lineHeight: 1.05, opacity: a, transform: `translateY(${(1 - a) * 14}px)` }}>{lead}</div>}
        <div style={{ fontFamily: FONT.heading, fontWeight: 800, fontSize: size, lineHeight: 0.95, marginTop: lead ? size * 0.1 : 0,
          opacity: b, filter: `blur(${(1 - b) * 10}px)`, transform: `translateY(${(1 - b) * 24}px)` }}>{upper(keyText)}</div>
      </div>
    );
  };

export const Card: React.FC<Live & Box & { title?: string; body?: string; img?: string }> = ({ title, body, img, ...l }) => (
  <Pop {...l}>
    <div style={{ ...cardStyle(), padding: 30, fontFamily: FONT.body }}>
      {img && <Img src={src(img)} style={{ width: "100%", borderRadius: Math.max(0, brand.card.radius - 10), display: "block", marginBottom: title || body ? 20 : 0 }} />}
      {title && <div style={{ fontFamily: FONT.heading, fontWeight: 800, fontSize: 52, lineHeight: 1 }}>{title}</div>}
      {body && <div style={{ fontSize: 34, lineHeight: 1.25, marginTop: title ? 12 : 0, opacity: 0.85 }}>{body}</div>}
    </div>
  </Pop>
);

/** A real picture (photo, screenshot, logo) shown as it really looks. */
export const Picture: React.FC<Live & Box & { img: string; frame?: boolean; grey?: boolean; credit?: string }> = ({ img, frame = true, grey, credit, ...l }) => (
  <Pop {...l}>
    <div style={frame ? { ...cardStyle(), padding: 10, background: "#fff" } : undefined}>
      <Img src={src(img)} style={{ width: "100%", display: "block", borderRadius: frame ? Math.max(0, brand.card.radius - 10) : 0, filter: grey ? "grayscale(1)" : undefined }} />
      {credit && <div style={{ fontFamily: FONT.body, fontSize: 18, color: "#555", padding: "8px 6px 2px" }}>{credit}</div>}
    </div>
  </Pop>
);

/** A number that counts up, with an optional label under it. */
export const Num: React.FC<Live & Box & { value: number; prefix?: string; suffix?: string; label?: string; size?: number }> =
  ({ value, prefix = "", suffix = "", label, size = 200, ...l }) => {
    const k = p(l.t, l.at, 0.9);
    const shown = Number.isInteger(value) ? Math.round(value * k) : (value * k).toFixed(1);
    return (
      <Pop {...l} style={{ textAlign: "center" }}>
        <div style={{ fontFamily: FONT.heading, fontWeight: 800, fontSize: size, lineHeight: 0.9, color: brand.colors.accent, textShadow: TEXT_SHADOW }}>{prefix}{shown}{suffix}</div>
        {label && <div style={{ fontFamily: FONT.body, fontWeight: 600, fontSize: size * 0.22, color: brand.colors.text, textShadow: TEXT_SHADOW, marginTop: 10 }}>{upper(label)}</div>}
      </Pop>
    );
  };

/** Items appear one after another, `gap` seconds apart. */
export const List: React.FC<Live & Box & { items: string[]; gap?: number }> = ({ items, gap = 0.45, ...l }) => (
  <>{items.map((it, k) => (
    <Pop key={k} {...l} at={l.at + k * gap} y={l.y + k * 104}>
      <div style={{ ...cardStyle(), padding: "18px 26px", fontFamily: FONT.body, fontWeight: 700, fontSize: 40 }}>{it}</div>
    </Pop>
  ))}</>
);

/** files in public/ by name, or full URLs */
export const src = (s: string) => (/^https?:|^data:/.test(s) ? s : staticFile(s));
