import os
import requests
import asyncio
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import subprocess
import edge_tts
import random
import time

# ---------------- CONFIG ----------------
CHANNEL_NAME = "Sanatan Gyan Dhara"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "audio/tanpura.mp3"  # light tanpura audio (create if not exists)
FRONT_COVER = f"{IMAGE_DIR}/front_cover.jpg"
BLOCKS = 5  # number of video blocks

# ---------------- CREATE FOLDERS ----------------
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs("audio", exist_ok=True)

# ---------------- UTILS ----------------
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

def placeholder(path, text="ॐ नमो नारायणाय"):
    img = Image.new("RGB", (1280, 720), (10, 5, 0))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except:
        font = None
    d.text((60, 330), text, fill=(255, 215, 0), font=font)
    img.save(path)

# ---------------- AUDIO GENERATION ----------------
async def generate_audio(text, index):
    out = f"{AUDIO_DIR}/{index:03d}.mp3"
    communicate = edge_tts.Communicate(text=text, voice="hi-IN-MadhurNeural")
    await communicate.save(out)

def generate_audio_blocks(blocks):
    async def runner():
        for i, text in enumerate(blocks):
            if text.strip():
                await generate_audio(text, i)
    asyncio.run(runner())

# ---------------- TANPURA GENERATION ----------------
def generate_tanpura(duration=180):
    if not os.path.exists(TANPURA_FILE):
        # simple sine wave as light tanpura
        run([
            "ffmpeg", "-y", "-f", "lavfi",
            f"-i", f"sine=frequency=110:duration={duration}",
            "-af", "volume=0.18",
            TANPURA_FILE
        ])

# ---------------- IMAGE FETCH ----------------
def fetch_bhagwanpuja_images(query, count):
    """
    Scrapes devotional wallpapers from Bhagwan Puja
    Returns list of local image paths
    """
    base_url = "https://www.bhagwanpuja.com/wallpapers/"
    try:
        res = requests.get(base_url, timeout=15)
        soup = BeautifulSoup(res.text, "lxml")
        imgs = [img["src"] for img in soup.find_all("img") if query.lower() in img.get("alt", "").lower()]
        if not imgs:
            print(f"❌ No {query} images found, using placeholders")
            imgs = []
        # download images
        paths = []
        for i, url in enumerate(imgs[:count]):
            path = f"{IMAGE_DIR}/{i:03d}.jpg"
            try:
                r = requests.get(url, timeout=15)
                if r.status_code == 200:
                    with open(path, "wb") as f:
                        f.write(r.content)
                    paths.append(path)
                else:
                    placeholder(path)
                    paths.append(path)
            except:
                placeholder(path)
                paths.append(path)
        return paths
    except Exception as e:
        print("⚠ Failed to fetch images:", e)
        # create placeholders if fetching fails
        paths = []
        for i in range(count):
            path = f"{IMAGE_DIR}/{i:03d}.jpg"
            placeholder(path, text="Vishnu")
            paths.append(path)
        return paths

# ---------------- VIDEO CREATION ----------------
def make_video_block(image_file, audio_file, index):
    out = f"{VIDEO_DIR}/{index:03d}.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_file,
        "-i", audio_file,
        "-i", TANPURA_FILE,
        "-filter_complex",
        "[2:a]volume=0.2[a2];[1:a][a2]amix=inputs=2:duration=first[a];"
        "[0:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720,zoompan=z='min(zoom+0.0005,1.06)':d=150:fps=25[v]",
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-shortest",
        out
    ]
    run(cmd)
    return out

def concat_videos(clips, output_file):
    with open("list.txt", "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy", output_file])

# ---------------- MAIN ----------------
def main():
    # ---------------- INTRO & OUTRO ----------------
    intro_text = f"नमस्कार। स्वागत है आप सभी का {CHANNEL_NAME} श्रृंखला में। आज हम आपके लिए Vishnu Purana का पहला एपिसोड लाए हैं।"
    outro_text = "🙏 अगर आपको यह वीडियो पसंद आया हो, तो कृपया लाइक, शेयर और सब्सक्राइब जरूर करें। हर दिन एक नया एपिसोड आएगा।"

    # ---------------- IMAGES ----------------
    images = []

    # 1️⃣ Front cover
    if os.path.exists(FRONT_COVER):
        images.append(FRONT_COVER)
        print("✅ Using existing front cover image")
    else:
        print("⚠ Front cover not found, fetching Vishnu image instead")
        front_image = fetch_bhagwanpuja_images("vishnu", 1)
        if front_image:
            images.append(front_image[0])
        else:
            placeholder_path = f"{IMAGE_DIR}/000.jpg"
            placeholder(placeholder_path, text="Vishnu")
            images.append(placeholder_path)

    # 2️⃣ Other devotional images
    other_images = fetch_bhagwanpuja_images("vishnu", BLOCKS-1)
    images.extend(other_images)

    if not images:
        raise Exception(f"No images found in {IMAGE_DIR}/")

    # ---------------- AUDIO ----------------
    print("🔊 Generating narration...")
    blocks_text = [intro_text] + ["ॐ नमो नारायणाय"]*(len(images)-2) + [outro_text]
    generate_audio_blocks(blocks_text)

    # ---------------- TANPURA ----------------
    generate_tanpura(duration=180)

    # ---------------- VIDEO BLOCKS ----------------
    print("🎞 Creating devotional video blocks...")
    video_clips = []
    for i, img in enumerate(images):
        audio_file = f"{AUDIO_DIR}/{i:03d}.mp3"
        clip = make_video_block(img, audio_file, i)
        video_clips.append(clip)

    # ---------------- CONCATENATE ----------------
    print("🔗 Concatenating video blocks...")
    concat_videos(video_clips, FINAL_VIDEO)
    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()