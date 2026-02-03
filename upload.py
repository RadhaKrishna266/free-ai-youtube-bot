import os
import asyncio
import subprocess
import requests
import edge_tts
from PIL import Image

# ================= CONFIG =================
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")
VOICE = "hi-IN-MadhurNeural"

START_IMAGE = "image1.png"
SCRIPT_FILE = "script.txt"
TANPURA = "tanpura.mp3"

os.makedirs("tts", exist_ok=True)
os.makedirs("images", exist_ok=True)
os.makedirs("clips", exist_ok=True)

# ================= HELPERS =================
def run(cmd):
    subprocess.run(cmd, check=True)

def audio_duration(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path
    ])
    return float(out.strip())

# ================= TTS =================
async def tts(text, out):
    communicate = edge_tts.Communicate(text=text, voice=VOICE)
    await communicate.save(out)
    print(f"▶ TTS saved: {out}")

# ================= PIXABAY =================
def fetch_images(query, count=10):
    print(f"▶ Fetching images for '{query}'")
    url = "https://pixabay.com/api/"
    params = {
        "key": PIXABAY_API_KEY,
        "q": query,
        "image_type": "photo",
        "per_page": count,
        "safesearch": "true"
    }
    r = requests.get(url, params=params).json()
    paths = []
    for i, hit in enumerate(r.get("hits", [])):
        img = requests.get(hit["largeImageURL"]).content
        p = f"images/{i:03}.jpg"
        with open(p, "wb") as f:
            f.write(img)
        paths.append(p)
    return paths

# ================= MAIN =================
async def main():
    print("🚀 Vishnu Purana Daily Bot Started")

    # ---------- Read Script ----------
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        story = [x.strip() for x in f.read().split("\n") if x.strip()]

    start_text = "सनातन ज्ञान की इस पावन धारा में आपका हार्दिक स्वागत है। आज हम विष्णु पुराण की कथा का श्रवण करेंगे।"
    end_text = "यह थी आज की विष्णु पुराण कथा। कल पुनः मिलेंगे एक नए अध्याय के साथ। हरि ओम्।"

    # ---------- TTS ----------
    audio_files = []
    await tts(start_text, "tts/start.mp3")
    audio_files.append("tts/start.mp3")

    for i, line in enumerate(story):
        out = f"tts/n_{i:03}.mp3"
        await tts(line, out)
        audio_files.append(out)

    await tts(end_text, "tts/end.mp3")
    audio_files.append("tts/end.mp3")

    # ---------- Combine Voice ----------
    with open("tts/list.txt", "w") as f:
        for a in audio_files:
            f.write(f"file '{a}'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "tts/list.txt",
        "-c", "copy",
        "voice.mp3"
    ])

    # ---------- Add Tanpura (optional) ----------
    if os.path.exists(TANPURA):
        run([
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", TANPURA,
            "-i", "voice.mp3",
            "-filter_complex",
            "[0:a]volume=0.25[a0];[a0][1:a]amix=inputs=2:dropout_transition=2",
            "-shortest",
            "final_audio.mp3"
        ])
    else:
        print("⚠ tanpura.mp3 not found, using voice only")
        os.rename("voice.mp3", "final_audio.mp3")

    # ---------- Images ----------
    images = []
    if os.path.exists(START_IMAGE):
        images.append(START_IMAGE)

    images += fetch_images("Vishnu krishna", 12)

    total_duration = audio_duration("final_audio.mp3")
    per_img = total_duration / len(images)

    clips = []
    for i, img in enumerate(images):
        clip = f"clips/c_{i:03}.mp4"
        run([
            "ffmpeg", "-y",
            "-loop", "1", "-i", img,
            "-t", str(per_img),
            "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:black",
            "-pix_fmt", "yuv420p",
            clip
        ])
        clips.append(clip)

    with open("clips/list.txt", "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "clips/list.txt",
        "-i", "final_audio.mp3",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        "final_video.mp4"
    ])

    print("✅ FINAL VIDEO READY: final_video.mp4")

# ================= RUN =================
if __name__ == "__main__":
    asyncio.run(main())