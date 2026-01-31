import os
import time
import requests
from pathlib import Path
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

# ================= CONFIG =================

HF_API_KEY = os.getenv("HF_API_KEY")
HF_MODEL = "stabilityai/stable-diffusion-2-1"
HF_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

HEADERS = {
    "Authorization": f"Bearer {HF_API_KEY}"
}

BASE_DIR = Path(".")
IMG_DIR = BASE_DIR / "images"
AUDIO_DIR = BASE_DIR / "audio"
VIDEO_DIR = BASE_DIR / "video"

IMG_DIR.mkdir(exist_ok=True)
AUDIO_DIR.mkdir(exist_ok=True)
VIDEO_DIR.mkdir(exist_ok=True)

FINAL_VIDEO = VIDEO_DIR / "vishnu_purana_episode_1.mp4"

# ================= SCRIPT =================

SCRIPT_TEXT = """
ॐ नमो नारायणाय।

विष्णु पुराण अठारह महापुराणों में से एक अत्यंत पवित्र ग्रंथ है।
इसमें सृष्टि की उत्पत्ति, धर्म, भक्ति और मोक्ष का दिव्य वर्णन मिलता है।

भगवान विष्णु को सम्पूर्ण सृष्टि का मूल कारण बताया गया है।
वे ही सृष्टि के कर्ता, पालनकर्ता और संहार के अधिष्ठाता हैं।

इस पवित्र श्रृंखला में हम प्रतिदिन
विष्णु पुराण के एक अध्याय का भावपूर्ण वर्णन करेंगे।

ॐ नमो नारायणाय।
"""

PROMPTS = [
    "Lord Vishnu resting on Ananta Shesha, Vaikuntha, divine Hindu devotional art, ultra detailed",
    "Vaikuntha loka golden palace, cosmic clouds, Vishnu Purana illustration",
    "Lord Vishnu with Shankha Chakra Gada Padma, blue complexion, calm face, Hindu art",
    "Cosmic Vishnu creating universe, spiritual glow, Indian mythology painting",
    "Vishnu Purana ancient manuscript style illustration, sacred Hindu artwork"
]

# ================= FUNCTIONS =================

def generate_ai_image(prompt, out_path):
    payload = {
        "inputs": prompt,
        "options": {"wait_for_model": True}
    }
    try:
        r = requests.post(HF_URL, headers=HEADERS, json=payload, timeout=15)
        if r.status_code == 200:
            with open(out_path, "wb") as f:
                f.write(r.content)
            print(f"✅ Image created: {out_path.name}")
        else:
            print(f"⚠ Image failed: {r.text}")
    except Exception as e:
        print(f"⚠ Image skipped: {e}")

def generate_images():
    print("🖼 Generating AI images...")
    for i, prompt in enumerate(PROMPTS, 1):
        out = IMG_DIR / f"scene_{i}.png"
        generate_ai_image(prompt, out)
        time.sleep(1)

def generate_audio():
    print("🎙 Generating audio...")
    tts = gTTS(text=SCRIPT_TEXT, lang="hi")
    audio_path = AUDIO_DIR / "narration.mp3"
    tts.save(audio_path)
    return audio_path

def generate_video(audio_path):
    print("🎬 Creating video...")
    clips = []
    audio = AudioFileClip(str(audio_path))
    duration_per_image = audio.duration / len(list(IMG_DIR.glob("*.png")))

    for img in sorted(IMG_DIR.glob("*.png")):
        clip = ImageClip(str(img)).set_duration(duration_per_image)
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")
    video = video.set_audio(audio)

    video.write_videofile(
        str(FINAL_VIDEO),
        fps=24,
        codec="libx264",
        audio_codec="aac"
    )

# ================= MAIN =================

def main():
    generate_images()
    audio = generate_audio()
    generate_video(audio)
    print(f"✅ VIDEO READY: {FINAL_VIDEO}")

if __name__ == "__main__":
    main()