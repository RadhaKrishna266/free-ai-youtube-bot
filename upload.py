import os
import subprocess
import asyncio
import edge_tts
from PIL import Image, ImageDraw, ImageFont

FINAL_VIDEO = "jee_complete_solution.mp4"

SLIDES = [
    "JEE Main 2019 — 4 Marks\n\nFind the MAXIMUM value of:\nf(x) = -x² + 4x + 1",

    "Step 1:\nFirst derivative nikaalte hain",

    "f'(x) = -2x + 4\nMaximum ke liye f'(x) = 0",

    "-2x + 4 = 0\nx = 2",

    "Step 2:\nSecond derivative test",

    "f''(x) = -2\nSince < 0 → Maximum",

    "Step 3:\nFunction me x = 2 put karte hain",

    "f(2) = -(2)² + 4(2) + 1 = 5",

    "Final Answer:\nMaximum Value = 5",

    "Thank you\nPractice more PYQs ✨"
]

AUDIO_LINES = [
    "JEE Main 2019 ka 4 marks ka question hai. Hume function ka maximum value find karna hai.",
    "Sabse pehle first derivative nikaalte hain.",
    "Maximum ya minimum point par first derivative zero hoti hai.",
    "Equation solve karne par x ki value 2 aati hai.",
    "Ab second derivative test lagate hain.",
    "Second derivative negative hai, isliye yeh maximum point hai.",
    "Ab function me x equal to 2 put karte hain.",
    "Calculation karne par value 5 aati hai.",
    "Isliye function ka maximum value 5 hai.",
    "Dhanyavaad. Aise hi previous year questions practice karte rahiye."
]

os.makedirs("slides", exist_ok=True)
os.makedirs("tts", exist_ok=True)


# ---------- SAFE SLIDE ----------

def create_slide(text, i):

    W, H = 720, 1280
    img = Image.new("RGB", (W, H), (15, 40, 25))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 52)
    except:
        font = ImageFont.load_default()

    margin = 50
    max_width = W - 2 * margin

    lines = []
    for para in text.split("\n"):
        words = para.split()
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
        lines.append("")

    y = (H - len(lines) * 70) // 2

    for line in lines:
        w, h = draw.textbbox((0, 0), line, font=font)[2:]
        x = (W - w) // 2
        draw.text((x, y), line, fill=(245, 245, 245), font=font)
        y += 70

    path = f"slides/slide_{i}.png"
    img.save(path)
    return path


# ---------- VOICE ----------

async def generate_voice(text, file):

    tts = edge_tts.Communicate(
        text,
        "hi-IN-MadhurNeural",
        rate="-10%"
    )

    await tts.save(file)


# ---------- MAIN ----------

async def main():

    clips = []

    for i in range(len(SLIDES)):

        img = create_slide(SLIDES[i], i)

        audio_file = f"tts/voice_{i}.mp3"
        await generate_voice(AUDIO_LINES[i], audio_file)

        clip = f"clip_{i}.mp4"

        subprocess.run([
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", img,
            "-i", audio_file,
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-pix_fmt", "yuv420p",
            "-shortest",
            clip
        ], check=True)

        clips.append(clip)

    with open("concat.txt", "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "concat.txt",
        "-c", "copy",
        FINAL_VIDEO
    ], check=True)

    print("🎬 JEE solution video created:", FINAL_VIDEO)


if __name__ == "__main__":
    asyncio.run(main())