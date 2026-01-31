import os
import subprocess
import requests
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
FALLBACK_IMAGES_DIR = "fallback_images"  # Pre-downloaded Vishnu/Avatars images
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY")

# ---------------- CREATE FOLDERS ----------------
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(FALLBACK_IMAGES_DIR, exist_ok=True)

# ---------------- UTILS ----------------
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ---------------- PLACEHOLDER ----------------
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

# ---------------- WIKIMEDIA IMAGE FETCH ----------------
def wikimedia_images(query="Vishnu Dashavatara illustration", limit=50):
    print(f"🖼 Downloading {limit} Vishnu images from Wikimedia...")
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": query,
        "gsrlimit": str(limit),
        "prop": "imageinfo",
        "iiprop": "url",
        "format": "json",
        "gsrnamespace": 6
    }
    headers = {"User-Agent": "VishnuPuranaVideoBot/1.0 (example@example.com)"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, ValueError) as e:
        print("❌ Wikimedia API failed:", e)
        return []

    images = []
    pages = data.get("query", {}).get("pages", {})
    for p in pages.values():
        ii = p.get("imageinfo", [])
        if ii:
            images.append(ii[0]["url"])
    print(f"✅ Found {len(images)} images from Wikimedia")
    return images

# ---------------- DOWNLOAD VISHNU IMAGES ----------------
def download_images(blocks):
    print("🖼 Preparing Vishnu images for video...")
    urls = wikimedia_images(limit=len(blocks) + 1)

    fallback_files = list(Path(FALLBACK_IMAGES_DIR).glob("*.jpg"))
    fallback_idx = 0

    for i, text in enumerate(blocks):
        path = f"{IMAGE_DIR}/{i:03d}.jpg"
        try:
            if urls:
                img_data = requests.get(urls[i % len(urls)], timeout=10).content
                with open(path, "wb") as f:
                    f.write(img_data)
            elif fallback_files:
                # Use fallback local image
                fallback_file = fallback_files[fallback_idx % len(fallback_files)]
                img = Image.open(fallback_file)
                img.save(path)
                fallback_idx += 1
            else:
                placeholder(path)
        except Exception as e:
            print("❌ Failed to download image, using placeholder:", e)
            placeholder(path)

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
        clip = f"{VIDEO_DIR}/{i:03d}.mp4"
        run([
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", f"{IMAGE_DIR}/{i:03d}.jpg",
            "-i", f"{AUDIO_DIR}/{i:03d}.wav",
            "-vf", "scale=1280:720,format=yuv420p",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            clip
        ])
        clips.append(clip)

    with open("list.txt", "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "list.txt",
        "-c", "copy",
        FINAL_VIDEO
    ])

# ---------------- MAIN ----------------
def main():
    # Read script and add daily intro/outro
    blocks = Path(SCRIPT_FILE).read_text(encoding="utf-8").split("\n\n")
    intro = "नमस्कार। स्वागत है आप सभी का VishnuPriya श्रृंखला में। आज हम आपके लिए Vishnu Purana का पहला एपिसोड लाए हैं।"
    outro = "\n\n🙏 अगर आपको यह वीडियो पसंद आया हो, तो कृपया लाइक, शेयर और सब्सक्राइब जरूर करें। हर दिन एक नया एपिसोड आएगा।"
    blocks.insert(0, intro)
    blocks.append(outro)

    download_images(blocks)
    generate_audio(blocks)
    create_video(blocks)
    print("✅ FINAL VISHNU VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()