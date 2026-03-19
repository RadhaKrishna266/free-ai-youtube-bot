import os
import requests
import subprocess
import random
import asyncio
import edge_tts
from pydub import AudioSegment

PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")

SEARCH_TERMS = ["nature", "ocean", "storm", "animal", "lightning"]

NUM_CLIPS = 4
CLIP_DURATION = 6
FINAL_VIDEO = "viral_shorts.mp4"

os.makedirs("clips", exist_ok=True)
os.makedirs("tts", exist_ok=True)

LINES = [
    "This moment shocked everyone.",
    "Watch carefully what happens next.",
    "Nobody expected this.",
    "This was caught on camera."
]

# ================= DOWNLOAD + PROPER VERTICAL FORMAT =================
def download_clip(term, i):

    url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={term}&per_page=3"
    data = requests.get(url).json()
    hits = data.get("hits", [])

    if not hits:
        return None

    video_url = hits[0]["videos"]["medium"]["url"]

    raw = f"clips/raw_{i}.mp4"
    clip = f"clips/clip_{i}.mp4"

    r = requests.get(video_url)

    with open(raw, "wb") as f:
        f.write(r.content)

    # ⭐ Proper landscape → vertical conversion
    subprocess.run([
        "ffmpeg",
        "-y",
        "-i", raw,
        "-t", str(CLIP_DURATION),
        "-vf",
        "scale=720:-1,pad=720:1280:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264",
        "-c:a", "aac",
        clip
    ], check=True)

    return clip


# ================= TTS =================
async def generate_voice(text, file):

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
def concat_videos(files):

    listfile = "clips/list.txt"

    with open(listfile, "w") as f:
        for clip in files:
            f.write(f"file '{os.path.abspath(clip)}'\n")

    out = "temp_video.mp4"

    subprocess.run([
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", listfile,
        "-c:v", "libx264",
        "-c:a", "aac",
        out
    ], check=True)

    return out


# ================= MERGE VIDEO + AUDIO =================
def merge_video_audio(video, audio):

    subprocess.run([
        "ffmpeg",
        "-y",
        "-stream_loop", "-1",   # 🔥 loop video if audio longer
        "-i", video,
        "-i", audio,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        "-movflags", "+faststart",
        FINAL_VIDEO
    ], check=True)


# ================= MAIN =================
async def main():

    clips = []

    for i in range(NUM_CLIPS):

        term = random.choice(SEARCH_TERMS)
        clip = download_clip(term, i)

        if clip:
            clips.append(clip)

    if not clips:
        print("❌ No clips downloaded")
        return

    audio_files = []

    for i in range(len(clips)):

        file = f"tts/voice_{i}.mp3"

        await generate_voice(LINES[i % len(LINES)], file)

        audio_files.append(file)

    final_audio = merge_audio(audio_files, "tts/final.mp3")

    video = concat_videos(clips)

    merge_video_audio(video, final_audio)

    os.remove(video)

    print("🎬 SUCCESS — Video created:", FINAL_VIDEO)


if __name__ == "__main__":
    asyncio.run(main())