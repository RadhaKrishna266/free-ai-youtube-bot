import os
import asyncio
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from huggingface_hub import hf_hub_download
import requests
from moviepy.editor import AudioFileClip, ImageClip, CompositeAudioClip, concatenate_videoclips
from gtts import gTTS

# ---------------- CONFIG ----------------
SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "video/vishnu_purana_episode_1.mp4"
HF_API_KEY = os.environ.get("HF_API_KEY")
TANPURA_FILE = "tanpura.wav"  # should exist in repo

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ---------------- UTIL: Placeholder ----------------
def placeholder(path, text="ॐ नमो नारायणाय"):
    img = Image.new("RGB", (1280, 720), (10, 5, 0))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except:
        font = None
    d.text((60, 330), text, fill=(255, 215, 0), font=font)
    img.save(path)

# ---------------- AI IMAGE GENERATION ----------------
def generate_ai_image(prompt, out_path):
    """Generates an image from Hugging Face API"""
    url = "https://api-inference.huggingface.co/models/SG161222/Realistic-Vishnu"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": prompt}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        if r.status_code == 200:
            with open(out_path, "wb") as f:
                f.write(r.content)
        else:
            print(f"❌ HF Image generation failed, status {r.status_code}")
            placeholder(out_path)
    except Exception as e:
        print("❌ HF Image generation exception:", e)
        placeholder(out_path)

def prepare_images(blocks):
    print("🖼 Generating AI images for video...")
    for i, text in enumerate(blocks):
        out_path = f"{IMAGE_DIR}/{i:03d}.png"
        prompt = f"Divine, cinematic, realistic illustration of Lord Vishnu: {text}"
        generate_ai_image(prompt, out_path)

# ---------------- AUDIO GENERATION ----------------
def generate_audio(blocks):
    print("🎙 Generating Hindi narration + tanpura background...")
    for i, text in enumerate(blocks):
        tts = gTTS(text=text, lang="hi")
        tts_file = f"{AUDIO_DIR}/{i:03d}.mp3"
        tts.save(tts_file)

# ---------------- VIDEO CREATION ----------------
def create_video(blocks):
    print("🎞 Creating final video...")
    clips = []
    for i in range(len(blocks)):
        img_file = f"{IMAGE_DIR}/{i:03d}.png"
        audio_file = f"{AUDIO_DIR}/{i:03d}.mp3"

        audio_clip = AudioFileClip(audio_file)
        if os.path.exists(TANPURA_FILE):
            tanpura_clip = AudioFileClip(TANPURA_FILE).volumex(0.1)
            audio_clip = CompositeAudioClip([audio_clip, tanpura_clip.set_duration(audio_clip.duration)])

        clip = ImageClip(img_file).set_duration(audio_clip.duration).set_audio(audio_clip)
        clips.append(clip)

    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile(FINAL_VIDEO, fps=24, codec="libx264", audio_codec="aac")
    print("✅ Video saved at", FINAL_VIDEO)

# ---------------- MAIN ----------------
def main():
    blocks = Path(SCRIPT_FILE).read_text(encoding="utf-8").split("\n\n")
    # Add intro/outro
    intro = "नमस्कार। स्वागत है आप सभी का Sanatan Gyan Dhara चैनल में।"
    outro = "\n\n🙏 यदि यह वीडियो पसंद आया हो तो कृपया लाइक, शेयर और सब्सक्राइब करें।"
    blocks.insert(0, intro)
    blocks.append(outro)

    prepare_images(blocks)
    generate_audio(blocks)
    create_video(blocks)

if __name__ == "__main__":
    main()