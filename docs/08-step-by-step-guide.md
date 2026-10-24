# Step-by-step guide: from script to a published YouTube video

Do the one-time setup (Part A) once. Then repeat Part B for every episode.
Everything runs on **your own computer** (Windows, Mac or Linux), not in this cloud session.

---
## PART A — One-time setup (about 1–2 hours)

### A1. Install the tools
1. **Python 3.9+** — python.org (tick "Add to PATH" on Windows).
2. **ffmpeg** — Windows: `winget install ffmpeg`; Mac: `brew install ffmpeg`; Linux: `sudo apt install ffmpeg`. Check: `ffmpeg -version`.
3. **Git** — to download this repo.
4. In a terminal:
```
git clone https://github.com/sudhirkrs/history-of-kings.git
cd history-of-kings
pip install edge-tts pillow google-api-python-client google-auth-oauthlib
```

### A2. Choose your AI voice
- The tool uses **edge-tts** (free Microsoft neural voices). Default: `en-IN-PrabhatNeural` (Indian English, male).
- Test 3 voices on one sentence and pick one for the whole channel (same voice every episode):
```
edge-tts --list-voices | grep en-
edge-tts --voice en-IN-PrabhatNeural --text "Around 261 BCE, on the east coast of India, a war came to an end." --write-media test1.mp3
edge-tts --voice en-GB-RyanNeural    --text "Around 261 BCE, on the east coast of India, a war came to an end." --write-media test2.mp3
```
- Use it with `--voice NAME` in Part B. (Check the voice list on your machine; names can change.)
- If you prefer a premium voice (ElevenLabs, Google, Azure), generate the audio there and swap it in — `make_video.py` only needs one audio file per scene (`out/aNNN.mp3`).

### A3. Prepare the YouTube channel (once)
1. Sign in to YouTube → **Settings → Channel → Feature eligibility → Intermediate features**: verify your phone number. This unlocks **custom thumbnails and videos longer than 15 minutes**.
2. Channel name, handle, logo (800×800), banner (2560×1440), About text, contact email.
3. **Settings → Upload defaults**: Category *Education*, language *English*, license *Standard*.
4. Create playlists: *Kings of India*, *Mongols & Central Asia*, *Russia*, *Europe*, *China*, *Ottomans*.
5. Record a 60-second channel trailer (optional, later).

### A4. Set up automatic upload (optional but saves time)
Skip this and upload by hand in YouTube Studio if it feels hard — both work.
1. Go to **console.cloud.google.com** → create a project → **APIs & Services → Library → "YouTube Data API v3" → Enable**.
2. **OAuth consent screen**: user type *External*, add your own Google account as a **Test user**.
3. **Credentials → Create credentials → OAuth client ID → Desktop app**. Download the JSON, rename it **`client_secret.json`**, put it in the repo folder. **Never share or commit it** (it is already in `.gitignore`).
4. First upload opens a browser to ask permission — click Allow.
5. **Important limit:** videos uploaded by an API project that Google has not audited are forced to **Private**. You can still upload with the script, then open YouTube Studio and switch each video to Public/Scheduled by hand (takes 1 minute). To lift the limit, apply for a YouTube API compliance audit (optional).

---
## PART B — For each episode (about 4–6 hours the first time, 2–3 later)

Replace `ep01-ashoka` with the episode folder (see `docs/02-episode-roadmap.md`).

### B1. Fact-check the script (do not skip)
1. Open `factcheck/ep01-ashoka.md`. Every line marked **NOT verified** must be checked in the books listed under *Sources* at the bottom of `episodes/ep01-ashoka/script.md`.
2. Fix the script where a claim is wrong or uncertain; keep legends labelled as legends.
3. Read the whole script **aloud once**. Rewrite any sentence you stumble on.
4. Optional but best: have one history-literate person read it.

### B2. Make a first draft video (check timing)
```
python tools/make_video.py episodes/ep01-ashoka
```
It creates, inside `episodes/ep01-ashoka/out/`: `video.mp4` (captioned cards + AI voice), `chapters.txt` (YouTube chapter timestamps), `scenes.json` (scene number, start time, caption for each scene).
- Quick test of only the first 5 scenes: add `--limit 5`.
- Different voice: add `--voice en-GB-RyanNeural`.
- Listen to it. Does the voice mispronounce names? Fix by respelling in `script.md` (e.g. write "Kal-ing-a" if needed), then re-run.

