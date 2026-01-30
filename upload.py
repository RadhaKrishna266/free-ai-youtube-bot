import os, json, base64, subprocess, requests
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from TTS.api import TTS

# ================= CONFIG =================
os.environ["COQUI_TOS_AGREED"] = "1"

SCRIPT_FILE = "script.txt"
VOICE_FILE = "narration.wav"
FINAL_VIDEO = "final.mp4"

IMAGE_DIR = "images"
CHUNK_DIR = "chunks"

MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"
MAX_CHARS = 180  # VERY SAFE = smooth voice

# ================= UTILS =================
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ================= IMAGE =================
def download_images():
    os.makedirs(IMAGE_DIR, exist_ok=True)

    if len(os.listdir(IMAGE_DIR)) >= 5:
        return

    print("🖼 Downloading divine images")

    r = requests.get(
        "https://pixabay.com/api/",
        params={
            "key": os.environ["PIXABAY_API_KEY"],
            "q": "Vishnu Narayan painting",
            "orientation": "horizontal",
            "per_page": 5
        }
    ).json()

    for i, hit in enumerate(r["hits"][:5]):
        img = requests.get(hit["largeImageURL"]).content
        with open(f"{IMAGE_DIR}/{i}.jpg", "wb") as f:
            f.write(img)

# ================= TEXT =================
def split_text(text):
    lines = text.splitlines()
    chunks, buf = [], ""

    for l in lines:
        if len(buf) + len(l) <= MAX_CHARS:
            buf += " " + l
        else:
            chunks.append(buf.strip())
            buf = l

    if buf.strip():
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
        out = f"{CHUNK_DIR}/{i}.wav"
        tts.tts_to_file(
            text=c,
            file_path=out,
            language="hi",
            speed=0.85  # 🔥 calm slow voice
        )
        wavs.append(out)

    with open("list.txt", "w") as f:
        for w in wavs:
            f.write(f"file '{w}'\n")

    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy", VOICE_FILE])

# ================= VIDEO =================
def create_video():
    images = sorted([f"{IMAGE_DIR}/{x}" for x in os.listdir(IMAGE_DIR)])

    with open("imgs.txt", "w") as f:
        for img in images:
            f.write(f"file '{img}'\n")
            f.write("duration 6\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "imgs.txt",
        "-i", VOICE_FILE,
        "-vf", "scale=1280:720,format=yuv420p",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        FINAL_VIDEO
    ])

# ================= YOUTUBE =================
def upload_youtube():
    print("📤 Uploading to YouTube")

    token = json.loads(base64.b64decode(os.environ["YOUTUBE_TOKEN_BASE64"]).decode())
    creds = Credentials.from_authorized_user_info(token)

    youtube = build("youtube", "v3", credentials=creds)

    youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "विष्णु पुराण अध्याय 1 | श्रीहरि नारायण की महिमा",
                "description": "शांत दिव्य कथा\nॐ नमो नारायणाय",
                "categoryId": "22"
            },
            "status": {"privacyStatus": "public"}
        },
        media_body=MediaFileUpload(FINAL_VIDEO, resumable=False)
    ).execute()

    print("✅ VIDEO LIVE")

# ================= MAIN =================
def main():
    download_images()
    create_audio()
    create_video()
    upload_youtube()

if __name__ == "__main__":
    main()