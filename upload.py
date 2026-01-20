import os
import subprocess
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

# ================= CONFIG =================
UPLOAD_TO_YOUTUBE = False  # keep False

IMAGES_DIR = "images"
FACE_IMAGE = os.path.join(IMAGES_DIR, "face.png")
AUDIO_FILE = "voice.m4a"
FINAL_VIDEO = "final.mp4"

os.makedirs(IMAGES_DIR, exist_ok=True)

# ================= IMAGE =================
def create_face_image():
    print("🎨 Creating AI face image")

    img = Image.new("RGB", (1024, 1024), (32, 32, 32))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 80)
    except:
        font = ImageFont.load_default()

    text = "AI FACT FACE"

    # safer than textsize
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]

    draw.text(
        ((1024 - w) / 2, (1024 - h) / 2),
        text,
        fill="white",
        font=font
    )

    img.save(FACE_IMAGE)
    print("✅ Face image created:", FACE_IMAGE)

# ================= AUDIO =================
def create_voice():
    print("🎧 Creating placeholder voice audio")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=440:duration=35",
        "-c:a", "aac",
        "-b:a", "128k",
        AUDIO_FILE
    ], check=True)

    print("✅ Audio created:", AUDIO_FILE)

# ================= VIDEO =================
def create_video():
    print("🎬 Creating animated video")

    audio = AudioFileClip(AUDIO_FILE)
    duration = audio.duration

    clips = []

    for i in range(5):
        clip = (
            ImageClip(FACE_IMAGE)
            .set_duration(duration / 5)
            .resize(lambda t: 1 + 0.03 * t)  # REAL animation
        )
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")
    video = video.set_audio(audio)

    video.write_videofile(
        FINAL_VIDEO,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=2
    )

    print("✅ Video created:", FINAL_VIDEO)

# ================= MAIN =================
def main():
    print("🚀 Starting AI Animated Face Video Bot")
    create_face_image()
    create_voice()
    create_video()
    print("🎉 DONE — Download video from GitHub Actions artifacts")

if __name__ == "__main__":
    main()