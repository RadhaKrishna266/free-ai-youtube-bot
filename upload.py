import os
import textwrap
import subprocess
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

# ---------------- CONFIG ----------------
WIDTH, HEIGHT = 1024, 1024
IMAGES_DIR = "images"
FACE_BG = f"{IMAGES_DIR}/face_bg.png"
AUDIO_FILE = "voice.m4a"
FINAL_VIDEO = "final.mp4"

os.makedirs(IMAGES_DIR, exist_ok=True)

# ---------------- FACTS ----------------
FACTS = [
    "Octopuses have three hearts and blue blood.",
    "Bananas are berries, but strawberries are not.",
    "A day on Venus is longer than a year on Venus."
]

# ---------------- CREATE BASE FACE ----------------
def create_face_bg():
    img = Image.new("RGB", (WIDTH, HEIGHT), (20, 20, 20))
    img.save(FACE_BG)

# ---------------- CREATE TALKING FRAME ----------------
def create_frame(text, mouth_open, index):
    img = Image.open(FACE_BG).copy()
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 56)
    except:
        font = ImageFont.load_default()

    wrapped = textwrap.fill(text, 26)

    bbox = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=8)
    tw = bbox[2] - bbox[0]

    draw.multiline_text(
        ((WIDTH - tw) // 2, 180),
        wrapped,
        fill="white",
        font=font,
        align="center",
        spacing=8
    )

    # 👄 FAKE TALKING MOUTH
    mouth_y = 620
    if mouth_open:
        draw.rectangle((450, mouth_y, 574, mouth_y + 40), fill="white")
    else:
        draw.rectangle((450, mouth_y + 20, 574, mouth_y + 26), fill="white")

    path = f"{IMAGES_DIR}/frame_{index}.png"
    img.save(path)
    return path

# ---------------- CREATE AUDIO ----------------
def create_voice():
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=440:duration=18",
        AUDIO_FILE
    ], check=True)

# ---------------- BUILD VIDEO ----------------
def create_video():
    audio = AudioFileClip(AUDIO_FILE)
    segments = []

    seg_duration = audio.duration / len(FACTS)
    frame_index = 0

    for fact in FACTS:
        clips = []
        for i in range(8):
            img_path = create_frame(
                fact,
                mouth_open=(i % 2 == 0),
                index=frame_index
            )
            frame_index += 1

            clips.append(
                ImageClip(img_path)
                .set_duration(seg_duration / 8)
            )

        segments.append(concatenate_videoclips(clips, method="compose"))

    video = concatenate_videoclips(segments, method="compose")
    video = video.set_audio(audio)

    video.write_videofile(
        FINAL_VIDEO,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=2
    )

# ---------------- MAIN ----------------
def main():
    print("🚀 AI Fact Face Bot Started")
    create_face_bg()
    create_voice()
    create_video()
    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()