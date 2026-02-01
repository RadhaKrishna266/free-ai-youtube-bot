import os
import subprocess
import requests
import json
from pathlib import Path
import edge_tts
import asyncio

# ================= CONFIG =================
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

IMAGE_DIR = "images"
AUDIO_DIR = "audio"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"

WIDTH, HEIGHT = 1280, 720
FPS = 25
CLIP_DURATION = 6  # seconds per image
VIDEO_DURATION = 12 * 60  # 12 minutes
IMAGES_COUNT = VIDEO_DURATION // CLIP_DURATION  # ~120 images

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ================= IMAGE PROMPTS =================
PROMPTS = [
    # First image: Front cover
    "Front cover of Vishnu Purana ancient Hindu scripture book, golden cover, Sanskrit text, temple background, ultra detailed digital art",
    # Main scenes
    "Lord Vishnu and Goddess Lakshmi seated on Sheshnag in Vaikuntha, divine light, celestial clouds, Hindu mythological digital painting",
    "Vaikuntha loka, Vishnu resting on Sheshnag, cosmic ocean, glowing sky, spiritual digital art",
    "Matsya avatar of Vishnu, cosmic waters, divine glow, Hindu illustration",
    "Kurma avatar of Vishnu, Mount Mandara, Samudra Manthan, epic digital painting",
    "Varaha avatar lifting Bhudevi, dramatic divine scene",
    "Narasimha avatar protecting Prahlada, intense divine energy",
    "Lord Rama avatar, bow and arrow, Ayodhya background, divine digital art",
    "Lord Krishna avatar, flute, Vrindavan, divine aura",
]

# ================= UTILS =================
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ================= IMAGE GENERATION =================
def generate_images():
    print(f"🎨 Generating {IMAGES_COUNT} AI devotional images...")
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    for i in range(IMAGES_COUNT):
        # Rotate prompts for variety
        prompt = PROMPTS[i % len(PROMPTS)]
        payload = {
            "model": "gpt-image-1",
            "prompt": prompt,
            "size": "1280x720"
        }

        r = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers=headers,
            data=json.dumps(payload),
            timeout=60
        )

        data = r.json()
        img_url = data["data"][0]["url"]
        img_data = requests.get(img_url).content

        with open(f"{IMAGE_DIR}/{i:03d}.png", "wb") as f:
            f.write(img_data)
        print(f"✅ Image saved: {IMAGE_DIR}/{i:03d}.png")

# ================= AUDIO =================
async def generate_audio():
    narration_file = f"{AUDIO_DIR}/narration.mp3"
    text = (
        "नमस्कार। आप देख रहे हैं सनातन ज्ञान धारा। "
        "आज हम आपके लिए विष्णु पुराण का दिव्य प्रसंग प्रस्तुत कर रहे हैं। "
        "भगवान विष्णु के अवतारों और वैकुंठ लोक की महिमा।"
    )

    # TTS Narration
    tts = edge_tts.Communicate(text, voice="hi-IN-MadhurNeural")
    await tts.save(narration_file)
    print(f"✅ Narration saved: {narration_file}")

    # Soft Tanpura
    tanpura_file = f"{AUDIO_DIR}/tanpura.mp3"
    if not os.path.exists(tanpura_file):
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"sine=frequency=110:duration={VIDEO_DURATION+60}",  # loop if needed
            "-af", "volume=0.18",
            tanpura_file
        ], check=True)
        print(f"✅ Soft tanpura saved: {tanpura_file}")

    # Mix Narration + Tanpura
    mixed_file = f"{AUDIO_DIR}/mixed.mp3"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", narration_file,
        "-stream_loop", "-1",  # loop tanpura
        "-i", tanpura_file,
        "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=longest:dropout_transition=2[a]",
        "-map", "[a]",
        mixed_file
    ], check=True)
    print(f"✅ Mixed narration + soft tanpura: {mixed_file}")

    return mixed_file

# ================= VIDEO =================
def create_video(mixed_audio_file):
    clips = []

    for i in range(IMAGES_COUNT):
        img = f"{IMAGE_DIR}/{i:03d}.png"
        out = f"{VIDEO_DIR}/{i:03d}.mp4"

        vf = f"zoompan=z='min(zoom+0.0006,1.08)':d={FPS*CLIP_DURATION}:s={WIDTH}x{HEIGHT}"

        run([
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", img,
            "-filter_complex", vf,
            "-t", str(CLIP_DURATION),
            "-pix_fmt", "yuv420p",
            "-c:v", "libx264",
            out
        ])

        clips.append(out)
        print(f"✅ Video block created: {out}")

    # Concatenate clips
    with open("list.txt", "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "list.txt",
        "-i", mixed_audio_file,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        FINAL_VIDEO
    ])
    print(f"✅ Final video ready: {FINAL_VIDEO}")

# ================= MAIN =================
def main():
    generate_images()
    mixed_audio_file = asyncio.run(generate_audio())
    create_video(mixed_audio_file)

if __name__ == "__main__":
    main()