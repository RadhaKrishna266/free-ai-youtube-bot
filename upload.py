import os
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    CompositeAudioClip,
    concatenate_videoclips
)
import edge_tts
import asyncio

# ================= CONFIG =================
IMAGE_PATH = "Image1.png"
SCRIPT_PATH = "script.txt"

VOICE = "hi-IN-MadhurNeural"
NARRATION_AUDIO = "narration.mp3"
BELL_AUDIO = "bell.mp3"        # you must keep this file
TANPURA_AUDIO = "tanpura.mp3"  # you must keep this file

FINAL_VIDEO = "final_video.mp4"
FPS = 24

# ================= TTS =================
async def generate_tts(text):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(NARRATION_AUDIO)

def clean_script(text):
    lines = []
    for line in text.splitlines():
        if line.strip().startswith("["):
            continue
        lines.append(line)
    return "\n".join(lines)

# ================= MAIN =================
def main():
    if not os.path.exists(IMAGE_PATH):
        raise FileNotFoundError("❌ Image1.png not found")

    if not os.path.exists(SCRIPT_PATH):
        raise FileNotFoundError("❌ script.txt not found")

    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        raw_script = f.read()

    narration_text = clean_script(raw_script)

    print("🔊 Generating narration...")
    asyncio.run(generate_tts(narration_text))

    narration = AudioFileClip(NARRATION_AUDIO)

    audio_tracks = []

    # Bell (start only)
    if os.path.exists(BELL_AUDIO):
        bell = AudioFileClip(BELL_AUDIO).volumex(1.0)
        audio_tracks.append(bell)

    # Tanpura (loop under narration)
    if os.path.exists(TANPURA_AUDIO):
        tanpura = AudioFileClip(TANPURA_AUDIO).volumex(0.15)
        tanpura = tanpura.audio_loop(duration=narration.duration)
        audio_tracks.append(tanpura)

    audio_tracks.append(narration)

    final_audio = CompositeAudioClip(audio_tracks)

    print("🖼️ Creating single-image video...")
    video = (
        ImageClip(IMAGE_PATH)
        .set_duration(narration.duration)
        .resize(height=1080)
        .set_audio(final_audio)
    )

    print("🎬 Rendering final video...")
    video.write_videofile(
        FINAL_VIDEO,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        threads=2,
        preset="medium"
    )

    print("✅ Video created:", FINAL_VIDEO)

if __name__ == "__main__":
    main()