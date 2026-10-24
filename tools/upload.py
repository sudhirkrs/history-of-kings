"""Upload a video + thumbnail to YouTube using metadata.json.

Setup: enable YouTube Data API v3 in Google Cloud, create an OAuth "Desktop app"
client, save it as client_secret.json (never commit it), then:
    pip install google-api-python-client google-auth-oauthlib
    python tools/upload.py episodes/ep01-ashoka video.mp4 thumbnail.jpg [publish_at_ISO8601]

The first run opens a browser to sign in; the refresh token is cached in token.json
(never commit it), so later runs, including scheduled ones, need no browser.
Uploads as private (or scheduled if publish_at is given, e.g. 2026-11-01T13:00:00Z).
Unverified API projects force uploads private; request an API audit to lift that.
Scopes: youtube.upload (videos, thumbnails) + youtube.force-ssl (playlists, captions, comments).
"""
import json
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.force-ssl"]
ROOT = Path(__file__).resolve().parent.parent
TOKEN = ROOT / "token.json"
SECRET = ROOT / "client_secret.json"


def credentials():
    creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES) if TOKEN.exists() else None
    if creds and not creds.has_scopes(SCOPES):
        creds = None  # token from an older version: sign in again to grant the new scopes
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        creds = InstalledAppFlow.from_client_secrets_file(str(SECRET), SCOPES).run_local_server(port=0)
    TOKEN.write_text(creds.to_json())
    return creds


def service():
    return build("youtube", "v3", credentials=credentials())


def upload_video(meta, video, thumb=None, publish_at=None, privacy=None, synthetic=True, yt=None):
    """Upload one video from a metadata dict and return the new video id."""
    yt = yt or service()
    status = {
        "privacyStatus": "private" if publish_at else (privacy or meta.get("privacyStatus", "private")),
        "selfDeclaredMadeForKids": meta.get("selfDeclaredMadeForKids", False),
    }
    if publish_at:
        status["publishAt"] = publish_at
    body = {
        "snippet": {
            "title": meta["title"],
            "description": meta["description"],
            "tags": meta.get("tags", []),
            "categoryId": meta.get("categoryId", "27"),
        },
        "status": status,
    }

    def insert(b):
        req = yt.videos().insert(part="snippet,status", body=b,
                                 media_body=MediaFileUpload(str(video), chunksize=-1, resumable=True))
        resp = None
        while resp is None:
            _, resp = req.next_chunk()
        return resp["id"]

    if synthetic:  # AI-voice disclosure; if the API rejects the field, retry without it
        try:
            vid = insert({**body, "status": {**status, "containsSyntheticMedia": True}})
        except HttpError as e:
            if e.resp.status != 400:
                raise
            print("note: containsSyntheticMedia not accepted; set 'Altered content' = Yes in Studio")
            vid = insert(body)
    else:
        vid = insert(body)
    if thumb and Path(thumb).exists():
        try:
            yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(thumb))).execute()
        except HttpError as e:
            print(f"warning: thumbnail not set ({e.resp.status}); verify your phone number in Studio")
    return vid


def upload(episode_dir, video, thumb, publish_at=None, privacy=None):
    """Upload an episode (reads its metadata.json) and return the video id."""
    meta = json.loads((Path(episode_dir) / "metadata.json").read_text())
    return upload_video(meta, video, thumb, publish_at, privacy)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        credentials()
        sys.exit(__doc__)
    print(f"Uploaded: https://youtu.be/{upload(*sys.argv[1:5])}")
