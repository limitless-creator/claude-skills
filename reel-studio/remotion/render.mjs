// Render the reel.   node render.mjs COMP OUT.mp4      (COMP: Reel, or Part1 for the first ~10 s)
// env: CONC=3 (parallel frames), MUTED=1 (picture only)
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import path from "node:path";
const [comp = "Reel", outArg = "out/reel.mp4"] = process.argv.slice(2);
// symlinkPublicDir: link public/ instead of copying it on every render (copies fill the disk and hang renders)
const serveUrl = process.env.SERVE || await bundle({ entryPoint: path.resolve("src/index.ts"), symlinkPublicDir: true });
const composition = await selectComposition({ serveUrl, id: comp });
let last = -1;
await renderMedia({ composition, serveUrl, codec: "h264", crf: 16, outputLocation: path.resolve(outArg), muted: process.env.MUTED === "1",
  concurrency: Number(process.env.CONC || 3),
  onProgress: ({ progress }) => { const p = Math.floor(progress * 10); if (p !== last) { last = p; console.log("progress", p * 10); } } });
console.log("done", path.resolve(outArg));
