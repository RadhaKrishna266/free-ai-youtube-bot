import os
import subprocess
import asyncio
import edge_tts
from PIL import Image, ImageDraw, ImageFont

FINAL_VIDEO = "true_foundation_class.mp4"

LINES = [

    # ---------- INTRO ----------
    ("Topic: Maxima & Minima (Basic Level)",
     "Aaj hum bilkul basic level se Maxima aur Minima padhenge."),

    # ---------- FUNCTION ----------
    ("Given: f(x) = -x² + 4x + 1",
     "Is function ka maximum value nikalna hai."),

    # ---------- DERIVATIVE RULE ----------
    ("Derivative Rule: d/dx(xⁿ) = n·xⁿ⁻¹",
     "Sabse pehle power rule samajhte hain."),

    ("x² → 2x",
     "Power 2 neeche aata hai aur power ek kam ho jati hai."),

    ("x → 1",
     "x ki power 1 hoti hai isliye derivative 1 hota hai."),

    ("Constant → 0",
     "Koi bhi constant number ka derivative zero hota hai."),

    # ---------- APPLY RULE ----------
    ("Term 1: -x² → -2x",
     "Power rule apply karne par minus x square ka derivative minus 2x aata hai."),

    ("Term 2: 4x → 4",
     "4x ka derivative sirf 4 hota hai."),

    ("Term 3: 1 → 0",
     "Constant 1 ka derivative zero hota hai."),

    ("So f'(x) = -2x + 4",
     "Sab terms jodne par first derivative milta hai."),

    # ---------- CRITICAL POINT ----------
    ("For max/min: f'(x) = 0",
     "Maximum ya minimum ke liye derivative zero karte hain."),

    ("-2x + 4 = 0",
     "Equation solve karte hain."),

    ("-2x = -4 → x = 2",
     "Dono side divide karne par x ki value 2 aati hai."),

    # ---------- SECOND DERIVATIVE ----------
    ("Second derivative f''(x) = -2",
     "Ab second derivative nikaalte hain."),

    ("-2 < 0 ⇒ Maximum",
     "Negative hone par yeh maximum point hota hai."),

    # ---------- VALUE ----------
    ("Put x = 2 in f(x)",
     "Ab function me value put karte hain."),

    ("f(2) = -(2)² + 4(2) + 1",
     "Substitution karte hain."),

    ("= -4 + 8 + 1",
     "Calculation solve karte hain."),

    ("= 5",
     "Final result milta hai."),

    ("Maximum Value = 5",
     "Isliye function ka maximum value 5 hai."),

    ("Thank you — Keep Learning ✨",
     "Dhanyavaad. Practice karte rahiye.")
]

os.makedirs("frames", exist_ok=True)
os.makedirs("tts", exist_ok=True)


def create_frame(text, i):

    W, H = 720, 1280
    img = Image.new("RGB", (W, H), (10, 40, 25))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 46)
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

    y = (H - len(lines) * 65) // 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (W - bbox[2]) // 2
        draw.text((x, y), line, fill=(240, 240, 240), font=font)
        y += 65

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

    print("🎬 True foundation video created:", FINAL_VIDEO)


if __name__ == "__main__":
    asyncio.run(main())