"""Upload a video + thumbnail to YouTube using metadata.json.

Setup: enable YouTube Data API v3 in Google Cloud, create an OAuth "Desktop app"
client, save it as client_secret.json (never commit it), then:
    pip install google-api-python-client google-auth-oauthlib
    python tools/upload.py episodes/ep01-ashoka video.mp4 thumbnail.png [publish_at_ISO8601]

Uploads as private (or scheduled if publish_at is given, e.g. 2026-11-01T13:00:00Z).
Unverified API projects force uploads private; request an API audit to lift that.
"""
import json
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main(episode_dir, video, thumb, publish_at=None):
    meta = json.loads((Path(episode_dir) / "metadata.json").read_text())
    creds = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES).run_local_server(port=0)
    yt = build("youtube", "v3", credentials=creds)
    status = {
        "privacyStatus": "private" if publish_at else meta["privacyStatus"],
        "selfDeclaredMadeForKids": meta["selfDeclaredMadeForKids"],
    }
    if publish_at:
        status["publishAt"] = publish_at
    body = {
        "snippet": {
            "title": meta["title"],
            "description": meta["description"],
            "tags": meta["tags"],
            "categoryId": meta["categoryId"],
        },
        "status": status,
    }
    req = yt.videos().insert(part="snippet,status", body=body,
                             media_body=MediaFileUpload(video, chunksize=-1, resumable=True))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    vid = resp["id"]
    yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(thumb)).execute()
    print(f"Uploaded: https://youtu.be/{vid}")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    main(*sys.argv[1:5])
