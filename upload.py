import os
import subprocess
import json
import base64
import requests
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from TTS.api import TTS

# ================== CONFIG ==================
os.environ["COQUI_TOS_AGREED"] = "1"

SCRIPT_FILE = "script.txt"
VOICE_FILE = "narration.wav"
MIXED_AUDIO = "mixed_audio.wav"
FINAL_VIDEO = "final.mp4"

SPEAKER_WAV = "audio/speaker.wav"
TANPURA = "audio/tanpura.mp3"
BELL = "audio/temple_bell.mp3"

IMAGE_FILE = "images/000.jpg"
CHUNK_DIR = "chunks"

MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"
MAX_CHARS = 200

# ================== UTILS ==================
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

# ================== IMAGE ==================
def create_image():
    os.makedirs("images", exist_ok=True)
    if os.path.exists(IMAGE_FILE):
        return

    print("🖼 Downloading image")
    r = requests.get(
        "https://pixabay.com/api/",
        params={
            "key": os.environ["PIXABAY_API_KEY"],
            "q": "Kashi Vishwanath temple",
            "orientation": "horizontal",
            "per_page": 3
        }
    ).json()

    img = requests.get(r["hits"][0]["largeImageURL"]).content
    with open(IMAGE_FILE, "wb") as f:
        f.write(img)

# ================== TEXT ==================
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

# ================== AUDIO ==================
def create_audio():
    print("🎤 Creating Hindi narration")
    Path(CHUNK_DIR).mkdir(exist_ok=True)

    text = Path(SCRIPT_FILE).read_text(encoding="utf-8")
    chunks = split_text(text)

    tts = TTS(MODEL, gpu=False)
    wavs = []

    for i, c in enumerate(chunks):
        out = f"{CHUNK_DIR}/part_{i}.wav"
        tts.tts_to_file(
            text=c,
            speaker_wav=SPEAKER_WAV,
            language="hi",
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

# ================== MIX ==================
def mix_audio():
    d = duration(VOICE_FILE)

    run([
        "ffmpeg", "-y",
        "-i", VOICE_FILE,
        "-stream_loop", "-1", "-i", TANPURA,
        "-stream_loop", "-1", "-i", BELL,
        "-filter_complex",
        f"[1:a]volume=0.25,atrim=0:{d}[bg1];"
        f"[2:a]volume=0.12,atrim=0:{d}[bg2];"
        "[0:a][bg1][bg2]amix=inputs=3",
        "-t", str(d),
        MIXED_AUDIO
    ])
    return d

# ================== VIDEO ==================
def create_video(d):
    run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", IMAGE_FILE,
        "-i", MIXED_AUDIO,
        "-t", str(d),
        "-vf", "scale=1280:720,format=yuv420p",
        "-r", "25",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-c:a", "aac",
        FINAL_VIDEO
    ])

# ================== YOUTUBE ==================
def upload_youtube():
    token = base64.b64decode(os.environ["YOUTUBE_TOKEN_BASE64"]).decode()
    creds = Credentials.from_authorized_user_info(
        json.loads(token),
        ["https://www.googleapis.com/auth/youtube.upload"]
    )

    yt = build("youtube", "v3", credentials=creds)

    request = yt.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "काशी विश्वनाथ – शिव की नगरी",
                "description": "ॐ नमः शिवाय",
                "categoryId": "22"
            },
            "status": {"privacyStatus": "public"}
        },
        media_body=MediaFileUpload(FINAL_VIDEO)
    )

    request.execute()
    print("✅ Uploaded to YouTube")

# ================== MAIN ==================
def main():
    create_image()
    create_audio()
    d = mix_audio()
    create_video(d)
    upload_youtube()

if __name__ == "__main__":
    main()