### B3. Add pictures (this is what makes it watchable)
Cards alone will not keep viewers. For each scene, add one image.
1. Open `out/scenes.json` — it lists each scene's number and its `[VISUAL: ...]` caption (e.g. scene 3 = "map of north India c. 325 BCE").
2. Find legal images:
   - **Wikimedia Commons** (commons.wikimedia.org): paintings, inscriptions, coins, monuments, maps. Check the licence on each file page ("Public domain" or CC-BY/CC-BY-SA are fine; CC-BY needs credit).
   - Museum open-access collections: Met Museum, Rijksmuseum, British Museum, Smithsonian, Library of Congress.
   - Maps: make your own in **Google Earth Studio / Mapchart / Canva** (screen-record or export).
   - AI-generated illustrations are allowed but must be labelled "illustration" in the description, never presented as real portraits.
   - **Do not** use random Google Images, film stills, or other YouTubers' footage.
3. Save each as `episodes/ep01-ashoka/images/001.jpg`, `002.jpg`, `003.jpg` … (number = scene number). Missing numbers fall back to a caption card.
4. Keep a file `episodes/ep01-ashoka/credits.md` listing: image title, creator, licence, link.
5. Re-run `python tools/make_video.py episodes/ep01-ashoka` to rebuild with images (slow zoom is added automatically).

### B4. Optional polish (recommended after the first few videos)
Open `video.mp4` in **DaVinci Resolve (free)** or CapCut and add: soft background music (YouTube Audio Library, volume ~ -20 dB under voice), a 3-second title card, on-screen dates/names, and your channel logo. Export 1080p, H.264, 16:9.

### B5. Thumbnail
- 1280×720, under 2 MB, JPG or PNG. Make in **Canva** (free).
- One strong image of the king (painting/statue) + 3–4 big words (e.g. "KING WHO SAID SORRY"). High contrast, same fonts and colours for every episode.
- Make two versions (A and B) and use YouTube's "Test & compare" after upload.

### B6. Metadata (title, description, tags, chapters)
```
python tools/build_meta.py episodes/ep01-ashoka
```
This writes `episodes/ep01-ashoka/metadata.json` using the title/hook/tags/sources at the bottom of the script plus the chapter timestamps from `out/chapters.txt`.
Then open `metadata.json` and:
- Check the title (under ~60 characters, one curiosity hook + the name).
- Add a short line: "Illustrations: see pinned comment" and paste your `credits.md` into the **pinned comment** after upload (or into the description if short).
- Keep the line "Narration is AI-generated."

### B7. Upload
**Option 1 — automatic (needs Part A4):**
```
python tools/upload.py episodes/ep01-ashoka episodes/ep01-ashoka/out/video.mp4 thumbnail.png
```
To schedule at a time (UTC), add a 4th argument, e.g. 1 November 2026, 1:00 pm UTC (6:30 pm IST):
```
python tools/upload.py episodes/ep01-ashoka episodes/ep01-ashoka/out/video.mp4 thumbnail.png 2026-11-01T13:00:00Z
```
A browser window opens the first time; click Allow. It prints the video link. (If it is Private because the project is unaudited, finish in Studio.)

**Option 2 — by hand (always works):** studio.youtube.com → **Create → Upload videos** → select `video.mp4` → paste title and description from `metadata.json`.

### B8. In YouTube Studio, set these before publishing
- **Thumbnail**: upload (if not done by script).
- **Audience**: "No, it's not made for kids."
- **Altered or synthetic content**: answer **Yes** if the narration is AI-generated or the visuals are AI-made and could look real. Be honest — YouTube requires this disclosure.
- **Tags** (optional; paste from `metadata.json`), **Category**: Education, **Language**: English.
- **Playlist**: add to the right playlist.
- **Subtitles**: upload an `.srt` or let YouTube auto-generate and correct names.
- **Chapters**: already in the description (first one must start at 0:00).
- **End screen** (last 20 s): "Next episode" + "Subscribe". **Cards**: link the related episode (e.g. Ashoka → Chandragupta).
- **Visibility**: *Schedule* (best) or Public.

