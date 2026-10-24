"""After an upload: playlist, captions (.srt) and a first comment.

    python tools/youtube_extras.py ep01 VIDEO_ID

The API cannot pin a comment or add end screens/cards; do those in Studio (one click each)
or with the Claude in Chrome prompt (docs/11).
"""
import json
import sys
from pathlib import Path

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

sys.path.insert(0, str(Path(__file__).resolve().parent))
import upload  # noqa: E402

ROOT = upload.ROOT
PLAYLISTS = {  # episode number -> playlist
    "Kings of India": [1, 2, 3, 4, 5, 6, 7, 8, 33, 34],
    "Mongols & Central Asia": [9, 10, 11, 12, 13, 35],
    "Russia": [14, 15, 16, 21, 22, 23, 38],
    "Europe": [17, 18, 19, 20, 24, 25, 26, 27, 36, 37],
    "China": [28, 29, 30, 31, 32, 40],
    "Ottomans": [39],
}


def playlist_name(ep_name):
    n = int(ep_name[2:4])
    return next((k for k, v in PLAYLISTS.items() if n in v), "Kings of History")


def find_or_create_playlist(yt, name):
    page = None
    while True:
        r = yt.playlists().list(part="snippet", mine=True, maxResults=50, pageToken=page).execute()
        for p in r.get("items", []):
            if p["snippet"]["title"] == name:
                return p["id"]
        page = r.get("nextPageToken")
        if not page:
            break
    r = yt.playlists().insert(part="snippet,status", body={
        "snippet": {"title": name, "description": f"{name}: History of Kings"},
        "status": {"privacyStatus": "public"}}).execute()
    return r["id"]


def first_comment(ep):
    credits = ep / "credits.md"
    lines = ["Which king should I cover next? Tell me below."]
    if credits.exists():
        lines += ["", "Image credits (Wikimedia Commons):", credits.read_text().strip()[:3000]]
    lines += ["", "Narration is AI-generated."]
    return "\n".join(lines)[:9000]


def run(ep, vid, comment=True):
    yt = upload.service()
    steps = []
    try:
        pid = find_or_create_playlist(yt, playlist_name(ep.name))
        yt.playlistItems().insert(part="snippet", body={"snippet": {
            "playlistId": pid, "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute()
        steps.append("playlist ok")
    except HttpError as e:
        steps.append(f"playlist FAILED ({e.resp.status})")
    srt = ep / "out" / "captions.srt"
    if srt.exists():
        try:
            yt.captions().insert(part="snippet", body={"snippet": {
                "videoId": vid, "language": "en", "name": "English", "isDraft": False}},
                media_body=MediaFileUpload(str(srt))).execute()
            steps.append("captions ok")
        except HttpError as e:
            steps.append(f"captions FAILED ({e.resp.status})")
    if comment:
        try:
            yt.commentThreads().insert(part="snippet", body={"snippet": {
                "videoId": vid, "topLevelComment": {"snippet": {"textOriginal": first_comment(ep)}}}}).execute()
            steps.append("comment ok (pin it in Studio)")
        except HttpError as e:
            steps.append(f"comment FAILED ({e.resp.status})")
    return steps


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    eps = [e for e in (ROOT / "episodes").glob("ep*") if e.name.startswith(sys.argv[1])]
    if len(eps) != 1:
        sys.exit("episode not found")
    print("; ".join(run(eps[0], sys.argv[2])))
