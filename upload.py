import os
import subprocess
import json
from TTS.api import TTS

os.environ["COQUI_TOS_AGREED"] = "1"

SCRIPT_FILE = "script.txt"
VOICE_FILE = "narration.wav"
MIXED_AUDIO = "mixed_audio.wav"

TANPURA_FILE = "audio/tanpura.mp3"
BELL_FILE = "audio/temple_bell.mp3"

IMAGE_FILE = "images/000.jpg"
FINAL_VIDEO = "final.mp4"

TTS_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"


def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)


def get_duration(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json", path
    ])
    return float(json.loads(out)["format"]["duration"])


# ---------------- AUDIO ----------------
def create_audio():
    print("🎤 Creating natural Hindi narration")

    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        text = f.read().strip()

    tts = TTS(TTS_MODEL, gpu=False)
    tts.tts_to_file(
        text=text,
        file_path=VOICE_FILE,
        language="hi"
    )

    print("✅ Hindi narration created")


def mix_audio():
    print("🎧 Mixing background audio safely")

    duration = get_duration(VOICE_FILE)
    print(f"⏱ Narration duration: {duration:.2f}s")

    run([
        "ffmpeg", "-y",
        "-i", VOICE_FILE,
        "-stream_loop", "-1", "-i", TANPURA_FILE,
        "-stream_loop", "-1", "-i", BELL_FILE,
        "-filter_complex",
        f"[1:a]volume=0.25,atrim=0:{duration}[a1];"
        f"[2:a]volume=0.12,atrim=0:{duration}[a2];"
        "[0:a][a1][a2]amix=inputs=3",
        "-t", str(duration),
        MIXED_AUDIO
    ])

    print("✅ Audio mix completed")
    return duration


# ---------------- VIDEO ----------------
def create_video(duration):
    print("🎬 Creating video (GUARANTEED EXIT)")

    run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", IMAGE_FILE,
        "-i", MIXED_AUDIO,
        "-t", str(duration),
        "-vf", "scale=1280:720,format=yuv420p",
        "-r", "25",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-tune", "stillimage",
        "-c:a", "aac",
        FINAL_VIDEO
    ])

    print("✅ Video created successfully")


# ---------------- MAIN ----------------
def main():
    create_audio()
    duration = mix_audio()
    create_video(duration)


if __name__ == "__main__":
    main()