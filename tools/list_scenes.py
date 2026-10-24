"""List an episode's scenes with their visual cues, so you can fill the images folder.

    python tools/list_scenes.py ep01                # table: scene, file name to use, status, cue
    python tools/list_scenes.py ep01 --missing      # only scenes that still have no image
    python tools/list_scenes.py ep01 --md           # also write episodes/<ep>/shotlist.md (checklist with narration)
    python tools/list_scenes.py --all               # one line per episode: scenes with images / total

Name each picture with the file name shown (001.jpg, 002.png ...) and put it in episodes/<ep>/images/.
Any image type works (jpg, png, webp). Scenes without an image get a plain caption card.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_video import parse  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def episode(prefix):
    hits = [e for e in sorted((ROOT / "episodes").glob("ep*")) if e.name.startswith(prefix)]
    if len(hits) != 1:
        sys.exit(f"'{prefix}' matches {[h.name for h in hits] or 'nothing'}")
    return hits[0]


def scenes(ep):
    """Scenes with section name carried forward and image status."""
    out, section = [], ""
    for n, s in enumerate(parse(ep / "script.md"), 1):
        section = s.get("chapter") or section
        found = sorted((ep / "images").glob(f"{n:03d}.*")) if (ep / "images").exists() else []
        words = len(s["narration"].split())
        out.append({"n": n, "section": section, "cue": s["caption"], "narration": s["narration"],
                    "image": found[0].name if found else None, "secs": round(words / 145 * 60)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode", nargs="?")
    ap.add_argument("--missing", action="store_true")
    ap.add_argument("--md", action="store_true")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    if a.all or not a.episode:
        for ep in sorted((ROOT / "episodes").glob("ep*")):
            sc = scenes(ep)
            have = sum(1 for s in sc if s["image"])
            print(f"{ep.name:30} {have:3}/{len(sc):3} scenes have images")
        return
    ep = episode(a.episode)
    sc = scenes(ep)
    have = sum(1 for s in sc if s["image"])
    print(f"{ep.name}: {len(sc)} scenes, {have} with images, {len(sc) - have} missing\n")
    last = None
    for s in sc:
        if a.missing and s["image"]:
            continue
        if s["section"] != last:
            print(f"[{s['section']}]")
            last = s["section"]
        mark = "have " + s["image"] if s["image"] else "MISSING"
        print(f"  {s['n']:03d}.jpg  {s['secs']:3d}s  {mark:14}  {s['cue']}")
    if a.md:
        lines = [f"# Shot list: {ep.name}", "",
                 "Put one image per scene in `images/` using the file name shown. Credit each in `credits.md`.", ""]
        last = None
        for s in sc:
            if s["section"] != last:
                lines += [f"## {s['section']}", ""]
                last = s["section"]
            box = "x" if s["image"] else " "
            lines += [f"- [{box}] **{s['n']:03d}** ({s['secs']}s) {s['cue']}",
                      f"  - narration: {s['narration'][:140]}{'...' if len(s['narration']) > 140 else ''}"]
        (ep / "shotlist.md").write_text("\n".join(lines) + "\n")
        print(f"\nwrote {ep / 'shotlist.md'}")


if __name__ == "__main__":
    main()
