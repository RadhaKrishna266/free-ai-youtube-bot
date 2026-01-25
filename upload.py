import os
import subprocess
from TTS.api import TTS

# ================= CONFIG =================
os.environ["COQUI_TOS_AGREED"] = "1"

SCRIPT_FILE = "script.txt"
VOICE_FILE = "narration.wav"

SPEAKER_WAV = "audio/speaker.wav"
TANPURA_FILE = "audio/tanpura.mp3"
BELL_FILE = "audio/temple_bell.mp3"

IMAGE_FILE = "images/000.jpg"
FINAL_VIDEO = "final.mp4"

# XTTS v2 – BEST NATURAL HINDI
TTS_MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"
# =========================================


def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)


# ================= AUDIO =================
def create_audio():
    print("🎤 Creating NATURAL Hindi narration")

    if not os.path.exists(SPEAKER_WAV):
        raise RuntimeError("❌ audio/speaker.wav is REQUIRED")

    if not os.path.exists(SCRIPT_FILE):
        raise RuntimeError("❌ script.txt missing")

    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        text = f.read().strip()

    tts = TTS(TTS_MODEL_NAME, gpu=False)

    tts.tts_to_file(
        text=text,
        file_path=VOICE_FILE,
        speaker_wav=SPEAKER_WAV,  # ✅ REQUIRED
        language="hi"             # ✅ FORCE HINDI
    )

    print("✅ Hindi narration created")


# ================= VIDEO =================
def create_video():
    print("🎬 Creating video")

    run([
        "ffmpeg", "-y",

        # Image (auto-extended)
        "-i", IMAGE_FILE,

        # Main narration
        "-i", VOICE_FILE,

        # Background loops
        "-stream_loop", "-1", "-i", TANPURA_FILE,
        "-stream_loop", "-1", "-i", BELL_FILE,

        # Audio mix
        "-filter_complex",
        "[2:a]volume=0.25[a2];"
        "[3:a]volume=0.12[a3];"
        "[1:a][a2][a3]amix=inputs=3:dropout_transition=3[a]",

        # Mapping
        "-map", "0:v",
        "-map", "[a]",

        # Video settings
        "-vf", "scale=1280:720,format=yuv420p",
        "-c:v", "libx264",
        "-c:a", "aac",

        # 🔑 END WITH NARRATION
        "-shortest",

        FINAL_VIDEO
    ])

    print("✅ Video created successfully")


# ================= MAIN =================
def main():
    create_audio()
    create_video()


if __name__ == "__main__":
    main()