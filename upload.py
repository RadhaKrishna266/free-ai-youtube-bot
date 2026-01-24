import os
import subprocess
import requests

# ================= CONFIG =================
PIXABAY_KEY = os.environ["PIXABAY_API_KEY"]

SCRIPT_FILE = "script.txt"
VOICE_FILE = "narration.wav"
FINAL_VIDEO = "final.mp4"

IMAGE_COUNT = 100          # 100 × 6 sec = 10 min
IMAGE_DURATION = 6

PIPER_BIN = "./piper/piper"
PIPER_MODEL = "piper/hi_IN-cmu_indic-medium.onnx"

# ========================================

def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

# ================= AUDIO =================
def create_audio():
    print("🎤 Creating Hindi devotional narration")

    if not os.path.exists(PIPER_MODEL):
        raise RuntimeError("❌ Hindi Piper model missing")

    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        text = f.read()

    cmd = [
        PIPER_BIN,
        "--model", PIPER_MODEL,
        "--output_file", VOICE_FILE
    ]

    subprocess.run(
        cmd,
        input=text.encode("utf-8"),
        check=True
    )

    print("✅ Hindi narration created")

# ================= IMAGES =================
def download_images():
    print("🖼️ Downloading GOD / TEMPLE images")

    os.makedirs("images", exist_ok=True)

    query = (
        "hindu+god+temple+shiva+krishna+ram+animated+spiritual"
    )

    url = (
        f"https://pixabay.com/api/?key={PIXABAY_KEY}"
        f"&q={query}"
        "&image_type=photo"
        "&orientation=horizontal"
        "&safesearch=true"
        "&per_page=200"
    )

    data = requests.get(url).json()
    hits = data.get("hits", [])

    if len(hits) < IMAGE_COUNT:
        raise RuntimeError("❌ Not enough images from Pixabay")

    for i in range(IMAGE_COUNT):
        img_url = hits[i]["largeImageURL"]
        img_data = requests.get(img_url).content

        with open(f"images/{i:03}.jpg", "wb") as f:
            f.write(img_data)

    print(f"✅ {IMAGE_COUNT} divine images downloaded")

# ================= SLIDESHOW =================
def create_slideshow():
    print("📝 Creating slideshow file")

    with open("slideshow.txt", "w") as f:
        for img in sorted(os.listdir("images")):
            f.write(f"file 'images/{img}'\n")
            f.write(f"duration {IMAGE_DURATION}\n")

# ================= VIDEO =================
def create_video():
    print("🎬 Creating GOD animated video")

    run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "slideshow.txt",
        "-i", VOICE_FILE,
        "-vf",
        "scale=1280:720:force_original_aspect_ratio=decrease,"
        "pad=1280:720:(ow-iw)/2:(oh-ih)/2,"
        "zoompan=z='min(zoom+0.0005,1.05)':d=150",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        FINAL_VIDEO
    ])

    print("✅ Final video created")

# ================= MAIN =================
def main():
    print("🔥 STARTING GOD ANIMATED VIDEO PIPELINE")

    create_audio()
    download_images()
    create_slideshow()
    create_video()

    print("🙏 VIDEO READY:", FINAL_VIDEO)

if __name__ == "__main__":
    main()