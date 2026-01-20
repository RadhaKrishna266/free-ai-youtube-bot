import os
import subprocess
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

UPLOAD_TO_YOUTUBE = False  # keep False while testing

IMAGES_DIR = "images"
FACE_IMAGE = f"{IMAGES_DIR}/face.png"
AUDIO_FILE = "voice.m4a"
FINAL_VIDEO = "final.mp4"

os.makedirs(IMAGES_DIR, exist_ok=True)

def create_face_image():
    print("🎨 Creating AI face image")

    img = Image.new("RGB", (1024, 1024), color=(32, 32, 32))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 80)
    except:
        font = ImageFont.load_default()

    text = "AI FACT FACE"
    w, h = draw.textsize(text, font=font)
    draw.text(((1024 - w) / 2, (1024 - h) / 2), text, fill="white", font=font)

    img.save(FACE_IMAGE)
    print("✅ Face image created")

def create_voice():
    print("🎧 Creating placeholder voice audio")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=440:duration=35",
        AUDIO_FILE
    ], check=True)

def create_video():
    print("🎬 Creating animated video")

    audio = AudioFileClip(AUDIO_FILE)

    clips = []
    for i in range(7):
        zoom = 1 + i * 0.03
        clip = (
            ImageClip(FACE_IMAGE)
            .resize(zoom)
            .set_duration(audio.duration / 7)
        )
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")
    video = video.set_audio(audio)

    video.write_videofile(
        FINAL_VIDEO,
        fps=24,
        codec="libx264",
        audio_codec="aac"
    )

def main():
    print("🚀 Starting AI Talking Face Video Bot")
    create_face_image()
    create_voice()
    create_video()
    print("✅ Video generated:", FINAL_VIDEO)

if __name__ == "__main__":
    main()