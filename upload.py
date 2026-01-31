import os
import subprocess
import asyncio
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import edge_tts

# ---------------- CONFIG ----------------
SCRIPT_FILE = "script.txt"
IMAGE_DIR = "images"
AUDIO_DIR = "audio_blocks"
VIDEO_DIR = "video_blocks"
FINAL_VIDEO = "final_video.mp4"
FALLBACK_IMAGES_DIR = "fallback_images"  # Put your Vishnu/Avatars images here
TANPURA_FILE = "tanpura.mp3"  # Pre-downloaded drone audio

# ---------------- CREATE FOLDERS ----------------
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ---------------- UTILS ----------------
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

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

# ---------------- DOWNLOAD / USE IMAGES ----------------
def prepare_images(blocks):
    fallback_files = list(Path(FALLBACK_IMAGES_DIR).glob("*.jpg"))
    if not fallback_files:
        raise RuntimeError("❌ No fallback images found in fallback_images/ folder!")

    for i, text in enumerate(blocks):
        path = f"{IMAGE_DIR}/{i:03d}.jpg"
        img_file = fallback_files[i % len(fallback_files)]
        img = Image.open(img_file)
        img.save(path)

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
    print("🎙 Generating HIGH-QUALITY Hindi Neural voice...")
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
        clip_file = f"{VIDEO_DIR}/{i:03d}.mp4"
        audio_file = f"{AUDIO_DIR}/{i:03d}.wav"

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", f"{IMAGE_DIR}/{i:03d}.jpg",
            "-i", audio_file,
            "-vf", "scale=1280:720,format=yuv420p",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            clip_file
        ]
        run(cmd)
        clips.append(clip_file)

    # Concatenate clips
    with open("list.txt", "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "list.txt",
        "-c", "copy",
        "temp_video.mp4"
    ])

    # Merge with tanpura drone if exists
    if Path(TANPURA_FILE).exists():
        run([
            "ffmpeg", "-y",
            "-i", "temp_video.mp4",
            "-stream_loop", "-1",
            "-i", TANPURA_FILE,
            "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2",
            "-c:v", "copy",
            FINAL_VIDEO
        ])
    else:
        os.rename("temp_video.mp4", FINAL_VIDEO)

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

    print("✅ FINAL VISHNU VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()