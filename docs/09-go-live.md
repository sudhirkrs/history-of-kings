# Go Live: from a fresh computer to a published video

Do these in order. Each step says what you should see.

## One time (about 30 minutes)
1. **Get the files.** `git clone https://github.com/sudhirkrs/history-of-kings.git`, then `cd history-of-kings`. You are on `main` already; later run `git pull` for updates.
2. **Install.** Python 3.10+, ffmpeg, git, then `pip install edge-tts pillow google-api-python-client google-auth-oauthlib`.
3. **Check.** `python tools/setup_check.py --voice`. Fix every `FIX` line it prints. Done when it says **Ready.**
4. **YouTube access.** In Google Cloud: new project, enable "YouTube Data API v3", create an OAuth client of type Desktop app, save it as `client_secret.json` in the repo folder (details: `docs/08-step-by-step-guide.md`, Part A). Add your Google account as a test user.
5. **Sign in once.** `python tools/upload.py`. A browser opens, you allow access, and `token.json` appears. You never sign in again.
6. **YouTube Studio, once.** Verify your phone number (needed for custom thumbnails and long videos), and create playlists.

## For each episode
7. **Fact-check.** Open `factcheck/epNN-*.md` and the "Fact-check flags" in the script. Check the NOT verified items in the books listed under Sources, and fix the script if needed.
8. **Images (recommended).** Put licensed pictures in `episodes/epNN-name/images/001.jpg, 002.jpg ...` (one per scene) and note credits in `credits.md`. Without images the video uses plain caption cards.
9. **Approve.** `python tools/approve.py ep01`, answer `y`.
10. **Make it and publish, in one command.**
    - Go live now: `python tools/pipeline.py run --ep ep01-ashoka --now`
    - Or schedule: `python tools/pipeline.py run --count 1` (goes public at its slot in `schedule/config.json`)
    This makes the AI voice and video, writes the title, description with chapters, tags, makes a thumbnail, uploads, and prints the YouTube link.
11. **Studio settings, once per video** (the API cannot do these): open the link, set "altered or synthetic content" to Yes for the AI voice, "not made for kids", add an end screen and a pinned comment ("Which king next?").
12. **After it is live.** Reply to comments for 2 hours. After 48 hours check click rate and watch time in Studio.

## Run it hands-off
`python tools/install_scheduler.py` makes the computer run step 10 every Sunday for the next episodes you have approved. Approving is the only thing you do each week.

## If it goes wrong
- The video stays private after upload: Google keeps uploads from unaudited API projects private. Click **Publish** in Studio, or apply for an API audit.
- Upload quota errors: the API allows only a few uploads per day on a new project; run fewer episodes per day.
- Nothing happens when scheduled: the computer was off. Run step 10 by hand.
- Check progress any time: `python tools/pipeline.py plan`.
