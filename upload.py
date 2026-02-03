import os
import asyncio
import subprocess
import requests
import edge_tts

PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")
VOICE = "hi-IN-MadhurNeural"

SCRIPT_FILE = "script.txt"
START_IMAGE = "image1.png"
TANPURA = "tanpura.mp3"

os.makedirs("tts", exist_ok=True)
os.makedirs("images", exist_ok=True)
os.makedirs("clips", exist_ok=True)

def run(cmd):
    subprocess.run(cmd, check=True)

def duration(file):
    out = subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file
    ])
    return float(out.strip())

async def tts(text, out):
    await edge_tts.Communicate(text, VOICE).save(out)
    print(f"▶ TTS saved: {out}")

def pixabay_images(query, count=12):
    url = "https://pixabay.com/api/"
    params = {
        "key": PIXABAY_API_KEY,
        "q": query,
        "image_type": "photo",
        "safesearch": "true",
        "per_page": count
    }
    r = requests.get(url, params=params).json()
    imgs = []
    for i, h in enumerate(r.get("hits", [])):
        img = requests.get(h["largeImageURL"]).content
        path = f"images/{i:03}.jpg"
        open(path, "wb").write(img)
        imgs.append(path)
    return imgs

async def main():
    print("🚀 Vishnu Purana Daily Bot Started")

    story = [x.strip() for x in open(SCRIPT_FILE, encoding="utf-8") if x.strip()]

    start = "सनातन धर्म की इस पावन धारा में आपका स्वागत है। आज हम विष्णु पुराण की कथा सुनेंगे।"
    end = "यह थी आज की विष्णु पुराण कथा। कल पुनः मिलेंगे। हरि ओम्।"

    audio = []

    await tts(start, "tts/start.mp3")
    audio.append("start.mp3")

    for i, line in enumerate(story):
        f = f"n_{i:03}.mp3"
        await tts(line, f"tts/{f}")
        audio.append(f)

    await tts(end, "tts/end.mp3")
    audio.append("end.mp3")

    # ✅ CORRECT concat list
    with open("tts/list.txt", "w") as f:
        for a in audio:
            f.write(f"file '{a}'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "tts/list.txt",
        "-c", "copy",
        "voice.mp3"
    ])

    if os.path.exists(TANPURA):
        run([
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", TANPURA,
            "-i", "voice.mp3",
            "-filter_complex",
            "[0:a]volume=0.25[a0];[a0][1:a]amix=inputs=2",
            "-shortest",
            "final_audio.mp3"
        ])
    else:
        os.rename("voice.mp3", "final_audio.mp3")

    images = []
    if os.path.exists(START_IMAGE):
        images.append(START_IMAGE)

    images += pixabay_images("Vishnu krishna")

    per = duration("final_audio.mp3") / len(images)

    clips = []
    for i, img in enumerate(images):
        c = f"clips/{i:03}.mp4"
        run([
            "ffmpeg", "-y",
            "-loop", "1", "-i", img,
            "-t", str(per),
            "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:black",
            "-pix_fmt", "yuv420p",
            c
        ])
        clips.append(c)

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

    print("✅ FINAL VIDEO READY → final_video.mp4")

if __name__ == "__main__":
    asyncio.run(main())