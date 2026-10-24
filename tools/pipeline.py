"""Run the whole pipeline unattended, with two human gates.

    python tools/pipeline.py plan                       # status table: facts / pictures / video / release / upload
    python tools/pipeline.py prepare --ep ep01          # pictures, voice, video, metadata, thumbnails, captions, Shorts
    python tools/pipeline.py prepare --count 2          # same for the next 2 approved episodes
    python tools/pipeline.py publish --ep ep01          # upload + playlist + captions + comment + Shorts (needs RELEASE)
    python tools/pipeline.py publish --ep ep01 --now    # make it public immediately
    python tools/pipeline.py run --count 2              # prepare then publish (publish only if RELEASE exists)

Gates (you are the approver):
  APPROVED  facts checked against books    -> python tools/approve.py ep01
  RELEASE   pictures + video watched, OK   -> python tools/approve.py ep01 --release
`prepare` needs APPROVED. `publish` needs APPROVED and RELEASE. --no-gate skips both (not advised).
Settings: schedule/config.json. Progress: schedule/state.json (nothing is uploaded twice).
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
CONF = ROOT / "schedule" / "config.json"
STATE = ROOT / "schedule" / "state.json"
DEFAULTS = {
    "order": [],                   # episode folder names, in publishing order; empty = all, sorted
    "first_publish": "2026-11-02T13:00:00Z",
    "interval_days": 3.5,          # 3.5 = twice a week; 7 = weekly
    "voice": "en-IN-PrabhatNeural",
    "tts": "edge",
    "images": "commons",           # "commons" = fetch licensed pictures from Wikimedia Commons; "none" = caption cards
    "shorts": 2,                   # Shorts to make per episode (0 = none)
    "shorts_gap_days": 1,          # first Short goes live this many days after the episode, then one per day
    "comment": True,               # post the first comment (credits + question)
}


def load(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def save_state(state):
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2))


def episodes(conf):
    names = conf["order"] or sorted(p.name for p in (ROOT / "episodes").glob("ep*"))
    return [n for n in names if (ROOT / "episodes" / n / "script.md").exists()]


def find(eps, prefix):
    hits = [n for n in eps if n.startswith(prefix)]
    if len(hits) != 1:
        sys.exit(f"'{prefix}' matches {hits or 'nothing'}")
    return hits[0]


def slot(conf, index):
    t0 = datetime.fromisoformat(conf["first_publish"].replace("Z", "+00:00"))
    return (t0 + timedelta(days=conf["interval_days"] * index)).astimezone(timezone.utc)


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def run(cmd, check=True):
    return subprocess.run([sys.executable, *cmd], cwd=ROOT, check=check).returncode


def thumb_of(ep):
    for n in ("thumbnail.png", "thumbnail.jpg"):
        if (ep / n).exists():
            return ep / n
    return None


def prepare(name, conf):
    ep = ROOT / "episodes" / name
    if conf["images"] == "commons":
        if run(["tools/fetch_images.py", name], check=False):
            print("  note: pictures could not be fetched (offline?); using caption cards for the rest")
    run(["tools/make_video.py", str(ep), "--voice", conf["voice"], "--tts", conf["tts"]])
    run(["tools/build_meta.py", str(ep)])
    if not (ep / "thumbnail.png").exists():
        run(["tools/make_thumb.py", name])
    run(["tools/make_captions.py", name])
    if conf["shorts"]:
        run(["tools/make_shorts.py", name, "--count", str(conf["shorts"])])
    print(f"  prepared {name}. Now review: {ep / 'out' / 'video.mp4'}, images/review.html, thumbnail_A/B.jpg, out/shorts/")
    print(f"  happy? python tools/approve.py {name[:4]} --release")


def publish(name, conf, when, now):
    import upload
    import youtube_extras
    ep = ROOT / "episodes" / name
    meta = json.loads((ep / "metadata.json").read_text())
    video = ep / "out" / "video.mp4"
    if not video.exists():
        raise RuntimeError("no video yet: run prepare first")
    yt = upload.service()
    vid = upload.upload_video(meta, video, thumb_of(ep), None if now else iso(when),
                              "public" if now else None, yt=yt)
    rec = {"url": f"https://youtu.be/{vid}", "publish_at": "now" if now else when.isoformat(), "id": vid}
    rec["extras"] = youtube_extras.run(ep, vid, conf["comment"])
    shorts = ep / "out" / "shorts" / "shorts.json"
    rec["shorts"] = []
    if shorts.exists():
        base = datetime.now(timezone.utc) if now else when
        for i, s in enumerate(json.loads(shorts.read_text())[:conf["shorts"]]):
            t = base + timedelta(days=conf["shorts_gap_days"] + i)
            m = {"title": s["title"],
                 "description": f"{meta['title']}\nFull episode: {rec['url']}\n\nNarration is AI-generated.\n#Shorts",
                 "tags": meta.get("tags", [])[:15], "categoryId": meta.get("categoryId", "27"),
                 "selfDeclaredMadeForKids": False}
            sv = upload.upload_video(m, ep / "out" / "shorts" / s["file"], None, iso(t), None, yt=yt)
            rec["shorts"].append({"url": f"https://youtu.be/{sv}", "publish_at": iso(t)})
    return rec


def status_row(name, conf, state, when):
    ep = ROOT / "episodes" / name
    imgs = len(list((ep / "images").glob("[0-9]*.*"))) if (ep / "images").exists() else 0
    sh = len(list((ep / "out" / "shorts").glob("short*.mp4"))) if (ep / "out" / "shorts").exists() else 0
    flags = [
        "facts" if (ep / "APPROVED").exists() else "-",
        f"pics={imgs}",
        "video" if (ep / "out" / "video.mp4").exists() else "-",
        "thumb" if thumb_of(ep) else "-",
        f"shorts={sh}",
        "RELEASE" if (ep / "RELEASE").exists() else "-",
    ]
    s = state.get(name, {})
    tail = s.get("url") or (f"ERROR {s['error'][:50]}" if "error" in s else "")
    return f"{when:%Y-%m-%d %H:%MZ}  {name:28} {' '.join(f'{f:9}' for f in flags)} {tail}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["plan", "prepare", "publish", "run"])
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--ep")
    ap.add_argument("--dry-run", action="store_true", help="run: prepare only, never upload")
    ap.add_argument("--no-gate", action="store_true")
    ap.add_argument("--now", action="store_true", help="publish immediately instead of scheduling")
    a = ap.parse_args()
    conf = {**DEFAULTS, **load(CONF, {})}
    state = load(STATE, {})
    eps = episodes(conf)
    if a.cmd == "plan":
        print("publish (UTC)      episode                      facts     pics      video     thumb     shorts    RELEASE   youtube")
        for i, n in enumerate(eps):
            print(status_row(n, conf, state, slot(conf, i)))
        return
    todo = [n for n in eps if "url" not in state.get(n, {})]
    if a.ep:
        todo = [find(eps, a.ep)]
    done = 0
    for n in todo:
        if done >= a.count:
            break
        ep = ROOT / "episodes" / n
        if not a.no_gate and not (ep / "APPROVED").exists():
            print(f"skip {n}: no APPROVED file (facts not signed off: python tools/approve.py {n[:4]})")
            continue
        try:
            if a.cmd in ("prepare", "run"):
                print(f"== preparing {n}")
                prepare(n, conf)
            if a.cmd in ("publish", "run") and not (a.cmd == "run" and a.dry_run):
                if not a.no_gate and not (ep / "RELEASE").exists():
                    print(f"hold {n}: not released yet. Review it, then: python tools/approve.py {n[:4]} --release")
                    done += 1
                    continue
                when = slot(conf, eps.index(n))
                if when <= datetime.now(timezone.utc) + timedelta(minutes=20):
                    when = datetime.now(timezone.utc) + timedelta(hours=1)
                rec = publish(n, conf, when, a.now)
                state[n] = rec
                save_state(state)
                print(f"{n}: {'published now' if a.now else 'scheduled ' + when.strftime('%Y-%m-%d %H:%MZ')} -> {rec['url']}")
                print("   extras:", "; ".join(rec["extras"]))
                for s in rec["shorts"]:
                    print(f"   short {s['publish_at']} -> {s['url']}")
                print("   still manual (API cannot): pin the comment, end screen, cards. See docs/11.")
        except Exception as e:
            print(f"FAILED {n}: {e}", file=sys.stderr)
            state[n] = {**state.get(n, {}), "error": str(e)}
            save_state(state)
            continue
        done += 1


if __name__ == "__main__":
    main()
