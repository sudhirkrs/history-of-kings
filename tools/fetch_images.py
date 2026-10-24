"""Find free, properly licensed pictures for every scene from Wikimedia Commons.

    python tools/fetch_images.py ep01                # fill images/NNN.jpg for scenes that have none
    python tools/fetch_images.py ep01 --redo 7 12    # re-pick scenes 7 and 12 (uses the next-best candidate)
    python tools/fetch_images.py ep01 --dry-run      # just print the search for each scene

Only public-domain, CC0, CC-BY and CC-BY-SA files are accepted. For every picture it records author,
licence and link in episodes/<ep>/credits.md, and writes images/review.html (open it in a browser to
look at each pick and its alternatives). Scenes whose cue is a title card, timeline, diagram, question
card or end screen are left as caption cards. Existing pictures you added yourself are never replaced.
Needs internet; Wikimedia asks for a descriptive User-Agent, set below.
"""
import argparse
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from list_scenes import ROOT, episode, scenes  # noqa: E402

API = "https://commons.wikimedia.org/w/api.php"
UA = "HistoryOfKingsBot/1.0 (educational channel; contact: channel owner)"
OK_LICENCE = re.compile(r"^(public domain|pd|cc0|cc[- ]by(-sa)?([- ]\d(\.\d)?)?|attribution)", re.I)
BAD_LICENCE = re.compile(r"(nc|nd|fair use|non-?commercial|no derivatives)", re.I)
SKIP_CUE = re.compile(r"(end screen|title card|question card|timeline|diagram|chart|on screen|numbers on screen|"
                      r"text overlay|quote card|labelled|cards?$)", re.I)
STOP = set("a an the of and or to in on at with for from by as is are was were then split screen close up "
           "slow zoom labelled label note shown showing image images picture portrait illustration".split())
BAD_TITLE = re.compile(r"(logo|flag of|icon|stub|signature|coat of arms of the|wikimedia|commons-logo|"
                       r"\.svg$|\.gif$|\.tif|\.pdf|\.ogg|\.webm)", re.I)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read()


def api(**params):
    params.update(format="json", formatversion="2")
    return json.loads(get(API + "?" + urllib.parse.urlencode(params)))


def subject(ep):
    """Person/subject name from the script title, e.g. 'Ashoka' from 'Ep 1 — Ashoka: The King ...'."""
    title = (ep / "script.md").read_text().splitlines()[0]
    m = re.match(r"#\s*Ep\s*\d+\s*[—-]\s*([^:]+):", title)
    name = m.group(1).strip() if m else ep.name.split("-", 1)[-1].replace("-", " ")
    return re.sub(r",?\s*Part \d+", "", name)


def query_for(cue, subj):
    words = [w for w in re.findall(r"[A-Za-z0-9']+", cue) if w.lower() not in STOP and len(w) > 2]
    return f"{subj} {' '.join(words[:6])}".strip()


def licence_ok(meta):
    lic = (meta.get("LicenseShortName", {}) or {}).get("value", "")
    if not lic or BAD_LICENCE.search(lic):
        return False
    return bool(OK_LICENCE.search(lic.strip()))


def candidates(query):
    """Return acceptable image dicts for a search query, best first."""
    r = api(action="query", generator="search", gsrnamespace=6, gsrsearch=query, gsrlimit=12,
            prop="imageinfo", iiprop="url|size|mime|extmetadata", iiurlwidth=1920)
    out = []
    for p in sorted(r.get("query", {}).get("pages", []), key=lambda x: x.get("index", 0)):
        info = (p.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})
        if BAD_TITLE.search(p.get("title", "")) or info.get("mime") not in ("image/jpeg", "image/png", "image/webp"):
            continue
        if info.get("width", 0) < 900 or not licence_ok(meta):
            continue
        strip = lambda k: re.sub(r"<[^>]+>", "", (meta.get(k, {}) or {}).get("value", "")).strip()
        out.append({"title": p["title"], "url": info.get("thumburl") or info["url"], "page": info.get("descriptionurl", ""),
                    "author": strip("Artist") or "Unknown", "licence": strip("LicenseShortName"), "w": info.get("width", 0)})
    return out


