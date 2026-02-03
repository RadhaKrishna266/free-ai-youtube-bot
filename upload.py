import os, asyncio, subprocess, requests, edge_tts

PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")
VOICE = "hi-IN-MadhurNeural"

os.makedirs("tts", exist_ok=True)
os.makedirs("images", exist_ok=True)
os.makedirs("clips", exist_ok=True)

def run(cmd):
    subprocess.run(cmd, check=True)

def audio_duration(path):
    return float(subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path
    ]))

async def tts(text, out):
    await edge_tts.Communicate(text, VOICE).save(out)
    print(f"▶ TTS saved: {out}")

def pixabay_images(query, count=10):
    r = requests.get(
        "https://pixabay.com/api/",
        params={
            "key": PIXABAY_API_KEY,
            "q": query,
            "image_type": "photo",
            "safesearch": "true",
            "per_page": count
        }
    ).json()

    imgs = []
    for i, h in enumerate(r.get("hits", [])):
        img = requests.get(h["largeImageURL"]).content
        path = f"images/{i:03}.jpg"
        open(path, "wb").write(img)
        imgs.append(path)
    return imgs

async def main():
    print("🚀 Vishnu Purana Daily Bot Started")

    story = [l.strip() for l in open("script.txt", encoding="utf-8") if l.strip()]

    start = "सनातन धर्म की इस पावन धारा में आपका स्वागत है। आज हम विष्णु पुराण की कथा सुनेंगे।"
    end = "यह थी आज की विष्णु पुराण कथा। हरि ओम्।"

    audio_files = []

    await tts(start, "tts/start.mp3")
    audio_files.append("start.mp3")

    for i, line in enumerate(story):
        f = f"n_{i:03}.mp3"
        await tts(line, f"tts/{f}")
        audio_files.append(f)

    await tts(end, "tts/end.mp3")
    audio_files.append("end.mp3")

    with open("tts/list.txt", "w") as f:
        for a in audio_files:
            f.write(f"file '{a}'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "tts/list.txt",
        "-c", "copy",
        "final_audio.mp3"
    ])

    images = pixabay_images("Vishnu krishna", 12)

    dur = audio_duration("final_audio.mp3")
    per = dur / len(images)

    clips = []
    for i, img in enumerate(images):
        out = f"clips/{i:03}.mp4"
        run([
            "ffmpeg", "-y",
            "-loop", "1", "-i", img,
            "-t", str(per),
            "-vf",
            "scale=1280:720:force_original_aspect_ratio=decrease,"
            "pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=black",
            "-pix_fmt", "yuv420p",
            out
        ])
        clips.append(out)

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

    print("✅ FINAL VIDEO CREATED → final_video.mp4")

if __name__ == "__main__":
    asyncio.run(main())