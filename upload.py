import os
import requests
import asyncio
from PIL import Image, ImageDraw, ImageFont
import edge_tts
import subprocess

# ================= CONFIG =================
IMAGE_DIR = "images"
TTS_DIR = "tts"
OUTPUT_VIDEO = "final_video.mp4"
BACKGROUND_MUSIC = "tanpura.mp3"
FIRST_PAGE = "image.png"
SCRIPT_FILE = "script.txt"
PIXABAY_KEY = os.environ.get("PIXABAY_API_KEY")
PIXABAY_API = "https://pixabay.com/api/"
IMAGE_COUNT = 10

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(TTS_DIR, exist_ok=True)

# ============== UTIL =================
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

def fetch_pixabay_images(query, count=10):
    params = {
        "key": PIXABAY_KEY,
        "q": query,
        "image_type": "photo",
        "per_page": count
    }
    try:
        res = requests.get(PIXABAY_API, params=params, timeout=15).json()
        urls = [hit['largeImageURL'] for hit in res.get('hits', [])]
        paths = []
        for i, url in enumerate(urls):
            img_res = requests.get(url, timeout=15)
            path = f"{IMAGE_DIR}/{i:03d}.jpg"
            with open(path, "wb") as f:
                f.write(img_res.content)
            paths.append(path)
        return paths
    except Exception as e:
        print("❌ Pixabay fetch failed:", e)
        return []

async def text_to_speech(text, out_file):
    communicate = edge_tts.Communicate(text, voice="hi-IN-MadhurNeural")
    await communicate.save(out_file)

# ============== MAIN =================
async def main():
    print("🚀 Starting video generation...")

    # 1️⃣ Fetch images
    print("🌐 Fetching Vishnu/Krishna images from Pixabay...")
    images = fetch_pixabay_images("lord krishna vishnu", IMAGE_COUNT)
    if os.path.exists(FIRST_PAGE):
        images = [FIRST_PAGE] + images
    if not images:
        print("❌ No images found. Exiting.")
        return

    # 2️⃣ Read script
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    # Add start & end text
    start_text = "नमस्कार। स्वागत है आप सभी का Sanatan Gyan Dhara श्रृंखला में। आज हम Vishnu Purana का पहला एपिसोड लाए हैं।"
    end_text = "🙏 अगर आपको यह वीडियो पसंद आया हो, तो कृपया लाइक, शेयर और सब्सक्राइब जरूर करें। यह केवल एक वीडियो नहीं, बल्कि आध्यात्मिक यात्रा है।"
    lines = [start_text] + lines + [end_text]

    # 3️⃣ Generate TTS audio files
    audio_files = []
    for idx, line in enumerate(lines):
        tts_path = f"{TTS_DIR}/tts_{idx:03d}.mp3"
        print(f"🔊 Generating narration {idx+1}/{len(lines)}...")
        await text_to_speech(line, tts_path)
        audio_files.append(tts_path)

    # 4️⃣ Concatenate narration audio
    with open("audio_list.txt", "w") as f:
        for af in audio_files:
            f.write(f"file '{af}'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "audio_list.txt", "-c", "copy", "narration.mp3"])

    # 5️⃣ Add tanpura music if exists
    if os.path.exists(BACKGROUND_MUSIC):
        run([
            "ffmpeg", "-y", "-i", "narration.mp3", "-i", BACKGROUND_MUSIC,
            "-filter_complex", "[1:a]volume=0.2[a1];[0:a][a1]amix=inputs=2:duration=first[aout]",
            "-map", "[aout]", "final_audio.mp3"
        ])
    else:
        run(["cp", "narration.mp3", "final_audio.mp3"])

    # 6️⃣ Create video from images
    for idx, img in enumerate(images):
        duration = 3  # minimum duration per image
        run([
            "ffmpeg", "-y", "-loop", "1", "-i", img,
            "-t", str(duration), "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:black",
            f"{IMAGE_DIR}/clip_{idx:03d}.mp4"
        ])

    # 7️⃣ Concatenate video clips
    with open("video_list.txt", "w") as f:
        for idx in range(len(images)):
            f.write(f"file '{IMAGE_DIR}/clip_{idx:03d}.mp4'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "video_list.txt", "-c", "copy", "video_temp.mp4"])

    # 8️⃣ Merge video + audio
    run([
        "ffmpeg", "-y", "-i", "video_temp.mp4", "-i", "final_audio.mp3",
        "-c:v", "copy", "-c:a", "aac", "-shortest", OUTPUT_VIDEO
    ])

    # 9️⃣ Done
    print("\n✅ ✅ ✅")
    print("🎉 FINAL VIDEO GENERATED SUCCESSFULLY!")
    print(f"📂 Saved as: {OUTPUT_VIDEO}")
    print("🙏 धन्यवाद! आपका आध्यात्मिक वीडियो तैयार है।")
    print("✅ ✅ ✅\n")

# ============== RUN =================
if __name__ == "__main__":
    asyncio.run(main())