def pick_for_scene(cue, subj, used):
    """Try a specific query, then a broader one. Returns (candidate_list)."""
    seen, result = set(), []
    for q in (query_for(cue, subj), subj):
        for c in candidates(q):
            if c["title"] not in used and c["title"] not in seen:
                seen.add(c["title"]); result.append(c)
        if len(result) >= 4:
            break
        time.sleep(0.3)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--redo", nargs="*", type=int, default=[])
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    ep = episode(a.episode)
    subj = subject(ep)
    img_dir = ep / "images"
    img_dir.mkdir(exist_ok=True)
    state_f = img_dir / "picks.json"
    state = json.loads(state_f.read_text()) if state_f.exists() else {}
    used = {v["chosen"]["title"] for v in state.values() if v.get("chosen")}
    for s in scenes(ep):
        n = s["n"]
        have = sorted(img_dir.glob(f"{n:03d}.*"))
        key = f"{n:03d}"
        if SKIP_CUE.search(s["cue"]):
            print(f"{key} skip (text card): {s['cue']}")
            continue
        if have and key not in state:
            print(f"{key} keep your own picture {have[0].name}")
            continue
        if have and n not in a.redo:
            continue
        print(f"{key} searching: {query_for(s['cue'], subj)}")
        if a.dry_run:
            continue
        try:
            if n in a.redo and key in state:
                cands = [c for c in state[key]["options"] if c["title"] != state[key]["chosen"]["title"]]
                used.discard(state[key]["chosen"]["title"])
            else:
                cands = pick_for_scene(s["cue"], subj, used)
        except Exception as e:  # network or API problem: leave the card, keep going
            print(f"      search failed ({e}); caption card kept")
            continue
        if not cands:
            print("      nothing suitable; caption card kept")
            continue
        best = cands[0]
        try:
            data = get(best["url"])
        except Exception as e:
            print(f"      download failed ({e}); caption card kept")
            continue
        for old in have:
            old.unlink()
        ext = ".png" if best["url"].lower().endswith(".png") else ".jpg"
        (img_dir / f"{key}{ext}").write_bytes(data)
        used.add(best["title"])
        state[key] = {"cue": s["cue"], "chosen": best, "options": cands}
        state_f.write_text(json.dumps(state, indent=1))
        print(f"      {best['title']}  [{best['licence']}]")
        time.sleep(0.4)
    if a.dry_run:
        return
    write_credits(ep, state)
    write_review(ep, state)
    print(f"\nPictures: {len(state)} chosen. Review: {img_dir / 'review.html'}   Credits: {ep / 'credits.md'}")


def write_credits(ep, state):
    lines = ["# Image credits", "", "Pictures from Wikimedia Commons. Illustrations are historical images, not photos of the event.", ""]
    for k in sorted(state):
        c = state[k]["chosen"]
        lines.append(f"- Scene {k}: {c['title'].replace('File:', '')} — {c['author']} — {c['licence']} — {c['page']}")
    (ep / "credits.md").write_text("\n".join(lines) + "\n")


def write_review(ep, state):
    rows = []
    for k in sorted(state):
        v = state[k]
        alts = "".join(f"<a href='{html.escape(o['page'])}'><img src='{html.escape(o['url'])}' height=90></a> " for o in v["options"][1:])
        c = v["chosen"]
        rows.append(f"<tr><td>{k}</td><td>{html.escape(v['cue'])}<br><small>{html.escape(c['title'])} — {html.escape(c['licence'])}</small></td>"
                    f"<td><img src='{k}.jpg' height=140 onerror=\"this.src='{k}.png'\"></td><td>{alts}</td></tr>")
    page = ("<meta charset=utf-8><title>Picture review</title><style>body{font:14px sans-serif;max-width:1100px;margin:20px auto}"
            "td{vertical-align:top;padding:6px;border-bottom:1px solid #ccc}</style>"
            "<h2>Picture review</h2><p>To swap scene N: <code>python tools/fetch_images.py EP --redo N</code>, "
            "or drop your own file named NNN.jpg into this folder.</p><table>" + "".join(rows) + "</table>")
    (ep / "images" / "review.html").write_text(page)


if __name__ == "__main__":
    main()
