import os
import random
import subprocess
import textwrap
from PIL import Image, ImageDraw, ImageFont
import moviepy.editor as mp
import requests

# ================= CONFIG =================
WIDTH, HEIGHT = 1080, 1920   # Vertical Shorts
IMAGES_DIR = "images"
FACE_IMAGE = f"{IMAGES_DIR}/face.png"
VOICE_FILE = "voice.m4a"
FINAL_VIDEO = "final.mp4"

PIXABAY_KEY = os.environ.get("PIXABAY_API_KEY")

os.makedirs(IMAGES_DIR, exist_ok=True)

# ================= FACT ENGINE =================
FACTS = [
    "Octopuses have three hearts.",
    "Bananas are berries, but strawberries are not.",
    "The human brain uses about 20 percent of the body's energy.",
    "Honey never spoils, even after thousands of years.",
    "A day on Venus is longer than a year on Venus."
]

def get_fact():
    return random.choice(FACTS)

# ================= FACE IMAGE =================
def create_face(text):
    img = Image.new("RGB", (WIDTH, HEIGHT), (20, 20, 20))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 70)
    except:
        font = ImageFont.load_default()

    wrapped = "\n".join(textwrap.wrap(text, 28))
    w, h = draw.multiline_textsize(wrapped, font=font)

    draw.multiline_text(
        ((WIDTH - w) / 2, HEIGHT / 2 - h),
        wrapped,
        fill="white",
        font=font,
        align="center"
    )

    img.save(FACE_IMAGE)

# ================= PIXABAY IMAGE =================
def download_pixabay():
    if not PIXABAY_KEY:
        return None

    url = f"https://pixabay.com/api/?key={PIXABAY_KEY}&q=science&image_type=photo&per_page=3"
    r = requests.get(url).json()

    if "hits" not in r or not r["hits"]:
        return None

    img_url = random.choice(r["hits"])["largeImageURL"]
    img_path = f"{IMAGES_DIR}/bg.jpg"

    with open(img_path, "wb") as f:
        f.write(requests.get(img_url).content)

    return img_path

# ================= AUDIO =================
def create_voice():
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=440:duration=25",
        VOICE_FILE
    ], check=True)

# ================= VIDEO =================
def create_video(bg_image):
    audio = mp.AudioFileClip(VOICE_FILE)
    duration = audio.duration

    face = (
        mp.ImageClip(FACE_IMAGE)
        .set_duration(duration)
        .resize(1.05)
        .set_position(("center", "center"))
    )

    # Fake talking motion
    face = face.fx(mp.vfx.resize, lambda t: 1 + 0.02 * (t % 0.5))

    if bg_image:
        bg = (
            mp.ImageClip(bg_image)
            .set_duration(duration)
            .resize(height=HEIGHT)
        )
    else:
        bg = mp.ColorClip((WIDTH, HEIGHT), color=(0, 0, 0), duration=duration)

    video = mp.CompositeVideoClip([bg, face]).set_audio(audio)

    video.write_videofile(
        FINAL_VIDEO,
        fps=24,
        codec="libx264",
        audio_codec="aac"
    )

# ================= MAIN =================
def main():
    print("🚀 AI Fact Face Bot Started")

    fact = get_fact()
    create_face(fact)
    bg = download_pixabay()
    create_voice()
    create_video(bg)

    print("✅ DONE → final.mp4")

if __name__ == "__main__":
    main()