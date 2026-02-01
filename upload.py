import os
import subprocess
import asyncio
import edge_tts
import requests
from PIL import Image, ImageDraw, ImageFont

# ================= CONFIG =================
CHANNEL_NAME = "Sanatan Gyan Dhara"
FINAL_VIDEO = "final_video.mp4"

IMAGE_DIR = "images"
AUDIO_DIR = "audio"
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

TANPURA = "audio/tanpura.mp3"
NARRATION = "audio/narration.mp3"

# Vishnu HD wallpaper (direct image – stable)
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

# ================= IMAGE =================
def download_images():
    paths = []
    for i, url in enumerate(IMAGE_URLS):
        path = f"{IMAGE_DIR}/{i}.jpg"
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                with open(path, "wb") as f:
                    f.write(r.content)
            else:
                raise Exception()
        except:
            img = Image.new("RGB", (1280, 720), (10, 5, 0))
            d = ImageDraw.Draw(img)
            d.text((400, 330), "ॐ नमो नारायणाय", fill=(255, 215, 0))
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

# ================= VIDEO =================
def create_video(images):
    inputs = []
    for img in images:
        inputs += ["-loop", "1", "-i", img]

    filter_complex = ""
    for i in range(len(images)):
        filter_complex += f"[{i}:v]scale=1280:720,setsar=1[v{i}];"

    filter_complex += "".join(
        f"[v{i}]" for i in range(len(images))
    ) + f"concat=n={len(images)}:v=1:a=0[v]"

    run([
        "ffmpeg", "-y",
        *inputs,
        "-i", NARRATION,
        "-i", TANPURA,
        "-filter_complex",
        filter_complex + ";[1:a][2:a]amix=inputs=2:duration=first[a]",
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-shortest",
        FINAL_VIDEO
    ])

# ================= MAIN =================
def main():
    print("🚀 Starting Sanatan Gyan Dhara bot")

    images = download_images()
    asyncio.run(generate_narration())
    create_video(images)

    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()