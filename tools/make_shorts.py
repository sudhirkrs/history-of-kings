"""Cut vertical (9:16) Shorts with burned-in captions from a built episode.

    python tools/make_shorts.py ep01             # 3 Shorts: the hook plus two more windows
    python tools/make_shorts.py ep01 --count 2
Run after make_video.py. Output: episodes/<ep>/out/shorts/short1.mp4 ... and shorts.json (title, description).
Windows are runs of consecutive scenes of at most 55 seconds. Short 1 is the hook; the others start at scene
boundaries a third and two thirds of the way through. To choose your own, create episodes/<ep>/shorts.json:
    [{"title": "Why did Ashoka say sorry?", "scenes": [31, 32, 33]}, ...]
"""
import argparse
import json
import re
import subprocess
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from list_scenes import episode, scenes  # noqa: E402
from make_captions import seg_len  # noqa: E402

MAXLEN = 55.0
FONTS = ["DejaVuSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"]


def font(size):
    for f in FONTS:
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


def overlay(text, dest):
    img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = font(54)
    lines = textwrap.wrap(text, 30)[:5]
    h = len(lines) * 70 + 50
    y0 = 1920 - 330 - h
    d.rounded_rectangle([50, y0, 1030, y0 + h], radius=28, fill=(0, 0, 0, 170))
    y = y0 + 25
    for ln in lines:
        d.text((540, y), ln, font=f, fill=(255, 255, 255, 255), anchor="ma")
        y += 70
    img.save(dest)


def windows(ep, lens, count):
    n = len(lens)
    def run_from(i):
        pick, t = [], 0.0
        while i < n and t + lens[i] <= MAXLEN:
            pick.append(i + 1); t += lens[i]; i += 1
        return pick or [i + 1]
    total = sum(lens)
    starts, acc = [0], 0.0
    targets = [total / 3, 2 * total / 3]
    for i, l in enumerate(lens):
        for tg in list(targets):
            if acc >= tg:
                starts.append(i); targets.remove(tg)
        acc += l
    return [run_from(s) for s in starts[:count]]


def title_of(ep):
    first = (ep / "script.md").read_text().splitlines()[0]
    m = re.match(r"#\s*Ep\s*\d+\s*[—-]\s*([^:]+):\s*(.+)", first)
    return (m.group(1).strip(), m.group(2).strip()) if m else (ep.name, "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--count", type=int, default=3)
    a = ap.parse_args()
    ep = episode(a.episode)
    out = ep / "out"
    sc = scenes(ep)
    lens = [seg_len(out / f"s{s['n']:03d}.mp4") for s in sc if (out / f"s{s['n']:03d}.mp4").exists()]
    custom = ep / "shorts.json"
    if custom.exists():
        plan = json.loads(custom.read_text())[:a.count]
    else:
        name, sub = title_of(ep)
        labels = [f"{name}: {sub}", f"{name}: the turning point", f"{name}: what historians still debate"]
        plan = [{"title": labels[i], "scenes": w} for i, w in enumerate(windows(ep, lens, a.count))]
    sdir = out / "shorts"
    sdir.mkdir(exist_ok=True)
    meta = []
    for k, p in enumerate(plan, 1):
        parts = []
        for n in p["scenes"]:
            seg = out / f"s{n:03d}.mp4"
            ov = sdir / f"o{k}_{n:03d}.png"
            overlay(next(s["narration"] for s in sc if s["n"] == n)[:170], ov)
            vid = sdir / f"p{k}_{n:03d}.mp4"
            fc = ("[0:v]split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30[bg];"
                  "[b]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2[v1];[v1][1:v]overlay=0:0,format=yuv420p[v]")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(seg), "-i", str(ov), "-filter_complex", fc,
                            "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "veryfast", "-c:a", "aac", str(vid)], check=True)
            parts.append(vid)
        lst = sdir / f"list{k}.txt"
        lst.write_text("".join(f"file '{v.name}'\n" for v in parts))
        dest = sdir / f"short{k}.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-i", str(lst), "-c", "copy", str(dest)], check=True)
        dur = seg_len(dest)
        meta.append({"file": dest.name, "title": (p["title"][:90] + " #Shorts"), "scenes": p["scenes"], "seconds": round(dur, 1)})
        print(f"short{k}: scenes {p['scenes']}  {dur:.0f}s  ->  {dest}")
        for tmp in list(sdir.glob(f"p{k}_*.mp4")) + list(sdir.glob(f"o{k}_*.png")) + [lst]:
            tmp.unlink()
    (sdir / "shorts.json").write_text(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
