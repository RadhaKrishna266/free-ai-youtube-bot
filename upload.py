import os
import subprocess
import asyncio
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import edge_tts
from moviepy.editor import AudioFileClip, ImageClip, CompositeAudioClip, concatenate_videoclips

# ---------------- CONFIG ----------------
SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "tanpura.mp3"  # Place your tanpura.mp3 in repo
MAX_IMAGE_BLOCKS = 50  # max AI images
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

# ---------------- AI IMAGE GENERATION ----------------
def generate_ai_image(prompt, out_path):
    """
    Generate AI image using stable diffusion or any external AI API.
    Here, it is a placeholder function. Replace with your actual AI API call.
    """
    print(f"🖼 Generating AI image for: {prompt}")
    # For testing without AI API, use placeholder
    placeholder(out_path, text=prompt.split(",")[0][:30])

def generate_images(blocks):
    print("🖼 Generating AI Vishnu / Vaikunth images...")
    for i, text in enumerate(blocks):
        path = f"{IMAGE_DIR}/{i:03d}.jpg"
        prompt = f"Lord Vishnu, Vaikunth, divine illustration, Hindu mythology, vibrant, detailed, cinematic"
        generate_ai_image(prompt, path)

# ---------------- HINDI NEURAL VOICE ----------------
async def generate_single_audio(text, index):
    out = f"{AUDIO_DIR}/{index:03d}.wav"
    communicate = edge_tts.Communicate(
        text=text,
        voice="hi-IN-MadhurNeural",
        rate="+0%",
        pitch="+0Hz"
    )
    await communicate.save(out)

def generate_audio(blocks):
    print("🎙 Generating Hindi narration...")
    async def runner():
        for i, text in enumerate(blocks):
            if text.strip():
                await generate_single_audio(text, i)
    asyncio.run(runner())

# ---------------- CREATE VIDEO CLIPS ----------------
def create_video(blocks):
    print("🎞 Creating video with tanpura...")
    clips = []
    tanpura_clip = None
    if os.path.exists(TANPURA_FILE):
        tanpura_clip = AudioFileClip(TANPURA_FILE)

    for i in range(len(blocks)):
        img_path = f"{IMAGE_DIR}/{i:03d}.jpg"
        audio_path = f"{AUDIO_DIR}/{i:03d}.wav"
        audio_clip = AudioFileClip(audio_path)
        if tanpura_clip:
            audio_clip = CompositeAudioClip([audio_clip, tanpura_clip.volumex(0.3).set_duration(audio_clip.duration)])
        clip = ImageClip(img_path).set_duration(audio_clip.duration).set_audio(audio_clip)
        clips.append(clip)

    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile(FINAL_VIDEO, fps=24, codec="libx264", audio_codec="aac")
    print(f"✅ FINAL VIDEO READY: {FINAL_VIDEO}")

# ---------------- MAIN ----------------
def main():
    # Read script and split into blocks
    blocks = Path(SCRIPT_FILE).read_text(encoding="utf-8").split("\n\n")
    intro = "नमस्कार। स्वागत है आप सभी का VishnuPriya श्रृंखला में। आज हम आपके लिए Vishnu Purana का पहला एपिसोड लाए हैं।"
    outro = "\n\n🙏 अगर आपको यह वीडियो पसंद आया हो, तो कृपया लाइक, शेयर और सब्सक्राइब जरूर करें। हर दिन एक नया एपिसोड आएगा।"
    blocks.insert(0, intro)
    blocks.append(outro)

    # Generate images, narration, video
    generate_images(blocks)
    generate_audio(blocks)
    create_video(blocks)

if __name__ == "__main__":
    main()