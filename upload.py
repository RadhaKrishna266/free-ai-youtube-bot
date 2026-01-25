import os
import subprocess
from pathlib import Path
from TTS.api import TTS

os.environ["COQUI_TOS_AGREED"] = "1"

SCRIPT_FILE = "script.txt"
VOICE_FILE = "narration.wav"
MIXED_AUDIO = "mixed_audio.wav"

SPEAKER_WAV = "audio/speaker.wav"
TANPURA_FILE = "audio/tanpura.mp3"
BELL_FILE = "audio/temple_bell.mp3"

IMAGE_FILE = "images/000.jpg"
FINAL_VIDEO = "final.mp4"

TTS_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"
CHUNK_DIR = "chunks"
MAX_CHARS = 200   # 🔒 SAFE FOR XTTS


# ---------------- UTIL ----------------
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)


def get_duration(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path
    ])
    return float(out.strip())


def split_text_safe(text):
    sentences = (
        text.replace("।", "।\n")
            .replace("?", "?\n")
            .replace("!", "!\n")
            .splitlines()
    )

    chunks, current = [], ""
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if len(current) + len(s) <= MAX_CHARS:
            current += " " + s
        else:
            chunks.append(current.strip())
            current = s
    if current.strip():
        chunks.append(current.strip())
    return chunks


# ---------------- AUDIO ----------------
def create_audio():
    print("🎤 Creating natural Hindi narration (TOKEN SAFE)")
    Path(CHUNK_DIR).mkdir(exist_ok=True)

    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        text = f.read().strip()

    chunks = split_text_safe(text)
    print(f"🧩 Total chunks: {len(chunks)}")

    tts = TTS(TTS_MODEL, gpu=False)
    wavs = []

    for i, chunk in enumerate(chunks):
        out = f"{CHUNK_DIR}/chunk_{i:03d}.wav"
        print(f"🔊 Chunk {i+1}/{len(chunks)}")

        tts.tts_to_file(
            text=chunk,
            file_path=out,
            speaker_wav=SPEAKER_WAV,
            language="hi"
        )
        wavs.append(out)

    with open("wav_list.txt", "w") as f:
        for w in wavs:
            f.write(f"file '{w}'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "wav_list.txt",
        "-c", "copy",
        VOICE_FILE
    ])

    print("✅ Full narration ready")


# ---------------- MIX AUDIO ----------------
def mix_audio():
    duration = get_duration(VOICE_FILE)
    print(f"⏱ Duration: {duration:.2f}s")

    run([
        "ffmpeg", "-y",
        "-i", VOICE_FILE,
        "-stream_loop", "-1", "-i", TANPURA_FILE,
        "-stream_loop", "-1", "-i", BELL_FILE,
        "-filter_complex",
        f"[1:a]volume=0.25,atrim=0:{duration}[bg1];"
        f"[2:a]volume=0.12,atrim=0:{duration}[bg2];"
        "[0:a][bg1][bg2]amix=inputs=3",
        "-t", str(duration),
        MIXED_AUDIO
    ])

    return duration


# ---------------- VIDEO ----------------
def create_video(duration):
    run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", IMAGE_FILE,
        "-i", MIXED_AUDIO,
        "-t", str(duration),
        "-vf", "scale=1280:720,format=yuv420p",
        "-r", "25",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "stillimage",
        "-c:a", "aac",
        FINAL_VIDEO
    ])

    print("✅ Final video created")


# ---------------- MAIN ----------------
def main():
    create_audio()
    duration = mix_audio()
    create_video(duration)


if __name__ == "__main__":
    main()