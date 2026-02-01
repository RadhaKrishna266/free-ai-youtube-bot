import os
import subprocess
import edge_tts
from pathlib import Path
from PIL import Image
import requests

# ---------------- CONFIG ----------------
SCRIPT_FILE = "script.txt"  # Your narration script
IMAGE_FOLDER = "images"     # AI images folder
VIDEO_BLOCKS = "video_blocks"
AUDIO_BLOCKS = "audio_blocks"
FINAL_VIDEO = "final_video.mp4"
TANPURA_FILE = "audio/bg_tanpura.mp3"
VIDEO_SIZE = (1280, 720)
FPS = 25
DURATION_PER_BLOCK = 6  # seconds per image block
ZOOM_SPEED = 0.0005
MAX_ZOOM = 1.06
TANPURA_FREQ = 110
TANPURA_VOLUME = 0.15

Path(VIDEO_BLOCKS).mkdir(exist_ok=True)
Path(AUDIO_BLOCKS).mkdir(exist_ok=True)
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

# ---------------- NARRATION ----------------
async def generate_single_narration(text, out_path):
    communicate = edge_tts.Communicate(text, voice="hi-IN-MadhurNeural")
    await communicate.save(out_path)

def generate_narration_blocks(script_path=SCRIPT_FILE):
    # Read script
    lines = [line.strip() for line in Path(script_path).read_text(encoding="utf-8").split("\n") if line.strip()]
    
    # Add intro/outro
    intro = "नमस्कार। स्वागत है आप सभी का Sanatan Gyan Dhara श्रृंखला में। आज हम आपके लिए Vishnu Purana का पहला एपिसोड लाए हैं।"
    outro = "🙏 अगर आपको यह वीडियो पसंद आया हो, तो कृपया लाइक, शेयर और सब्सक्राइब जरूर करें। हर दिन एक नया एपिसोड आएगा।"
    
    blocks = [intro] + lines + [outro]
    
    narr_files = []
    import asyncio
    for i, text in enumerate(blocks):
        out_file = f"{AUDIO_BLOCKS}/{i:03}.mp3"
        asyncio.run(generate_single_narration(text, out_file))
        narr_files.append(out_file)
    return narr_files

# ---------------- VIDEO BLOCK ----------------
def create_video_block(img_path, narration_file, tanpura_file, output_file):
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", img_path,
        "-i", narration_file,
        "-i", tanpura_file,
        "-filter_complex",
        f"[0:v]scale={VIDEO_SIZE[0]}:{VIDEO_SIZE[1]}:force_original_aspect_ratio=decrease,"
        f"pad={VIDEO_SIZE[0]}:{VIDEO_SIZE[1]}:(ow-iw)/2:(oh-ih)/2,"
        f"zoompan=z='min(zoom+{ZOOM_SPEED},{MAX_ZOOM})':d={DURATION_PER_BLOCK*FPS}:fps={FPS}[v];"
        f"[1:a][2:a]amix=inputs=2:duration=first[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-shortest", output_file
    ]
    run(cmd)

def create_video_blocks(images, narr_files, tanpura_file):
    blocks = []
    for i, (img, narr) in enumerate(zip(images, narr_files)):
        out_file = f"{VIDEO_BLOCKS}/{i:03}.mp4"
        create_video_block(img, narr, tanpura_file, out_file)
        blocks.append(out_file)
    return blocks

# ---------------- MERGE ----------------
def merge_blocks(blocks, output_file=FINAL_VIDEO):
    with open("blocks.txt", "w") as f:
        for b in blocks:
            f.write(f"file '{b}'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "blocks.txt", "-c", "copy", output_file])

# ---------------- MAIN ----------------
def main():
    print("🎨 Preparing AI images...")
    images = sorted(Path(IMAGE_FOLDER).glob("*.*"))
    if not images:
        raise Exception(f"No images found in {IMAGE_FOLDER}/")
    
    print("🔊 Preparing audio...")
    tanpura_file = create_tanpura_audio()
    narr_files = generate_narration_blocks()
    
    print("🎞 Creating video blocks...")
    blocks = create_video_blocks([str(img) for img in images], narr_files, tanpura_file)
    
    print("🔗 Merging video blocks...")
    merge_blocks(blocks)
    
    print(f"✅ Final video ready: {FINAL_VIDEO}")

if __name__ == "__main__":
    main()