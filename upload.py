import os
import requests
from PIL import Image
from io import BytesIO
import subprocess
import asyncio
import edge_tts

# ================= CONFIG =================
IMAGE_DIR = "images"
os.makedirs(IMAGE_DIR, exist_ok=True)
SCRIPT_FILE = "script.txt"
OUTPUT_VIDEO = "final_video.mp4"
BACKGROUND_MUSIC = "tanpura.mp3"
FIRST_IMAGE = "image1.png"  # Your front cover (for start)
END_IMAGE = f"{IMAGE_DIR}/end_krishna.jpg"  # Krishna image for end
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY")
PIXABAY_API = "https://pixabay.com/api/"
# Hindi text for start and end narration
START_TEXT = "सनातन ज्ञान धारा में आपका स्वागत है।"
END_TEXT = "धन्यवाद। कृपया सब्सक्राइब करें। ॐ नमो नारायणाय।"
# ==========================================

# ================= HELPER =================
def run(cmd):
    subprocess.run(cmd, check=True)

def download_pixabay_image(query, out_path):
    try:
        params = {
            "key": PIXABAY_API_KEY,
            "q": query,
            "image_type": "photo",
            "per_page": 3
        }
        res = requests.get(PIXABAY_API, params=params, timeout=15).json()
        hits = res.get('hits', [])
        if not hits:
            print("No Pixabay images found for", query)
            return None
        url = hits[0]['largeImageURL']
        img_res = requests.get(url)
        with open(out_path, "wb") as f:
            f.write(img_res.content)
        return out_path
    except Exception as e:
        print("Pixabay download failed:", e)
        return None

async def tts_save(text, out_file):
    communicate = edge_tts.Communicate(text, "hi-IN-SwaraNeural")
    await communicate.save(out_file)

def make_video_block(img_path, duration, out_path):
    run([
        "ffmpeg", "-y", "-loop", "1", "-i", img_path,
        "-t", str(duration),
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:black",
        out_path
    ])

def fetch_pixabay_images(query, count=10):
    params = {
        "key": PIXABAY_API_KEY,
        "q": query,
        "image_type": "photo",
        "per_page": count
    }
    try:
        res = requests.get(PIXABAY_API, params=params, timeout=15).json()
        urls = [hit['largeImageURL'] for hit in res.get('hits', [])]
        paths = []
        for i, url in enumerate(urls):
            path = f"{IMAGE_DIR}/{i:03d}.jpg"
            img_res = requests.get(url)
            with open(path, "wb") as f:
                f.write(img_res.content)
            paths.append(path)
        return paths
    except Exception as e:
        print("Pixabay fetch failed:", e)
        return []

# ================= MAIN =================
async def main():
    # 1️⃣ Start block (FIRST_IMAGE with START_TEXT)
    start_clip = f"{IMAGE_DIR}/clip_start.mp4"
    make_video_block(FIRST_IMAGE, 5, start_clip)
    await tts_save(START_TEXT, "start.mp3")

    # 2️⃣ Fetch other images for middle narration
    middle_images = fetch_pixabay_images("lord vishnu krishna", 10)

    # 3️⃣ Script narration
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    os.makedirs("tts", exist_ok=True)
    audio_list = []
    for idx, line in enumerate(lines):
        out_file = f"tts/narration_{idx:03d}.mp3"
        await tts_save(line, out_file)
        audio_list.append(out_file)

    # Combine audio
    with open("audio_list.txt", "w", encoding="utf-8") as f:
        for a in audio_list:
            f.write(f"file '{a}'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "audio_list.txt", "-c", "copy", "narration.mp3"])
    final_audio = "narration.mp3"

    # Add background music if exists
    if os.path.exists(BACKGROUND_MUSIC):
        run([
            "ffmpeg", "-y", "-i", final_audio, "-i", BACKGROUND_MUSIC,
            "-filter_complex", "[1:a]volume=0.3[a1];[0:a][a1]amix=inputs=2:duration=longest",
            "final_audio.mp3"
        ])
        final_audio = "final_audio.mp3"

    # 4️⃣ Create video clips for middle images
    clip_files = []
    duration_per_image = max(3, float(final_audio) / len(middle_images))  # safe minimum 3s
    for i, img in enumerate(middle_images):
        clip_path = f"{IMAGE_DIR}/clip_{i:03d}.mp4"
        make_video_block(img, duration_per_image, clip_path)
        clip_files.append(clip_path)

    # 5️⃣ End block (Krishna image with END_TEXT)
    end_img_path = END_IMAGE
    if not os.path.exists(end_img_path):
        download_pixabay_image("lord krishna", end_img_path)
    end_clip = f"{IMAGE_DIR}/clip_end.mp4"
    make_video_block(end_img_path, 5, end_clip)
    await tts_save(END_TEXT, "end.mp3")
    run([
        "ffmpeg", "-y", "-i", final_audio, "-i", "end.mp3",
        "-filter_complex", "[0:a][1:a]concat=n=2:v=0:a=1[outa]", "-map", "[outa]", "final_audio_end.mp3"
    ])
    final_audio = "final_audio_end.mp3"
    clip_files.append(end_clip)

    # 6️⃣ Combine all clips
    with open("clip_list.txt", "w", encoding="utf-8") as f:
        for clip in [start_clip] + clip_files:
            f.write(f"file '{clip}'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "clip_list.txt", "-i", final_audio,
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", OUTPUT_VIDEO])

    print("✅ Video created:", OUTPUT_VIDEO)

# ================= RUN =================
if __name__ == "__main__":
    asyncio.run(main())