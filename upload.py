import os
import subprocess
import asyncio
import edge_tts
from PIL import Image, ImageDraw, ImageFont

FINAL_VIDEO = "jee_coaching_video.mp4"

STEPS = [

("Topic: Maxima & Minima",
 "Namaste. Aaj hum Maxima aur Minima concept bilkul aasaan tareeke se padhenge."),

("Key Idea: f'(x) = 0 at extreme point",
 "Maximum ya minimum point par derivative zero hota hai."),

("Second derivative test:",
 "Agar second derivative negative ho to maximum hota hai."),

("Given Question (JEE Main 2019 — 4 marks)",
 "Ab JEE Main 2019 ka question solve karte hain."),

("f(x) = -x² + 4x + 1",
 "Is function ka maximum value nikalna hai."),

("Step 1: First derivative",
 "Sabse pehle derivative nikaalte hain."),

("f'(x) = -2x + 4",
 "Power rule apply karne par derivative milta hai."),

("Step 2: Set f'(x) = 0",
 "Maximum ya minimum ke liye derivative zero karte hain."),

("-2x + 4 = 0",
 "Equation solve karte hain."),

("x = 2",
 "x ki value 2 milti hai."),

("Step 3: Second derivative",
 "Ab second derivative nikaalte hain."),

("f''(x) = -2 < 0",
 "Negative hone par yeh maximum point hai."),

("Step 4: Find value",
 "Ab x = 2 ko function me put karte hain."),

("f(2) = -4 + 8 + 1",
 "Calculation karte hain."),

("Maximum Value = 5",
 "Is function ka maximum value 5 hai."),

("Quick Trick:",
 "Downward parabola ka vertex hi maximum hota hai."),

("Practice Question:",
 "Find maximum of f(x) = -x² + 6x"),

("Thank you",
 "Aise hi practice karte rahiye. Aap zarur succeed karenge.")
]

os.makedirs("frames", exist_ok=True)
os.makedirs("tts", exist_ok=True)


def create_frame(lines, i):

    W, H = 720, 1280
    img = Image.new("RGB", (W, H), (15, 60, 35))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 42)
    except:
        font = ImageFont.load_default()

    y = 60

    for line in lines:
        draw.text((60, y), line, fill=(245, 245, 245), font=font)
        y += 55

    path = f"frames/frame_{i}.png"
    img.save(path)
    return path


async def generate_voice(text, file):

    tts = edge_tts.Communicate(
        text,
        "hi-IN-SwaraNeural",
        rate="-18%",
        pitch="-2Hz"
    )

    await tts.save(file)


async def main():

    clips = []
    board = []

    for i, (text, voice) in enumerate(STEPS):

        board.append(text)

        img = create_frame(board, i)
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

    print("🎬 Coaching video created:", FINAL_VIDEO)


if __name__ == "__main__":
    asyncio.run(main())