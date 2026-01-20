import os
import json
import base64
import subprocess
import random
import textwrap
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from PIL import Image, ImageDraw, ImageFont

# ================= CONFIG =================
DURATION = 60  # seconds (safe for testing)
UPLOAD_TO_YOUTUBE = False  # 🔴 SET TRUE ONLY WHEN READY
OUTPUT_VIDEO = "final.mp4"
IMAGE_DIR = "images"
os.makedirs(IMAGE_DIR, exist_ok=True)

# ================= FACT ENGINE =================
FACTS = [
    "Octopuses have three hearts and blue blood.",
    "Bananas are berries, but strawberries are not.",
    "There are more possible games of chess than atoms in the universe.",
    "Humans glow faintly due to bioluminescence, but our eyes can't see it.",
    "Your brain rewires itself every time you learn something new.",
    "A day on Venus is longer than a year on Venus.",
    "Butterflies remember being caterpillars.",
    "The human body contains enough carbon to make 9,000 pencils."
]

def generate_fact():
    return random.choice(FACTS)

# ================= AUDIO =================
def create_audio():
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=440",
        "-t", str(DURATION),
        "-c:a", "aac",
        "-b:a", "128k",
        "voice.m4a"
    ], check=True)

# ================= AI FACE (NO FFMPEG BUG) =================
def create_face():
    img = Image.new("RGB", (1024, 1024), "#1f1f1f")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 72)
    except:
        font = ImageFont.load_default()

    draw.text((512, 420), "AI FACT FACE", fill="white", anchor="mm", font=font)
    draw.text((512, 520), "Talking AI", fill="#bbbbbb", anchor="mm", font=font)

    img.save(f"{IMAGE_DIR}/face.jpg")

# ================= SUBTITLES =================
def create_subtitles(text):
    wrapped = textwrap.fill(text, 35)
    with open("subs.txt", "w") as f:
        f.write(wrapped)

# ================= ANIMATED VIDEO =================
def create_video():
    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", f"{IMAGE_DIR}/face.jpg",
        "-i", "voice.m4a",
        "-vf",
        (
            "scale=1280:720,"
            "zoompan=z='min(zoom+0.0008,1.15)':d=125,"
            "drawtext=textfile=subs.txt:"
            "fontcolor=white:fontsize=36:"
            "x=(w-text_w)/2:y=h-120:"
            "box=1:boxcolor=black@0.5:boxborderw=10"
        ),
        "-t", str(DURATION),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        OUTPUT_VIDEO
    ], check=True)

# ================= YOUTUBE =================
def get_youtube():
    token = base64.b64decode(os.environ["YOUTUBE_TOKEN_BASE64"]).decode()
    creds = Credentials.from_authorized_user_info(
        json.loads(token),
        ["https://www.googleapis.com/auth/youtube.upload"]
    )
    return build("youtube", "v3", credentials=creds)

def upload_video(title, description):
    youtube = get_youtube()
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "categoryId": "27"
            },
            "status": {"privacyStatus": "public"}
        },
        media_body=MediaFileUpload(OUTPUT_VIDEO, resumable=True)
    )
    request.execute()

# ================= MAIN =================
def main():
    print("🚀 AI Talking Fact Video Generator")

    fact = generate_fact()
    print("🧠 FACT:", fact)

    create_audio()
    create_face()
    create_subtitles(fact)
    create_video()

    print(f"✅ VIDEO READY: {OUTPUT_VIDEO}")

    if UPLOAD_TO_YOUTUBE:
        upload_video(
            title="Unknown Fact That Will Blow Your Mind",
            description=fact
        )
        print("✅ Uploaded to YouTube")
    else:
        print("⬇️ Upload disabled — download video from workflow artifacts")

if __name__ == "__main__":
    main()
