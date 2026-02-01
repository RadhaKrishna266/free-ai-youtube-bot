import os
import subprocess
import asyncio
import requests
import edge_tts
from PIL import Image, ImageDraw

# ================= CONFIG =================
CHANNEL_NAME = "Sanatan Gyan Dhara"
FINAL_VIDEO = "final_video.mp4"

IMAGE_DIR = "images"
AUDIO_DIR = "audio"
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

TANPURA = "audio/tanpura.mp3"
NARRATION = "audio/narration.mp3"
MIXED_AUDIO = "audio/mixed.mp3"
SLIDESHOW = "video.mp4"

# Stable Vishnu wallpapers (direct CDN)
IMAGE_URLS = [
    "https://wallpapercave.com/wp/wp6607474.jpg",
    "https://wallpapercave.com/wp/wp6607481.jpg",
    "https://wallpapercave.com/wp/wp6607487.jpg",
    "https://wallpapercave.com/wp/wp6607494.jpg",
]

SCRIPT = """
नमस्कार।
सनातन ज्ञान धारा में आप सभी का हार्दिक स्वागत है।

आज हम प्रारंभ कर रहे हैं विष्णु पुराण।
यह पुराण सृष्टि की उत्पत्ति, भगवान विष्णु की महिमा,
धर्म, कर्म और मोक्ष के रहस्यों को प्रकट करता है।

भगवान विष्णु इस ब्रह्मांड के पालनकर्ता हैं।
जब जब धर्म की हानि होती है,
तब तब वे अवतार लेकर सृष्टि की रक्षा करते हैं।

ॐ नमो नारायणाय।
"""

# ================= UTILS =================
def run(cmd):
    subprocess.run(cmd, check=True)

# ================= IMAGES =================
def download_images():
    paths = []
    for i, url in enumerate(IMAGE_URLS):
        path = f"{IMAGE_DIR}/{i}.jpg"
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            with open(path, "wb") as f:
                f.write(r.content)
        except:
            img = Image.new("RGB", (1280, 720), (10, 5, 0))
            d = ImageDraw.Draw(img)
            d.text((420, 340), "ॐ नमो नारायणाय", fill=(255, 215, 0))
            img.save(path)
        paths.append(path)
    return paths

# ================= AUDIO =================
async def generate_narration():
    communicate = edge_tts.Communicate(
        text=SCRIPT,
        voice="hi-IN-MadhurNeural"
    )
    await communicate.save(NARRATION)

def mix_audio():
    run([
        "ffmpeg", "-y",
        "-i", NARRATION,
        "-i", TANPURA,
        "-filter_complex", "amix=inputs=2:duration=first:weights=1 0.3",
        MIXED_AUDIO
    ])

# ================= VIDEO =================
def create_slideshow(images):
    with open("images.txt", "w") as f:
        for img in images:
            f.write(f"file '{img}'\n")
            f.write("duration 8\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "images.txt",
        "-vf", "scale=1280:720,format=yuv420p",
        "-r", "25",
        SLIDESHOW
    ])

def mux_final():
    run([
        "ffmpeg", "-y",
        "-i", SLIDESHOW,
        "-i", MIXED_AUDIO,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        FINAL_VIDEO
    ])

# ================= MAIN =================
def main():
    print("🚀 Starting Sanatan Gyan Dhara bot")

    images = download_images()
    asyncio.run(generate_narration())
    mix_audio()
    create_slideshow(images)
    mux_final()

    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()