import os
import requests
import subprocess
import random
import asyncio
import edge_tts
from pydub import AudioSegment

PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")

SEARCH_TERMS = [
    "surprise", "explosion", "storm",
    "wild animal", "accident", "lightning"
]

NUM_CLIPS = 4
CLIP_DURATION = 6
FINAL_VIDEO = "viral_shorts.mp4"

os.makedirs("clips", exist_ok=True)
os.makedirs("tts", exist_ok=True)

# 🔥 Suspense narration
LINES = [
    "This moment shocked everyone.",
    "Watch carefully what happens next.",
    "Nobody expected this.",
    "This was caught on camera."
]

# ================= DOWNLOAD + TRIM =================
def download_clip(term, i):
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={term}&per_page=5"
    data = requests.get(url).json()
    hits = data.get("hits", [])

    if not hits:
        return None

    video_url = hits[0]["videos"]["medium"]["url"]

    raw = f"clips/raw_{i}.mp4"
    out = f"clips/clip_{i}.mp4"

    with requests.get(video_url, stream=True) as r:
        with open(raw, "wb") as f:
            for chunk in r.iter_content(1024 * 1024):
                f.write(chunk)

    # ⭐ Convert to vertical + trim
    subprocess.run([
        "ffmpeg", "-y",
        "-i", raw,
        "-t", str(CLIP_DURATION),
        "-vf", "scale=1080:1920,setsar=1",
        "-c:v", "libx264",
        "-c:a", "aac",
        out
    ], check=True)

    return out


# ================= TTS =================
async def generate_tts(text, file):
    tts = edge_tts.Communicate(text, "en-US-GuyNeural")
    await tts.save(file)


# ================= MERGE AUDIO =================
def merge_audio(files, output):
    combined = AudioSegment.empty()
    for f in files:
        combined += AudioSegment.from_file(f)
    combined.export(output, format="mp3")
    return output


# ================= CONCAT VIDEO =================
def concat_clips(files, out="clips/concat.mp4"):
    txt = "clips/list.txt"
    with open(txt, "w") as f:
        for clip in files:
            f.write(f"file '{os.path.abspath(clip)}'\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", txt,
        "-c", "copy",
        out
    ], check=True)

    return out


# ================= MERGE VIDEO + AUDIO =================
def merge_video_audio(video, audio, out):
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video,
        "-i", audio,
        "-map", "0:v",
        "-map", "1:a",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        out
    ], check=True)


# ================= MAIN =================
async def main():

    clips = []

    for i in range(NUM_CLIPS):
        term = random.choice(SEARCH_TERMS)
        c = download_clip(term, i)
        if c:
            clips.append(c)

    if not clips:
        return

    # 🎤 Narration
    audio_files = []
    for i in range(len(clips)):
        text = LINES[i % len(LINES)]
        f = f"tts/a{i}.mp3"
        await generate_tts(text, f)
        audio_files.append(f)

    final_audio = merge_audio(audio_files, "tts/final.mp3")
    video = concat_clips(clips)

    merge_video_audio(video, final_audio, FINAL_VIDEO)


if __name__ == "__main__":
    asyncio.run(main())