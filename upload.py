import os
import asyncio
from moviepy.editor import ImageClip, AudioFileClip, concatenate_audioclips, CompositeVideoClip
from pydub import AudioSegment
from gtts import gTTS

# ================= CONFIG =================
IMAGE_FILE = "Image1.png"
SCRIPT_FILE = "script.txt"
FINAL_VIDEO = "final_video_episode_1.mp4"
VIDEO_SIZE = (1280, 720)  # YouTube standard HD

TANPURA_FILE = "tanpura.mp3"       # Light tanpura background
BELL_FILE = "temple_bell.mp3"      # Starting temple bell

# ================= FUNCTIONS =================
def load_script_text():
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        return f.read()

def create_narration_audio(text, filename):
    """Convert Hindi text to speech and save as mp3."""
    tts = gTTS(text=text, lang='hi')
    tts.save(filename)
    return filename

def combine_audio_clips(audio_files):
    """Combine multiple audio clips using pydub."""
    combined = AudioSegment.empty()
    for file in audio_files:
        combined += AudioSegment.from_file(file)
    temp_file = "combined_audio.mp3"
    combined.export(temp_file, format="mp3")
    return temp_file

async def main():
    print("🔹 Loading script...")
    script_text = load_script_text()

    # ================= AUDIO =================
    print("🔹 Creating start narration...")
    start_text = "नमस्ते! आपका स्वागत है Sanatan Gyan Dhara चैनल पर। हम रोज़ विष्णु पुराण की नई कथा प्रस्तुत करेंगे।"
    start_audio_file = create_narration_audio(start_text, "start_narration.mp3")

    print("🔹 Creating main narration...")
    main_audio_file = create_narration_audio(script_text, "main_narration.mp3")

    print("🔹 Creating end narration...")
    end_text = "आज का अध्याय समाप्त हुआ। Sanatan Gyan Dhara चैनल को सब्सक्राइब करें और रोज़ नई कथा देखें।"
    end_audio_file = create_narration_audio(end_text, "end_narration.mp3")

    # Combine all audio: tanpura + bell + start + main + end
    print("🔹 Combining audio clips...")
    combined_audio_file = combine_audio_clips([TANPURA_FILE, BELL_FILE, start_audio_file, main_audio_file, end_audio_file])

    # ================= VIDEO =================
    print("🔹 Creating video...")
    image_clip = ImageClip(IMAGE_FILE).set_duration(AudioSegment.from_file(combined_audio_file).duration_seconds)
    image_clip = image_clip.resize(height=VIDEO_SIZE[1]).set_position("center")

    audio_clip = AudioFileClip(combined_audio_file)
    final_clip = image_clip.set_audio(audio_clip)

    print("🔹 Writing final video...")
    final_clip.write_videofile(FINAL_VIDEO, fps=25, codec="libx264", audio_codec="aac")

    print(f"✅ Video created successfully: {FINAL_VIDEO}")

# ================= RUN =================
if __name__ == "__main__":
    asyncio.run(main())