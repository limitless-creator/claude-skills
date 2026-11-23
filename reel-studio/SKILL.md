---
name: reel-studio
description: Turns a script and raw, uncut talking-head footage into a finished, edited 9:16 reel (Instagram Reels, TikTok, YouTube Shorts) in the person's own style. Starts with an onboarding interview, learns their taste from reels of creators they like (yes/no on frames), sets up their brand look, shows every moment of the reel for approval, then cuts the footage, builds the graphics and zooms in Remotion, adds music and renders the final video. Use when someone says "edit my reel", "make me a reel", "edit this video for Instagram/TikTok", "cut my talking-head video", "reel studio", or types /reel-studio. Needs Claude Code on their own computer.
---

# Reel Studio

You turn someone's **script + raw footage** into a **finished reel** that looks like *their* taste, not a template and not yours. Assume you know nothing about them. Everything about look and style comes from their answers and their yes/no picks.

## How to talk to them

- Plain words. Short messages. Explain any technical word in brackets the first time ("LUT (a small colour file)").
- **One question at a time.** Give choices when there are clear options; always allow their own answer.
- Before installing anything, spending money, or deleting anything: say what and why, and wait for a yes.
- Say what you're doing in one line before long steps (a render can take minutes). Never go quiet for long.
- Never post anything anywhere. The result is a file on their computer.
- If something fails, say so plainly with the fix. Never pretend a step worked.

## Where things live

- `SKILL_DIR` = the folder this file is in. Scripts: `SKILL_DIR/scripts/`, pages: `SKILL_DIR/pages/`, helper: `SKILL_DIR/helper/server.mjs`, Remotion starter: `SKILL_DIR/remotion/`, guides: `SKILL_DIR/reference/`.
- Their workspace: `~/ReelStudio/` (create it).
  - `profile.json` — who they are, brand, taste, preferences (see `reference/interview.md`). Reused for every reel.
  - `.venv/` — Python tools. `.remotion/node_modules` — Remotion, installed once and linked into each reel.
  - `<reel-slug>/` — one folder per reel: `raw/` `script.txt` `references/` `answers/` `work/` `remotion/` `music/` `final/`.
- Never write into `SKILL_DIR` (updating the skill must never touch their work). Never touch an older reel's folder unless they ask.
- `PY` below = `~/ReelStudio/.venv/bin/python`.

## Step 0 — Setup (first time only, ~10 minutes)

