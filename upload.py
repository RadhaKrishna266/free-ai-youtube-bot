import os
import asyncio
from pydub import AudioSegment
import edge_tts
import subprocess

# ================= FILE PATHS =================
IMAGE_FILE = "Image1.png"
RESIZED_IMAGE = "Image1_resized.png"
SCRIPT_FILE = "script.txt"

TANPURA_FILE = "audio/tanpura.mp3"
FINAL_VIDEO = "final_video_episode_1.mp4"

# ================= RESIZE IMAGE =================
def resize_image(input_file, output_file, width=1280, height=720):
    subprocess.run([
        "ffmpeg", "-y", "-i", input_file,
        "-vf", f"scale={width}:{height}",
        output_file
    ], check=True)
    print("✅ Image resized successfully")

# ================= GENERATE TTS =================
async def generate_tts(text, output_file):
    communicate = edge_tts.Communicate(text, "hi-IN-SwaraNeural")
    await communicate.save(output_file)
    print(f"🎤 TTS generated: {output_file}")

# ================= READ SCRIPT =================
def get_script_text(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()

# ================= MERGE AUDIO =================
def merge_audio(start_tanpura_file, main_tts_files, end_tanpura_file, om_narayan_file, output_file):
    # Load and trim start/end tanpura
    start_tanpura = AudioSegment.from_file(start_tanpura_file)[:100]  # 0.10 sec
    end_tanpura = AudioSegment.from_file(end_tanpura_file)[:1000]     # 1 sec

    # Load main narration files
    final_audio = start_tanpura
    for file in main_tts_files:
        final_audio += AudioSegment.from_file(file)
    # Add 1 sec end tanpura + om namo narayan
    final_audio += end_tanpura + AudioSegment.from_file(om_narayan_file)

    final_audio.export(output_file, format="mp3")
    return output_file

# ================= CREATE VIDEO =================
def create_video(image_file, audio_file, output_file):
    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_file,
        "-i", audio_file,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_file
    ], check=True)
    print(f"✅ Final video created: {output_file}")

# ================= MAIN =================
async def main():
    # 1️⃣ Resize image
    resize_image(IMAGE_FILE, RESIZED_IMAGE)

    # 2️⃣ Prepare narrations
    start_narration_text = (
        "नमस्कार। आप देख रहे हैं सनातन ज्ञान धारा। "
        "हम प्रतिदिन विष्णु पुराण के वीडियो अपलोड करेंगे।"
    )
    main_script_text = get_script_text(SCRIPT_FILE)
    end_narration_text = (
        "धन्यवाद। आपने सनातन ज्ञान धारा देखा। "
        "हम प्रतिदिन विष्णु पुराण के वीडियो अपलोड करेंगे।"
    )
    om_narayan_text = "ॐ नमो नारायण"

    # 3️⃣ Generate TTS files
    os.makedirs("tts", exist_ok=True)
    await generate_tts(start_narration_text, "tts/start.mp3")
    await generate_tts(main_script_text, "tts/main.mp3")
    await generate_tts(end_narration_text, "tts/end.mp3")
    await generate_tts(om_narayan_text, "tts/om_narayan.mp3")

    # 4️⃣ Merge all audio with short tanpura at start and end
    final_audio_file = merge_audio(
        TANPURA_FILE,
        ["tts/start.mp3", "tts/main.mp3", "tts/end.mp3"],
        TANPURA_FILE,
        "tts/om_narayan.mp3",
        "final_audio.mp3"
    )

    # 5️⃣ Create final video
    create_video(RESIZED_IMAGE, final_audio_file, FINAL_VIDEO)

# ================= RUN =================
if __name__ == "__main__":
    asyncio.run(main())