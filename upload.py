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

TTS_MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"
# =========================================


def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)


# ================= AUDIO =================
def create_audio():
    print("🎤 Creating NATURAL Hindi narration")

    if not os.path.exists(SPEAKER_WAV):
        raise RuntimeError("❌ audio/speaker.wav missing")

    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        text = f.read().strip()

    tts = TTS(TTS_MODEL_NAME, gpu=False)

    tts.tts_to_file(
        text=text,
        file_path=VOICE_FILE,
        speaker_wav=SPEAKER_WAV,
        language="hi"
    )

    print("✅ Hindi narration created")


# ================= VIDEO =================
def create_video():
    print("🎬 Creating video")

    run([
        "ffmpeg", "-y",

        # Loop image forever
        "-loop", "1", "-i", IMAGE_FILE,

        # Narration (controls duration)
        "-i", VOICE_FILE,

        # Background audio (NORMAL input)
        "-i", TANPURA_FILE,
        "-i", BELL_FILE,

        # Filters
        "-filter_complex",
        "[2:a]aloop=loop=-1:size=2e+09,volume=0.25[a2];"
        "[3:a]aloop=loop=-1:size=2e+09,volume=0.12[a3];"
        "[1:a][a2][a3]amix=inputs=3:dropout_transition=2[a]",

        # Mapping
        "-map", "0:v",
        "-map", "[a]",

        # Video
        "-vf", "scale=1280:720,format=yuv420p",
        "-r", "25",
        "-c:v", "libx264",
        "-c:a", "aac",

        # END WHEN NARRATION ENDS
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