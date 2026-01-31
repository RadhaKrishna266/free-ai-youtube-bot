import os
import asyncio
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip, CompositeAudioClip, concatenate_videoclips
import requests
import edge_tts
from io import BytesIO

# ---------------- CONFIG ----------------
SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "tanpura.wav"  # Must be in repo
HF_API_KEY = os.environ.get("HF_API_KEY")
IMG_SIZE = (1280, 720)

# ---------------- CREATE FOLDERS ----------------
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ---------------- UTILS ----------------
def placeholder(path, text="ॐ नमो नारायणाय"):
    img = Image.new("RGB", IMG_SIZE, (10, 5, 0))
    draw = ImageDraw.Draw(img)
    font = None
    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except:
        pass
    draw.text((60, 330), text, fill=(255, 215, 0), font=font)
    img.save(path)

# ---------------- HF IMAGE GENERATION ----------------
def generate_ai_image(prompt, path):
    print(f"🖼 Generating image for prompt: {prompt[:50]}...")
    url = f"https://api-inference.huggingface.co/models/gsdf/Counterfeit-V2.5"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": prompt, "options": {"wait_for_model": True}}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        img_bytes = BytesIO(r.content)
        img = Image.open(img_bytes)
        img = img.resize(IMG_SIZE)
        img.save(path)
        print("✅ Image saved:", path)
    except Exception as e:
        print("❌ Failed AI image, using placeholder:", e)
        placeholder(path)

def prepare_images(blocks):
    for i, text in enumerate(blocks):
        path = f"{IMAGE_DIR}/{i:03d}.jpg"
        prompt = f"Lord Vishnu, divine, HD illustration, {text[:50]}"
        generate_ai_image(prompt, path)

# ---------------- EDGE TTS ----------------
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

# ---------------- VIDEO CREATION ----------------
def create_video(blocks):
    print("🎞 Creating final video...")
    clips = []

    for i in range(len(blocks)):
        img_file = f"{IMAGE_DIR}/{i:03d}.jpg"
        audio_file = f"{AUDIO_DIR}/{i:03d}.wav"
        if not os.path.exists(img_file):
            placeholder(img_file)
        if not os.path.exists(audio_file):
            print(f"❌ Missing audio: {audio_file}")
            continue

        # Add tanpura background
        audio_clip = AudioFileClip(audio_file)
        if os.path.exists(TANPURA_FILE):
            tanpura = AudioFileClip(TANPURA_FILE).volumex(0.3).loop(duration=audio_clip.duration)
            audio_clip = CompositeAudioClip([audio_clip, tanpura])

        clip = ImageClip(img_file).set_duration(audio_clip.duration).set_audio(audio_clip)
        clips.append(clip)

    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile(FINAL_VIDEO, fps=24)
    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

# ---------------- MAIN ----------------
def main():
    blocks = Path(SCRIPT_FILE).read_text(encoding="utf-8").split("\n\n")
    intro = "नमस्कार। स्वागत है आप सभी का VishnuPriya श्रृंखला में।"
    outro = "\n\n🙏 अगर आपको यह वीडियो पसंद आया हो, तो कृपया लाइक, शेयर और सब्सक्राइब जरूर करें।"
    blocks.insert(0, intro)
    blocks.append(outro)

    prepare_images(blocks)
    generate_audio(blocks)
    create_video(blocks)

if __name__ == "__main__":
    main()