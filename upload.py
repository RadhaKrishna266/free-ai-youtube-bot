import os, random, subprocess, math
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont

# ================= CONFIG =================

VOICE = "en-IN-PrabhatNeural"
FPS = 30
WIDTH, HEIGHT = 1920, 1080
TARGET_MINUTES = 7

TOPICS = [
    "Mystery of Stonehenge",
    "Secrets of Egyptian Pyramids",
    "Lost City of Atlantis",
    "Ancient Roman Colosseum"
]

# ================= SCRIPT =================

def generate_script(topic):
    paragraphs = []
    for i in range(22):
        paragraphs.append(
            f"{topic} is one of the most fascinating subjects in human history. "
            f"This section explains its origins, theories, construction methods, "
            f"and unanswered questions in a clear and engaging way. "
            f"Historians and scientists still debate its true purpose today."
        )
    script = "\n\n".join(paragraphs)

    with open("script.txt", "w", encoding="utf-8") as f:
        f.write(script)

    return script

# ================= VOICE =================

def generate_voice():
    subprocess.run([
        "edge-tts",
        "--voice", VOICE,
        "--file", "script.txt",
        "--write-media", "voice.mp3"
    ], check=True)

# ================= FALLBACK IMAGES =================

def generate_fallback_images(topic, count=40):
    os.makedirs("frames", exist_ok=True)
    images = []

    for i in range(count):
        img = Image.new("RGB", (WIDTH, HEIGHT), (20, 20, 20))
        draw = ImageDraw.Draw(img)

        text = topic.upper()
        draw.text((WIDTH//2-400, HEIGHT//2-30), text, fill=(255,255,255))

        path = f"frames/frame_{i}.png"
        img.save(path)
        images.append(path)

    return images

# ================= VIDEO =================

def create_video(images):
    clips = []
    for img in images:
        clip = ImageClip(img).set_duration(4)
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")
    audio = AudioFileClip("voice.mp3")

    loops = math.ceil(audio.duration / video.duration)
    video = concatenate_videoclips([video] * loops)
    video = video.subclip(0, audio.duration)

    final = video.set_audio(audio)

    final.write_videofile(
        "final.mp4",
        fps=FPS,
        codec="libx264",
        audio_codec="aac"
    )

# ================= MAIN =================

def main():
    print("🚀 Starting Auto Video Generator")

    topic = random.choice(TOPICS)
    print("Topic:", topic)

    generate_script(topic)
    generate_voice()

    images = generate_fallback_images(topic)
    create_video(images)

    print("✅ Video created successfully")

if __name__ == "__main__":
    main()