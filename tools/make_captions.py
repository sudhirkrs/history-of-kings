"""Build subtitles (out/captions.srt) from the script and the rendered scene lengths.

    python tools/make_captions.py ep01
Run after make_video.py. Each scene's narration is split into short lines timed across that scene.
"""
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from list_scenes import episode, scenes  # noqa: E402


def seg_len(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)])
    return float(out)


def chunks(text, limit=84):
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    out = []
    for s in sentences:
        words, cur = s.split(), ""
        for w in words:
            if len(cur) + len(w) + 1 > limit and cur:
                out.append(cur); cur = w
            else:
                cur = f"{cur} {w}".strip()
        if cur:
            out.append(cur)
    return out


def stamp(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def build(ep):
    out_dir = ep / "out"
    t, n, lines = 0.0, 0, []
    for s in scenes(ep):
        seg = out_dir / f"s{s['n']:03d}.mp4"
        if not seg.exists():
            break
        dur = seg_len(seg)
        parts = chunks(s["narration"])
        total = sum(len(p) for p in parts) or 1
        at = t
        for p in parts:
            d = (dur - 0.4) * len(p) / total
            n += 1
            lines += [str(n), f"{stamp(at)} --> {stamp(at + d)}", p, ""]
            at += d
        t += dur
    (out_dir / "captions.srt").write_text("\n".join(lines))
    return out_dir / "captions.srt", n


if __name__ == "__main__":
    p, n = build(episode(sys.argv[1]))
    print(f"wrote {p} ({n} lines)")
