import os
import requests
from pathlib import Path
from TTS.api import TTS
from moviepy.editor import ImageSequenceClip, AudioFileClip

# ================= CONFIG =================

SCRIPT_FILE = "script.txt"
VOICE_FILE = "voice.wav"
FINAL_VIDEO = "final.mp4"
IMAGE_DIR = "images"
MAX_IMAGES = 60

# ================= IMAGES =================

def download_images():
    print("🖼 Downloading divine images")
    os.makedirs(IMAGE_DIR, exist_ok=True)

    r = requests.get(
        "https://pixabay.com/api/",
        params={
            "key": os.environ["PIXABAY_API_KEY"],
            "q": "Lord Vishnu divine spiritual art",
            "orientation": "horizontal",
            "image_type": "photo",
            "safesearch": "true",
            "per_page": 200
        }
    ).json()

    hits = r.get("hits", [])
    if not hits:
        raise RuntimeError("No images returned from Pixabay")

    usable = min(len(hits), MAX_IMAGES)

    for i in range(usable):
        img = requests.get(hits[i]["largeImageURL"]).content
        with open(f"{IMAGE_DIR}/{i:03}.jpg", "wb") as f:
            f.write(img)

    print(f"✅ Downloaded {usable} images")

# ================= AUDIO =================

def create_audio():
    print("🎙 Creating calm divine narration")

    text = Path(SCRIPT_FILE).read_text(encoding="utf-8")

    tts = TTS(
        model_name="tts_models/hi/tacotron2-DDC",
        gpu=False
    )

    tts.tts_to_file(
        text=text,
        file_path=VOICE_FILE
    )

    print("✅ Voice generated")

# ================= VIDEO =================

def create_video():
    print("🎞 Creating video")

    images = sorted(
        [os.path.join(IMAGE_DIR, f) for f in os.listdir(IMAGE_DIR)]
    )

    audio = AudioFileClip(VOICE_FILE)

    clip = ImageSequenceClip(
        images,
        fps=len(images) / audio.duration
    ).set_audio(audio)

    clip.write_videofile(
        FINAL_VIDEO,
        codec="libx264",
        audio_codec="aac",
        fps=24
    )

    print("✅ Final video ready")

# ================= MAIN =================

def main():
    download_images()
    create_audio()
    create_video()

if __name__ == "__main__":
    main()