import os
import time
import random
import requests
import asyncio
import subprocess
from pathlib import Path
from PIL import Image
from io import BytesIO
import edge_tts

# ---------------- CONFIG ----------------
SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "audio/tanpura.mp3"

NUM_IMAGES = 5
IMAGE_SIZE = (1280, 720)

HF_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"

PROMPTS = [
    "Lord Vishnu Hindu god blue skin four arms holding shankha chakra gada padma, divine light, ultra realistic, 4k",
    "Lord Vishnu resting on Ananta Shesha cosmic ocean, glowing aura, devotional art, high detail",
    "Vishnu standing in Vaikuntha, golden crown, lotus flowers, celestial background, realistic painting",
    "Hindu god Vishnu divine portrait, blue complexion, peaceful face, spiritual light, 4k realism",
    "Lord Vishnu with Lakshmi blessing devotees, sacred atmosphere, temple art style, ultra detailed"
]

NEGATIVE_PROMPT = "blurry, distorted, extra limbs, low quality, cartoon, anime"

# ---------------- SETUP ----------------
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ---------------- UTILS ----------------
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ---------------- AI IMAGE GENERATION ----------------
def generate_image(prompt, index):
    payload = {"inputs": f"{prompt}. Negative prompt: {NEGATIVE_PROMPT}"}
    response = requests.post(HF_API_URL, json=payload, timeout=120)
    if response.status_code != 200:
        raise RuntimeError(f"Image generation failed: {response.text}")
    image = Image.open(BytesIO(response.content)).convert("RGB")
    image.thumbnail(IMAGE_SIZE, Image.Resampling.LANCZOS)
    path = os.path.join(IMAGE_DIR, f"{index:03d}.jpg")
    image.save(path)
    print(f"✅ Saved {path}")
    return path

def generate_images(count):
    paths = []
    for i in range(count):
        prompt = random.choice(PROMPTS)
        print(f"🎨 Generating Vishnu image {i+1}/{count}")
        paths.append(generate_image(prompt, i))
        time.sleep(5)  # rate-limit safety
    return paths

# ---------------- AUDIO ----------------
async def gen_audio(text, idx):
    out = f"{AUDIO_DIR}/{idx:03d}.mp3"
    tts = edge_tts.Communicate(text=text, voice="hi-IN-MadhurNeural")
    await tts.save(out)

def generate_audio(blocks):
    async def runner():
        for i, t in enumerate(blocks):
            await gen_audio(t, i)
    asyncio.run(runner())

# ---------------- VIDEO CREATION ----------------
def create_video(images, blocks_count):
    clips = []

    for i in range(blocks_count):
        img = images[i % len(images)]
        aud = f"{AUDIO_DIR}/{i:03d}.mp3"
        clip = f"{VIDEO_DIR}/{i:03d}.mp4"

        run([
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", img,
            "-i", aud,
            "-i", TANPURA_FILE,
            "-filter_complex",
            "[2:a]volume=0.2[a2];[1:a][a2]amix=inputs=2:duration=first[a]",
            "-map", "0:v",
            "-map", "[a]",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            clip
        ])
        clips.append(clip)

    # Concatenate all clips
    with open("list.txt", "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "list.txt",
        "-c", "copy",
        FINAL_VIDEO
    ])

# ---------------- MAIN ----------------
def main():
    # Read script
    blocks = Path(SCRIPT_FILE).read_text(encoding="utf-8").split("\n\n")
    intro = "नमस्कार। स्वागत है आप सभी का Sanatan Gyan Dhara श्रृंखला में। आज हम आपके लिए Vishnu Purana का पहला एपिसोड लाए हैं।"
    outro = "\n\n🙏 अगर आपको यह वीडियो पसंद आया हो, तो कृपया लाइक, शेयर और सब्सक्राइब जरूर करें। हर दिन एक नया एपिसोड आएगा।"
    blocks.insert(0, intro)
    blocks.append(outro)

    # Generate images
    print("🕉️ Generating Vishnu images automatically...")
    image_files = generate_images(NUM_IMAGES)

    # Generate audio
    print("🔊 Generating audio blocks...")
    generate_audio(blocks)

    # Create video
    print("🎬 Creating video...")
    create_video(image_files, len(blocks))

    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()