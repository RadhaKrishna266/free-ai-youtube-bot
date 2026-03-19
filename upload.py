import os
import subprocess
import asyncio
import edge_tts
from PIL import Image, ImageDraw, ImageFont

FINAL_VIDEO = "jee_teaching_style.mp4"

# -------- SCREEN TEXT (ONLY KEY POINTS) --------

SLIDES = [
    "APPLICATION OF DERIVATIVES\nMaxima & Minima",

    "Maximum = Highest value\nMinimum = Lowest value",

    "Condition:\nf'(x) = 0",

    "Second Derivative Test:\nf''(x) < 0 → Maximum\nf''(x) > 0 → Minimum",

    "JEE Main 2019\n4 Marks Question",

    "f(x) = -x² + 4x + 1",

    "Step 1:\nf'(x) = -2x + 4\nSet = 0 → x = 2",

    "Step 2:\nf''(x) = -2 < 0\nMaximum point",

    "Step 3:\nf(2) = 5",

    "Maximum Value = 5"
]

# -------- AUDIO SCRIPT (FULL EXPLANATION) --------

AUDIO_LINES = [
    "Aaj hum applications of derivatives me maxima aur minima samjhenge.",
    "Maximum function ka highest value hota hai aur minimum lowest value hota hai.",
    "Maximum ya minimum point par first derivative zero hoti hai.",
    "Second derivative se pata chalta hai maximum hai ya minimum.",
    "Ab JEE Main 2019 ka 4 marks ka question dekhte hain.",
    "Function diya hai minus x square plus 4x plus 1.",
    "Sabse pehle first derivative nikalte hain aur zero ke equal karte hain jisse x ki value 2 aati hai.",
    "Second derivative negative hai isliye yeh maximum point hai.",
    "Ab function me x equal to 2 put karte hain.",
    "Isliye function ka maximum value 5 hai."
]

os.makedirs("slides", exist_ok=True)
os.makedirs("tts", exist_ok=True)


# -------- CREATE TEACHING STYLE SLIDE --------

def create_slide(text, i):

    width, height = 720, 1280
    img = Image.new("RGB", (width, height), (15, 40, 25))
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 64)
        body_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 52)
    except:
        title_font = body_font = ImageFont.load_default()

    lines = text.split("\n")

    y = 300
    for j, line in enumerate(lines):
        font = title_font if i == 0 else body_font
        w, h = draw.textbbox((0, 0), line, font=font)[2:]
        x = (width - w) // 2
        draw.text((x, y), line, fill=(245, 245, 245), font=font)
        y += 120

    path = f"slides/slide_{i}.png"
    img.save(path)
    return path


# -------- GENERATE VOICE --------

async def generate_voice(text, file):

    tts = edge_tts.Communicate(
        text,
        "hi-IN-MadhurNeural",
        rate="-10%"
    )

    await tts.save(file)


# -------- MAIN --------

async def main():

    videos = []

    for i in range(len(SLIDES)):

        img = create_slide(SLIDES[i], i)

        audio_file = f"tts/voice_{i}.mp3"
        await generate_voice(AUDIO_LINES[i], audio_file)

        output_clip = f"clip_{i}.mp4"

        # Create video clip synced with audio
        subprocess.run([
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", img,
            "-i", audio_file,
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            output_clip
        ], check=True)

        videos.append(output_clip)

    # Merge all clips
    with open("concat.txt", "w") as f:
        for v in videos:
            f.write(f"file '{v}'\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "concat.txt",
        "-c", "copy",
        FINAL_VIDEO
    ], check=True)

    print("🎬 Teaching-style video created:", FINAL_VIDEO)


if __name__ == "__main__":
    asyncio.run(main())