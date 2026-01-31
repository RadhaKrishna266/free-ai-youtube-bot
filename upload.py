import os
import subprocess
import asyncio
import requests
from pathlib import Path
import edge_tts

# ---------------- CONFIG ----------------
SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ---------------- UTILS ----------------
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ---------------- AI IMAGE (POLLINATIONS) ----------------
def generate_ai_image(prompt, out_path):
    url = "https://image.pollinations.ai/prompt/" + requests.utils.quote(prompt)
    r = requests.get(url, timeout=20)
    with open(out_path, "wb") as f:
        f.write(r.content)

# ---------------- IMAGES ----------------
def generate_images(blocks):
    print("🖼 Generating AI Vishnu images (Vaikuntha style)...")

    prompts = [
        "Vishnu Purana ancient manuscript illustration book cover, Indian miniature painting",
        "Lord Vishnu seated on Sheshnag in Vaikuntha, divine Hindu art",
        "Dashavatara of Vishnu, Matsya Kurma Varaha Narasimha Vamana Parashurama Rama Krishna Kalki, epic painting",
        "Cosmic Vishnu Vishwaroop form, galaxies, stars, divine glow",
        "Lord Vishnu holding Shankha Chakra Gada Padma, devotional painting"
    ]

    for i, text in enumerate(blocks):
        prompt = prompts[i % len(prompts)] + f", ultra detailed, sacred art, episode {i+1}"
        out = f"{IMAGE_DIR}/{i:03d}.jpg"
        generate_ai_image(prompt, out)

# ---------------- AUDIO ----------------
async def gen_audio(text, idx):
    out = f"{AUDIO_DIR}/{idx:03d}.wav"
    tts = edge_tts.Communicate(
        text=text,
        voice="hi-IN-MadhurNeural",
        rate="+0%",
        pitch="+0Hz"
    )
    await tts.save(out)

def generate_audio(blocks):
    print("🎙 Generating Hindi Neural Voice...")
    async def runner():
        for i, b in enumerate(blocks):
            if b.strip():
                await gen_audio(b, i)
    asyncio.run(runner())

# ---------------- VIDEO ----------------
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

# ---------------- MAIN ----------------
def main():
    blocks = Path(SCRIPT_FILE).read_text(encoding="utf-8").split("\n\n")

    intro = (
        "नमस्कार। VishnuPriya श्रृंखला में आपका स्वागत है। "
        "आज हम विष्णु पुराण का प्रथम अध्याय आरंभ कर रहे हैं।"
    )
    outro = (
        "यदि आपको यह दिव्य ज्ञान प्रिय लगे, तो कृपया लाइक, शेयर और सब्सक्राइब करें। "
        "हम प्रतिदिन विष्णु पुराण का एक नया एपिसोड प्रस्तुत करेंगे।"
    )

    blocks.insert(0, intro)
    blocks.append(outro)

    generate_images(blocks)
    generate_audio(blocks)
    create_video(blocks)

    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()