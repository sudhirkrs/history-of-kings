# Prompt for Claude Code + Chrome (publish a video with help)

Use this when you run Claude Code on your own computer with the Claude in Chrome extension.

Before you start:
1. Clone the repo (`git clone https://github.com/sudhirkrs/history-of-kings.git`) and open a terminal in the folder.
2. Start Claude Code in that folder.
3. In Chrome, sign in to YouTube Studio with the channel account and connect the Claude in Chrome extension.
4. Optional but best: put licensed pictures in `episodes/ep01-ashoka/images/001.jpg, 002.jpg ...` first. Without them the video is plain caption cards.
5. Paste everything in the box below. To publish another episode, replace `ep01` / `ep01-ashoka` with the new episode (for example `ep02` / `ep02-chandragupta`) and the playlist name if needed.

```
You are helping me publish the first History of Kings video. The repo is the current folder (branch main). Chrome is open with YouTube Studio signed in as the channel owner, and the Claude in Chrome extension is connected.

Work through the steps below in order. At each step, tell me in one line what you did and what you saw. If something fails, stop and show me the exact error. Do not skip ahead and do not guess.

SAFETY RULES
- Never type, read out or store my Google password or any code sent to me. If a login, 2-step check or consent screen appears, stop and tell me to complete it myself.
- Do not commit client_secret.json or token.json.
- Do not click Publish or change visibility to Public until I reply "publish" for this video.
- Do not delete or edit anything on the channel except the video we create.

STEP 1: Check the computer
Run: python tools/setup_check.py --voice
Fix each FIX line it prints (pip installs are fine to run yourself). If client_secret.json is missing, walk me through creating it using docs/10-novice-guide.md Part 3, one step at a time, and wait for me to confirm each step. Repeat until it says Ready.

STEP 2: Sign in to YouTube for the tool
If token.json is missing, run: python tools/upload.py
The browser will open a Google consent page. Stop and let me approve it. Then confirm token.json exists.

STEP 3: Fact-check gate for Episode 1
Open factcheck/ep01-ashoka.md and the "Fact-check flags" in episodes/ep01-ashoka/script.md. List every item marked NOT verified. Ask me whether I have checked them in the books. Do not continue until I say yes. If I give corrections, edit the script text and note them in the fact-check log.

STEP 4: Approve and test build
Run: python tools/approve.py ep01 (answer y only after I said yes in step 3).
Run: python tools/pipeline.py run --ep ep01-ashoka --dry-run
Tell me where episodes/ep01-ashoka/out/video.mp4 is and its length. Ask me to watch it and tell you "ok" before you continue.

STEP 5: Upload
Run: python tools/pipeline.py run --ep ep01-ashoka --now
Show me the youtu.be link it prints.

STEP 6: Studio settings (in Chrome)
Open the link, then "Edit in Studio" (or go to Studio > Content). For this video:
- Audience: "No, it's not made for kids"
- Altered content / synthetic media: answer Yes (the narration is AI-generated)
- Add it to the playlist "Kings of India" (create the playlist if it does not exist)
- Confirm the description shows chapters starting at 0:00
- Add an end screen if Studio offers it for this video
Take care to Save after each change. Then show me a summary of the settings.

STEP 7: Go public
Ask me: "Ready to publish?" Only after I answer "publish", set Visibility to Public (if it is Private or Scheduled, ask me which I want) and Save. Open the public watch page and confirm the video plays.

STEP 8: Pinned comment
Post this as the channel and pin it: "Which king should we cover next? Tell me in the comments." Confirm it is pinned.

STEP 9: Wrap up
Run python tools/pipeline.py plan and show me the status of ep01. Remind me of the next episode to approve (ep02), and what to check after 48 hours (click rate and average view duration in Studio Analytics).
```

Notes:
- If YouTube keeps the upload Private because the API project is not audited, step 7 sets it to Public in Studio.
- The prompt stops at the points only you can handle: Google sign-in, the book fact-check, watching the test video, and the final "publish".
