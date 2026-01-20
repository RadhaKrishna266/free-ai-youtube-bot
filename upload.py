import os
import subprocess
import random

DURATION = 600  # 10 minutes
FPS = 30

IMAGES_DIR = "images"
VOICE_WAV = "voice.wav"
FINAL_VIDEO = "final.mp4"

PIPER_BIN = "./piper/piper"
PIPER_MODEL = "./piper/en_US-lessac-medium.onnx"

FACTS = [
    "A day on Venus is longer than a year on Venus.",
    "Octopuses have three hearts.",
    "Bananas are berries but strawberries are not.",
    "Honey never spoils.",
    "Sharks existed before trees.",
    "The Eiffel Tower grows in summer.",
    "Wombats have cube shaped poop.",
]

os.makedirs(IMAGES_DIR, exist_ok=True)

def run(cmd, input_data=None):
    subprocess.run(cmd, input=input_data, check=True)

def create_voice():
    print("🎙️ Creating REAL voice using Piper")

    text = ""
    while len(text.split()) < 1300:
        text += random.choice(FACTS) + " "

    run(
        [PIPER_BIN, "--model", PIPER_MODEL, "--output_file", VOICE_WAV],
        input_data=text.encode("utf-8")
    )

def create_images():
    print("🖼️ Creating images")

    for i, fact in enumerate(FACTS):
        run([
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "color=c=black:s=1280x720",
            "-vf",
            f"drawtext=text='{fact}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2",
            f"{IMAGES_DIR}/img{i}.png"
        ])

def create_video():
    print("🎬 Creating video")

    images = sorted(os.listdir(IMAGES_DIR))
    duration_per_image = DURATION / len(images)

    with open("list.txt", "w") as f:
        for img in images:
            f.write(f"file '{IMAGES_DIR}/{img}'\n")
            f.write(f"duration {duration_per_image}\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "list.txt",
        "-i", VOICE_WAV,
        "-vf", "zoompan=z='min(zoom+0.0005,1.15)':d=1:s=1280x720",
        "-t", str(DURATION),
        "-r", str(FPS),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        FINAL_VIDEO
    ])

def main():
    print("🚀 AI FACT VIDEO BOT STARTED")
    create_voice()
    create_images()
    create_video()
    print("✅ DONE:", FINAL_VIDEO)

if __name__ == "__main__":
    main()