### B9. After publishing
1. **Pin a comment**: "Which king should I cover next?" plus the image credits.
2. Reply to comments for the first 2 hours.
3. Make 2–3 **Shorts** (45–60 s): cut the hook and the most surprising moment; add captions; link to the full video.
4. Share in relevant communities (history subreddits, WhatsApp/Telegram groups, Instagram) — don't spam.
5. After **48 hours** check Studio → Analytics: Click-through rate (aim 4–8%), average view duration (aim 35%+), and where viewers drop off. Note lessons in `docs/lessons.md` and adjust the next script (shorter intros, stronger hook).

---
## PART C — Launch plan

1. **Before launch**: finish channel branding; make Episodes 1, 2 and 3 completely (B1–B8).
2. **Launch week**: publish Ep 1 on day 1 (Sat/Sun evening IST works well), Ep 2 on day 3, Ep 3 on day 5. Shorts every day.
3. **Then**: 1 long video per week. Keep a buffer of 3 finished episodes. Alternate regions (India → Mongols → Russia → Europe → China → Ottomans) so each audience gets something regularly.
4. **Monetisation**: YouTube Partner Programme needs 1,000 subscribers + 4,000 public watch hours (12 months) or 10 million Shorts views (90 days). Apply when eligible. Content must be original in script and structure — your fact-checked, narrated scripts qualify; avoid purely re-posted images with no commentary.

---
## Checklist you can print (per episode)
- [ ] Facts verified against books, script read aloud
- [ ] `make_video.py` run; voice sounds right
- [ ] Images added (001.jpg …) and `credits.md` written
- [ ] Final `video.mp4` watched start to finish
- [ ] Thumbnail made (two versions)
- [ ] `build_meta.py` run; title/description checked
- [ ] Uploaded; synthetic-content box answered; playlist, end screen, subtitles set
- [ ] Scheduled; pinned comment ready; Shorts planned
- [ ] 48-hour analytics review done

## If something goes wrong
- `ffmpeg: command not found` → reinstall ffmpeg and reopen the terminal.
- `edge_tts` errors / no internet → check connection; or use `--tts silent` to test the video build without voice.
- Upload says "quota" or video is Private → normal for an unaudited API project; finish in Studio.
- "Custom thumbnail" not allowed → verify your phone number on the channel.
- Voice mispronounces a name → respell it phonetically in `script.md` and re-run.


## Part D — Run it all automatically

First run `python tools/setup_check.py` (add `--voice` to test the AI voice). If you signed in before this update, delete `token.json` and run `python tools/upload.py` once to sign in again (new permissions: playlists, captions, comments).

Two sign-offs are yours, everything else is automatic:

1. **Facts.** After checking the flags against books: `python tools/approve.py ep01` (creates `APPROVED`).
2. **Prepare.** `python tools/pipeline.py prepare --ep ep01` fetches licensed pictures from Wikimedia Commons (credits written to `credits.md`), makes the AI voice and video, metadata, two thumbnails (A and B), captions (`.srt`) and 2 Shorts.
3. **Review.** Open `images/review.html` (every picture and its licence; re-pick a scene with `python tools/fetch_images.py ep01 --redo 7`), watch `out/video.mp4`, look at `thumbnail_A.jpg` / `thumbnail_B.jpg` and `out/shorts/`.
4. **Release.** `python tools/approve.py ep01 --release`.
5. **Publish.** `python tools/pipeline.py publish --ep ep01` (or `--now`) uploads the video (AI-voice disclosure set), thumbnail, adds it to its playlist, uploads captions, posts the first comment (credits + "Which king next?") and schedules the Shorts, one per day after the episode.
6. `python tools/pipeline.py plan` shows every episode's status. `python tools/pipeline.py run --count 2` does prepare, and publish for any already released episode. `python tools/install_scheduler.py` runs `run` weekly.

Only these stay manual because the YouTube API cannot do them: pinning the comment, end screens and cards (one click each in Studio, or use the Claude in Chrome prompt, docs/11), and switching a video from Private to Public while the API project is unaudited. Put your own pictures in `images/NNN.jpg` and the tool never overwrites them; `thumbnail.png` in the folder replaces the generated thumbnail. `config.json` keys: `images` ("commons" or "none"), `shorts` (count), `shorts_gap_days`, `comment`.
