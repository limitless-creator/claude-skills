# Reel Studio

**A Claude skill that edits your talking-head reels for you, in your own style.**

You bring a script and your raw, uncut video. Claude interviews you, learns what you like from reels of creators you admire, sets up your brand look, shows you every moment of the reel for approval, and then cuts, edits and renders the finished 9:16 video for Instagram Reels, TikTok or YouTube Shorts.

> **Licence note:** Reel Studio uses [Remotion](https://www.remotion.dev) to build the graphics. Remotion is free for individuals and companies with up to 3 people. Bigger companies need a [Remotion company licence](https://www.remotion.dev/license). Reel Studio itself is MIT-licensed (see LICENSE in the collection).

## How it works

1. **Interview.** Claude asks about you, your audience, your brand and your taste, one question at a time. Your answers are saved, so next time it only asks what changed.
2. **Your taste.** Claude downloads a few recent reels from creators you like (or you drop in screenshots), and you click **Yes** or **No** on frames with a short reason. Claude turns that into a style summary you can correct.
3. **Your brand.** Claude uses your brand fonts and colours. If you don't have a brand yet, you choose from 2–3 looks Claude designs for you.
4. **The cut.** Claude transcribes your footage, keeps the best take of every line and removes the mistakes, retakes and long pauses. You approve the clean cut before anything else happens.
5. **Every moment, approved.** A page shows each moment of your reel as a picture: the camera framing, the text and graphics. You approve, ask for a change, or drop each one.
6. **The finished reel.** Claude builds it, checks it, adds music if you want it, and saves the final video on your computer. You approve the first 10 seconds before the full render.

Nothing is posted anywhere. Everything stays on your computer.

## What you need

- **[Claude Code](https://claude.com/claude-code)** (the desktop app or the terminal), not just the claude.ai chat. It needs to run programs on your computer.
- A **Mac** is recommended (that's where it's tested). Windows should work, with the same tools installed.
- About **5 GB free** disk space.
- Your **script** and your **raw video files** (phone or camera, any number of files, uncut is fine). Your voice should be recorded in the video files.
- Optional: a free **[Apify](https://apify.com)** account to download reference reels. It costs a few cents per run (about $0.06 for 3 creators × 8 reels). Claude asks you for a spending limit first and never goes over it. No account? Use screenshots instead.

Claude installs the free tools it needs (ffmpeg, Node, Python packages, Remotion) the first time, after asking you.

## Install

1. Download the collection: on https://github.com/limitless-creator/claude-skills click **Code → Download ZIP** (or `git clone https://github.com/limitless-creator/claude-skills`).
2. Copy the `reel-studio` folder (inside the download) into your Claude skills folder:
   - Mac/Linux: `~/.claude/skills/reel-studio`
   - Windows: `%USERPROFILE%\.claude\skills\reel-studio`
   ```bash
   mkdir -p ~/.claude/skills && cp -R reel-studio ~/.claude/skills/
   ```
3. Start Claude Code and say: **"Make me a reel"** (or type `/reel-studio`).

## Your first reel

- Have your script ready (paste it in when Claude asks).
- Put your raw video files in the folder Claude tells you (`~/ReelStudio/<your-reel>/raw/`).
- Set aside about an hour for the first one. Most of it is Claude working. You answer questions and click through two pages in your browser.
- Your answers live in `~/ReelStudio/profile.json`, so the second reel is much quicker.

## What it costs

| | |
|---|---|
| Reel Studio | free (MIT) |
| ffmpeg, Node, Python, Whisper | free |
| Remotion | free for individuals and companies of up to 3 people; otherwise a company licence |
| Apify (optional) | a few cents per run, capped at the limit you choose |
| Music | free tracks from Pixabay, or your own |
| Claude | your normal Claude plan |

## Privacy and respect

- Your footage, script and answers stay in `~/ReelStudio/` on your computer.
- Reference reels are only used on your computer to learn your taste. Reel Studio never reposts them and never copies other creators' graphics, names or catchphrases.
- Your Apify token is never written into any file.

## FAQ

**I don't have an Apify account.** Put 10–20 screenshots of reels you like into the `references/own/` folder Claude shows you. It works the same.

**My footage looks grey and flat.** You probably filmed in a "log" colour profile. Claude asks for your camera maker's official LUT (a small colour file, free from Apple, Sony, Canon, DJI…) and applies it.

**My reel isn't in English.** Tell Claude. It switches the transcription to the multilingual model.

**Can I edit the result further?** Yes. The finished file is a normal MP4. The Remotion project for each reel is in `~/ReelStudio/<your-reel>/remotion/` if you want to tweak it.

**Something broke.** Tell Claude what you see. It checks its own work and explains fixes in plain words.

## For developers

- `reel-studio/SKILL.md`: the process Claude follows.
- `reel-studio/scripts/`: prep, transcription, cut list, render, finish, Apify, frame extraction.
- `reel-studio/remotion/`: the Remotion starter (`beats.json` + `brand.json` → reel).
- `reel-studio/pages/` + `helper/`: the two local approval pages and the tiny server that saves the answers.
- Tests (run from the collection folder; Mac, need ffmpeg, Node, and a Python with numpy + faster-whisper):
  ```bash
  node --test reel-studio/helper/
  PY=~/ReelStudio/.venv/bin/python tests/reel-studio/test_pipeline.sh
  PY=~/ReelStudio/.venv/bin/python tests/reel-studio/test_references.sh
  PY=~/ReelStudio/.venv/bin/python tests/reel-studio/test_remotion.sh
  ```

## Credits

Built by AI With Elias with Claude. MIT licence.
