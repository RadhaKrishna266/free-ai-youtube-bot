import os
import time
import requests
import subprocess
from pathlib import Path
from PIL import Image
from moviepy.editor import *
import edge_tts

# ================= CONFIG =================
HF_TOKEN = os.getenv("HF_TOKEN")
IMG_DIR = Path("images")
AUDIO_DIR = Path("audio")
FINAL_VIDEO = "final_video.mp4"

IMG_DIR.mkdir(exist_ok=True)
AUDIO_DIR.mkdir(exist_ok=True)

HF_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"

# Vishnu-specific prompts (NO randomness)
IMAGE_PROMPTS = [
    "Lord Vishnu resting on Sheshnag in Vaikuntha, divine light, ultra detailed, hindu devotional art",
    "Vaikuntha loka golden palace, celestial clouds, divine atmosphere, hindu art",
    "Lord Vishnu four arms holding shankha chakra gada padma, glowing blue skin",
    "Cosmic Vishnu source of creation, universe emerging, spiritual art",
    "Devotees listening to Vishnu Purana, ancient rishis, spiritual ambience"
]

# ================= IMAGE GENERATION =================
def generate_ai_image(prompt, out_path):
    url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": prompt}

    for attempt in range(3):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=40)
            if r.status_code == 200:
                with open(out_path, "wb") as f:
                    f.write(r.content)
                Image.open(out_path).verify()
                return
        except Exception as e:
            print(f"⚠ Image retry {attempt+1}/3 failed:", e)
            time.sleep(5)

    raise RuntimeError("❌ AI image generation failed")

def generate_images():
    print("🖼 Generating Vishnu / Vaikuntha images...")
    paths = []
    for i, prompt in enumerate(IMAGE_PROMPTS):
        out = IMG_DIR / f"img_{i}.png"
        generate_ai_image(prompt, out)
        paths.append(str(out))
    return paths

# ================= VOICE =================
async def generate_voice(text):
    print("🎙 Generating narration...")
    out = AUDIO_DIR / "voice.mp3"
    communicate = edge_tts.Communicate(
        text=text,
        voice="hi-IN-MadhurNeural",
        rate="-5%"
    )
    await communicate.save(str(out))
    return str(out)

# ================= VIDEO =================
def create_video(images, voice_path):
    print("🎬 Creating video...")
    clips = []
    duration_per_image = 12

    for img in images:
        clips.append(
            ImageClip(img)
            .set_duration(duration_per_image)
            .resize(height=1080)
        )

    video = concatenate_videoclips(clips, method="compose")

    narration = AudioFileClip(voice_path)
    tanpura = AudioFileClip("tanpura.mp3").volumex(0.25)

    if tanpura.duration < narration.duration:
        tanpura = tanpura.audio_loop(duration=narration.duration)

    final_audio = CompositeAudioClip([tanpura, narration])
    video = video.set_audio(final_audio)

    video.write_videofile(
        FINAL_VIDEO,
        fps=24,
        codec="libx264",
        audio_codec="aac"
    )

# ================= MAIN =================
def main():
    script = Path("script.txt").read_text(encoding="utf-8")

    images = generate_images()

    import asyncio
    voice = asyncio.run(generate_voice(script))

    create_video(images, voice)

    print("✅ FINAL VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()