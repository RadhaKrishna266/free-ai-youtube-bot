import os
import time
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
from moviepy.editor import AudioFileClip, ImageClip, CompositeAudioClip, concatenate_videoclips

# ---------------- CONFIG ----------------
SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video"
FINAL_VIDEO = f"{VIDEO_DIR}/vishnu_purana_episode_1.mp4"
HF_API_KEY = os.environ.get("HF_API_KEY")
TANPURA_FILE = "tanpura.mp3"  # include a short tanpura loop in repo

# ---------------- CREATE FOLDERS ----------------
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ---------------- PLACEHOLDER IMAGE ----------------
def placeholder(path, text="ॐ नमो नारायणाय।"):
    img = Image.new("RGB", (1280, 720), (10, 5, 0))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except:
        font = None
    d.text((60, 330), text, fill=(255, 215, 0), font=font)
    img.save(path)

# ---------------- HF AI IMAGE GENERATION ----------------
def generate_ai_image(prompt, out_path, retries=3):
    url = "https://api-inference.huggingface.co/models/SG161222/Realistic-Vishnu"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}

    for attempt in range(1, retries+1):
        try:
            r = requests.post(url, headers=headers, json={"inputs": prompt}, timeout=60)
            if r.status_code == 200:
                with open(out_path, "wb") as f:
                    f.write(r.content)
                print(f"✅ Image saved: {out_path}")
                return
            print(f"❌ HF attempt {attempt} failed, status {r.status_code}")
        except Exception as e:
            print(f"❌ HF attempt {attempt} exception:", e)
        time.sleep(5)
    print("⚠ Using placeholder image.")
    placeholder(out_path)

def prepare_images(blocks):
    print("🖼 Generating AI Vishnu images...")
    for i, text in enumerate(blocks):
        prompt = f"Divine image of Lord Vishnu, Vaikunth style, serene, traditional Indian painting, {text[:30]}"
        out_path = f"{IMAGE_DIR}/{i:03d}.jpg"
        generate_ai_image(prompt, out_path)

# ---------------- GENERATE AUDIO ----------------
def generate_audio(blocks):
    print("🎙 Generating Hindi narration...")
    for i, text in enumerate(blocks):
        tts = gTTS(text=text, lang="hi")
        tts.save(f"{AUDIO_DIR}/{i:03d}.mp3")

# ---------------- COMBINE VIDEO ----------------
def create_video(blocks):
    print("🎞 Creating final video...")
    clips = []

    for i in range(len(blocks)):
        img_clip = ImageClip(f"{IMAGE_DIR}/{i:03d}.jpg").set_duration(5)  # default 5 sec per block
        audio_clip = AudioFileClip(f"{AUDIO_DIR}/{i:03d}.mp3")
        if os.path.isfile(TANPURA_FILE):
            tanpura_clip = AudioFileClip(TANPURA_FILE).subclip(0, audio_clip.duration).volumex(0.1)
            final_audio = CompositeAudioClip([audio_clip, tanpura_clip])
        else:
            final_audio = audio_clip
        img_clip = img_clip.set_audio(final_audio)
        clips.append(img_clip)

    final = concatenate_videoclips(clips)
    final.write_videofile(FINAL_VIDEO, fps=24)

# ---------------- MAIN ----------------
def main():
    blocks = Path(SCRIPT_FILE).read_text(encoding="utf-8").split("\n\n")
    intro = "नमस्कार। स्वागत है आप सभी का VishnuPriya श्रृंखला में। आज हम आपके लिए Vishnu Purana का पहला एपिसोड लाए हैं।"
    outro = "\n\n🙏 अगर आपको यह वीडियो पसंद आया हो, तो कृपया लाइक, शेयर और सब्सक्राइब जरूर करें। हर दिन एक नया एपिसोड आएगा।"
    blocks.insert(0, intro)
    blocks.append(outro)

    prepare_images(blocks)
    generate_audio(blocks)
    create_video(blocks)
    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()