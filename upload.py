import os
import requests
import subprocess
from pathlib import Path
import edge_tts
import asyncio

# ===================== CONFIG =====================
IMAGE_DIR = "images"
os.makedirs(IMAGE_DIR, exist_ok=True)

SCRIPT_FILE = "script.txt"
OUTPUT_VIDEO = "final_video.mp4"
BACKGROUND_MUSIC = "tanpura.mp3"

START_IMAGE = "image1.png"       # Your front cover
END_IMAGE = "end.png"            # Krishna/Vishnu for end
PIXABAY_KEY = os.environ.get("PIXABAY_API_KEY")
PIXABAY_API = "https://pixabay.com/api/"

# ===================== UTILS =====================
def log(msg):
    print(f"▶ {msg}")

def fetch_pixabay_images(query, count=5):
    log(f"Fetching {count} images for '{query}' from Pixabay...")
    urls = []
    try:
        res = requests.get(
            PIXABAY_API,
            params={
                "key": PIXABAY_KEY,
                "q": query,
                "image_type": "photo",
                "per_page": count
            },
            timeout=15
        ).json()
        urls = [hit['largeImageURL'] for hit in res.get('hits', [])]
    except Exception as e:
        log(f"Pixabay fetch failed: {e}")

    paths = []
    for i, url in enumerate(urls):
        try:
            img_res = requests.get(url, timeout=15)
            path = f"{IMAGE_DIR}/{i:03d}.jpg"
            with open(path, "wb") as f:
                f.write(img_res.content)
            paths.append(path)
            log(f"✅ Image saved: {path}")
        except Exception as e:
            log(f"❌ Failed to download {url}: {e}")
    return paths

async def text_to_speech(text, out_file):
    communicate = edge_tts.Communicate(text, "hi-IN-SwaraNeural")
    await communicate.save(out_file)
    log(f"✅ TTS saved: {out_file}")

def make_video_block(image_path, duration, out_file):
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-t", str(duration),
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:black",
        out_file
    ]
    subprocess.run(cmd, check=True)
    log(f"✅ Video block created: {out_file}")

# ===================== MAIN =====================
async def main():
    log("🚀 Starting Sanatan Gyan Dhara Bot")

    # 1️⃣ Read script
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        script_lines = [line.strip() for line in f if line.strip()]

    # 2️⃣ Generate TTS
    os.makedirs("tts", exist_ok=True)
    tts_files = []

    # Start narration
    start_text = "स्नातक ज्ञान धारा में आपका स्वागत है। आइए भगवान विष्णु और कृष्ण की कथा सुनते हैं।"
    start_tts = "tts/start.mp3"
    await text_to_speech(start_text, start_tts)
    tts_files.append(start_tts)

    # Main narration
    for idx, line in enumerate(script_lines):
        out_file = f"tts/narration_{idx:03d}.mp3"
        await text_to_speech(line, out_file)
        tts_files.append(out_file)

    # End narration
    end_text = "धन्यवाद! आप देख रहे थे सनातन ज्ञान धारा। जय श्री कृष्ण!"
    end_tts = "tts/end.mp3"
    await text_to_speech(end_text, end_tts)
    tts_files.append(end_tts)

    # 3️⃣ Combine audio into one file
    with open("audio_list.txt", "w", encoding="utf-8") as f:
        for file in tts_files:
            f.write(f"file '{file}'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "audio_list.txt", "-c", "copy", "final_audio.mp3"], check=True)
    log("✅ Combined final audio: final_audio.mp3")

    # 4️⃣ Fetch main images from Pixabay
    images = fetch_pixabay_images("lord krishna vishnu", count=10)
    if not images:
        log("❌ No images fetched. Exiting.")
        return

    # Insert start and end images
    if Path(START_IMAGE).exists():
        images = [START_IMAGE] + images
    else:
        log(f"❌ START_IMAGE not found: {START_IMAGE}")

    if Path(END_IMAGE).exists():
        images.append(END_IMAGE)
    else:
        log(f"❌ END_IMAGE not found: {END_IMAGE}")

    # 5️⃣ Make video clips for each image
    os.makedirs("clips", exist_ok=True)
    total_audio_duration = float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", "final_audio.mp3"]
    ).strip())
    duration_per_image = max(total_audio_duration / len(images), 3)

    clip_files = []
    for idx, img in enumerate(images):
        clip_file = f"clips/clip_{idx:03d}.mp4"
        make_video_block(img, duration_per_image, clip_file)
        clip_files.append(clip_file)

    # 6️⃣ Combine video clips with audio
    with open("clips_list.txt", "w", encoding="utf-8") as f:
        for clip in clip_files:
            f.write(f"file '{clip}'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "clips_list.txt",
                    "-i", "final_audio.mp3", "-c:v", "libx264", "-c:a", "aac", "-strict", "experimental", OUTPUT_VIDEO], check=True)
    log(f"✅ Final video created: {OUTPUT_VIDEO}")

if __name__ == "__main__":
    asyncio.run(main())