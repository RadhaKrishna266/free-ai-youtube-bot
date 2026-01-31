import os
import requests
from PIL import Image

from moviepy import (
    ImageSequenceClip,
    AudioFileClip,
    CompositeAudioClip
)

from TTS.api import TTS

PIXABAY_KEY = os.getenv("PIXABAY_API_KEY")

SCRIPT_FILE = "script.txt"
VOICE_FILE = "voice.wav"
FINAL_AUDIO = "final_audio.wav"
FINAL_VIDEO = "final.mp4"
IMAGE_DIR = "images"
TANPURA_FILE = "tanpura.mp3"

IMAGES_COUNT = 60
IMAGE_DURATION = 10  # seconds → 60 images = 10 minutes


def download_images():
    os.makedirs(IMAGE_DIR, exist_ok=True)

    query = "Vishnu Narayan divine painting art"
    url = (
        "https://pixabay.com/api/"
        f"?key={PIXABAY_KEY}"
        f"&q={query}"
        "&image_type=illustration"
        "&per_page=200"
    )

    data = requests.get(url).json()
    hits = data.get("hits", [])

    if not hits:
        raise RuntimeError("❌ No images received from Pixabay")

    count = min(IMAGES_COUNT, len(hits))

    for i in range(count):
        img_url = hits[i]["largeImageURL"]
        img_bytes = requests.get(img_url).content

        with open(f"{IMAGE_DIR}/{i:03}.jpg", "wb") as f:
            f.write(img_bytes)


def create_voice():
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        text = f.read()

    tts = TTS(
        model_name="tts_models/hi/vits",
        gpu=False
    )

    tts.tts_to_file(
        text=text,
        file_path=VOICE_FILE
    )


def mix_tanpura():
    voice = AudioFileClip(VOICE_FILE)
    tanpura = AudioFileClip(TANPURA_FILE).volumex(0.12)

    tanpura = tanpura.audio_loop(duration=voice.duration)

    final_audio = CompositeAudioClip([tanpura, voice])
    final_audio.write_audiofile(FINAL_AUDIO)


def create_video():
    images = sorted(
        os.path.join(IMAGE_DIR, f)
        for f in os.listdir(IMAGE_DIR)
        if f.endswith(".jpg")
    )

    clip = ImageSequenceClip(
        images,
        durations=[IMAGE_DURATION] * len(images)
    )

    audio = AudioFileClip(FINAL_AUDIO)
    clip = clip.with_audio(audio)

    clip.write_videofile(
        FINAL_VIDEO,
        fps=24,
        codec="libx264",
        audio_codec="aac"
    )


def main():
    print("🖼 Downloading divine images")
    download_images()

    print("🎙 Creating Hindi divine narration")
    create_voice()

    print("🎵 Mixing tanpura background")
    mix_tanpura()

    print("🎬 Rendering final video")
    create_video()

    print("✅ VIDEO READY:", FINAL_VIDEO)


if __name__ == "__main__":
    main()