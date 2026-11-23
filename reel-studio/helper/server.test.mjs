import { test, after } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync, readFileSync, mkdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { start } from "./server.mjs";

const dir = mkdtempSync(join(tmpdir(), "reel-"));
mkdirSync(join(dir, "answers"));
writeFileSync(join(dir, "answers", "references.data.json"), JSON.stringify({ title: "t", items: [] }));
const srv = await start(dir, 0);
const base = `http://127.0.0.1:${srv.address().port}`;
after(() => srv.close());

test("GET data returns the data file", async () => {
  const r = await fetch(`${base}/api/data/references`);
  assert.equal(r.status, 200);
  assert.equal((await r.json()).title, "t");
});
test("POST answers writes the answers file", async () => {
  const r = await fetch(`${base}/api/answers/references`, { method: "POST", body: JSON.stringify({ done: true }) });
  assert.deepEqual(await r.json(), { ok: true });
  assert.equal(JSON.parse(readFileSync(join(dir, "answers", "references.json"))).done, true);
});
test("GET answers returns saved answers, empty object when none", async () => {
  assert.equal((await (await fetch(`${base}/api/answers/references`)).json()).done, true);
  assert.deepEqual(await (await fetch(`${base}/api/answers/elements`)).json(), {});
});
test("bad names are refused", async () => {
  assert.equal((await fetch(`${base}/api/answers/..%2Fx`, { method: "POST", body: "{}" })).status, 400);
  assert.equal((await fetch(`${base}/api/answers/references`, { method: "POST", body: "not json" })).status, 400);
});
test("paths outside the reel folder are refused", async () => {
  assert.equal((await fetch(`${base}/..%2F..%2Fetc%2Fpasswd`)).status, 403);
});
