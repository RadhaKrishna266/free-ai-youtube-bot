import os
import asyncio
from pathlib import Path
from PIL import Image
import requests
from moviepy.editor import AudioFileClip, ImageClip, CompositeAudioClip, concatenate_videoclips
import edge_tts

# ---------------- CONFIG ----------------
SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "audio/tanpura.mp3"
HF_API_KEY = os.environ.get("HF_API_KEY")

# ---------------- CREATE FOLDERS ----------------
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ---------------- HUGGINGFACE IMAGE ----------------
def hf_generate_image(prompt, path):
    """Generate image using HuggingFace text-to-image API."""
    url = "https://api-inference.huggingface.co/models/gsdf/Counterfeit-V2.5"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {
        "inputs": prompt,
        "options": {"wait_for_model": True}
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        img_data = r.content
        with open(path, "wb") as f:
            f.write(img_data)
        print(f"✅ Generated image for: {prompt}")
    except Exception as e:
        print("❌ Failed to generate image:", e)
        # fallback: blank placeholder
        Image.new("RGB", (1280, 720), (10, 5, 0)).save(path)

def prepare_images(blocks):
    print("🖼 Generating images from HF API...")
    for i, text in enumerate(blocks):
        path = f"{IMAGE_DIR}/{i:03d}.png"
        hf_generate_image(text[:100] + " Vishnu illustration, temple, devotional, divine", path)

# ---------------- EDGE-TTS AUDIO ----------------
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
    print("🎙 Generating narration using Edge TTS...")
    async def runner():
        for i, text in enumerate(blocks):
            if text.strip():
                await generate_single_audio(text, i)
    asyncio.run(runner())

# ---------------- VIDEO CREATION ----------------
def create_video(blocks):
    print("🎞 Combining images and audio into final video...")
    clips = []
    tanpura_clip = AudioFileClip(TANPURA_FILE)

    for i in range(len(blocks)):
        img_path = f"{IMAGE_DIR}/{i:03d}.png"
        aud_path = f"{AUDIO_DIR}/{i:03d}.wav"

        img_clip = ImageClip(img_path).set_duration(AudioFileClip(aud_path).duration)
        audio_clip = CompositeAudioClip([AudioFileClip(aud_path), tanpura_clip.volumex(0.2)])
        img_clip = img_clip.set_audio(audio_clip)
        clips.append(img_clip)

    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile(FINAL_VIDEO, fps=24, codec="libx264", audio_codec="aac")
    print("✅ FINAL VIDEO CREATED:", FINAL_VIDEO)

# ---------------- MAIN ----------------
def main():
    blocks = Path(SCRIPT_FILE).read_text(encoding="utf-8").split("\n\n")
    # add intro/outro if desired
    intro = "नमस्कार। स्वागत है आप सभी का Sanatan Gyan Dhara में। आज हम आपके लिए Vishnu Purana का पहला एपिसोड लाए हैं।"
    outro = "\n\n🙏 अगर आपको यह वीडियो पसंद आया हो, तो कृपया लाइक, शेयर और सब्सक्राइब जरूर करें।"
    blocks.insert(0, intro)
    blocks.append(outro)

    prepare_images(blocks)
    generate_audio(blocks)
    create_video(blocks)

if __name__ == "__main__":
    main()