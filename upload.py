import os
import requests
import subprocess
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

# ---------------- CONFIG ----------------
PIXABAY_KEY = os.environ.get("PIXABAY_API_KEY")
WIDTH, HEIGHT = 1280, 720

IMAGES_DIR = "images"
AUDIO_FILE = "voice.m4a"
FINAL_VIDEO = "final.mp4"

os.makedirs(IMAGES_DIR, exist_ok=True)

# ---------------- FACTS (AUTO-REPEATED) ----------------
BASE_FACTS = [
    ("Venus planet", "A day on Venus is longer than a year on Venus."),
    ("Octopus ocean", "Octopuses have three hearts and blue blood."),
    ("Banana fruit", "Bananas are berries, but strawberries are not."),
    ("Space galaxy", "There are more stars in the universe than grains of sand on Earth."),
    ("Human brain", "Your brain uses about 20% of your body's energy.")
]

FACTS = BASE_FACTS * 6   # 5 facts × 6 = 30 facts → ~10 minutes

# ---------------- DOWNLOAD REAL IMAGES ----------------
def download_images(query, limit=3):
    url = "https://pixabay.com/api/"
    params = {
        "key": PIXABAY_KEY,
        "q": query,
        "image_type": "photo",
        "per_page": limit,
        "safesearch": "true"
    }
    r = requests.get(url, params=params).json()
    paths = []

    for i, hit in enumerate(r.get("hits", [])):
        img_url = hit["largeImageURL"]
        path = f"{IMAGES_DIR}/{query.replace(' ', '_')}_{i}.jpg"
        with open(path, "wb") as f:
            f.write(requests.get(img_url).content)
        paths.append(path)

    return paths

# ---------------- AUDIO (10 MIN) ----------------
def create_audio():
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=440",
        "-t", "600",
        AUDIO_FILE
    ], check=True)

# ---------------- VIDEO ----------------
def create_video():
    audio = AudioFileClip(AUDIO_FILE)
    clips = []

    fact_duration = 20  # seconds per fact

    for query, text in FACTS:
        images = download_images(query)
        if not images:
            continue

        img_duration = fact_duration / len(images)

        for img in images:
            clip = (
                ImageClip(img)
                .resize(height=HEIGHT)
                .set_duration(img_duration)
                .fx(lambda c: c.crop(
                    x_center=c.w / 2,
                    y_center=c.h / 2,
                    width=WIDTH,
                    height=HEIGHT
                ))
            )
            clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")
    video = video.set_audio(audio.subclip(0, video.duration))

    video.write_videofile(
        FINAL_VIDEO,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=2
    )

# ---------------- MAIN ----------------
def main():
    print("🚀 Creating 10-minute REAL IMAGE FACT VIDEO")
    create_audio()
    create_video()
    print("✅ DONE:", FINAL_VIDEO)

if __name__ == "__main__":
    main()