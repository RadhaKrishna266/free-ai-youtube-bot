import os
import subprocess
import textwrap
import random

# ================= CONFIG =================
DURATION = 600  # 10 minutes
FPS = 30
IMAGES_DIR = "images"
VOICE_WAV = "voice.wav"
VOICE_M4A = "voice.m4a"
FINAL_VIDEO = "final.mp4"

PIPER_BIN = "./piper/piper"
PIPER_MODEL = "./piper/en_US-lessac-medium.onnx"

FACTS = [
    "Octopuses have three hearts and blue blood.",
    "Bananas are berries, but strawberries are not.",
    "A day on Venus is longer than a year on Venus.",
    "Honey never spoils, even after thousands of years.",
    "Sharks existed before trees.",
    "The human brain uses about twenty percent of the body's energy.",
    "There are more possible games of chess than atoms in the universe.",
    "Some turtles can breathe through their butts.",
    "Wombat poop is cube shaped.",
    "The Eiffel Tower grows taller in summer."
]

# ==========================================

os.makedirs(IMAGES_DIR, exist_ok=True)


def run(cmd, input_data=None):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, input=input_data, check=True)


# 🎙️ REAL HUMAN VOICE (PIPER)
def create_voice():
    print("🎙️ Generating real voice with Piper")

    script = ""
    while len(script.split()) < 1200:  # ~10 min
        script += random.choice(FACTS) + " "

    run(
        [PIPER_BIN, "--model", PIPER_MODEL, "--output_file", VOICE_WAV],
        input_data=script.encode("utf-8")
    )

    run(["ffmpeg", "-y", "-i", VOICE_WAV, VOICE_M4A])
    print("✅ Voice created")


# 🖼️ GENERATE FACT IMAGES (TEXT-BASED)
def create_images():
    print("🖼️ Creating fact images")

    for i, fact in enumerate(FACTS):
        wrapped = "\\n".join(textwrap.wrap(fact, 30))

        run([
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "color=c=black:s=1280x720",
            "-vf",
            f"drawtext=text='{wrapped}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2",
            f"{IMAGES_DIR}/img{i}.png"
        ])

    print("✅ Images created")


# 🎬 CREATE ANIMATED VIDEO (NO MOVIEPY)
def create_video():
    print("🎬 Creating animated video")

    images = sorted(os.listdir(IMAGES_DIR))
    img_duration = DURATION / len(images)

    with open("list.txt", "w") as f:
        for img in images:
            f.write(f"file '{IMAGES_DIR}/{img}'\n")
            f.write(f"duration {img_duration}\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "list.txt",
        "-vf",
        "zoompan=z='min(zoom+0.0005,1.15)':d=1:s=1280x720,format=yuv420p",
        "-r", str(FPS),
        "-t", str(DURATION),
        "-i", VOICE_M4A,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        FINAL_VIDEO
    ])

    print("✅ final.mp4 created")


def main():
    print("🚀 STARTING AI FACT VIDEO BOT")
    create_voice()
    create_images()
    create_video()
    print("🎉 DONE — Video ready:", FINAL_VIDEO)


if __name__ == "__main__":
    main()