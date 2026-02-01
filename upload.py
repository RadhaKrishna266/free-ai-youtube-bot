import os
import requests
from bs4 import BeautifulSoup
from PIL import Image
import subprocess
import shutil

# ================= CONFIG =================
QUERY = "vaikunth vishnu vishnu avtara lakshmi vishnu wallpaper"
BLOCKS = 5  # Number of video blocks you want
OUTPUT_DIR = "video_blocks"
IMAGES_DIR = "images"
AUDIO_BLOCKS_DIR = "audio_blocks"
TANPURA_AUDIO = "audio/tanpura.mp3"
FINAL_VIDEO = "final_video.mp4"

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ================= FETCH GOOGLE IMAGES =================
def fetch_google_images_highres(query, max_images=20):
    url = f"https://www.google.com/search?q={query}&tbm=isch"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    urls = []
    for img in soup.find_all("img"):
        src = img.get("data-src") or img.get("src")
        if src and src.startswith("http") and src not in urls:
            urls.append(src)
        if len(urls) >= max_images:
            break
    return urls

# ================= DOWNLOAD IMAGES =================
def download_images(urls):
    paths = []
    for i, url in enumerate(urls):
        path = os.path.join(IMAGES_DIR, f"{i:03}.jpg")
        try:
            r = requests.get(url, stream=True, timeout=10)
            if r.status_code == 200:
                with open(path, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
                resize_for_video(path)
                paths.append(path)
        except:
            continue
    return paths

# ================= RESIZE IMAGES =================
def resize_for_video(path):
    with Image.open(path) as img:
        img.thumbnail((1280, 720))
        new_img = Image.new("RGB", (1280, 720), (0,0,0))
        new_img.paste(img, ((1280-img.width)//2, (720-img.height)//2))
        new_img.save(path)

# ================= CREATE VIDEO BLOCK =================
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

def create_video(images, audio_blocks, tanpura_audio):
    for i, (img, audio) in enumerate(zip(images, audio_blocks)):
        out = os.path.join(OUTPUT_DIR, f"{i:03}.mp4")
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", img,
            "-i", audio,
            "-i", tanpura_audio,
            "-filter_complex",
            "[2:a]volume=0.2[a2];[1:a][a2]amix=inputs=2:duration=first:dropout_transition=2[a]",
            "-map", "0:v", "-map", "[a]",
            "-c:v", "libx264", "-c:a", "aac", "-shortest", out
        ]
        run(cmd)

# ================= MERGE VIDEO BLOCKS =================
def merge_videos():
    with open("video_list.txt", "w") as f:
        for i in range(len(os.listdir(OUTPUT_DIR))):
            f.write(f"file '{OUTPUT_DIR}/{i:03}.mp4'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "video_list.txt", "-c", "copy", FINAL_VIDEO])
    os.remove("video_list.txt")

# ================= MAIN =================
def main():
    print("🌐 Fetching images from Google...")
    urls = fetch_google_images_highres(QUERY, max_images=BLOCKS*2)
    images = download_images(urls)

    if len(images) < BLOCKS:
        raise Exception("❌ Not enough unique images. Increase blocks or max_images.")

    audio_files = sorted([os.path.join(AUDIO_BLOCKS_DIR, f"{i:03}.mp3") for i in range(BLOCKS)])
    create_video(images[:BLOCKS], audio_files, TANPURA_AUDIO)
    merge_videos()
    print(f"✅ Final video created: {FINAL_VIDEO}")

if __name__ == "__main__":
    main()