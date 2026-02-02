import os
import requests
import asyncio
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import subprocess
import edge_tts
import math

# ---------------- CONFIG ----------------
CHANNEL_NAME = "Sanatan Gyan Dhara"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "audio/tanpura.mp3"  # your tanpura.mp3
SCRIPT_FILE = "script.txt"
IMAGE_DISPLAY_TIME = 12  # seconds per image approx
FRONT_COVER = f"{IMAGE_DIR}/front_cover.jpg"

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
async def generate_audio(text, out_path):
    communicate = edge_tts.Communicate(text=text, voice="hi-IN-MadhurNeural")
    await communicate.save(out_path)

def generate_narration(text, out_path):
    asyncio.run(generate_audio(text, out_path))
    return out_path

# ---------------- TANPURA CHECK ----------------
def check_tanpura():
    if not os.path.exists(TANPURA_FILE):
        run([
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", "sine=frequency=110:duration=180",
            "-af", "volume=0.18",
            TANPURA_FILE
        ])

# ---------------- PIXABAY IMAGE FETCH ----------------
PIXABAY_KEY = os.getenv("PIXABAY_API_KEY")
PIXABAY_URL = "https://pixabay.com/api/"

def fetch_pixabay_images(query, count):
    print(f"🌐 Fetching {count} images for '{query}' from Pixabay...")
    images = []
    page = 1
    while len(images) < count:
        params = {
            "key": PIXABAY_KEY,
            "q": query,
            "image_type": "photo",
            "orientation": "horizontal",
            "safesearch": "true",
            "per_page": min(50, count),
            "page": page
        }
        try:
            res = requests.get(PIXABAY_URL, params=params, timeout=15).json()
            hits = res.get("hits", [])
            if not hits:
                break
            for hit in hits:
                url = hit["largeImageURL"]
                path = f"{IMAGE_DIR}/{len(images):03d}.jpg"
                try:
                    r = requests.get(url, timeout=15)
                    if r.status_code == 200:
                        with open(path, "wb") as f:
                            f.write(r.content)
                        images.append(path)
                        if len(images) >= count:
                            break
                except:
                    placeholder(path)
                    images.append(path)
            page += 1
        except Exception as e:
            print("⚠ Failed to fetch images:", e)
            break
    while len(images) < count:
        path = f"{IMAGE_DIR}/{len(images):03d}.jpg"
        placeholder(path, text="Vishnu")
        images.append(path)
    return images

# ---------------- VIDEO BLOCKS ----------------
def make_video_block(image_file, audio_file, index, duration):
    out = f"{VIDEO_DIR}/{index:03d}.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-t", str(duration),
        "-i", image_file,
        "-i", audio_file,
        "-i", TANPURA_FILE,
        "-filter_complex",
        "[2:a]volume=0.2[a2];[1:a][a2]amix=inputs=2:duration=first[a];"
        "[0:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720[v]",
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
    print("🚀 Starting Sanatan Gyan Dhara bot")

    # ---------------- TANPURA ----------------
    check_tanpura()

    # ---------------- INTRO ----------------
    intro_text = f"नमस्कार। स्वागत है आप सभी का {CHANNEL_NAME} श्रृंखला में। आज हम आपके लिए Vishnu Purana का पहला एपिसोड लाए हैं।"
    intro_audio = "audio/000_intro.mp3"
    generate_narration(intro_text, intro_audio)
    intro_img = f"{IMAGE_DIR}/intro.jpg"
    placeholder(intro_img, text=intro_text)

    # ---------------- NARRATION SCRIPT ----------------
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        script_text = f.read()
    narration_file = "audio/narration.mp3"
    generate_narration(script_text, narration_file)

    # ---------------- OUTRO ----------------
    outro_text = f"🙏 अगर आपको यह वीडियो पसंद आया हो, तो कृपया लाइक, शेयर और सब्सक्राइब जरूर करें। हर दिन एक नया एपिसोड आएगा।"
    outro_audio = "audio/999_outro.mp3"
    generate_narration(outro_text, outro_audio)
    outro_img = f"{IMAGE_DIR}/outro.jpg"
    placeholder(outro_img, text=outro_text)

    # ---------------- IMAGE COUNT ----------------
    # get narration duration using ffprobe
    result = subprocess.run(
        ["ffprobe", "-i", narration_file, "-show_entries", "format=duration", "-v", "quiet", "-of", "csv=p=0"],
        capture_output=True, text=True
    )
    duration = float(result.stdout.strip())
    num_images = max(5, math.ceil(duration / 12))
    print(f"ℹ Narration duration: {duration:.2f}s, using {num_images} images (~{duration/num_images:.2f}s per image)")

    # ---------------- FETCH IMAGES ----------------
    front_image = fetch_pixabay_images("lord krishna", 1)
    other_images = fetch_pixabay_images("lord vishnu", num_images - 1)
    middle_images = front_image + other_images

    # ---------------- VIDEO BLOCKS ----------------
    print("🎞 Creating video blocks...")
    clips = []

    # intro
    clips.append(make_video_block(intro_img, intro_audio, 0, 8))

    # main images
    img_duration = duration / len(middle_images)
    for i, img in enumerate(middle_images, start=1):
        clips.append(make_video_block(img, narration_file, i, img_duration))

    # outro
    clips.append(make_video_block(outro_img, outro_audio, len(middle_images)+1, 8))

    # ---------------- CONCATENATE ----------------
    print("🔗 Concatenating all blocks...")
    concat_videos(clips, FINAL_VIDEO)
    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()