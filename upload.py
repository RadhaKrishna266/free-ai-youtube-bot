import os
import asyncio
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, ImageClip, CompositeAudioClip, concatenate_videoclips
import edge_tts
import requests
import time

# ---------------- CONFIG ----------------
SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "tanpura.mp3"  # You can include your tanpura background file here

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

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

# ---------------- AI IMAGE GENERATION ----------------
def generate_ai_image(prompt, out_path, retries=3):
    """
    Uses Pollinations AI API to generate image.
    """
    url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}"
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, timeout=25)
            if r.status_code == 200 and r.content:
                with open(out_path, "wb") as f:
                    f.write(r.content)
                print(f"✅ Image saved: {out_path}")
                return
        except Exception as e:
            print(f"⚠ Image retry {attempt}/{retries} failed:", e)
            time.sleep(3)
    print("❌ Failed to generate AI image, using placeholder.")
    placeholder(out_path)

# ---------------- GENERATE IMAGES ----------------
def generate_images(blocks):
    print("🖼 Generating AI Vishnu Purana images...")
    for i, text in enumerate(blocks):
        prompt = f"Divine Lord Vishnu illustration, Vaikunth, Vishnu Purana style, highly detailed, vibrant, digital art"
        out_path = f"{IMAGE_DIR}/{i:03d}.jpg"
        generate_ai_image(prompt, out_path)

# ---------------- HINDI NEURAL VOICE ----------------
async def generate_single_audio(text, index):
    out = f"{AUDIO_DIR}/{index:03d}.wav"
    communicate = edge_tts.Communicate(
        text=text,
        voice="hi-IN-MadhurNeural"
    )
    await communicate.save(out)

def generate_audio(blocks):
    print("🎙 Generating Hindi narration...")
    async def runner():
        for i, text in enumerate(blocks):
            if text.strip():
                await generate_single_audio(text, i)
    asyncio.run(runner())

# ---------------- VIDEO CREATION ----------------
def create_video(blocks):
    print("🎞 Creating video...")
    clips = []

    for i in range(len(blocks)):
        img_path = f"{IMAGE_DIR}/{i:03d}.jpg"
        audio_path = f"{AUDIO_DIR}/{i:03d}.wav"

        img_clip = ImageClip(img_path).set_duration(AudioFileClip(audio_path).duration)
        audio_clip = AudioFileClip(audio_path)

        if os.path.exists(TANPURA_FILE):
            tanpura_clip = AudioFileClip(TANPURA_FILE).volumex(0.2)
            audio_clip = CompositeAudioClip([audio_clip, tanpura_clip])

        img_clip = img_clip.set_audio(audio_clip)
        clips.append(img_clip)

    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile(FINAL_VIDEO, fps=24, codec="libx264", audio_codec="aac")

# ---------------- MAIN ----------------
def main():
    blocks = Path(SCRIPT_FILE).read_text(encoding="utf-8").split("\n\n")

    # Intro & outro
    intro = "नमस्कार। स्वागत है आप सभी का VishnuPriya श्रृंखला में। आज हम आपके लिए Vishnu Purana का पहला एपिसोड लाए हैं।"
    outro = "\n\n🙏 अगर आपको यह वीडियो पसंद आया हो, तो कृपया लाइक, शेयर और सब्सक्राइब जरूर करें। हर दिन एक नया एपिसोड आएगा।"
    blocks.insert(0, intro)
    blocks.append(outro)

    generate_images(blocks)
    generate_audio(blocks)
    create_video(blocks)
    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()