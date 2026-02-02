import os
import requests
from PIL import Image
from io import BytesIO
import subprocess
import asyncio
import edge_tts

# ===================== CONFIG =====================
IMAGE_DIR = "images"
os.makedirs(IMAGE_DIR, exist_ok=True)
SCRIPT_FILE = "script.txt"
OUTPUT_VIDEO = "final_video.mp4"
BACKGROUND_MUSIC = "tanpura.mp3"

START_IMAGE = "start.png"      # Starting welcome image
FRONT_COVER = "image.png"      # Front cover image
END_IMAGE = "end.png"          # Ending image

PIXABAY_API = "https://pixabay.com/api/"
PIXABAY_KEY = os.environ.get("PIXABAY_API_KEY")  # Pixabay free API key

# ===================== UTILS =====================
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

def fetch_pixabay_images(query, count=5):
    """Fetch images from Pixabay."""
    try:
        params = {
            "key": PIXABAY_KEY,
            "q": query,
            "image_type": "photo",
            "per_page": count
        }
        res = requests.get(PIXABAY_API, params=params, timeout=15).json()
        urls = [hit['largeImageURL'] for hit in res.get('hits', [])]
        paths = []
        for i, url in enumerate(urls):
            img_res = requests.get(url)
            path = f"{IMAGE_DIR}/{i:03d}.jpg"
            with open(path, "wb") as f:
                f.write(img_res.content)
            paths.append(path)
        return paths
    except Exception as e:
        print("Pixabay fetch failed:", e)
        return []

async def text_to_speech(text, out_file):
    """Generate TTS narration."""
    communicate = edge_tts.Communicate(text, "hi-IN-SwaraNeural")  # Hindi voice
    await communicate.save(out_file)

def make_video_block(image_path, duration, output_path):
    """Create a video clip for a single image."""
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", image_path,
        "-t", str(duration),
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:black",
        output_path
    ]
    run(cmd)

# ===================== MAIN =====================
async def main():
    print("🚀 Starting Sanatan Gyan Dhara Bot")

    # 1️⃣ Start page (Hindi narration)
    start_narration = "सनातन ज्ञान धारा में आपका स्वागत है। इस दिव्य ज्ञान के माध्यम से हम आज विष्णु पुराण का एक अध्याय समझेंगे।"
    os.makedirs("tts", exist_ok=True)
    start_audio = "tts/start.mp3"
    await text_to_speech(start_narration, start_audio)
    make_video_block(START_IMAGE, 5, f"{IMAGE_DIR}/clip_start.mp4")

    # 2️⃣ Front cover page (Hindi narration)
    front_narration = "ॐ नमो नारायणाय। विष्णु पुराण के इस अध्याय में हम भगवान विष्णु के चरित्र और दिव्य ज्ञान को समझेंगे।"
    front_audio = "tts/front.mp3"
    await text_to_speech(front_narration, front_audio)
    make_video_block(FRONT_COVER, 5, f"{IMAGE_DIR}/clip_front.mp4")

    # 3️⃣ Fetch main images from Pixabay
    images = fetch_pixabay_images("lord krishna vishnu", count=10)
    if not images:
        print("❌ No images fetched from Pixabay. Exiting.")
        return

    # 4️⃣ Main script narration
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    narration_files = []
    for idx, line in enumerate(lines):
        tts_file = f"tts/narration_{idx:03d}.mp3"
        print(f"🔊 Generating narration {idx+1}/{len(lines)}...")
        await text_to_speech(line, tts_file)
        narration_files.append(tts_file)

    # Combine narration into single audio
    with open("audio_list.txt", "w") as f:
        for file in narration_files:
            f.write(f"file '{os.path.abspath(file)}'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "audio_list.txt", "-c", "copy", "narration.mp3"])

    # 5️⃣ Background music
    final_audio = "final_audio.mp3"
    if os.path.exists(BACKGROUND_MUSIC):
        run([
            "ffmpeg", "-y", "-i", "narration.mp3", "-i", BACKGROUND_MUSIC,
            "-filter_complex", "[1:a]volume=0.3[a1];[0:a][a1]amix=inputs=2:duration=first",
            final_audio
        ])
    else:
        run(["cp", "narration.mp3", final_audio])

    # 6️⃣ Create video clips for main images
    clip_files = []
    # Add start and front cover
    clip_files.append(f"{IMAGE_DIR}/clip_start.mp4")
    clip_files.append(f"{IMAGE_DIR}/clip_front.mp4")

    duration_per_image = max(3, sum([AudioFileClip(f).duration for f in narration_files]) / len(images))
    for idx, img in enumerate(images):
        clip_file = f"{IMAGE_DIR}/clip_{idx:03d}.mp4"
        make_video_block(img, duration_per_image, clip_file)
        clip_files.append(clip_file)

    # 7️⃣ End page (Hindi narration)
    end_narration = "धन्यवाद। यदि आपको यह वीडियो पसंद आया हो, तो कृपया सब्सक्राइब करें और इस ज्ञान को अन्य भक्तों के साथ साझा करें। ॐ नमो नारायणाय।"
    end_audio = "tts/end.mp3"
    await text_to_speech(end_narration, end_audio)
    make_video_block(END_IMAGE, 5, f"{IMAGE_DIR}/clip_end.mp4")
    clip_files.append(f"{IMAGE_DIR}/clip_end.mp4")

    # 8️⃣ Concatenate all video clips
    with open("clip_list.txt", "w") as f:
        for clip in clip_files:
            f.write(f"file '{os.path.abspath(clip)}'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "clip_list.txt", "-i", final_audio,
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", OUTPUT_VIDEO])

    print(f"✅ Video created successfully: {OUTPUT_VIDEO}")

# ===================== RUN =====================
if __name__ == "__main__":
    asyncio.run(main())