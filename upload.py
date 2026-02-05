import os
import asyncio
from pydub import AudioSegment
import edge_tts
import subprocess

from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

# ================= FILE PATHS =================
IMAGE_FILE = "Image1.png"
RESIZED_IMAGE = "Image1_resized.png"
SCRIPT_FILE = "script.txt"

BELL_FILE = "audio/temple_bell.mp3"
TANPURA_FILE = "audio/tanpura.mp3"
FINAL_VIDEO = "final_video_episode_1.mp4"

# ================= RESIZE IMAGE =================
def resize_image(input_file, output_file, width=1280, height=720):
    # Use ffmpeg to resize
    subprocess.run([
        "ffmpeg", "-y", "-i", input_file,
        "-vf", f"scale={width}:{height}",
        output_file
    ], check=True)
    print("✅ Image resized successfully")

# ================= MERGE AUDIO FILES =================
def merge_audio(audio_files, output_file):
    final_audio = AudioSegment.silent(duration=0)
    for file in audio_files:
        final_audio += AudioSegment.from_file(file)
    final_audio.export(output_file, format="mp3")
    return output_file

# ================= GENERATE TTS =================
async def generate_tts(text, output_file):
    communicate = edge_tts.Communicate(text, "hi-IN-SwaraNeural")
    await communicate.save(output_file)
    print(f"🎤 TTS generated: {output_file}")

# ================= READ SCRIPT =================
def get_script_text(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()

# ================= MAIN =================
async def main():
    # 1️⃣ Resize image
    resize_image(IMAGE_FILE, RESIZED_IMAGE)

    # 2️⃣ Prepare narrations
    start_narration_text = "नमस्कार। आप देख रहे हैं सनातन ज्ञान धारा। हम प्रतिदिन विष्णु पुराण के वीडियो अपलोड करेंगे।"
    end_narration_text = "धन्यवाद। आपने सनातन ज्ञान धारा देखा। हम प्रतिदिन विष्णु पुराण के वीडियो अपलोड करेंगे।"
    main_script_text = get_script_text(SCRIPT_FILE)

    # 3️⃣ Generate TTS files
    os.makedirs("tts", exist_ok=True)
    await generate_tts(start_narration_text, "tts/start.mp3")
    await generate_tts(main_script_text, "tts/main.mp3")
    await generate_tts(end_narration_text, "tts/end.mp3")

    # 4️⃣ Merge intro audio: temple bell + tanpura + start narration
    intro_audio_file = merge_audio([BELL_FILE, TANPURA_FILE, "tts/start.mp3"], "intro.mp3")

    # 5️⃣ Merge outro audio: end narration + tanpura
    outro_audio_file = merge_audio(["tts/end.mp3", TANPURA_FILE], "outro.mp3")

    # 6️⃣ Merge all audio: intro + main script + outro
    final_audio_file = merge_audio([intro_audio_file, "tts/main.mp3", outro_audio_file], "final_audio.mp3")

    # 7️⃣ Create video
    image_clip = ImageClip(RESIZED_IMAGE).set_duration(AudioSegment.from_file(final_audio_file).duration_seconds)
    audio_clip = AudioFileClip(final_audio_file)
    video_clip = image_clip.set_audio(audio_clip)
    video_clip.write_videofile(FINAL_VIDEO, fps=25)
    print(f"✅ Final video created: {FINAL_VIDEO}")

# ================= RUN =================
if __name__ == "__main__":
    asyncio.run(main())