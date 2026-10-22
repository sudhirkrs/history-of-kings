"""Build an MP4 from an episode script.

    pip install edge-tts pillow        # ffmpeg must be on PATH
    python tools/make_video.py episodes/ep01-ashoka [--voice en-IN-PrabhatNeural] [--tts silent]

Reads episodes/<ep>/script.md. Each [VISUAL: ...] cue starts a scene; the narration
before it is spoken over that scene. If episodes/<ep>/images/NNN.jpg|png exists
(NNN = scene number, 001 first) it is used as the background (slow zoom); otherwise a
styled caption card is drawn. Output: episodes/<ep>/out/video.mp4 + scenes.json (timings).
Voice: edge-tts (free neural voices, needs internet). `--tts silent` makes placeholder
audio so the render can be tested offline.
"""
import argparse, asyncio, json, re, string, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 30
BG, FG, ACCENT = (24, 20, 16), (244, 236, 220), (201, 150, 60)


def parse(script):
    """Return [{narration, caption}] scenes."""
    scenes, buf, heading = [], [], None
    for raw in script.read_text().splitlines():
        line = raw.strip()
        if line.startswith(("## Fact-check", "## Metadata")):
            break
        if line.startswith("## "):
            heading = re.sub(r"^\d+\.\s*|\s*\(.*?\)\s*$", "", line[3:]).strip()
            heading = string.capwords(heading.lower())
            continue
        if not line or line.startswith(("#", "---", "**NARRATION", "Target:")) or line.startswith("- ["):
            continue
        cues = re.findall(r"\[VISUAL:\s*(.*?)\]", line)
        text = re.sub(r"\[(VISUAL|SOURCE):.*?\]", "", line).replace("**", "").replace("*", "").strip()
        if text:
            buf.append(text)
        for cue in cues:
            scenes.append({"narration": " ".join(buf), "caption": cue, "chapter": heading})
            heading = None
            buf = []
    if buf:
        scenes.append({"narration": " ".join(buf), "caption": scenes[-1]["caption"] if scenes else ""})
    return [s for s in scenes if s["narration"]]


def duration(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                   "-of", "csv=p=0", str(path)])
    return float(out)


async def tts(text, path, voice):
    import edge_tts
    await edge_tts.Communicate(text, voice, rate="-5%").save(str(path))


def make_audio(i, text, out, kind, voice):
    path = out / f"a{i:03d}.mp3"
    if kind == "silent":
        secs = max(2.0, len(text.split()) / 2.4)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                        "-t", f"{secs:.2f}", "-q:a", "9", str(path)], check=True)
    else:
        asyncio.run(tts(text, path, voice))
    return path


def font(size):
    for f in ("DejaVuSerif-Bold.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


def card(i, caption, title, out):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([80, 80, W - 80, H - 80], outline=ACCENT, width=4)
    d.text((140, 120), title.upper(), font=font(36), fill=ACCENT)
    words, lines, cur = caption.split(), [], ""
    for w in words:
        if len(cur) + len(w) > 32:
            lines.append(cur); cur = w
        else:
            cur = f"{cur} {w}".strip()
    lines.append(cur)
    y = H // 2 - len(lines) * 45
    for ln in lines:
        d.text((140, y), ln, font=font(80), fill=FG)
        y += 100
    p = out / f"c{i:03d}.png"
    img.save(p)
    return p


def render_scene(i, image, audio, out):
    secs = duration(audio) + 0.4
    seg = out / f"s{i:03d}.mp4"
    zoom = f"zoompan=z='min(zoom+0.0004,1.12)':d={int(secs*FPS)}:s={W}x{H}:fps={FPS}"
    vf = f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},{zoom},format=yuv420p"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(image), "-i", str(audio),
                    "-vf", vf, "-t", f"{secs:.2f}", "-c:v", "libx264", "-preset", "veryfast",
                    "-c:a", "aac", "-ar", "44100", "-ac", "2", "-shortest", str(seg)], check=True)
    return seg, secs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--voice", default="en-IN-PrabhatNeural")
    ap.add_argument("--tts", default="edge", choices=["edge", "silent"])
    ap.add_argument("--limit", type=int, default=0, help="only first N scenes (test)")
    a = ap.parse_args()
    ep = Path(a.episode)
    out = ep / "out"; out.mkdir(exist_ok=True)
    scenes = parse(ep / "script.md")
    if a.limit:
        scenes = scenes[:a.limit]
    title = (ep / "script.md").read_text().splitlines()[0].lstrip("# ").strip()
    segs, t, timing = [], 0.0, []
    for n, s in enumerate(scenes, 1):
        audio = make_audio(n, s["narration"], out, a.tts, a.voice)
        imgs = sorted((ep / "images").glob(f"{n:03d}.*")) if (ep / "images").exists() else []
        image = imgs[0] if imgs else card(n, s["caption"], title.split("—")[0], out)
        seg, secs = render_scene(n, image, audio, out)
        segs.append(seg)
        timing.append({"scene": n, "start": round(t, 1), "caption": s["caption"], "chapter": s.get("chapter")})
        t += secs
        print(f"scene {n}/{len(scenes)} {secs:.0f}s", file=sys.stderr)
    lst = out / "list.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in segs))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-i", str(lst), "-c", "copy",
                    str(out / "video.mp4")], check=True)
    ch = [f"{int(x['start'])//60}:{int(x['start'])%60:02d} {x['chapter']}" for x in timing if x["chapter"]]
    if ch:
        ch[0] = "0:00 " + ch[0].split(" ", 1)[1]
    (out / "chapters.txt").write_text("\n".join(ch) + "\n")
    (out / "scenes.json").write_text(json.dumps(timing, indent=1))
    print(f"Done: {out/'video.mp4'} ({t/60:.1f} min)")


if __name__ == "__main__":
    main()
