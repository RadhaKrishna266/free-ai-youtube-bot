import os
import requests
from PIL import Image
from io import BytesIO
import imageio
import imageio_ffmpeg as ffmpeg
import edge_tts
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip

# ===================== CONFIG =====================
IMAGE_DIR = "images"
os.makedirs(IMAGE_DIR, exist_ok=True)
SCRIPT_FILE = "script.txt"
OUTPUT_VIDEO = "final_video.mp4"
BACKGROUND_MUSIC = "tanpura.mp3"
FIRST_PAGE = "image.png"  # Front cover image
PIXABAY_API = "https://pixabay.com/api/"
PIXABAY_KEY = "YOUR_PIXABAY_API_KEY"  # Replace with free Pixabay API key
# ===================================================

# ===================== PIXABAY IMAGES =====================
def fetch_pixabay_images(query, count=5):
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
            img_res = requests.get(url)
            path = f"{IMAGE_DIR}/{i:03d}.jpg"
            with open(path, "wb") as f:
                f.write(img_res.content)
            paths.append(path)
        return paths
    except Exception as e:
        print("Pixabay fetch failed:", e)
        return []

# ===================== TEXT TO SPEECH =====================
async def text_to_speech(text, out_file):
    communicate = edge_tts.Communicate(text, "en-US-JennyNeural")
    await communicate.save(out_file)

# ===================== MAIN VIDEO =====================
import asyncio

async def main():
    # 1️⃣ Fetch images
    images = fetch_pixabay_images("lord krishna vishnu", count=10)
    if not images:
        print("No images fetched from Pixabay. Exiting.")
        return

    # Add first page/front cover
    if os.path.exists(FIRST_PAGE):
        images = [FIRST_PAGE] + images

    # 2️⃣ Read script
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    # 3️⃣ Generate narration files
    os.makedirs("tts", exist_ok=True)
    narration_clips = []
    for idx, line in enumerate(lines):
        tts_file = f"tts/narration_{idx:03d}.mp3"
        await text_to_speech(line, tts_file)
        narration_clips.append(AudioFileClip(tts_file))

    # Combine narration into one audio
    narration_audio = concatenate_videoclips([clip.set_duration(clip.duration) for clip in narration_clips], method="compose")
    narration_audio.write_audiofile("narration_final.mp3")
    narration_clip = AudioFileClip("narration_final.mp3")

    # 4️⃣ Combine with background music
    if os.path.exists(BACKGROUND_MUSIC):
        bg_music = AudioFileClip(BACKGROUND_MUSIC)
        # Adjust volume of music
        bg_music = bg_music.volumex(0.3)
        final_audio = CompositeAudioClip([narration_clip, bg_music.set_duration(narration_clip.duration)])
    else:
        final_audio = narration_clip

    # 5️⃣ Create video clips for each image
    duration_per_image = max(final_audio.duration / len(images), 3)  # At least 3s per image
    clips = []
    for img_path in images:
        clip = ImageClip(img_path).set_duration(duration_per_image)
        clips.append(clip)

    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip = final_clip.set_audio(final_audio)
    final_clip.write_videofile(OUTPUT_VIDEO, fps=24)

# ===================== RUN =====================
if __name__ == "__main__":
    asyncio.run(main())