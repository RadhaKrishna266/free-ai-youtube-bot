import os
import requests
from TTS.api import TTS
from moviepy.editor import ImageSequenceClip, AudioFileClip

# ---------------- CONFIG ---------------- #

SCRIPT_FILE = "script.txt"
AUDIO_FILE = "voice.wav"
VIDEO_FILE = "video.mp4"
IMAGE_DIR = "images"
MAX_IMAGES = 60

# ---------------------------------------- #


def download_images():
    print("🖼 Downloading divine images")
    os.makedirs(IMAGE_DIR, exist_ok=True)

    r = requests.get(
        "https://pixabay.com/api/",
        params={
            "key": os.environ["PIXABAY_API_KEY"],
            "q": "Lord Vishnu Hindu divine art painting",
            "orientation": "horizontal",
            "image_type": "photo",
            "safesearch": "true",
            "per_page": 200
        }
    ).json()

    hits = r.get("hits", [])
    if len(hits) < 10:
        raise RuntimeError("❌ Too few images returned from Pixabay")

    usable = min(len(hits), MAX_IMAGES)

    for i in range(usable):
        img_url = hits[i]["largeImageURL"]
        img_data = requests.get(img_url).content
        with open(f"{IMAGE_DIR}/{i:03}.jpg", "wb") as f:
            f.write(img_data)

    print(f"✅ Downloaded {usable} images")


def create_audio():
    print("🎙 Creating calm divine narration")

    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        text = f.read()

    # SINGLE-SPEAKER HINDI MODEL (NO speaker needed)
    tts = TTS(
        model_name="tts_models/hi/tacotron2-DDC",
        progress_bar=False,
        gpu=False
    )

    tts.tts_to_file(
        text=text,
        file_path=AUDIO_FILE
    )

    print("✅ Divine voice generated")


def create_video():
    print("🎞 Creating video")

    images = sorted(
        [os.path.join(IMAGE_DIR, f) for f in os.listdir(IMAGE_DIR)]
    )

    audio = AudioFileClip(AUDIO_FILE)

    clip = ImageSequenceClip(images, fps=len(images) / audio.duration)
    clip = clip.set_audio(audio)

    clip.write_videofile(
        VIDEO_FILE,
        codec="libx264",
        audio_codec="aac",
        fps=24
    )

    print("✅ Video created successfully")


def main():
    download_images()
    create_audio()
    create_video()


if __name__ == "__main__":
    main()