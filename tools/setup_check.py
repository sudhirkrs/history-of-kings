"""Check that this computer is ready to run the pipeline.

    python tools/setup_check.py            # checks everything, prints a fix for each problem
    python tools/setup_check.py --voice    # also makes a 3-second test clip with the neural voice (needs internet)
"""
import argparse
import importlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
bad = []


def ok(msg):
    print(f"  OK    {msg}")


def fail(msg, fix):
    print(f"  FIX   {msg}\n        -> {fix}")
    bad.append(msg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", action="store_true")
    a = ap.parse_args()

    print("Python")
    v = sys.version_info
    ok(f"Python {v.major}.{v.minor}") if v >= (3, 10) else fail(f"Python {v.major}.{v.minor} is too old", "install Python 3.10 or newer")

    print("Programs")
    for exe, fix in (("ffmpeg", "install ffmpeg (Windows: winget install ffmpeg; Mac: brew install ffmpeg; Linux: apt install ffmpeg)"),
                     ("ffprobe", "ffprobe comes with ffmpeg; reinstall ffmpeg"),
                     ("git", "install git from git-scm.com")):
        ok(exe) if shutil.which(exe) else fail(f"{exe} not found", fix)

    print("Python packages")
    for mod, pkg in (("edge_tts", "edge-tts"), ("PIL", "pillow"), ("googleapiclient", "google-api-python-client"),
                     ("google_auth_oauthlib", "google-auth-oauthlib"), ("requests", "requests")):
        try:
            importlib.import_module(mod)
            ok(pkg)
        except ImportError:
            fail(f"{pkg} missing", f"pip install {pkg}")

    print("Repo")
    ok("episodes found: " + str(len(list((ROOT / "episodes").glob("ep*"))))) if (ROOT / "episodes").exists() else fail("episodes folder missing", "run from a full clone of the repo")
    cfg = ROOT / "schedule" / "config.json"
    if cfg.exists():
        c = json.loads(cfg.read_text())
        ok(f"schedule/config.json (first publish {c.get('first_publish')}, tts={c.get('tts')})")
        if c.get("tts") != "edge":
            fail("config tts is not 'edge'", 'set "tts": "edge" in schedule/config.json for the real AI voice')
    else:
        fail("schedule/config.json missing", "git pull to get it")

    print("YouTube")
    cs, tok = ROOT / "client_secret.json", ROOT / "token.json"
    ok("client_secret.json") if cs.exists() else fail("client_secret.json missing", "create an OAuth Desktop client in Google Cloud and save it here (guide, Part A)")
    ok("token.json (signed in)") if tok.exists() else fail("token.json missing (not signed in yet)", "after client_secret.json exists, run: python tools/upload.py  (sign in once in the browser)")
    ig = (ROOT / ".gitignore").read_text() if (ROOT / ".gitignore").exists() else ""
    ok("secrets are git-ignored") if "client_secret.json" in ig and "token.json" in ig else fail("secrets not in .gitignore", "add client_secret.json and token.json to .gitignore")

    if tok.exists():
        try:
            sc = json.loads(tok.read_text()).get("scopes") or []
            ok("token has playlist/caption/comment access") if any("force-ssl" in x for x in sc) else fail(
                "token.json is from an older version (no playlist/comment scope)", "delete token.json and run: python tools/upload.py  (sign in again)")
        except ValueError:
            fail("token.json unreadable", "delete it and sign in again")
    print("Approvals")
    n = len(list((ROOT / "episodes").glob("ep*/APPROVED")))
    ok(f"{n} episode(s) approved") if n else print("  NOTE  no episode approved yet -> python tools/approve.py ep01")

    if a.voice:
        print("Voice test")
        try:
            import asyncio
            import edge_tts
            out = Path(tempfile.mkdtemp()) / "t.mp3"
            asyncio.run(edge_tts.Communicate("This is a test of the History of Kings narrator.", "en-IN-PrabhatNeural").save(str(out)))
            ok(f"neural voice works ({out.stat().st_size // 1024} KB clip)")
        except Exception as e:
            fail(f"voice test failed: {e}", "check your internet connection / firewall")

    print()
    print("Ready." if not bad else f"{len(bad)} thing(s) to fix (see FIX lines above).")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
