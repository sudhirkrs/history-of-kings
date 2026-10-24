# Prompt for Claude Code + Chrome (publish a video with help)

Use this when you run Claude Code on your own computer with the Claude in Chrome extension.

Before you start:
1. Clone the repo (Mac: in Terminal, `cd ~/Documents` first) (`git clone https://github.com/sudhirkrs/history-of-kings.git`) and open a terminal in the folder.
2. Start Claude Code in that folder.
3. In Chrome, sign in to YouTube Studio with the channel account and connect the Claude in Chrome extension.
4. Optional but best: put licensed pictures in `episodes/ep01-ashoka/images/001.jpg, 002.jpg ...` first. Without them the video is plain caption cards.
5. Paste everything in the box below. To publish another episode, replace `ep01` / `ep01-ashoka` with the new episode (for example `ep02` / `ep02-chandragupta`) and the playlist name if needed.

```
```
You are helping me publish the first History of Kings video. The repo is the current folder (branch main). I am on a Mac: use python3 and pip3 (or a venv named venv if pip refuses with "externally-managed-environment"). Chrome is open with YouTube Studio signed in as the channel owner, and the Claude in Chrome extension is connected.

Work through the steps below in order. At each step, tell me in one line what you did and what you saw. If something fails, stop and show me the exact error. Do not skip ahead and do not guess.

SAFETY RULES
- Never type, read out or store my Google password or any code sent to me. If a login, 2-step check or consent screen appears, stop and tell me to complete it myself.
- Do not commit client_secret.json or token.json.
- Do not make anything Public until I reply "publish" for this video.
- Do not delete or edit anything on the channel except the videos we create.

STEP 1: Check the computer
Run: python3 tools/setup_check.py --voice
Fix each FIX line it prints (brew and pip installs are fine to run yourself). If client_secret.json is missing, use Chrome to walk through Google Cloud (docs/10-novice-guide.md Part 3) one step at a time, and wait for me to confirm each step. Repeat until it says Ready.

STEP 2: Sign in to YouTube for the tool
If token.json is missing or setup_check says it lacks playlist/comment access, delete it and run: python3 tools/upload.py
A Google consent page opens. Stop and let me approve it. Then confirm token.json exists.

STEP 3: Fact-check gate for Episode 1
Open factcheck/ep01-ashoka.md and the sources in episodes/ep01-ashoka/sources.md. List every item marked NOT verified. Ask me whether I have checked them in the books. Do not continue until I say yes. If I give corrections, edit episodes/ep01-ashoka/script.md and note them in the fact-check log.

STEP 4: Approve the facts and build
Run: python3 tools/approve.py ep01 -y (only after I said yes in step 3).
Run: python3 tools/pipeline.py prepare --ep ep01
This fetches licensed pictures, makes the AI voice and video, two thumbnails, captions and 2 Shorts. Tell me the video length. Open episodes/ep01-ashoka/out/video.mp4, images/review.html, thumbnail_A.jpg, thumbnail_B.jpg and out/shorts for me. If I name a scene with a wrong picture, run python3 tools/fetch_images.py ep01 --redo N and rebuild. Wait until I say "ok".

STEP 5: Release and upload
Run: python3 tools/approve.py ep01 --release -y
Run: python3 tools/pipeline.py publish --ep ep01
(no --now: it uploads private and schedules). Show me the youtu.be links for the video and its Shorts and the extras line (playlist, captions, comment).

STEP 6: Studio settings (in Chrome)
Open the video link, then "Edit in Studio". Check and set:
- Audience: "No, it's not made for kids"
- Altered content / synthetic media: Yes (the narration is AI-generated)
- Playlist "Kings of India" is set
- Chapters in the description start at 0:00
- Add an end screen if Studio offers it
Save after each change and show me a summary.

STEP 7: Go public
Ask me: "Ready to publish?" Only after I answer "publish", set the video's Visibility to Public (or keep the schedule, ask me which) and Save. Open the public watch page and confirm it plays.

STEP 8: Pin the comment
The tool already posted the first comment. In Studio > Comments, pin it and confirm it shows as pinned.

STEP 9: Wrap up
Run python3 tools/pipeline.py plan and show me ep01's status. Remind me to approve ep02 next and to check click rate and average view duration after 48 hours.
```

Notes:
- If YouTube keeps the upload Private because the API project is not audited, step 7 sets it to Public in Studio.
- The prompt stops at the points only you can handle: Google sign-in, the book fact-check, watching the test video, and the final "publish".
