"""Run the whole pipeline (voice + video -> metadata -> thumbnail -> scheduled upload) unattended.

    python tools/pipeline.py plan                      # show the queue and publish dates
    python tools/pipeline.py run --count 2             # build + upload the next 2 episodes
    python tools/pipeline.py run --ep ep04-shivaji     # one specific episode
    python tools/pipeline.py run --count 1 --dry-run   # build everything, skip the upload

Settings live in schedule/config.json. Progress is recorded in schedule/state.json, so
re-running never uploads an episode twice and a failed episode is retried next time.

Safety gate: an episode is only built when episodes/<ep>/APPROVED exists (create it after
you have checked the 'Fact-check flags' against books). Pass --no-gate to skip this.
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONF = ROOT / "schedule" / "config.json"
STATE = ROOT / "schedule" / "state.json"
DEFAULTS = {
    "order": [],                   # episode folder names, in publishing order; empty = all, sorted
    "first_publish": "2026-11-02T13:00:00Z",
    "interval_days": 3.5,          # 3.5 = twice a week; 7 = weekly
    "voice": "en-IN-PrabhatNeural",
    "tts": "edge",
}


def load(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def episodes(conf):
    names = conf["order"] or sorted(p.name for p in (ROOT / "episodes").glob("ep*"))
    return [n for n in names if (ROOT / "episodes" / n / "script.md").exists()]


def slot(conf, index):
    t0 = datetime.fromisoformat(conf["first_publish"].replace("Z", "+00:00"))
    return (t0 + timedelta(days=conf["interval_days"] * index)).astimezone(timezone.utc)


def thumbnail(ep_dir):
    """Use thumbnail.png if you made one; otherwise draw a plain title card."""
    thumb = ep_dir / "thumbnail.png"
    if thumb.exists():
        return thumb
    from PIL import Image, ImageDraw, ImageFont
    title = (ep_dir / "script.md").read_text().splitlines()[0].lstrip("# ").split("—", 1)[-1].strip()
    img = Image.new("RGB", (1280, 720), (24, 20, 16))
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype("DejaVuSans-Bold.ttf", 78)
    except OSError:
        f = ImageFont.load_default()
    words, lines, cur = title.split(), [], ""
    for w in words:
        if d.textlength(f"{cur} {w}".strip(), font=f) > 1100:
            lines.append(cur); cur = w
        else:
            cur = f"{cur} {w}".strip()
    lines.append(cur)
    y = 360 - 50 * len(lines)
    for ln in lines:
        d.text((90, y), ln, font=f, fill=(240, 200, 90))
        y += 105
    img.save(ep_dir / "thumbnail_auto.png")
    return ep_dir / "thumbnail_auto.png"


def run(cmd):
    subprocess.run([sys.executable, *cmd], cwd=ROOT, check=True)


def process(name, conf, when, dry):
    ep = ROOT / "episodes" / name
    run(["tools/make_video.py", str(ep), "--voice", conf["voice"], "--tts", conf["tts"]])
    run(["tools/build_meta.py", str(ep)])
    thumb = thumbnail(ep)
    if dry:
        return None
    sys.path.insert(0, str(ROOT / "tools"))
    import upload
    return upload.upload(ep, ep / "out" / "video.mp4", thumb, when.strftime("%Y-%m-%dT%H:%M:%SZ"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["plan", "run"])
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--ep")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-gate", action="store_true")
    a = ap.parse_args()
    conf = {**DEFAULTS, **load(CONF, {})}
    state = load(STATE, {})
    eps = episodes(conf)
    if a.cmd == "plan":
        for i, n in enumerate(eps):
            s = state.get(n, {})
            ok = "approved" if (ROOT / "episodes" / n / "APPROVED").exists() else "needs APPROVED"
            print(f"{slot(conf, i):%Y-%m-%d %H:%MZ}  {n:32} {s.get('url', ok)}")
        return
    todo = [n for n in eps if "url" not in state.get(n, {})]
    if a.ep:
        todo = [a.ep]
    done = 0
    for n in todo:
        if done >= a.count:
            break
        if not a.no_gate and not (ROOT / "episodes" / n / "APPROVED").exists():
            print(f"skip {n}: no APPROVED file (fact-check not signed off)")
            continue
        when = slot(conf, eps.index(n))
        if when <= datetime.now(timezone.utc) + timedelta(minutes=20):
            when = datetime.now(timezone.utc) + timedelta(hours=1)
        try:
            vid = process(n, conf, when, a.dry_run)
        except Exception as e:
            print(f"FAILED {n}: {e}", file=sys.stderr)
            state[n] = {"error": str(e)}
            STATE.parent.mkdir(exist_ok=True)
            STATE.write_text(json.dumps(state, indent=2))
            continue
        if vid:
            state[n] = {"url": f"https://youtu.be/{vid}", "publish_at": when.isoformat()}
            STATE.parent.mkdir(exist_ok=True)
            STATE.write_text(json.dumps(state, indent=2))
            print(f"{n}: scheduled {when:%Y-%m-%d %H:%MZ} -> {state[n]['url']}")
        done += 1


if __name__ == "__main__":
    main()
