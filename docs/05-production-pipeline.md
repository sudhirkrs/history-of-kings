# Production Pipeline

## 1. Voiceover
- Easiest: ElevenLabs / Azure Neural / Google Cloud TTS (pick a calm, clear voice; use the same voice always) — or record yourself with a USB mic (more authentic, better retention).
- Export WAV, remove breaths/noise (Audacity, free). Break narration into scene files if you want precise sync.

## 2. Visuals
- Maps: Google Earth Studio, Mapchart + After Effects/DaVinci, or Canva animations.
- Images: Wikimedia Commons, Met/Rijksmuseum/British Museum open access, Archive.org. Record licence + author in `credits.md`.
- AI-generated art: allowed but label as "illustration", never present as real portraits/photos.
- Motion: slow zoom (Ken Burns), parallax, text overlays for dates/names.

## 3. Editing
- DaVinci Resolve (free) or CapCut/Premiere. Template: intro ≤ 5 s, lower-third name cards, timeline strip, chapter markers.
- Music: YouTube Audio Library or Epidemic/Artlist; duck under voice (-20 dB).
- Captions: auto-generate then correct; upload `.srt` for accessibility and SEO.
- Export: 1080p (or 4K), H.264, 16:9, loudness -14 LUFS.

## 4. Thumbnail
- 1280×720, ≤2 MB. One face/figure, 3–4 words max, high contrast. Make 2 variants for A/B test (YouTube "Test & compare").

## 5. Optional automation (later)
Script → TTS → ffmpeg slideshow can be scripted, but keep a human edit pass for quality. `tools/upload.py` handles the upload step.

## Budget (monthly, rough)
Free-tier: ₹0 using Resolve + Audio Library + own voice. Typical: TTS ₹1,000–2,000 + stock ₹0–2,000.

## Time per episode
Research 2 h · Script 2 h · Fact-check 1 h · Voice 0.5 h · Edit 3–4 h · Thumbnail/metadata 0.5 h.
