import os
import subprocess
import asyncio
import edge_tts
from PIL import Image, ImageDraw, ImageFont

FINAL_VIDEO = "real_board_coaching.mp4"

STEPS = [

("Topic: Maxima & Minima",
 "Aaj hum Maxima aur Minima topic bilkul basic se padhenge."),

("Given: f(x) = -x² + 4x + 1",
 "Is function ka maximum value nikalna hai."),

("Derivative Rule: d/dx(xⁿ) = n·xⁿ⁻¹",
 "Sabse pehle power rule samajhte hain."),

("d/dx(-x²) = -2x",
 "Minus x square ka derivative minus 2x hota hai."),

("d/dx(4x) = 4",
 "4x ka derivative 4 hota hai."),

("d/dx(1) = 0",
 "Constant ka derivative zero hota hai."),

("f'(x) = -2x + 4",
 "Sabko jodne par first derivative milta hai."),

("For max/min: f'(x) = 0",
 "Maximum ya minimum ke liye derivative zero karte hain."),

("-2x + 4 = 0",
 "Equation solve karte hain."),

("-2x = -4",
 "4 ko dusri side le jaate hain."),

("x = 2",
 "Divide karne par x ki value 2 aati hai."),

("Second derivative f''(x) = -2",
 "Ab second derivative nikaalte hain."),

("-2 < 0 ⇒ Maximum",
 "Negative hone par yeh maximum point hota hai."),

("Put x = 2 in f(x)",
 "Ab function me value put karte hain."),

("f(2) = -(2)² + 4(2) + 1",
 "Substitution karte hain."),

("= -4 + 8 + 1",
 "Square aur multiplication solve karte hain."),

("= 5",
 "Final calculation karte hain."),

("Maximum Value = 5",
 "Isliye function ka maximum value 5 hai."),

("Thank you",
 "Dhanyavaad. Practice karte rahiye.")
]

os.makedirs("frames", exist_ok=True)
os.makedirs("tts", exist_ok=True)


# ---------- CREATE BOARD WITH ACCUMULATED TEXT ----------

def create_frame(all_lines, i):

    W, H = 720, 1280
    img = Image.new("RGB", (W, H), (8, 50, 25))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 42)
    except:
        font = ImageFont.load_default()

    y = 60
    line_height = 58

    for line in all_lines:
        draw.text((60, y), line, fill=(240, 240, 240), font=font)
        y += line_height

    path = f"frames/frame_{i}.png"
    img.save(path)
    return path


# ---------- VOICE ----------

async def generate_voice(text, file):

    tts = edge_tts.Communicate(
        text,
        "hi-IN-MadhurNeural",
        rate="-20%",      # slower
        pitch="-5%"       # deeper clearer tone
    )

    await tts.save(file)


# ---------- MAIN ----------

async def main():

    clips = []
    board_lines = []

    for i, (text, voice) in enumerate(STEPS):

        board_lines.append(text)

        img = create_frame(board_lines, i)
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

    print("🎬 Real board coaching video created:", FINAL_VIDEO)


if __name__ == "__main__":
    asyncio.run(main())