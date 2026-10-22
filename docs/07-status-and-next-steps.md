# Status & Next Steps

## What exists
- 20 draft scripts (≈30,500 words, ≈3.5 hours of narration), each with chapter headings, `[VISUAL]` cues, a fact-check list, metadata and sources.
- `tools/make_video.py` (script → narrated MP4 with caption cards), `tools/build_meta.py` (script → metadata.json incl. chapters), `tools/upload.py` (upload to YouTube).

## Not done — needs a human
1. **Fact-check every script** (docs/04). Scripts were written from general knowledge, with no internet access to the sources.
   Dates, numbers and quotes marked in each "Fact-check flags" list are the first to verify. Some sentences are still rough and should be read aloud and tidied.
2. **Images.** Add licensed images per scene (`episodes/<ep>/images/001.jpg`, …); card-only videos will not retain viewers. Note credits in `credits.md`.
3. **Voice test.** Run edge-tts with 2–3 voices on one scene, pick one (default `en-IN-PrabhatNeural`).
4. **YouTube setup + OAuth** (see README) — requires your Google account.
5. **Thumbnails** (1280×720) per episode.

## Per-episode flow
```
python tools/make_video.py episodes/epNN-name        # video.mp4, chapters.txt, scenes.json
python tools/build_meta.py episodes/epNN-name        # metadata.json (title, description with chapters, tags)
python tools/upload.py episodes/epNN-name episodes/epNN-name/out/video.mp4 thumbnail.png 2026-11-01T13:00:00Z
```
