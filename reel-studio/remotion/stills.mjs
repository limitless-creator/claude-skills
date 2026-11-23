// Still pictures at given seconds.   node stills.mjs COMP sec1 sec2 ...  -> out/still_<sec>.png
// SERVE=<bundle dir> skips re-bundling.
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";
import path from "node:path";
const [comp, ...secs] = process.argv.slice(2);
const serveUrl = process.env.SERVE || await bundle({ entryPoint: path.resolve("src/index.ts"), symlinkPublicDir: true });
const composition = await selectComposition({ serveUrl, id: comp });
for (const s of secs) {
  const frame = Math.min(composition.durationInFrames - 1, Math.round(Number(s) * composition.fps));
  await renderStill({ composition, serveUrl, frame, output: path.resolve(`out/still_${s}.png`) });
  console.log("still", s);
}
