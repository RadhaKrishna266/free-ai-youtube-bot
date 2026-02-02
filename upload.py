import os
import requests
from PIL import Image
from io import BytesIO
import asyncio
import edge_tts
import subprocess

# ---------------- CONFIG ----------------
IMAGE_DIR = "images"
os.makedirs(IMAGE_DIR, exist_ok=True)

SCRIPT_FILE = "script.txt"
OUTPUT_VIDEO = "final_video.mp4"
BACKGROUND_MUSIC = "tanpura.mp3"
FIRST_PAGE = "image.png"  # front cover
PIXABAY_KEY = os.getenv("PIXABAY_API_KEY")
PIXABAY_API = "https://pixabay.com/api/"

# video clip duration minimum
MIN_DURATION_PER_IMAGE = 3

# ---------------- UTILS ----------------
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

def ensure_jpg(path):
    try:
        im = Image.open(path).convert("RGB")
        im = im.resize((1280, 720))
        im.save(path, "JPEG")
    except Exception as e:
        print(f"❌ Failed to process {path}:", e)

# ---------------- PIXABAY IMAGE FETCH ----------------
def fetch_pixabay_images(query, count=10):
    urls = []
    try:
        params = {"key": PIXABAY_KEY, "q": query, "image_type": "photo", "per_page": count}
        res = requests.get(PIXABAY_API, params=params, timeout=15).json()
        hits = res.get("hits", [])
        for hit in hits:
            urls.append(hit.get("largeImageURL"))
    except Exception as e:
        print("⚠ Pixabay fetch failed:", e)
    paths = []
    for i, url in enumerate(urls[:count]):
        try:
            r = requests.get(url, timeout=15)
            path = f"{IMAGE_DIR}/{i:03d}.jpg"
            with open(path, "wb") as f:
                f.write(r.content)
            ensure_jpg(path)
            paths.append(path)
        except Exception as e:
            print(f"❌ Failed to download {url}: {e}")
    return paths

# ---------------- TTS ----------------
async def text_to_speech(text, out_file):
    communicate = edge_tts.Communicate(text, "hi-IN-MadhurNeural")
    await communicate.save(out_file)

# ---------------- AUDIO CONCAT ----------------
def concat_audios(audio_files, output_file):
    with open("audio_list.txt", "w") as f:
        for a in audio_files:
            f.write(f"file '{a}'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "audio_list.txt", "-c", "copy", output_file])
    run(["cp", output_file, "final_audio.mp3"])

# ---------------- VIDEO BLOCKS ----------------
def make_video_block(image_file, duration, output_file):
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_file,
        "-t", str(duration),
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:black",
        output_file
    ]
    run(cmd)

# ---------------- MAIN ----------------
async def main():
    print("🚀 Starting Sanatan Gyan Dhara bot")

    # 1️⃣ Fetch images
    images = fetch_pixabay_images("lord krishna vishnu", count=15)
    if not images:
        raise Exception("❌ No images fetched from Pixabay!")

    # Add front cover
    if os.path.exists(FIRST_PAGE):
        ensure_jpg(FIRST_PAGE)
        images = [FIRST_PAGE] + images

    # 2️⃣ Read script
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    # Add start & end text
    lines = ["नमस्कार। स्वागत है आप सभी का Sanatan Gyan Dhara श्रृंखला में।"] + lines + ["धन्यवाद! कृपया लाइक, शेयर और सब्सक्राइब करें।"]

    # 3️⃣ Generate narration
    os.makedirs("audio", exist_ok=True)
    audio_files = []
    print(f"🔊 Generating narration {len(lines)} lines...")
    for idx, line in enumerate(lines):
        out_file = f"audio/{idx:03d}.mp3"
        await text_to_speech(line, out_file)
        audio_files.append(out_file)
        print(f"🔊 Line {idx+1}/{len(lines)} done")

    # 4️⃣ Concatenate narration
    concat_audios(audio_files, "narration.mp3")

    # 5️⃣ Add background music if exists
    if os.path.exists(BACKGROUND_MUSIC):
        run([
            "ffmpeg", "-y",
            "-i", "narration.mp3",
            "-i", BACKGROUND_MUSIC,
            "-filter_complex", "[1:a]volume=0.2[a1];[0:a][a1]amix=inputs=2:duration=first[aout]",
            "-map", "[aout]",
            "final_audio.mp3"
        ])

    # 6️⃣ Create video blocks
    duration_per_image = max(len(lines)*2 / len(images), MIN_DURATION_PER_IMAGE)
    clip_files = []
    for idx, img in enumerate(images):
        clip_file = f"images/clip_{idx:03d}.mp4"
        make_video_block(img, duration_per_image, clip_file)
        clip_files.append(clip_file)

    # 7️⃣ Concatenate video blocks with audio
    with open("clips_list.txt", "w") as f:
        for c in clip_files:
            f.write(f"file '{c}'\n")
    run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "clips_list.txt",
        "-i", "final_audio.mp3",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        OUTPUT_VIDEO
    ])

    print("✅ FINAL VIDEO READY:", OUTPUT_VIDEO)

# ---------------- RUN ----------------
if __name__ == "__main__":
    asyncio.run(main())