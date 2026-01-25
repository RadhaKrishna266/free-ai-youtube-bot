import os
import subprocess
import json
from TTS.api import TTS

os.environ["COQUI_TOS_AGREED"] = "1"

SCRIPT_FILE = "script.txt"
VOICE_FILE = "narration.wav"

SPEAKER_WAV = "audio/speaker.wav"
TANPURA_FILE = "audio/tanpura.mp3"
BELL_FILE = "audio/temple_bell.mp3"

IMAGE_FILE = "images/000.jpg"
FINAL_VIDEO = "final.mp4"

TTS_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"


def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)


# ---------------- AUDIO ----------------
def create_audio():
    print("🎤 Creating natural Hindi narration")

    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        text = f.read().strip()

    tts = TTS(TTS_MODEL, gpu=False)
    tts.tts_to_file(
        text=text,
        file_path=VOICE_FILE,
        speaker_wav=SPEAKER_WAV,
        language="hi"
    )

    print("✅ Hindi narration created")


def get_audio_duration(path):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json", path
    ]
    out = subprocess.check_output(cmd)
    return float(json.loads(out)["format"]["duration"])


# ---------------- VIDEO ----------------
def create_video():
    print("🎬 Creating video")

    duration = get_audio_duration(VOICE_FILE)
    print(f"⏱ Narration duration: {duration:.2f}s")

    run([
        "ffmpeg", "-y",

        "-loop", "1", "-i", IMAGE_FILE,
        "-i", VOICE_FILE,
        "-i", TANPURA_FILE,
        "-i", BELL_FILE,

        "-filter_complex",
        f"[2:a]volume=0.25,atrim=0:{duration}[a2];"
        f"[3:a]volume=0.12,atrim=0:{duration}[a3];"
        "[1:a][a2][a3]amix=inputs=3[a]",

        "-map", "0:v",
        "-map", "[a]",

        "-t", str(duration),
        "-vf", "scale=1280:720,format=yuv420p",
        "-r", "25",
        "-c:v", "libx264",
        "-c:a", "aac",

        FINAL_VIDEO
    ])

    print("✅ Video created successfully")


# ---------------- MAIN ----------------
def main():
    create_audio()
    create_video()


if __name__ == "__main__":
    main()