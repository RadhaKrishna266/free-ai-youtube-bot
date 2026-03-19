import os
import subprocess
import asyncio
import edge_tts
from PIL import Image, ImageDraw, ImageFont

FINAL_VIDEO = "jee_long_coaching_video.mp4"

LINES = [

    # ---------- TOPIC ----------
    ("Topic: Maxima & Minima (Class 12)", 
     "Aaj hum Class 12 Maths ka important topic Maxima aur Minima detail me padhenge."),

    ("Maximum → Highest value", 
     "Maximum function ka sabse bada value hota hai."),

    ("Minimum → Lowest value", 
     "Minimum function ka sabse chhota value hota hai."),

    ("Critical point jab f'(x) = 0", 
     "Critical point wahan milta hai jahan first derivative zero hoti hai."),

    ("Second Derivative Test", 
     "Second derivative se pata chalta hai maximum hai ya minimum."),

    ("f''(x) < 0 → Maximum", 
     "Negative hone par point maximum hota hai."),

    ("f''(x) > 0 → Minimum", 
     "Positive hone par point minimum hota hai."),

    ("Shortcut: ax² + bx + c → x = -b / 2a", 
     "Quadratic function ke liye vertex formula fastest method hai."),

    # ---------- EXAMPLE ----------
    ("Example: f(x) = -x² + 4x + 1", 
     "Ab ek example solve karte hain."),

    ("Step 1: f'(x) = -2x + 4", 
     "Derivative nikaalte hain."),

    ("Set = 0 → x = 2", 
     "Derivative zero karne par x ki value 2 aati hai."),

    ("Step 2: f''(x) = -2 < 0", 
     "Second derivative negative hai isliye maximum point hai."),

    ("Step 3: f(2) = 5", 
     "Function me value put karte hain."),

    ("Maximum Value = 5", 
     "Isliye maximum value 5 hai."),

    # ---------- JEE PYQ 1 ----------
    ("JEE Main 2019 — 4 Marks", 
     "Ab JEE Main 2019 ka previous year question dekhte hain."),

    ("Find MAXIMUM of f(x) = -x² + 4x + 1", 
     "Hume maximum value find karna hai."),

    ("Answer = 5", 
     "Iska answer 5 hai."),

    # ---------- JEE PYQ 2 ----------
    ("JEE Main 2021 — 4 Marks", 
     "Ab JEE Main 2021 ka question dekhte hain."),

    ("Find MINIMUM of f(x) = x² - 6x + 10", 
     "Isme minimum value nikalni hai."),

    ("x = 3 → Minimum point", 
     "Vertex formula se x ki value 3 aati hai."),

    ("Minimum Value = 1", 
     "Final minimum value 1 hai."),

    # ---------- JEE PYQ 3 ----------
    ("JEE Main 2022 — 4 Marks", 
     "Ab JEE Main 2022 ka question."),

    ("Find maximum of f(x) = -x² + 6x - 5", 
     "Maximum value nikalte hain."),

    ("x = 3 → Maximum point", 
     "Vertex se x ki value 3 aati hai."),

    ("Maximum Value = 4", 
     "Final answer 4 hai."),

    ("Thank you — Practice PYQs ✨", 
     "Dhanyavaad. Aur bhi previous year questions practice kariye.")
]

os.makedirs("frames", exist_ok=True)
os.makedirs("tts", exist_ok=True)


def create_frame(text, i):

    W, H = 720, 1280
    img = Image.new("RGB", (W, H), (12, 45, 25))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 48)
    except:
        font = ImageFont.load_default()

    margin = 60
    max_width = W - 2 * margin

    words = text.split()
    lines = []
    current = ""

    for w in words:
        test = current + " " + w if current else w
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] <= max_width:
            current = test
        else:
            lines.append(current)
            current = w
    lines.append(current)

    y = (H - len(lines) * 70) // 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (W - bbox[2]) // 2
        draw.text((x, y), line, fill=(240, 240, 240), font=font)
        y += 70

    path = f"frames/frame_{i}.png"
    img.save(path)
    return path


async def generate_voice(text, file):

    tts = edge_tts.Communicate(text, "hi-IN-MadhurNeural", rate="-8%")
    await tts.save(file)


async def main():

    clips = []

    for i, (text, voice) in enumerate(LINES):

        img = create_frame(text, i)
        audio_file = f"tts/voice_{i}.mp3"

        await generate_voice(voice, audio_file)

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

    print("🎬 Long coaching video created:", FINAL_VIDEO)


if __name__ == "__main__":
    asyncio.run(main())