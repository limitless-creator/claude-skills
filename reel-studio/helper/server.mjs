// Serves one reel folder to the browser and saves what the person clicks.
// usage: node server.mjs <reelDir> [--port 4321]
//   /pages/<file>              the skill's pages (picker.html, elements.html)
//   /<path>                    files inside <reelDir> (frames, stills)
//   GET  /api/data/<name>      <reelDir>/answers/<name>.data.json  (what the page shows)
//   GET  /api/answers/<name>   <reelDir>/answers/<name>.json       ({} when nothing saved yet)
//   POST /api/answers/<name>   writes <reelDir>/answers/<name>.json
import http from "node:http";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { join, resolve, sep, extname, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const PAGES = join(dirname(fileURLToPath(import.meta.url)), "..", "pages");
const TYPES = { ".html": "text/html; charset=utf-8", ".json": "application/json", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
  ".png": "image/png", ".webp": "image/webp", ".mp4": "video/mp4", ".svg": "image/svg+xml", ".css": "text/css", ".js": "text/javascript" };
const NAME = /^[a-z0-9-]+$/;

const send = (res, code, body, type = "application/json") => {
  res.writeHead(code, { "content-type": type, "cache-control": "no-store" });
  res.end(typeof body === "string" || Buffer.isBuffer(body) ? body : JSON.stringify(body));
};

// resolve a path inside root, or null if it escapes root
const inside = (root, rel) => {
  const p = resolve(root, "." + sep + rel);
  return p === root || p.startsWith(root + sep) ? p : null;
};

const readJson = (p, fallback) => readFile(p, "utf8").then(JSON.parse, () => fallback);

export function start(reelDir, port = 4321) {
  const root = resolve(reelDir);
  const server = http.createServer(async (req, res) => {
    try {
      const url = new URL(req.url, "http://x");
      const path = decodeURIComponent(url.pathname);
      const api = path.match(/^\/api\/(data|answers)\/(.*)$/);
      if (api) {
        const [, kind, name] = api;
        if (!NAME.test(name)) return send(res, 400, { error: "bad name" });
        const file = join(root, "answers", kind === "data" ? `${name}.data.json` : `${name}.json`);
        if (req.method === "POST" && kind === "answers") {
          let body = "";
          for await (const chunk of req) body += chunk;
          let data;
          try { data = JSON.parse(body); } catch { return send(res, 400, { error: "not json" }); }
          await mkdir(dirname(file), { recursive: true });
          await writeFile(file, JSON.stringify(data, null, 1));
          return send(res, 200, { ok: true });
        }
        const data = await readJson(file, kind === "answers" ? {} : null);
        return data === null ? send(res, 404, { error: "no data yet" }) : send(res, 200, data);
      }
      const [base, rel] = path.startsWith("/pages/") ? [resolve(PAGES), path.slice(7)] : [root, path];
      const file = inside(base, rel);
      if (!file) return send(res, 403, "forbidden", "text/plain");
      const body = await readFile(file).catch(() => null);
      if (!body) return send(res, 404, "not found", "text/plain");
      send(res, 200, body, TYPES[extname(file).toLowerCase()] || "application/octet-stream");
    } catch (e) {
      send(res, 500, { error: String(e) });
    }
  });
  return new Promise((ok) => server.listen(port, "127.0.0.1", () => ok(server)));
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const dir = process.argv[2];
  if (!dir) { console.error("usage: node server.mjs <reelDir> [--port 4321]"); process.exit(2); }
  const i = process.argv.indexOf("--port");
  const srv = await start(dir, i > 0 ? Number(process.argv[i + 1]) : 4321);
  console.log(`serving ${resolve(dir)} at http://127.0.0.1:${srv.address().port}`);
}
