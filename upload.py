import os
import subprocess
import textwrap

FACTS = [
    "Octopuses have three hearts and blue blood.",
    "The human brain uses about twenty percent of the body's energy.",
    "Bananas are berries but strawberries are not.",
    "A day on Venus is longer than a year on Venus.",
    "Honey never spoils and can last thousands of years."
]

VIDEO_DURATION_MINUTES = 10
IMAGE_DIR = "images"
AUDIO_FILE = "voice.wav"
VIDEO_FILE = "final.mp4"
PIPER_BIN = "./piper/piper"
VOICE_MODEL = "./piper/en_US-lessac-medium.onnx"

os.makedirs(IMAGE_DIR, exist_ok=True)

def generate_images():
    print("🖼 Generating fact images")
    for i, fact in enumerate(FACTS):
        img = f"{IMAGE_DIR}/img_{i}.png"
        subprocess.run([
            "convert",
            "-size", "1280x720",
            "gradient:#0f2027-#203a43",
            "-gravity", "center",
            "-fill", "white",
            "-pointsize", "48",
            "-annotate", "+0+0", textwrap.fill(fact, 40),
            img
        ], check=True)

def generate_voice():
    print("🎙 Generating REAL voice using Piper")
    text = ". ".join(FACTS * 20)  # enough for ~10 minutes
    subprocess.run([
        PIPER_BIN,
        "--model", VOICE_MODEL,
        "--output_file", AUDIO_FILE
    ], input=text.encode(), check=True)

def generate_video():
    print("🎬 Creating 10-minute video")
    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", "1/5",
        "-i", f"{IMAGE_DIR}/img_%d.png",
        "-i", AUDIO_FILE,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        VIDEO_FILE
    ], check=True)

def main():
    print("🚀 AI FACT VIDEO BOT STARTED")
    generate_images()
    generate_voice()
    generate_video()
    print("✅ DONE:", VIDEO_FILE)

if __name__ == "__main__":
    main()