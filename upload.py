import os
import asyncio
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, ImageClip, CompositeAudioClip, concatenate_videoclips
import edge_tts
from diffusers import StableDiffusionPipeline
import torch

# ---------------- CONFIG ----------------
SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio"
VIDEO_DIR = "video"
FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "tanpura.mp3"  # Place tanpura file in repo root
HF_MODEL = "runwayml/stable-diffusion-v1-5"

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ---------------- AI IMAGE GENERATION ----------------
def generate_ai_image(prompt, out_path):
    pipe = StableDiffusionPipeline.from_pretrained(
        HF_MODEL,
        torch_dtype=torch.float16,
        revision="fp16",
        use_auth_token=os.environ.get("HF_API_KEY")
    ).to("cuda" if torch.cuda.is_available() else "cpu")

    image = pipe(prompt, guidance_scale=7.5).images[0]
    image.save(out_path)

def generate_images(blocks):
    print("🖼 Generating AI images for each block...")
    for i, text in enumerate(blocks):
        prompt = f"Divine, traditional Indian painting of Lord Vishnu, {text[:50]}"
        out = f"{IMAGE_DIR}/{i:03d}.png"
        try:
            generate_ai_image(prompt, out)
        except Exception as e:
            print("❌ Failed to generate AI image, using placeholder:", e)
            placeholder(out)

# ---------------- PLACEHOLDER ----------------
def placeholder(path, text="ॐ नमो नारायणाय"):
    img = Image.new("RGB", (1280, 720), (10, 5, 0))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except:
        font = None
    d.text((60, 330), text, fill=(255, 215, 0), font=font)
    img.save(path)

# ---------------- AUDIO GENERATION ----------------
async def generate_single_audio(text, index):
    out_file = f"{AUDIO_DIR}/{index:03d}.mp3"
    communicate = edge_tts.Communicate(text=text, voice="hi-IN-MadhurNeural")
    await communicate.save(out_file)
    return out_file

def generate_audio(blocks):
    print("🎙 Generating narration...")
    async def runner():
        tasks = [generate_single_audio(text, i) for i, text in enumerate(blocks) if text.strip()]
        await asyncio.gather(*tasks)
    asyncio.run(runner())

# ---------------- VIDEO CREATION ----------------
def create_video(blocks):
    print("🎞 Creating final video...")
    clips = []
    for i in range(len(blocks)):
        img_file = f"{IMAGE_DIR}/{i:03d}.png"
        audio_file = f"{AUDIO_DIR}/{i:03d}.mp3"

        img_clip = ImageClip(img_file).set_duration(AudioFileClip(audio_file).duration)
        audio_clip = AudioFileClip(audio_file)

        if os.path.exists(TANPURA_FILE):
            tanpura_clip = AudioFileClip(TANPURA_FILE).subclip(0, audio_clip.duration)
            composite_audio = CompositeAudioClip([audio_clip, tanpura_clip.volumex(0.3)])
        else:
            composite_audio = audio_clip

        img_clip = img_clip.set_audio(composite_audio)
        clips.append(img_clip)

    final_clip = concatenate_videoclips(clips)
    final_clip.write_videofile(FINAL_VIDEO, fps=24, codec="libx264", audio_codec="aac")

# ---------------- MAIN ----------------
def main():
    blocks = Path(SCRIPT_FILE).read_text(encoding="utf-8").split("\n\n")
    intro = "नमस्कार। स्वागत है आप सभी का VishnuPriya श्रृंखला में। आज हम आपके लिए Vishnu Purana का पहला एपिसोड लाए हैं।"
    outro = "\n\n🙏 अगर आपको यह वीडियो पसंद आया हो, तो कृपया लाइक, शेयर और सब्सक्राइब जरूर करें। हर दिन एक नया एपिसोड आएगा।"
    blocks.insert(0, intro)
    blocks.append(outro)

    generate_images(blocks)
    generate_audio(blocks)
    create_video(blocks)
    print("✅ FINAL VISHNU VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()