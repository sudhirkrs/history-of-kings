"""Sign off an episode for the pipeline.

    python tools/approve.py ep04            # shows open flags + unverified claims, asks y/N
    python tools/approve.py ep04 ep05 -y    # approve without asking
    python tools/approve.py --list          # approval status of every episode
    python tools/approve.py ep04 --revoke

Creates episodes/<ep>/APPROVED, which tools/pipeline.py requires before building or uploading.
Only approve after you have checked the listed items against books.
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EPS = sorted((ROOT / "episodes").glob("ep*"))


def find(prefix):
    hits = [e for e in EPS if e.name.startswith(prefix)]
    if len(hits) != 1:
        sys.exit(f"'{prefix}' matches {[h.name for h in hits] or 'nothing'}")
    return hits[0]


def open_items(ep):
    items = []
    script = (ep / "script.md").read_text()
    flags = script.split("## Fact-check flags", 1)[-1].split("## Metadata", 1)[0]
    items += [l.strip() for l in flags.splitlines() if l.strip().startswith("- [ ]")]
    log = next((ROOT / "factcheck").glob(ep.name.split("-")[0] + "-*.md"), None)
    if log:
        items += [re.sub(r"\s+", " ", l).strip(" |") for l in log.read_text().splitlines()
                  if "NOT verified" in l or "FLAG" in l]
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episodes", nargs="*")
    ap.add_argument("-y", "--yes", action="store_true")
    ap.add_argument("--revoke", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list or not a.episodes:
        for e in EPS:
            print(("APPROVED  " if (e / "APPROVED").exists() else "pending   ") + e.name)
        return
    for p in a.episodes:
        ep = find(p)
        mark = ep / "APPROVED"
        if a.revoke:
            mark.unlink(missing_ok=True); print("revoked", ep.name); continue
        items = open_items(ep)
        print(f"\n{ep.name}: {len(items)} item(s) to check against books")
        for i in items:
            print("  -", i[:160])
        if a.yes or input("Checked them all? Approve (y/N): ").strip().lower() == "y":
            mark.write_text("approved\n"); print("approved", ep.name)
        else:
            print("not approved", ep.name)


if __name__ == "__main__":
    main()
