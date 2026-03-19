import os
import subprocess
import asyncio
import edge_tts
from PIL import Image, ImageDraw, ImageFont

FINAL_VIDEO = "maxima_minima_jee.mp4"

LINES = [
    "Namaste dosto, aaj hum applications of derivatives me maxima aur minima samjhenge",

    "Maxima matlab function ka highest value aur minima matlab lowest value",

    "Maximum ya minimum point par derivative zero hoti hai",

    "Isliye sabse pehle first derivative ko zero ke equal karte hain",

    "Uske baad second derivative test se pata chalta hai maximum hai ya minimum",

    "Second derivative negative ho to maximum aur positive ho to minimum",

    "Ab ek JEE Main 2019 ka question dekhte hain, 4 marks ka question",

    "Function diya hai minus x square plus 4x plus 1",

    "Sabse pehle first derivative nikalte hain, jo hoti hai minus 2x plus 4",

    "Isko zero ke equal karte hain, to x ki value aati hai 2",

    "Ab second derivative nikalte hain, jo hoti hai minus 2",

    "Ye negative hai, isliye yahan maximum milega",

    "Ab function me x barabar 2 put karte hain",

    "Answer aata hai 5",

    "Isliye function ka maximum value 5 hai",

    "Isi method se aap JEE ke maxima minima questions fast solve kar sakte hain"
]

os.makedirs("slides", exist_ok=True)
os.makedirs("tts", exist_ok=True)


# -------- BLACKBOARD STYLE --------

def create_slide(text, i):

    width, height = 720, 1280
    img = Image.new("RGB", (width, height), (15, 40, 25))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 54)
    except:
        font = ImageFont.load_default()

    margin = 60
    max_width = width - 2 * margin

    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = current + " " + word if current else word
        w, h = draw.textbbox((0, 0), test, font=font)[2:]
        if w <= max_width:
            current = test
        else:
            lines.append(current)
            current = word

    if current:
        lines.append(current)

    total_height = len(lines) * 80
    y = (height - total_height) // 2

    for line in lines:
        w, h = draw.textbbox((0, 0), line, font=font)[2:]
        x = (width - w) // 2
        draw.text((x, y), line, fill=(245, 245, 245), font=font)
        y += 80

    path = f"slides/slide_{i}.png"
    img.save(path)
    return path


# -------- VOICE --------

async def generate_voice(text, file):

    tts = edge_tts.Communicate(
        text,
        "hi-IN-MadhurNeural",
        rate="-12%"
    )

    await tts.save(file)


# -------- MAIN --------

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

    print("🎬 JEE maxima-minima video created:", FINAL_VIDEO)


if __name__ == "__main__":
    asyncio.run(main())