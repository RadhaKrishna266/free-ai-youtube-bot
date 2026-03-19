import os
import subprocess
import asyncio
import edge_tts
from PIL import Image, ImageDraw, ImageFont

FINAL_VIDEO = "derivative_blackboard.mp4"

LINES = [
    "Namaste dosto, aaj hum derivative ka concept samjhenge",

    "Derivative batata hai function kitni fast change ho raha hai",

    "Sabse important rule hai power rule",

    "x ki power n ka derivative hota hai n guna x ki power n minus 1",

    "Example dekhte hain",

    "y barabar x cube plus 2x square plus 5",

    "x cube ka derivative hota hai 3x square",

    "2x square ka derivative hota hai 4x",

    "constant 5 ka derivative zero hota hai",

    "Final answer hota hai 3x square plus 4x",

    "Isi tarah aap kisi bhi polynomial ka derivative nikal sakte hain"
]

os.makedirs("slides", exist_ok=True)
os.makedirs("tts", exist_ok=True)


# ---------- BLACKBOARD SLIDE ----------

def create_blackboard(text, i):

    img = Image.new("RGB", (720, 1280), (15, 40, 25))  # dark green board
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 60)
    except:
        font = ImageFont.load_default()

    draw.multiline_text(
        (60, 350),
        text,
        fill=(245, 245, 245),  # chalk white
        font=font,
        align="center"
    )

    path = f"slides/slide_{i}.png"
    img.save(path)

    return path


# ---------- BETTER HINDI VOICE ----------

async def generate_voice(text, file):

    tts = edge_tts.Communicate(
        text,
        "hi-IN-MadhurNeural",
        rate="-10%"  # slower speech
    )

    await tts.save(file)


# ---------- MAIN ----------

async def main():

    images = []
    audios = []

    for i, line in enumerate(LINES):

        img = create_blackboard(line, i)
        images.append(img)

        audio_file = f"tts/voice_{i}.mp3"
        await generate_voice(line, audio_file)
        audios.append(audio_file)

    # Create video from slides
    with open("slides.txt", "w") as f:
        for img in images:
            f.write(f"file '{img}'\n")
            f.write("duration 6\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "slides.txt",
        "-pix_fmt", "yuv420p",
        "temp_video.mp4"
    ], check=True)

    # Merge audio
    audio_list = "|".join(audios)

    subprocess.run([
        "ffmpeg", "-y",
        "-i", f"concat:{audio_list}",
        "-acodec", "mp3",
        "final_audio.mp3"
    ], check=True)

    # Merge video + audio
    subprocess.run([
        "ffmpeg", "-y",
        "-i", "temp_video.mp4",
        "-i", "final_audio.mp3",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        FINAL_VIDEO
    ], check=True)

    print("🎬 Blackboard video created:", FINAL_VIDEO)


if __name__ == "__main__":
    asyncio.run(main())