import os
import requests
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
import edge_tts
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
# Intro & outro text
INTRO_TEXT = "नमस्कार। स्वागत है आप सभी का Sanatan Gyan Dhara श्रृंखला में।"
OUTRO_TEXT = "यदि आपको यह वीडियो पसंद आया हो, तो कृपया लाइक, शेयर और सब्सक्राइब जरूर करें।"
# ===================================================

# ===================== PIXABAY IMAGES =====================
def fetch_pixabay_images(query, count=10):
    params = {
        "key": PIXABAY_KEY,
        "q": query,
        "image_type": "photo",
        "per_page": count,
        "safesearch": True
    }
    try:
        res = requests.get(PIXABAY_API, params=params, timeout=15).json()
        hits = res.get("hits", [])
        paths = []
        for i, hit in enumerate(hits):
            img_url = hit["largeImageURL"]
            path = f"{IMAGE_DIR}/{i:03d}.jpg"
            r = requests.get(img_url, timeout=15)
            if r.status_code == 200:
                with open(path, "wb") as f:
                    f.write(r.content)
                paths.append(path)
        return paths
    except Exception as e:
        print("⚠ Failed to fetch images:", e)
        return []

# ===================== EDGE-TTS AUDIO =====================
async def text_to_speech(text, out_file):
    communicate = edge_tts.Communicate(text, "hi-IN-MadhurNeural")
    await communicate.save(out_file)

async def generate_narration(script_lines):
    os.makedirs("tts", exist_ok=True)
    audio_files = []
    for idx, line in enumerate(script_lines):
        out_file = f"tts/narration_{idx:03d}.mp3"
        await text_to_speech(line, out_file)
        audio_files.append(out_file)
    return audio_files

# ===================== VIDEO CREATION =====================
def create_video(images, audio_files):
    clips = []

    # If images < audio, repeat last image
    while len(images) < len(audio_files):
        images.append(images[-1])

    # Create video clip for each image with audio
    for img_path, aud_path in zip(images, audio_files):
        audio_clip = AudioFileClip(aud_path)
        # Add tanpura if available
        if os.path.exists(BACKGROUND_MUSIC):
            tanpura_clip = AudioFileClip(BACKGROUND_MUSIC).volumex(0.2).set_duration(audio_clip.duration)
            final_audio = CompositeAudioClip([audio_clip, tanpura_clip])
        else:
            final_audio = audio_clip
        clip = ImageClip(img_path).set_duration(audio_clip.duration)
        clip = clip.set_audio(final_audio)
        clips.append(clip)

    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile(OUTPUT_VIDEO, fps=24, codec="libx264", audio_codec="aac")
    print("✅ Video ready:", OUTPUT_VIDEO)

# ===================== MAIN =====================
async def main():
    print("🚀 Starting video creation...")

    # 1️⃣ Fetch images
    images = fetch_pixabay_images("lord krishna vishnu", count=10)
    if os.path.exists(FIRST_PAGE):
        images = [FIRST_PAGE] + images

    # 2️⃣ Read script
    if not os.path.exists(SCRIPT_FILE):
        raise Exception(f"❌ {SCRIPT_FILE} not found")
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        script_lines = [line.strip() for line in f if line.strip()]

    # Add intro and outro to script
    script_lines = [INTRO_TEXT] + script_lines + [OUTRO_TEXT]

    # 3️⃣ Generate narration
    print("🔊 Generating narration...")
    audio_files = await generate_narration(script_lines)

    # 4️⃣ Create video
    print("🎞 Creating video...")
    create_video(images, audio_files)

if __name__ == "__main__":
    asyncio.run(main())