"""Build export/notion-import.zip for Notion's Settings > Import > Text & Markdown.

    python tools/export_notion.py

Zip layout: Docs/*.md, Episodes/epNN-*.md (script + metadata + fact-check log), Episodes.csv
(import the CSV separately as a database: Import > CSV). Needs no network.
"""
import csv, glob, io, re, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, "/tmp")
BLOCK = {}
for ln in (ROOT / "docs" / "02-episode-roadmap.md").read_text().splitlines():
    m = re.match(r"\| (\d+) \| (.+?) \| (.+?) \| (.+?) \|$", ln)
    if m:
        BLOCK[int(m[1])] = (m[3], m[4])


def page(ep):
    s = (ROOT / "episodes" / ep / "script.md").read_text()
    title, *lines = s.split("\n")
    out = [title]
    for l in lines:
        if l.startswith("Target:") or l.strip() == "**NARRATION**":
            continue
        m = re.match(r"\[VISUAL: (.*)\]\s*$", l)
        out.append(f"*Visual: {m[1]}*" if m else l)
    fc = next(iter(glob.glob(str(ROOT / "factcheck" / (ep.split("-")[0] + "-*.md")))), None)
    body = "\n".join(out).strip()
    if fc:
        body += "\n\n## Fact-check log\n" + re.sub(r"(?m)^# .*\n", "", Path(fc).read_text()).strip()
    return title.lstrip("# ").strip(), body, s


def main():
    (ROOT / "export").mkdir(exist_ok=True)
    rows = io.StringIO()
    w = csv.writer(rows)
    w.writerow(["Episode", "No", "Block", "Question", "Status", "Words", "Minutes"])
    with zipfile.ZipFile(ROOT / "export" / "notion-import.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for d in sorted((ROOT / "docs").glob("*.md")):
            z.writestr(f"Docs/{d.name}", d.read_text())
        for e in sorted((ROOT / "episodes").glob("ep*")):
            title, body, raw = page(e.name)
            z.writestr(f"Episodes/{e.name}.md", body + "\n")
            n = int(e.name[2:4])
            tm = re.search(r"~(\d+) min \((\d+) words\)", raw)
            blk, q = BLOCK.get(n, ("", ""))
            w.writerow([title, n, blk, q, "Fact-checked (search)", tm[2], tm[1]])
        z.writestr("Episodes.csv", rows.getvalue())
    print("wrote export/notion-import.zip")


if __name__ == "__main__":
    main()
