import os
import requests
from PIL import Image
from moviepy.editor import (
    ImageSequenceClip,
    AudioFileClip,
    CompositeAudioClip
)
from TTS.api import TTS

PIXABAY_KEY = os.getenv("PIXABAY_API_KEY")

SCRIPT_FILE = "script.txt"
AUDIO_FILE = "voice.wav"
FINAL_AUDIO = "final_audio.wav"
FINAL_VIDEO = "final.mp4"
IMAGE_DIR = "images"
TANPURA = "tanpura.mp3"

IMAGES_COUNT = 60
IMAGE_DURATION = 10  # seconds per image (60 × 10 = 10 minutes)


def download_images():
    os.makedirs(IMAGE_DIR, exist_ok=True)

    query = "Vishnu Narayan divine art painting"
    url = f"https://pixabay.com/api/?key={PIXABAY_KEY}&q={query}&image_type=illustration&per_page=200"

    r = requests.get(url).json()
    hits = r.get("hits", [])

    if len(hits) == 0:
        raise Exception("No images received from Pixabay")

    for i in range(min(IMAGES_COUNT, len(hits))):
        img_url = hits[i]["largeImageURL"]
        img_data = requests.get(img_url).content

        with open(f"{IMAGE_DIR}/{i:03}.jpg", "wb") as f:
            f.write(img_data)


def create_voice():
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        text = f.read()

    tts = TTS(
        model_name="tts_models/hi/vits",
        gpu=False
    )

    tts.tts_to_file(
        text=text,
        file_path=AUDIO_FILE
    )


def mix_tanpura():
    voice = AudioFileClip(AUDIO_FILE)
    tanpura = AudioFileClip(TANPURA).volumex(0.15)

    tanpura = tanpura.audio_loop(duration=voice.duration)

    final_audio = CompositeAudioClip([tanpura, voice])
    final_audio.write_audiofile(FINAL_AUDIO)


def create_video():
    images = [
        os.path.join(IMAGE_DIR, img)
        for img in sorted(os.listdir(IMAGE_DIR))
    ]

    clip = ImageSequenceClip(
        images,
        durations=[IMAGE_DURATION] * len(images)
    )

    audio = AudioFileClip(FINAL_AUDIO)
    clip = clip.set_audio(audio)

    clip.write_videofile(
        FINAL_VIDEO,
        fps=24,
        codec="libx264",
        audio_codec="aac"
    )


def main():
    print("🖼 Downloading images")
    download_images()

    print("🎙 Creating divine Hindi narration")
    create_voice()

    print("🎵 Adding tanpura background")
    mix_tanpura()

    print("🎬 Creating final video")
    create_video()

    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)


if __name__ == "__main__":
    main()