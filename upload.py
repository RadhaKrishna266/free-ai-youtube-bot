import os
import json
import base64
import subprocess
import requests
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from TTS.api import TTS

# ================= CONFIG =================
os.environ["COQUI_TOS_AGREED"] = "1"

SCRIPT_FILE = "script.txt"
VOICE_FILE = "narration.wav"
MIXED_AUDIO = "mixed_audio.wav"
FINAL_VIDEO = "final.mp4"

TANPURA = "audio/tanpura.mp3"
BELL = "audio/temple_bell.mp3"

IMAGE_DIR = "images"
CHUNK_DIR = "chunks"

MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"
MAX_CHARS = 200
YOUTUBE_SCOPE = "https://www.googleapis.com/auth/youtube.upload"

# ================= UTILS =================
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

def duration(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path
    ])
    return float(out.strip())

# ================= IMAGES =================
def create_images():
    os.makedirs(IMAGE_DIR, exist_ok=True)
    if len(list(Path(IMAGE_DIR).glob("*.jpg"))) >= 5:
        return

    print("🖼 Downloading divine images")
    r = requests.get(
        "https://pixabay.com/api/",
        params={
            "key": os.environ["PIXABAY_API_KEY"],
            "q": "Vishnu Narayan temple painting",
            "orientation": "horizontal",
            "per_page": 10
        }
    ).json()

    for i, hit in enumerate(r["hits"][:5]):
        img = requests.get(hit["largeImageURL"]).content
        with open(f"{IMAGE_DIR}/{i:03}.jpg", "wb") as f:
            f.write(img)

# ================= TEXT =================
def split_text(text):
    text = text.replace("।", "।\n")
    parts = text.splitlines()

    chunks, buf = [], ""
    for p in parts:
        if len(buf) + len(p) <= MAX_CHARS:
            buf += " " + p
        else:
            chunks.append(buf.strip())
            buf = p
    if buf:
        chunks.append(buf.strip())
    return chunks

# ================= AUDIO =================
def create_audio():
    print("🎙 Creating calm divine narration")
    Path(CHUNK_DIR).mkdir(exist_ok=True)

    text = Path(SCRIPT_FILE).read_text(encoding="utf-8")
    chunks = split_text(text)

    tts = TTS(MODEL, gpu=False)
    wavs = []

    for i, c in enumerate(chunks):
        out = f"{CHUNK_DIR}/part_{i}.wav"
        tts.tts_to_file(
            text=c,
            language="hi",
            speaker="random",   # ✅ REQUIRED FIX
            file_path=out
        )
        wavs.append(out)

    with open("wav_list.txt", "w") as f:
        for w in wavs:
            f.write(f"file '{w}'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "wav_list.txt",
        "-c", "copy",
        VOICE_FILE
    ])

# ================= MIX =================
def mix_audio():
    d = duration(VOICE_FILE)
    run([
        "ffmpeg", "-y",
        "-i", VOICE_FILE,
        "-stream_loop", "-1", "-i", TANPURA,
        "-stream_loop", "-1", "-i", BELL,
        "-filter_complex",
        f"[1:a]volume=0.18,atrim=0:{d}[bg1];"
        f"[2:a]volume=0.08,atrim=0:{d}[bg2];"
        "[0:a][bg1][bg2]amix=inputs=3",
        "-t", str(d),
        MIXED_AUDIO
    ])
    return d

# ================= VIDEO =================
def create_video(d):
    images = sorted(Path(IMAGE_DIR).glob("*.jpg"))
    with open("images.txt", "w") as f:
        for img in images:
            f.write(f"file '{img}'\n")
            f.write(f"duration {d/len(images)}\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "images.txt",
        "-i", MIXED_AUDIO,
        "-vf", "scale=1280:720,format=yuv420p",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-c:a", "aac",
        "-shortest",
        FINAL_VIDEO
    ])

# ================= YOUTUBE =================
def upload_youtube():
    print("📤 Uploading to YouTube")

    token = json.loads(
        base64.b64decode(os.environ["YOUTUBE_TOKEN_BASE64"]).decode()
    )

    creds = Credentials(
        token=token["token"],
        refresh_token=token["refresh_token"],
        token_uri=token["token_uri"],
        client_id=token["client_id"],
        client_secret=token["client_secret"],
        scopes=[YOUTUBE_SCOPE]
    )

    if creds.expired:
        creds.refresh(Request())

    yt = build("youtube", "v3", credentials=creds)

    req = yt.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "विष्णु पुराण अध्याय 1 | सनातन ज्ञान",
                "description": (
                    "विष्णु पुराण का दिव्य अध्याय।\n\n"
                    "🙏 प्रतिदिन नया अध्याय\n"
                    "👍 Like | 🔔 Subscribe | 📿 Share\n"
                ),
                "categoryId": "22"
            },
            "status": {"privacyStatus": "public"}
        },
        media_body=MediaFileUpload(FINAL_VIDEO, resumable=True)
    )

    res = req.execute()
    print("✅ Uploaded:", res["id"])

# ================= MAIN =================
def main():
    create_images()
    create_audio()
    d = mix_audio()
    create_video(d)
    upload_youtube()

if __name__ == "__main__":
    main()