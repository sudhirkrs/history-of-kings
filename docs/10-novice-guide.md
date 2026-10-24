# Novice Guide: one small step at a time (Windows; Mac notes in brackets)

Take your time. Do one step, check the "You should see", then go on. If something differs, stop and look at "If stuck" at the end.

## PART 1 — Install the tools (once)
1. **Python.** Go to python.org/downloads, download the newest Python, run it. **Tick "Add python.exe to PATH"** on the first screen, then Install. [Mac: it is usually already there, or `brew install python`.]
2. **Check it.** Press the Windows key, type `cmd`, press Enter. Type `python --version` and press Enter. *You should see* `Python 3.10` or higher.
3. **ffmpeg** (makes the video). In the same black window type `winget install ffmpeg` and press Enter. Close the window and open a new one. Type `ffmpeg -version`. *You should see* version text. [Mac: `brew install ffmpeg`.]
4. **Git** (gets the files). Download from git-scm.com, install with all default options.

## PART 2 — Get the project (once)
5. In `cmd` type these, one line at a time, pressing Enter after each:
   - `cd %USERPROFILE%\Documents`
   - `git clone https://github.com/sudhirkrs/history-of-kings.git`
   - `cd history-of-kings`
   *You should see* a new folder `history-of-kings` (it is already on the `main` branch). (Git may ask you to sign in to GitHub in a browser: do it.)
6. Install the helper packages: `pip install edge-tts pillow google-api-python-client google-auth-oauthlib`. *You should see* "Successfully installed".
7. **Check everything:** `python tools/setup_check.py --voice`. It lists problems as `FIX` with the command that cures each. Repeat until the last line says **Ready.** (Two FIX lines about `client_secret.json` and `token.json` are normal until Part 3.)

## PART 3 — Let the program use your YouTube channel (once)
8. Open console.cloud.google.com and sign in with the Google account that owns the History of Kings channel.
9. Top bar → project picker → **New Project** → name it `history-of-kings` → Create. Make sure it is selected.
10. Menu (☰) → **APIs & Services** → **Library**. Search `YouTube Data API v3` → click it → **Enable**.
11. **APIs & Services → OAuth consent screen** (may be called "Google Auth Platform"). Choose **External**, fill the app name (`History of Kings`) and your email, Save. Under **Test users** click Add and enter your own Gmail address.
12. **APIs & Services → Credentials → Create credentials → OAuth client ID**. Application type: **Desktop app**. Create, then **Download JSON**.
13. Rename the downloaded file to exactly `client_secret.json` and move it into the `history-of-kings` folder (inside Documents).
14. Back in `cmd` (still in that folder): `python tools/upload.py`. A browser opens: pick your account, click **Advanced → Go to history-of-kings (unsafe)** (it is your own app), then **Continue/Allow**. *You should see* a file `token.json` appear. (The command then prints a usage message; that is fine.)
15. Run `python tools/setup_check.py` again. *You should see* **Ready.**

## PART 4 — YouTube Studio prep (once)
16. studio.youtube.com → Settings → Channel → Feature eligibility → **verify your phone number** (needed for custom thumbnails and long videos).
17. Content → Playlists → create `Kings of India`, `Mongols`, `Russia`, `Europe`, `China`.

## PART 5 — Publish your first video
18. **Fact-check.** Open `factcheck\ep01-ashoka.md` (Notepad is fine). Rows marked NOT verified: look them up in the books under "Sources" in `episodes\ep01-ashoka\script.md`. Edit the script text if a fact is wrong.
19. **Approve the facts:** `python tools/approve.py ep01`. Type `y` when asked.
20. **Build everything:** `python tools/pipeline.py prepare --ep ep01`. It downloads licensed pictures, makes the voice, the video, two thumbnails, captions and two Shorts. (About 10–20 minutes.)
21. **Look at it.** Open `episodes\ep01-ashoka\out\video.mp4`, `images\review.html` (pictures and licences), `thumbnail_A.jpg`, `thumbnail_B.jpg`, and the `out\shorts` folder. Wrong picture for a scene? `python tools/fetch_images.py ep01 --redo 7`, then run step 20 again.
22. **Release and publish:** `python tools/approve.py ep01 --release` then `python tools/pipeline.py publish --ep ep01 --now`. *You should see* a `https://youtu.be/...` link, plus lines saying playlist, captions and comment are ok.
23. **Open the link** → click **Edit in Studio**. Set:
    - Audience: **No, it's not made for kids**
    - Altered content: **Yes** (the voice is AI)
    - If the video is Private: click **Visibility → Public → Save** (Google keeps new API projects private until audited)
    - Pin the first comment (three dots → Pin) and add an end screen
24. **After a day or two:** reply to comments; after 48 h check Analytics → click rate and average view duration.

## PART 6 — Make it automatic
25. For each next episode just do steps 18, 19, 20, 21, 22. Then run `python tools/install_scheduler.py` once: every Sunday the computer builds and schedules the next approved episodes. Keep the computer on at that time (default Sunday 9:00).
26. Get future updates: `git pull` (always on `main`).

## If stuck
- "python is not recognized": reinstall Python and tick "Add to PATH" (step 1), open a new `cmd`.
- "ffmpeg is not recognized": open a new `cmd` window after installing.
- Google says "access blocked": your Gmail is not in Test users (step 11).
- Video upload stays Private: step 23.
- Anything else: copy the red error text and send it to me.
