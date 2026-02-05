import subprocess
from pydub import AudioSegment
import asyncio
from edge_tts import Communicate

# ================= FILES =================
image_file = "Image1.png"
temple_bell = "temple_bell.mp3"
tanpura_bg = "tanpura.mp3"
script_file = "script.txt"
final_video = "final_video_episode_1.mp4"

# ================= FIX IMAGE =================
# Make sure the image is 1280x720
subprocess.run([
    "ffmpeg", "-y", "-i", image_file, "-vf", "scale=1280:720", image_file
])

# ================= LOAD SCRIPT =================
with open(script_file, "r", encoding="utf-8") as f:
    main_narration_text = f.read().strip()

# ================= START / END NARRATION =================
start_text = "स्वागत है Sanatan Gyan Dhara चैनल पर। हम Vishnu Purana की कथा रोज़ाना प्रस्तुत करेंगे।"
end_text = "धन्यवाद Sanatan Gyan Dhara चैनल देखने के लिए। अगले अध्याय के लिए जुड़े रहें।"

# Combine start, main, end
full_narration_text = f"{start_text}\n\n{main_narration_text}\n\n{end_text}"

# ================= GENERATE TTS =================
async def generate_tts(text, output_file):
    communicate = Communicate(text, "hi-IN-AriaNeural")
    await communicate.save(output_file)

narration_file = "narration.mp3"
asyncio.run(generate_tts(full_narration_text, narration_file))

# ================= COMBINE AUDIO =================
bell = AudioSegment.from_file(temple_bell).fade_in(2000).fade_out(2000)  # 2 sec fade in/out
narration = AudioSegment.from_file(narration_file).fade_in(2000).fade_out(2000)
tanpura = AudioSegment.from_file(tanpura_bg)

# Repeat tanpura to match narration length
while len(tanpura) < len(narration):
    tanpura += tanpura
tanpura = tanpura[:len(narration)]

# Overlay narration on tanpura and prepend temple bell
combined_audio = bell + (narration.overlay(tanpura))
combined_audio.export("final_audio.mp3", format="mp3")

# ================= CREATE VIDEO =================
subprocess.run([
    "ffmpeg", "-y",
    "-loop", "1",
    "-i", image_file,
    "-i", "final_audio.mp3",
    "-c:v", "libx264",
    "-tune", "stillimage",
    "-c:a", "aac",
    "-b:a", "192k",
    "-pix_fmt", "yuv420p",
    "-shortest",
    final_video
])

print(f"✅ Video created with fade-in/out: {final_video}")