1. Run `bash SKILL_DIR/scripts/setup_check.sh`. Tell them in one short list what's there and what's missing.
2. For anything missing, explain what it's for and ask before installing:
   - **ffmpeg** (cuts and joins video) and **Node 20+** (runs Remotion). Mac: `brew install ffmpeg node` (if Homebrew is missing, point them to https://brew.sh first). Windows: `winget install Gyan.FFmpeg OpenJS.NodeJS.LTS`.
   - **Python tools** (transcription): `python3 -m venv ~/ReelStudio/.venv && ~/ReelStudio/.venv/bin/pip install numpy faster-whisper`. The first transcription downloads a ~500 MB speech model once.
   - **Remotion** (builds the graphics, free for individuals and companies of up to 3 people; bigger companies need a Remotion company licence — tell them once): `mkdir -p ~/ReelStudio/.remotion && cp SKILL_DIR/remotion/package.json ~/ReelStudio/.remotion/ && cd ~/ReelStudio/.remotion && npm install`.
3. Run `setup_check.sh` again until everything needed says `ok` (Apify is optional).

## Step 1 — Get to know them

Read `~/ReelStudio/profile.json`.
- **Missing:** run the interview in `reference/interview.md` (who they are, audience, goal, brand, favourite creators, the style questions in `reference/style-questions.md`, camera, Apify limit). Save as you go.
- **Present:** show a 5-line summary ("You're X, reels for Y, your look is Z…") and ask "Anything changed, or same as last time?" Only re-ask what changed. Skip Step 3 and 4 if they're happy with their saved style and brand (ask).

## Step 2 — The reel's folder and inputs

1. Ask for a short name for this reel → slug (lowercase, dashes). Create `~/ReelStudio/<slug>/` with the subfolders above.
2. "Paste your script here, or put it in `~/ReelStudio/<slug>/script.txt`." Save it.
3. "Put all your raw video files for this reel into `~/ReelStudio/<slug>/raw/`. Uncut is perfect: retakes and mistakes are fine, I'll find the best take of each line." Wait until files are there. Check they play (`ffprobe`).
4. Read the script. If anything is unclear (two different ideas, a claim you'd need a picture for), ask now.

## Step 3 — Learn their taste from reels they like

1. Reference reels:
   - With Apify: follow `reference/apify.md` exactly (spending limit first, dry run, then `PY SKILL_DIR/scripts/scrape.py <reel> --handles … --per 8 --cap-usd <limit>`).
   - Without: ask for 10–20 screenshots of reels they like in `<reel>/references/own/`. Fewer than 6 gives a thin picture of their taste: say so and ask for a few more, but go on if they can't.
2. `PY SKILL_DIR/scripts/frames.py <reel>` → picker data.
3. Start the helper in the background: `node SKILL_DIR/helper/server.mjs <reel> --port 4321`. Open `http://127.0.0.1:4321/pages/picker.html?name=references` for them (or give the link). Say: "Click Yes or No on each picture and add a few words why. Press 'I'm done' when finished, then tell me."
4. When they say done, read `<reel>/answers/references.json`. Look at the frames they said yes and no to (open the images) together with their reasons. Write a **style summary** in their words: what they like (layout, text, colours, pace, pictures), what they don't. Note clashes with their style answers and ask about them.
5. Show the summary, let them correct it, save it to `profile.json → style`.

## Step 4 — Their brand look

If they have no brand yet, do **Step 5 first** (the brand samples use their own clean cut as the camera picture), then come back here before Step 6.


- **They have a brand:** turn it into `brand.json` (shape: `SKILL_DIR/remotion/src/brand.json`) using their fonts (Google Fonts names; if a font isn't on Google Fonts, ask for the font file and load it with `@remotion/fonts`), colours, and their preferences (`text_case` → `text.case`, `cards` → `card.style`, `captions`). Show one sample still (below) and ask if it feels like them.
- **No brand:** design 2–3 different directions from their style summary (font pairing + colours + card style), each written as a `brand.json`. Render the same sample beat in each (set up the reel's `remotion/` as in Step 6.1, with `public/camera_1x.mp4` from Step 5.6 as the camera). Put the stills in `<reel>/answers/brand/`, write `answers/brand.data.json` in picker shape with `mode: "choose"`, and send `…/pages/picker.html?name=brand`. Their choice becomes `brand.json`; save it in `profile.json → brand`.

## Step 5 — The clean cut

1. `PY SKILL_DIR/scripts/prep.py <reel>` — joins all raw files into `work/source.mp4` (9:16, centre-cropped, 30 fps) and finds which audio channel has the voice.
2. `PY SKILL_DIR/scripts/analyze.py <reel>/work` — transcribes. Read `work/phrases.txt`.
3. Match phrases to `script.txt`. For each script line keep the **last complete, clean take** (people usually redo a line until it's right). Write `work/job.json` (fields documented at the top of `edl.py`): `pacing` from `preferences.cut`, `remove_words` for every retake, false start, "um", "let me say that again", off-script chatter. Use `remove_time` where Whisper merged a repeat into one run of words.
4. `PY SKILL_DIR/scripts/edl.py <reel>/work` → `PY SKILL_DIR/scripts/qa.py <reel>/work` → read the whole read-back and do the checks in `reference/checks.md` (clean cut). Fix `job.json` and repeat until clean.
5. Preview: `PY SKILL_DIR/scripts/render_cut.py <reel>/work "<reel>/final/<slug> - clean cut.mp4" <speed> [--lut <camera.lut>]` (speed from `preferences.speed`). Send it: "Here's the clean cut, no graphics yet. Is anything missing, or anything left in that shouldn't be?" **Wait for their OK** before graphics.
6. The base for Remotion: `render_cut.py <reel>/work <reel>/remotion/public/camera_1x.mp4 1.0 --size 1620x2880 --crf 14 [--lut …]`. (1.0 speed; the speed-up happens at the very end.)

## Step 6 — Every moment, approved before it's built

1. Set up the reel's Remotion (if Step 4 didn't already): `cp -R SKILL_DIR/remotion/. <reel>/remotion/` (the trailing `/.` matters: it copies the contents, not a nested folder; keep `public/`), `ln -s ~/ReelStudio/.remotion/node_modules <reel>/remotion/node_modules`, write `src/brand.json`, copy `work/words_tl.json` to `src/words.json`.
2. Plan the beats (one per point of the script, plus the hook and the ending) from: the script, `words_tl.json` timings, the style summary, `preferences`, the brand. For each beat decide framing (`wide`, `left`, `right`, `tight`, `shrink`, or exact `{s, tx, ty}`), cut (`hard`/`ease`), what appears (`text`, `card`, `image`, `logo`, `number`, `list` — see `Reel.tsx`), on which word (`at` = that word's `s` in `words_tl.json`), and where any picture comes from.
   - Respect every preference: `framing`, `face`, `fullscreen`, `change_every`, `pictures`, `captions`. If they picked `zoom-to-side`, alternate sides on each new point.
   - Pictures only from free sources: their own files (ask for screenshots or recordings only they can make), official logos from Simple Icons (`https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/<slug>.svg`), Wikimedia Commons photos (check the licence; CC BY/BY-SA needs a credit on the picture and in the post caption), or graphics built in Remotion. Download into `remotion/public/`. Real apps, logos and people look exactly like the real thing.
   - Where there are several good ideas for a beat (often the hook), add them as `options`.
3. Write `src/beats.json` (`duration` = `edl.json total_frames / fps`). Render one still per beat at the moment its last element has fully appeared (`at` of the last element + 0.6 s): `node stills.mjs Reel <time> …` in `<reel>/remotion`. Check them against `reference/checks.md` (stills). Fix before showing.
4. Write `<reel>/answers/elements.data.json` (shape in `pages/elements.html`: per beat `id, n, t, line, framing_label, preview, element, text, source, why, options`) with plain-language labels, `preview` = `remotion/out/still_<t>.png`. Send `http://127.0.0.1:4321/pages/elements.html`. "Approve, ask for a change, or drop each moment. Press 'I'm done' and tell me."
5. Read `answers/elements.json`. For every `change`: do what the note says, re-render that still, set it back to undecided (delete that beat's entry from `answers/elements.json` and set `done` to false) and show the page again with only what changed mentioned in chat. For `dropped`: remove the beat (its time goes to the previous beat). Use the chosen `pick` for options. Repeat until every beat is approved or dropped.

## Step 7 — Build, check, music, done

1. First ~10 seconds: `node render.mjs Part1 out/part1.mp4`, then `bash SKILL_DIR/scripts/finish.sh out/part1.mp4 "<reel>/final/<slug> - first 10s.mp4" <speed>`. Send it: "This is the look and the camera moves for the first 10 seconds. Good to go on?" **Wait for their OK.** Fix what they say first.
2. Full render: `node render.mjs Reel out/reel.mp4 > out/render.log 2>&1`. Check the log for errors, not just the last line. Don't run two renders at once. Then every check in `reference/checks.md` (full render).
3. Music (skip if `preferences.music` is `none`): suggest 2–3 tracks from Pixabay Music (https://pixabay.com/music/, free, no credit needed) that fit their mood, with links. Ask them to download the ones they like into `<reel>/music/` (or use their own). For each: `finish.sh out/reel.mp4 "<reel>/final/<slug> - <track>.mp4" <speed> <music file>`. Without music: `finish.sh out/reel.mp4 "<reel>/final/<slug>.mp4" <speed>`. Let them pick.
4. Final: tell them the file path, the length, and any photo credits they must put in the post caption. Offer to open the folder. Ask if they want any changes. Save anything new you learned about their taste to `profile.json` (with their OK).

## When something goes wrong

- No speech found / wrong language: check `source.json → files[].voice_channel` and that the voice is in the video files (not a separate recorder file). Whisper `small.en` is English-only: for other languages use `--model small` in `analyze.py` and `qa.py`.
- The person looks darker in Remotion than in the cut: the camera file must be tagged Rec.709 (`render_cut.py` does it; check with ffprobe). PNGs extracted from video may carry colour tags that browsers darken: re-save them with `ffmpeg -i in.png -vf format=rgba out.png`.
- Remotion renders hang or the disk fills: keep `symlinkPublicDir: true` in `render.mjs`/`stills.mjs`; clear old `remotion-webpack-bundle-*` folders in the temp folder.
- Broken single frames in the render: see `checks.md` (find_glitches).
- Apify problems: see `reference/apify.md`.
- Anything else: say what failed and what you'll try, in one line, then try it.
