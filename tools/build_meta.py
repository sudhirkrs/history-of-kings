"""Create metadata.json for an episode from the '## Metadata' block of its script.md.

    python tools/build_meta.py episodes/ep04-shivaji
Uses out/chapters.txt (from make_video.py) if present. Block format:
    ## Metadata
    Title: ...
    Hook: ...
    Tags: a, b, c
    Hashtags: #A #B
    Sources:
    - ...
"""
import json, sys
from pathlib import Path

ep = Path(sys.argv[1])
text = (ep / "script.md").read_text()
block = text.split("## Metadata", 1)[1]
meta, sources, in_src = {}, [], False
for ln in block.splitlines():
    if ln.startswith("Sources:"):
        in_src = True
    elif in_src and ln.startswith("- "):
        sources.append(ln)
    elif ":" in ln and not in_src:
        k, v = ln.split(":", 1)
        meta[k.strip()] = v.strip()
ch = (ep / "out" / "chapters.txt")
chapters = "CHAPTERS\n" + ch.read_text() + "\n" if ch.exists() else ""
desc = (f"{meta['Hook']}\n\n{chapters}SOURCES\n" + "\n".join(sources) +
        f"\n\nNarration is AI-generated. Images are credited in the pinned comment.\n\n{meta['Hashtags']}")
(ep / "metadata.json").write_text(json.dumps({
    "title": meta["Title"], "description": desc,
    "tags": [t.strip() for t in meta["Tags"].split(",")],
    "categoryId": "27", "privacyStatus": "private", "selfDeclaredMadeForKids": False}, indent=2))
print("wrote", ep / "metadata.json")
