"""Make two thumbnails (A and B) for an episode from its pictures.

    python tools/make_thumb.py ep01
Writes thumbnail_A.jpg, thumbnail_B.jpg and thumbnail.jpg (= A) in the episode folder, 1280x720, under 2 MB.
Picture: the first real picture in images/ (override: put THUMB_IMAGE=007 in thumbnail.txt).
Words: A = 3-5 word hook from the episode title; B = the king's name. Override with thumbnail.txt:
    line 1 = text for A, line 2 = text for B.
"""
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
from list_scenes import episode  # noqa: E402

W, H = 1280, 720
GOLD, WHITE = (245, 196, 66), (255, 255, 255)
FONTS = ["Impact.ttf", "impact.ttf", "Arial Bold.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf",
         "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf"]


def font(size):
    for f in FONTS:
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


def words_for(ep):
    first = (ep / "script.md").read_text().splitlines()[0]
    m = re.match(r"#\s*Ep\s*\d+\s*[—-]\s*([^:]+):\s*(.+)", first)
    name, sub = (m.group(1).strip(), m.group(2).strip()) if m else (ep.name, ep.name)
    sub = re.sub(r"^(The|A|An)\s+", "", sub, flags=re.I)
    hook = " ".join(sub.split()[:5]).upper()
    over = ep / "thumbnail.txt"
    if over.exists():
        ls = [l.strip() for l in over.read_text().splitlines() if l.strip() and not l.startswith("THUMB_IMAGE")]
        if ls:
            return ls[0].upper(), (ls[1] if len(ls) > 1 else name).upper()
    return hook, name.upper()


def pick_image(ep):
    over = ep / "thumbnail.txt"
    if over.exists():
        m = re.search(r"THUMB_IMAGE=(\d+)", over.read_text())
        if m:
            for p in (ep / "images").glob(f"{int(m.group(1)):03d}.*"):
                return p
    imgs = sorted(p for p in (ep / "images").glob("[0-9][0-9][0-9].*") if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"))
    return imgs[0] if imgs else None


def wrap(draw, text, fnt, width):
    lines, cur = [], ""
    for w in text.split():
        test = f"{cur} {w}".strip()
        if draw.textlength(test, font=fnt) > width and cur:
            lines.append(cur); cur = w
        else:
            cur = test
    lines.append(cur)
    return lines


def render(src, text, dest, variant):
    base = ImageOps.fit(Image.open(src).convert("RGB"), (W, H), method=Image.LANCZOS, centering=(0.5, 0.35)) if src else Image.new("RGB", (W, H), (24, 20, 16))
    shade = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(shade)
    for x in range(W):
        sd.line([(x, 0), (x, H)], fill=int(200 * max(0, 1 - x / (W * 0.85))))
    base = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), base, shade)
    d = ImageDraw.Draw(base)
    size = 150 if variant == "B" else 118
    while size > 60:
        f = font(size)
        lines = wrap(d, text, f, 700)
        if len(lines) * size * 1.05 <= H - 160:
            break
        size -= 6
    y = (H - len(lines) * size * 1.05) / 2
    for i, ln in enumerate(lines):
        col = GOLD if i == 0 else WHITE
        for dx, dy in ((-3, -3), (3, 3), (-3, 3), (3, -3)):
            d.text((60 + dx, y + dy), ln, font=f, fill=(0, 0, 0))
        d.text((60, y), ln, font=f, fill=col)
        y += size * 1.05
    q = 90
    while True:
        base.save(dest, "JPEG", quality=q)
        if dest.stat().st_size < 1_900_000 or q < 50:
            break
        q -= 8
    return dest


def main():
    ep = episode(sys.argv[1])
    a_text, b_text = words_for(ep)
    src = pick_image(ep)
    a = render(src, a_text, ep / "thumbnail_A.jpg", "A")
    render(src, b_text, ep / "thumbnail_B.jpg", "B")
    (ep / "thumbnail.jpg").write_bytes(a.read_bytes())
    print(f"thumbnails: A='{a_text}'  B='{b_text}'  picture={src.name if src else 'none (plain card)'}")


if __name__ == "__main__":
    main()
