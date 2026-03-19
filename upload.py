import os
import subprocess
import asyncio
import edge_tts
from PIL import Image, ImageDraw, ImageFont

FINAL_VIDEO = "coaching_style_class.mp4"

BOARD_TEXT = [
"Topic: Maxima & Minima (Class 12)",
"",
"Maximum → Highest value of function",
"Minimum → Lowest value",
"",
"Critical point when f'(x) = 0",
"",
"Second Derivative Test:",
"f''(x) < 0 → Maximum",
"f''(x) > 0 → Minimum",
"",
"Shortcut for ax² + bx + c:",
"Vertex x = -b / 2a",
"",
"Example:",
"f(x) = -x² + 4x + 1",
"",
"Step 1: f'(x) = -2x + 4",
"Set = 0 → x = 2",
"",
"Step 2: f''(x) = -2 < 0",
"Maximum point",
"",
"Step 3: f(2) = 5",
"",
"Final Answer:",
"Maximum Value = 5",
"",
"JEE Main 2019 — 4 Marks"
]

VOICE_TEXT = """
Namaste students. Aaj hum Class 12 Maths ka important topic Maxima aur Minima padhenge.

Maximum function ka sabse bada value hota hai aur minimum sabse chhota.

Critical point wahan milta hai jahan first derivative zero hoti hai.

Second derivative test se pata chalta hai ki point maximum hai ya minimum.

Quadratic function ke liye vertex formula minus b by 2a fastest method hai.

Ab example solve karte hain.

Derivative zero karne par x ki value 2 aati hai.

Second derivative negative hone se yeh maximum point hai.

Function me x equal to 2 put karne par value 5 aati hai.

Isliye maximum value 5 hai.

Yeh JEE Main 2019 ka 4 marks ka question tha.

Dhanyavaad. Practice karte rahiye.
"""

os.makedirs("tts", exist_ok=True)


# ---------- CREATE BLACKBOARD IMAGE ----------

def create_board():

    W, H = 720, 1280
    img = Image.new("RGB", (W, H), (10, 50, 20))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 38)
    except:
        font = ImageFont.load_default()

    y = 40
    for line in BOARD_TEXT:
        draw.text((40, y), line, fill=(240, 240, 240), font=font)
        y += 48

    img.save("board.png")


# ---------- VOICE ----------

async def generate_voice():

    tts = edge_tts.Communicate(
        VOICE_TEXT,
        "hi-IN-MadhurNeural",
        rate="-8%"
    )

    await tts.save("tts/voice.mp3")


# ---------- MAIN ----------

async def main():

    create_board()
    await generate_voice()

    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", "board.png",
        "-i", "tts/voice.mp3",
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        "-shortest",
        FINAL_VIDEO
    ], check=True)

    print("🎬 Coaching style lecture created:", FINAL_VIDEO)


if __name__ == "__main__":
    asyncio.run(main())