import os
import requests
from PIL import Image
from io import BytesIO
import edge_tts
from moviepy.video.VideoClip import ImageClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.audio.CompositeAudioClip import CompositeAudioClip
import asyncio

# ===================== CONFIG =====================
IMAGE_DIR = "images"
os.makedirs(IMAGE_DIR, exist_ok=True)
SCRIPT_FILE = "script.txt"
OUTPUT_VIDEO = "final_video.mp4"
BACKGROUND_MUSIC = "tanpura.mp3"
FIRST_PAGE = "image.png"  # Front cover image
PIXABAY_API = "https://pixabay.com/api/"
PIXABAY_KEY = os.environ.get("PIXABAY_API_KEY")  # Set in GitHub Secrets
# ===================================================

# ===================== PIXABAY IMAGES =====================
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
        print("Pixabay fetch failed:", e)
        return []

# ===================== TEXT TO SPEECH =====================
async def text_to_speech(text, out_file):
    communicate = edge_tts.Communicate(text, "hi-IN-MadhurNeural")
    await communicate.save(out_file)

# ===================== MAIN VIDEO =====================
async def main():
    print("🚀 Starting video generation...")

    # 1️⃣ Fetch images
    print("🌐 Fetching Vishnu/Krishna images from Pixabay...")
    images = fetch_pixabay_images("lord krishna vishnu", count=10)
    if not images:
        print("❌ No images fetched from Pixabay. Exiting.")
        return

    # 1a️⃣ Add first page/front cover
    if os.path.exists(FIRST_PAGE):
        images = [FIRST_PAGE] + images

    # 2️⃣ Read script
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        script_lines = [line.strip() for line in f if line.strip()]

    # Add start & end narration
    start_text = "नमस्कार। स्वागत है आप सभी का Sanatan Gyan Dhara श्रृंखला में। आज हम Vishnu Purana का पहला एपिसोड लाए हैं।"
    end_text = "🙏 अगर आपको यह वीडियो पसंद आया हो, तो कृपया लाइक, शेयर और सब्सक्राइब जरूर करें। यह केवल एक वीडियो नहीं, बल्कि आध्यात्मिक यात्रा है।"
    script_lines = [start_text] + script_lines + [end_text]

    # 3️⃣ Generate narration audio clips
    os.makedirs("tts", exist_ok=True)
    narration_clips = []
    for idx, line in enumerate(script_lines):
        tts_file = f"tts/narration_{idx:03d}.mp3"
        print(f"🔊 Generating narration for line {idx+1}/{len(script_lines)}...")
        await text_to_speech(line, tts_file)
        narration_clips.append(AudioFileClip(tts_file))

    # Combine narration into one audio clip
    narration_audio = concatenate_videoclips([clip.set_duration(clip.duration) for clip in narration_clips], method="compose")
    narration_audio.write_audiofile("narration_final.mp3")
    narration_clip = AudioFileClip("narration_final.mp3")

    # 4️⃣ Add tanpura background music
    if os.path.exists(BACKGROUND_MUSIC):
        bg_music = AudioFileClip(BACKGROUND_MUSIC).volumex(0.3)
        final_audio = CompositeAudioClip([narration_clip, bg_music.set_duration(narration_clip.duration)])
    else:
        final_audio = narration_clip

    # 5️⃣ Create video clips for each image
    duration_per_image = max(final_audio.duration / len(images), 3)  # At least 3s per image
    video_clips = []
    for img_path in images:
        clip = ImageClip(img_path).set_duration(duration_per_image)
        video_clips.append(clip)

    final_clip = concatenate_videoclips(video_clips, method="compose")
    final_clip = final_clip.set_audio(final_audio)

    # 6️⃣ Write final video
    print("🎬 Rendering final video...")
    final_clip.write_videofile(OUTPUT_VIDEO, fps=24)

    # 7️⃣ Status message at end
    print("\n✅ ✅ ✅")
    print("🎉 FINAL VIDEO GENERATED SUCCESSFULLY!")
    print(f"📂 Saved as: {OUTPUT_VIDEO}")
    print("🙏 धन्यवाद! आपका आध्यात्मिक वीडियो तैयार है।")
    print("✅ ✅ ✅\n")

# ===================== RUN =====================
if __name__ == "__main__":
    asyncio.run(main())