import os
import subprocess
from TTS.api import TTS

# ---------------- CONFIG ----------------
os.environ["COQUI_TOS_AGREED"] = "1"

SCRIPT_FILE = "script.txt"
VOICE_FILE = "narration.wav"

SPEAKER_WAV = "audio/speaker.wav"
TANPURA_FILE = "audio/tanpura.mp3"
BELL_FILE = "audio/temple_bell.mp3"

IMAGE_FILE = "images/000.jpg"
FINAL_VIDEO = "final.mp4"

TTS_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"
# ---------------------------------------


def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)


# ---------------- AUDIO ----------------
def create_audio():
    print("🎤 Creating natural Hindi narration")

    if not os.path.exists(SPEAKER_WAV):
        raise RuntimeError("❌ audio/speaker.wav is REQUIRED")

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


# ---------------- VIDEO ----------------
def create_video():
    print("🎬 Creating video")

    run([
        "ffmpeg", "-y",

        # Static image
        "-loop", "1", "-i", IMAGE_FILE,

        # Main narration
        "-i", VOICE_FILE,

        # Background sounds (NO looping / NO trimming)
        "-i", TANPURA_FILE,
        "-i", BELL_FILE,

        # Mix audio safely
        "-filter_complex",
        "[2:a]volume=0.25[a2];"
        "[3:a]volume=0.12[a3];"
        "[1:a][a2][a3]amix=inputs=3:dropout_transition=2[a]",

        # Map video + mixed audio
        "-map", "0:v",
        "-map", "[a]",

        # Video settings
        "-vf", "scale=1280:720,format=yuv420p",
        "-r", "25",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-tune", "stillimage",

        # Audio
        "-c:a", "aac",

        # CRITICAL: stop when narration ends
        "-shortest",

        FINAL_VIDEO
    ])

    print("✅ Video created successfully")


# ---------------- MAIN ----------------
def main():
    create_audio()
    create_video()


if __name__ == "__main__":
    main()