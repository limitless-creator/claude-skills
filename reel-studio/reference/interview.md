# Onboarding interview

Goal: know the person well enough to make a hundred small editing decisions the way they would. Ask **one question at a time**, in plain words, in their language. Short questions. If an answer is vague, ask one follow-up, then move on. Explain any technical word in brackets the first time.

Before asking, check `~/ReelStudio/profile.json`. Never ask what's already there; show it and ask "anything changed?".

Save every answer into `profile.json` as you go (so a crash or a closed window loses nothing).

## 1. Who they are (why: the reel has to sound and look like *their* business)

1. "What's your name, and what do you do? One or two sentences is perfect."
2. "Who is this reel for? Describe the person you want watching it."
3. "After watching, what should they do? (follow you, comment a word, visit a link, book a call, just remember you…)"
4. "Where will you post it? (Instagram, TikTok, YouTube Shorts, LinkedIn…)" → all are 9:16; note it for safe areas.

## 2. Brand (why: their graphics use their fonts and colours, never ours)

5. "Do you have brand guidelines: fonts, colours, a logo? If yes, drop the files (or a link to your website) into `~/ReelStudio/brand/` and tell me." 
   - Files or a website → read them, extract fonts (Google Fonts names if possible), colours (hex), logo files. Show what you found, ask if it's right.
   - Nothing → "No problem. Later I'll show you 2–3 looks to choose from, based on the reels you like."

## 3. Taste (why: this is what makes it *their* reel, not a template)

6. "Name 2–5 creators whose editing you love. Instagram handles are best." Ask what they like about each, in their own words.
7. Then the style questions in `style-questions.md`, one at a time.

## 4. Footage (why: the colour and the cut depend on it)

8. "What did you film with? Phone, or a camera?" 
   - "Did you use a log or flat colour profile? (If you don't know, you probably didn't. Log footage looks grey and washed out straight from the camera.)" 
   - Log → ask for the camera maker's official LUT (a small colour file that turns grey log video into normal colour). Point them to the maker's site (e.g. Apple's "Apple Log" LUT, Sony "S-Log3", Canon "C-Log", DJI "D-Log"). Save its path in `profile.json` (`camera.lut`). Never guess a LUT.
9. "Is your voice recorded by the camera, or by a separate microphone file?" — a separate audio file isn't supported yet; ask them to use the camera's audio or a mic that records into the camera/phone.

## 5. Money (why: nothing costs money without a number they chose)

10. Only if they want reference reels downloaded: "Downloading reels from those creators uses a service called Apify. It costs a few cents. What's the most you want to spend? I suggest $2." No account → offer screenshots instead (see `apify.md`).

## Profile file

`~/ReelStudio/profile.json`:
```json
{
  "name": "", "business": "", "audience": "", "goal_action": "", "platforms": [],
  "brand": { "source": "files|website|chosen|none", "fonts": {}, "colors": {}, "logo": "", "notes": "" },
  "creators": [{ "handle": "", "likes": "" }],
  "style": { "summary": "", "likes": [], "dislikes": [] },
  "preferences": {},
  "camera": { "device": "", "log": false, "lut": null },
  "apify_cap_usd": null,
  "updated": "YYYY-MM-DD"
}
```
Keep their own words in `likes`/`dislikes`/`summary` where you can. Never store an Apify token or any password here.
