import os
import asyncio
import requests
from pathlib import Path
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import subprocess

# ---------------- CONFIG ----------------
SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "tanpura.wav"  # pre-uploaded tanpura audio in repo
HF_API_KEY = os.environ.get("HF_API_KEY")

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ---------------- UTILS ----------------
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ---------------- PLACEHOLDER IMAGE ----------------
def placeholder(path, text="ॐ नमो नारायणाय"):
    img = Image.new("RGB", (1280, 720), (10, 5, 0))
    d = ImageDraw.Draw(img)
    font = None
    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except:
        pass
    d.text((60, 330), text, fill=(255, 215, 0), font=font)
    img.save(path)

# ---------------- HF AI IMAGE GENERATION ----------------
def generate_ai_image(prompt, out_path):
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2"
    payload = {"inputs": prompt}
    try:
        r = requests.post(api_url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        with open(out_path, "wb") as f:
            f.write(r.content)
        print(f"✅ Generated image {out_path}")
    except Exception as e:
        print("❌ HF AI image generation failed, using placeholder:", e)
        placeholder(out_path)

def prepare_images(blocks):
    print("🖼 Generating AI Vishnu images...")
    for i, text in enumerate(blocks):
        path = f"{IMAGE_DIR}/{i:03d}.jpg"
        prompt = f"Divine Lord Vishnu, traditional Indian style, epic illustration, scene: {text[:60]}"
        generate_ai_image(prompt, path)

# ---------------- EDGE TTS ----------------
import edge_tts

async def generate_single_audio(text, index):
    out = f"{AUDIO_DIR}/{index:03d}.wav"
    communicate = edge_tts.Communicate(
        text=text,
        voice="hi-IN-MadhurNeural"
    )
    await communicate.save(out)

def generate_audio(blocks):
    print("🎙 Generating narration...")
    async def runner():
        for i, text in enumerate(blocks):
            if text.strip():
                await generate_single_audio(text, i)
    asyncio.run(runner())

# ---------------- VIDEO CREATION USING FFMPEG ----------------
def create_video(blocks):
    print("🎞 Creating video clips...")
    for i in range(len(blocks)):
        img_file = f"{IMAGE_DIR}/{i:03d}.jpg"
        audio_file = f"{AUDIO_DIR}/{i:03d}.wav"
        clip_file = f"{VIDEO_DIR}/{i:03d}.mp4"

        # Combine narration + tanpura background
        run([
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", img_file,
            "-i", audio_file,
            "-stream_loop", "-1",
            "-i", TANPURA_FILE,
            "-filter_complex", "[1:a][2:a]amix=inputs=2:duration=first:dropout_transition=0[a]",
            "-map", "0:v",
            "-map", "[a]",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            clip_file
        ])

    # Concatenate all clips
    with open("list.txt", "w") as f:
        for i in range(len(blocks)):
            f.write(f"file '{VIDEO_DIR}/{i:03d}.mp4'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "list.txt",
        "-c", "copy",
        FINAL_VIDEO
    ])
    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

# ---------------- MAIN ----------------
def main():
    if not Path(TANPURA_FILE).exists():
        raise FileNotFoundError(f"❌ {TANPURA_FILE} not found in repo!")

    blocks = Path(SCRIPT_FILE).read_text(encoding="utf-8").split("\n\n")
    intro = "नमस्कार। स्वागत है आप सभी का Sanatan Gyan Dhara श्रृंखला में। आज हम आपके लिए Vishnu Purana का पहला एपिसोड लाए हैं।"
    outro = "\n\n🙏 अगर आपको यह वीडियो पसंद आया हो, तो कृपया लाइक, शेयर और सब्सक्राइब जरूर करें। हर दिन एक नया एपिसोड आएगा।"
    blocks.insert(0, intro)
    blocks.append(outro)

    prepare_images(blocks)
    generate_audio(blocks)
    create_video(blocks)

if __name__ == "__main__":
    main()