import os
import asyncio
import edge_tts
from pydub import AudioSegment
import subprocess

# ---------- CONFIG ----------
IMAGE_FILE = "Image1.png"
TEMP_IMAGE_FILE = "Image1_resized.png"
FINAL_VIDEO = "final_video_episode_1.mp4"
SCRIPT_FILE = "script.txt"
TANPURA_FILE = "light_tanpura.mp3"
BELL_FILE = "temple_bell.mp3"

# ---------- FUNCTIONS ----------
def fix_image():
    # Resize safely using FFmpeg
    subprocess.run([
        "ffmpeg", "-y", "-i", IMAGE_FILE, "-vf", "scale=1280:720", TEMP_IMAGE_FILE
    ])
    os.replace(TEMP_IMAGE_FILE, IMAGE_FILE)
    print("✅ Image resized successfully")

async def generate_tts(text, output_file):
    communicate = edge_tts.Communicate(text, voice="hi-IN-SwaraNeural")
    await communicate.save(output_file)

def merge_audio(audio_files, output_file):
    final_audio = AudioSegment.empty()
    for file in audio_files:
        final_audio += AudioSegment.from_file(file)
    final_audio.export(output_file, format="mp3")
    print(f"✅ Audio merged into {output_file}")

def create_video(image_file, audio_file, output_file):
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", image_file,
        "-i", audio_file, "-c:v", "libx264",
        "-tune", "stillimage", "-c:a", "aac",
        "-b:a", "192k", "-pix_fmt", "yuv420p",
        "-shortest", output_file
    ])
    print(f"✅ Final video created: {output_file}")

# ---------- MAIN SCRIPT ----------
async def main():
    fix_image()

    # Read main narration from script
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        main_narration = f.read()

    # Define start and end narration
    start_narration = ("नमस्कार! आप देख रहे हैं Sanatan Gyan Dhara। "
                       "हम हर दिन विष्णु पुराण की एक नई कथा लेकर आते हैं।")
    end_narration = ("यह कथा समाप्त हुई। Sanatan Gyan Dhara पर जुड़े रहें "
                     "और हर दिन नई विष्णु पुराण की कथा देखें।")

    # Generate TTS in chunks to avoid errors
    audio_files = []
    for i, text in enumerate([start_narration, main_narration, end_narration]):
        file_name = f"tts_{i}.mp3"
        print(f"🎤 Generating TTS for part {i+1}...")
        await generate_tts(text, file_name)
        audio_files.append(file_name)

    # Prepend temple bell + tanpura
    intro_audio = merge_audio([BELL_FILE, TANPURA_FILE], "intro.mp3")
    merge_audio(["intro.mp3"] + audio_files, "final_audio.mp3")

    # Create final video
    create_video(IMAGE_FILE, "final_audio.mp3", FINAL_VIDEO)

# Run
asyncio.run(main())