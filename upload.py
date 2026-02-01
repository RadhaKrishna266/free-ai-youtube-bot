import os
import subprocess
import asyncio
from pathlib import Path
from PIL import Image
import openai
import edge_tts

# ---------------- CONFIG ----------------
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
IMAGE_FOLDER = "images"
AUDIO_FOLDER = "audio_blocks"
VIDEO_FOLDER = "video_blocks"
FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "audio/tanpura.mp3"
SCRIPT_FILE = "script.txt"

VIDEO_SIZE = (1280, 720)
FPS = 25
DURATION_PER_BLOCK = 6
ZOOM_SPEED = 0.0005
MAX_ZOOM = 1.06
TANPURA_FREQ = 110
TANPURA_VOLUME = 0.15
NUM_IMAGES = 5  # Number of blocks/images

Path(IMAGE_FOLDER).mkdir(exist_ok=True)
Path(AUDIO_FOLDER).mkdir(exist_ok=True)
Path(VIDEO_FOLDER).mkdir(exist_ok=True)
Path("audio").mkdir(exist_ok=True)

# ---------------- UTILS ----------------
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ---------------- TANPURA ----------------
def create_tanpura_audio(path=TANPURA_FILE):
    if not os.path.exists(path):
        print("🎵 Creating light tanpura audio...")
        run([
            "ffmpeg", "-y", "-f", "lavfi", f"-i", f"sine=frequency={TANPURA_FREQ}:duration=180",
            "-af", f"volume={TANPURA_VOLUME}", path
        ])
    return path

# ---------------- OPENAI IMAGE GENERATION ----------------
def generate_ai_image(prompt, out_path):
    print(f"🎨 Generating image: {prompt}")
    openai.api_key = OPENAI_API_KEY
    resp = openai.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024",
        n=1
    )
    img_url = resp.data[0].url
    import requests
    r = requests.get(img_url)
    with open(out_path, "wb") as f:
        f.write(r.content)

def generate_all_images():
    prompts = [
        "Vishnu Puran book front cover, realistic, detailed",
        "Lord Vishnu in Vaikunth, Hindu digital art, vibrant",
        "Goddess Lakshmi with Lord Vishnu, divine illustration",
        "Vishnu in Krishna avatar, digital painting, bright colors",
        "Vishnu in Rama avatar, Hindu mythology, artistic style"
    ]
    image_paths = []
    for i, p in enumerate(prompts):
        path = f"{IMAGE_FOLDER}/{i:03}.png"
        generate_ai_image(p, path)
        image_paths.append(path)
    return image_paths

# ---------------- NARRATION ----------------
async def generate_single_narration(text, out_path):
    communicate = edge_tts.Communicate(text, voice="hi-IN-MadhurNeural")
    await communicate.save(out_path)

def generate_narration_blocks(script_path=SCRIPT_FILE):
    lines = [line.strip() for line in Path(script_path).read_text(encoding="utf-8").split("\n") if line.strip()]
    intro = "नमस्कार। स्वागत है आप सभी का Sanatan Gyan Dhara श्रृंखला में। आज हम आपके लिए Vishnu Purana का पहला एपिसोड लाए हैं।"
    outro = "🙏 अगर आपको यह वीडियो पसंद आया हो, तो कृपया लाइक, शेयर और सब्सक्राइब जरूर करें। हर दिन एक नया एपिसोड आएगा।"
    blocks = [intro] + lines + [outro]

    narr_files = []
    for i, text in enumerate(blocks):
        out_file = f"{AUDIO_FOLDER}/{i:03}.mp3"
        asyncio.run(generate_single_narration(text, out_file))
        narr_files.append(out_file)
    return narr_files

# ---------------- VIDEO BLOCK ----------------
def create_video_block(img_path, narr_file, tanpura_file, out_file):
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", img_path,
        "-i", narr_file,
        "-i", tanpura_file,
        "-filter_complex",
        f"[0:v]scale={VIDEO_SIZE[0]}:{VIDEO_SIZE[1]}:force_original_aspect_ratio=decrease,"
        f"pad={VIDEO_SIZE[0]}:{VIDEO_SIZE[1]}:(ow-iw)/2:(oh-ih)/2,"
        f"zoompan=z='min(zoom+{ZOOM_SPEED},{MAX_ZOOM})':d={DURATION_PER_BLOCK*FPS}:fps={FPS}[v];"
        f"[1:a][2:a]amix=inputs=2:duration=first[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-shortest", out_file
    ]
    run(cmd)

def create_video_blocks(images, narr_files, tanpura_file):
    blocks = []
    for i, (img, narr) in enumerate(zip(images, narr_files)):
        out_file = f"{VIDEO_FOLDER}/{i:03}.mp4"
        create_video_block(img, narr, tanpura_file, out_file)
        blocks.append(out_file)
    return blocks

# ---------------- MERGE ----------------
def merge_blocks(blocks):
    with open("blocks.txt", "w") as f:
        for b in blocks:
            f.write(f"file '{b}'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "blocks.txt", "-c", "copy", FINAL_VIDEO])

# ---------------- MAIN ----------------
def main():
    print("🎨 Generating AI images...")
    images = generate_all_images()
    
    print("🔊 Preparing audio...")
    tanpura_file = create_tanpura_audio()
    narr_files = generate_narration_blocks()
    
    print("🎞 Creating video blocks...")
    blocks = create_video_blocks(images, narr_files[:len(images)], tanpura_file)
    
    print("🔗 Merging video blocks...")
    merge_blocks(blocks)
    
    print(f"✅ Final video ready: {FINAL_VIDEO}")

if __name__ == "__main__":
    main()