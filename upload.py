import os
import subprocess
import asyncio
import requests
from pathlib import Path
from PIL import Image
import edge_tts
import time
import urllib.parse

# ================= CONFIG =================
SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ================= UTILS =================
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ================= AI IMAGE GENERATION =================
def generate_ai_image(prompt, out_path):
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&seed={int(time.time())}"

    for attempt in range(3):  # max 3 tries
        try:
            r = requests.get(url, timeout=20)
            r.raise_for_status()
            with open(out_path, "wb") as f:
                f.write(r.content)
            return
        except Exception as e:
            print(f"⚠ Image retry {attempt+1}/3 failed:", e)
            time.sleep(2)

    raise RuntimeError("❌ AI image generation failed completely")

def generate_images(blocks):
    print("🖼 Generating AI Vishnu Purana images...")

    prompts = []

    # First image: Vishnu Purana book (MANDATORY)
    prompts.append(
        "ancient Vishnu Purana manuscript book on lotus altar, divine golden light, temple background, ultra detailed, devotional art"
    )

    avatars = [
        "Matsya avatar of Vishnu",
        "Kurma avatar of Vishnu",
        "Varaha avatar of Vishnu",
        "Narasimha avatar of Vishnu",
        "Vamana avatar of Vishnu",
        "Parashurama avatar of Vishnu",
        "Rama avatar of Vishnu",
        "Krishna avatar of Vishnu",
        "Buddha avatar of Vishnu",
        "Kalki avatar of Vishnu"
    ]

    for i in range(1, len(blocks)):
        avatar = avatars[i % len(avatars)]
        prompts.append(
            f"{avatar}, Vaikuntha background, celestial clouds, divine aura, Hindu mythology illustration, ultra realistic, sacred art"
        )

    for i, prompt in enumerate(prompts):
        out = f"{IMAGE_DIR}/{i:03d}.jpg"
        generate_ai_image(prompt, out)

# ================= HINDI NEURAL VOICE =================
async def generate_single_audio(text, index):
    out = f"{AUDIO_DIR}/{index:03d}.wav"
    tts = edge_tts.Communicate(
        text=text,
        voice="hi-IN-MadhurNeural",
        rate="+0%",
        pitch="+0Hz"
    )
    await tts.save(out)

def generate_audio(blocks):
    print("🎙 Generating Hindi neural voice...")
    async def runner():
        for i, text in enumerate(blocks):
            if text.strip():
                await generate_single_audio(text, i)
    asyncio.run(runner())

# ================= VIDEO =================
def create_video(blocks):
    print("🎞 Creating video...")
    clips = []

    for i in range(len(blocks)):
        clip = f"{VIDEO_DIR}/{i:03d}.mp4"
        run([
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", f"{IMAGE_DIR}/{i:03d}.jpg",
            "-i", f"{AUDIO_DIR}/{i:03d}.wav",
            "-vf", "scale=1280:720,format=yuv420p",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            clip
        ])
        clips.append(clip)

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

# ================= MAIN =================
def main():
    base_blocks = Path(SCRIPT_FILE).read_text(encoding="utf-8").split("\n\n")

    intro = (
        "नमस्कार। आप सभी का स्वागत है Sanatan Gyan Dhara चैनल पर। "
        "आज हम आरंभ कर रहे हैं श्री विष्णु पुराण की दिव्य श्रृंखला का प्रथम एपिसोड।"
    )

    outro = (
        "यदि यह ज्ञान आपको प्रिय लगा हो, "
        "तो कृपया लाइक करें, शेयर करें और Sanatan Gyan Dhara को सब्सक्राइब करें। "
        "अब प्रतिदिन विष्णु पुराण का एक नया एपिसोड प्रकाशित किया जाएगा। "
        "ॐ नमो नारायणाय।"
    )

    blocks = [intro] + base_blocks + [outro]

    generate_images(blocks)
    generate_audio(blocks)
    create_video(blocks)

    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()