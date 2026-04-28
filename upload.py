import os
import random
import base64
import requests
import asyncio
import subprocess
import edge_tts

# =========================
# SETUP
# =========================
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

HF_API_KEY = os.getenv("HF_API_KEY")

API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}

# =========================
# VIRAL COMEDY STORY
# =========================
def generate_story():
    return [
        "गांव में एक बहुत ही आलसी भूत रहता था… नाम था चंपू भूत 👻😂",
        "इतना आलसी कि डराने भी नहीं जाता था, बस पेड़ के नीचे बैठकर WiFi ढूंढता रहता था 📶🤣",
        "एक दिन उसने WhatsApp स्टेटस लगाया - मुझे भी शादी करनी है 💍👻",
        "गांव वालों ने सोचा मजाक है… लेकिन 2 दिन बाद सच में बारात आ गई 😳😂",
        "दुल्हन भूतनी बोली - मुझे भी आलसी लड़का ही चाहिए था 😂",
        "अब दोनों रोज WiFi ढूंढते रहते हैं और गांव का नेटवर्क खत्म कर देते हैं 📶🤣👻"
    ]

# =========================
# TTS
# =========================
async def tts(text, path):
    voice = edge_tts.Communicate(text, "hi-IN-SwaraNeural")
    await voice.save(path)

def create_voice(text):
    path = f"{OUTPUT_DIR}/voice.mp3"
    asyncio.run(tts(text, path))
    return path

# =========================
# IMAGE PROMPT
# =========================
def build_prompt(line):
    return f"""
    Champu Bhoot, cute funny ghost character,
    SAME CHARACTER consistency, white glowing ghost,
    big expressive eyes, comedy expression,
    indian village background, cinematic lighting,
    funny scene: {line},
    pixar style 2D animation, viral youtube shorts style
    """

# =========================
# IMAGE GENERATION (FIXED HF)
# =========================
def generate_image(prompt, i):
    path = f"{OUTPUT_DIR}/img_{i}.jpg"

    try:
        payload = {
            "inputs": prompt,
            "parameters": {"guidance_scale": 7.5}
        }

        r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=90)

        # JSON response (most common)
        if "application/json" in r.headers.get("content-type", ""):
            data = r.json()

            if "images" in data:
                img = base64.b64decode(data["images"][0])
                with open(path, "wb") as f:
                    f.write(img)
                return path

            if "image" in data:
                img = base64.b64decode(data["image"])
                with open(path, "wb") as f:
                    f.write(img)
                return path

        # raw image response
        if r.status_code == 200 and "image" in r.headers.get("content-type", ""):
            with open(path, "wb") as f:
                f.write(r.content)
            return path

    except Exception as e:
        print("Image error:", e)

    # fallback
    print("⚠️ Fallback image used")
    img = requests.get(
        f"https://picsum.photos/1080/1920?random={random.randint(1,9999)}"
    ).content

    with open(path, "wb") as f:
        f.write(img)

    return path

# =========================
# VIDEO CREATION
# =========================
def create_video(images, audio_file):
    print("🎬 Creating video...")

    # rename sequential
    for i, img in enumerate(images):
        os.rename(img, f"{OUTPUT_DIR}/img_{i}.jpg")

    video_path = f"{OUTPUT_DIR}/video.mp4"
    final_path = f"{OUTPUT_DIR}/final.mp4"

    # slideshow
    cmd1 = [
        "ffmpeg", "-y",
        "-framerate", "1/3",
        "-i", f"{OUTPUT_DIR}/img_%d.jpg",
        "-s", "1080x1920",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        video_path
    ]
    subprocess.run(cmd1, check=True)

    # add audio
    cmd2 = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_file,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        final_path
    ]
    subprocess.run(cmd2, check=True)

    return final_path

# =========================
# MAIN
# =========================
def run():
    print("🚀 Starting Viral Shorts Generator...")

    if not HF_API_KEY:
        print("⚠️ HF_API_KEY missing - image quality may fallback")

    lines = generate_story()
    text = " ".join(lines)

    print("🎤 Generating voice...")
    audio = create_voice(text)

    print("🖼 Generating images...")
    images = []
    for i, line in enumerate(lines):
        img = generate_image(build_prompt(line), i)
        images.append(img)

    print("🎬 Creating video...")
    video = create_video(images, audio)

    print("✅ DONE VIDEO:", video)

if __name__ == "__main__":
    run()