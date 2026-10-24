# History of Kings — Channel Production Kit

Everything needed to take an episode from idea to published YouTube video.

| File | Purpose |
|---|---|
| `docs/01-channel-strategy.md` | Positioning, audience, format, schedule, growth |
| `docs/02-episode-roadmap.md` | Season-by-season list of kings (India → Mongols → Russia → Europe → China) |
| `docs/03-script-guide.md` | Script template, writing style, length maths |
| `docs/04-research-and-fact-check.md` | Source rules and the fact-check checklist (authenticity) |
| `docs/05-production-pipeline.md` | Voice, visuals, editing, thumbnail, tools and cost |
| `docs/06-publishing-checklist.md` | Upload, SEO, titles, description template, post-publish |
| `episodes/ep01-ashoka/` | Finished first script + metadata |
| `tools/upload.py` | Optional: upload a video + metadata via the YouTube Data API |

## Workflow per episode (about 6–8 hours once routine)
1. Pick topic from the roadmap → 2. Research (2–3 sources) → 3. Write script from template →
4. Fact-check against checklist → 5. Voiceover → 6. Visuals + edit → 7. Thumbnail + metadata →
8. Review → 9. Upload & schedule → 10. Check analytics after 48 h, note lessons.

## Making a video (on your own machine)
```
pip install edge-tts pillow google-api-python-client google-auth-oauthlib   # + ffmpeg installed
python tools/make_video.py episodes/ep01-ashoka            # AI voice (en-IN-PrabhatNeural) + captioned cards
# optional: drop licensed images into episodes/ep01-ashoka/images/001.jpg, 002.jpg ... (one per scene) and re-run
python tools/upload.py episodes/ep01-ashoka episodes/ep01-ashoka/out/video.mp4 thumbnail.png
```
Scene timings for chapters are written to `out/scenes.json`.
