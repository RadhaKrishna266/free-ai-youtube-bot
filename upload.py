import os
import subprocess
import asyncio
import edge_tts
from PIL import Image, ImageDraw, ImageFont
import random

FINAL_VIDEO = "derivative_jee_complete.mp4"

LINES = [
    "Namaste dosto, aaj hum derivative ka complete JEE concept samjhenge",

    "Derivative batata hai function kitni fast change ho raha hai",
    "Graph par slope bhi derivative se hi milti hai",

    "Sabse important rule hai power rule",
    "x ki power n ka derivative hota hai n guna x ki power n minus 1",

    "Trigonometry formulas bhi important hain",
    "sin x ka derivative hota hai cos x",
    "cos x ka derivative hota hai minus sin x",
    "tan x ka derivative hota hai sec square x",

    "Exponential functions me e ki power x ka derivative e ki power x hota hai",
    "ln x ka derivative hota hai 1 by x",

    "Ab fast tricks dekhte hain",
    "Power ko multiply karo aur power me se ek minus karo",
    "Constant ka derivative hamesha zero hota hai",
    "Polynomial me har term ko alag differentiate karo",

    "Ab JEE level example solve karte hain",

    "y barabar x power 4 plus 3x cube minus 5x plus 7",

    "x power 4 ka derivative 4x cube",
    "3x cube ka derivative 9x square",
    "minus 5x ka derivative minus 5",
    "constant 7 ka derivative zero",

    "Final answer hota hai 4x cube plus 9x square minus 5",

    "Isi method se aap JEE ke questions jaldi solve kar sakte hain",

    "Video pasand aaye to like aur subscribe zaroor karein"
]

os.makedirs("slides", exist_ok=True)
os.makedirs("tts", exist_ok=True)


def create_slide(text, i):

    bg = (
        random.randint(70, 200),
        random.randint(70, 200),
        random.randint(70, 200),
    )

    img = Image.new("RGB", (720, 1280), bg)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 60)
    except:
        font = ImageFont.load_default()

    draw.multiline_text((60, 450), text, fill="white", font=font, align="center")

    path = f"slides/slide_{i}.png"
    img.save(path)

    return path


async def generate_voice(text, file):

    tts = edge_tts.Communicate(text, "hi-IN-MadhurNeural")
    await tts.save(file)


async def main():

    images = []
    audios = []

    for i, line in enumerate(LINES):

        img = create_slide(line, i)
        images.append(img)

        audio_file = f"tts/voice_{i}.mp3"
        await generate_voice(line, audio_file)
        audios.append(audio_file)

    with open("slides.txt", "w") as f:
        for img in images:
            f.write(f"file '{img}'\n")
            f.write("duration 6\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "slides.txt",
        "-vsync", "vfr",
        "-pix_fmt", "yuv420p",
        "temp_video.mp4"
    ], check=True)

    audio_list = "|".join(audios)

    subprocess.run([
        "ffmpeg", "-y",
        "-i", f"concat:{audio_list}",
        "-acodec", "mp3",
        "final_audio.mp3"
    ], check=True)

    subprocess.run([
        "ffmpeg", "-y",
        "-i", "temp_video.mp4",
        "-i", "final_audio.mp3",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        FINAL_VIDEO
    ], check=True)

    print("🎬 JEE derivative video created:", FINAL_VIDEO)


if __name__ == "__main__":
    asyncio.run(main())