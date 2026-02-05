import os
import asyncio
from pathlib import Path
from pydub import AudioSegment
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip

# File paths
IMAGE_FILE = "Image1.png"
SCRIPT_FILE = "script.txt"
OUTPUT_VIDEO = "final_video.mp4"
TANPURA_FILE = "tanpura.mp3"      # Light tanpura background
BELL_FILE = "temple_bell.mp3"     # Starting temple bell

# Read main narration from script.txt
with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
    main_script = f.read().strip()

# Start and End narration text
START_TEXT = "स्वागत है Sanatan Gyan Dhara में — यहाँ हम प्रतिदिन विष्णु पुराण की कहानियाँ अपलोड करते हैं।"
END_TEXT = "धन्यवाद Sanatan Gyan Dhara देखने के लिए। अगले विष्णु पुराण अध्याय के लिए जुड़े रहें।"

# Function to convert text to Hindi speech
def text_to_speech(text, filename):
    tts = gTTS(text=text, lang="hi")
    tts.save(filename)

# Generate start, main, and end narration audios
text_to_speech(START_TEXT, "start.mp3")
text_to_speech(main_script, "main.mp3")
text_to_speech(END_TEXT, "end.mp3")

# Combine audio tracks with fade-in/out
def combine_audio():
    # Load audio segments
    tanpura = AudioSegment.from_file(TANPURA_FILE)
    bell = AudioSegment.from_file(BELL_FILE)
    start_narration = AudioSegment.from_file("start.mp3")
    main_narration = AudioSegment.from_file("main.mp3")
    end_narration = AudioSegment.from_file("end.mp3")

    # Apply fade-in/out to bell and tanpura
    bell = bell.fade_in(1000).fade_out(1000)  # 1 second fade
    tanpura = tanpura.fade_in(2000).fade_out(2000)  # 2 second fade

    # Calculate total duration of narration + bell
    total_duration = len(bell) + len(start_narration) + len(main_narration) + len(end_narration)

    # Loop tanpura to match total duration
    tanpura_looped = tanpura * ((total_duration // len(tanpura)) + 1)
    tanpura_final = tanpura_looped[:total_duration]

    # Overlay other audios
    combined = tanpura_final.overlay(bell, position=0)
    combined = combined.overlay(start_narration, position=len(bell))
    combined = combined.overlay(main_narration, position=len(bell)+len(start_narration))
    combined = combined.overlay(end_narration, position=len(bell)+len(start_narration)+len(main_narration))
    
    # Export final audio
    combined.export("final_audio.mp3", format="mp3")

combine_audio()

# Create video from image with audio
audio_clip = AudioFileClip("final_audio.mp3")
video_clip = ImageClip(IMAGE_FILE, duration=audio_clip.duration).set_audio(audio_clip)
video_clip.write_videofile(OUTPUT_VIDEO, fps=1)  # fps=1 is enough for single image