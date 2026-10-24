"""Install a weekly job that runs the pipeline (builds + schedules the next episodes on YouTube).

    python tools/install_scheduler.py            # weekly, Sunday 09:00 local, 2 episodes per run
    python tools/install_scheduler.py --count 4 --day SUN --time 09:00
    python tools/install_scheduler.py --remove

Linux/macOS: adds a crontab line. Windows: creates a Task Scheduler task. Logs go to schedule/run.log.
The computer must be on at that time. Run `python tools/upload.py` once by hand first so
token.json exists (the first sign-in needs a browser).
"""
import argparse
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAG = "# history-of-kings"
DAYS = {"SUN": 0, "MON": 1, "TUE": 2, "WED": 3, "THU": 4, "FRI": 5, "SAT": 6}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=2)
    ap.add_argument("--day", default="SUN", choices=DAYS)
    ap.add_argument("--time", default="09:00")
    ap.add_argument("--remove", action="store_true")
    a = ap.parse_args()
    hh, mm = a.time.split(":")
    py, script, log = sys.executable, ROOT / "tools" / "pipeline.py", ROOT / "schedule" / "run.log"
    if platform.system() == "Windows":
        if a.remove:
            subprocess.run(["schtasks", "/Delete", "/TN", "HistoryOfKings", "/F"])
        else:
            cmd = f'cmd /c "cd /d {ROOT} && {py} {script} run --count {a.count} >> {log} 2>&1"'
            subprocess.run(["schtasks", "/Create", "/TN", "HistoryOfKings", "/SC", "WEEKLY", "/D", a.day,
                            "/ST", a.time, "/TR", cmd, "/F"], check=True)
        return
    cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
    lines = [l for l in cur.splitlines() if TAG not in l]
    if not a.remove:
        lines.append(f"{int(mm)} {int(hh)} * * {DAYS[a.day]} cd {ROOT} && {py} {script} run --count {a.count} >> {log} 2>&1 {TAG}")
    subprocess.run(["crontab", "-"], input="\n".join(lines) + "\n", text=True, check=True)
    print("removed" if a.remove else "installed:\n" + lines[-1])


if __name__ == "__main__":
    main()
