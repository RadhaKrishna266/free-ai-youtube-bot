import os
import requests
import subprocess
import random
import asyncio
import edge_tts
from pydub import AudioSegment

PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")

# ================= VIRAL TOPIC =================
SEARCH_TERMS = [
    "building collapse",
    "bridge collapse",
    "storm destruction",
    "car crash slow motion",
    "danger accident"
]

HOOK_TEXT = "MOMENTS BEFORE DISASTER 😱"

LINES = [
    "Everything looked normal just seconds before disaster",
    "Nobody realized what was about to happen",
    "One small moment changed everything instantly",
    "This footage was captured just before impact"
]

NUM_CLIPS = 4
CLIP_DURATION = 5
FINAL_VIDEO = "viral_shorts.mp4"

os.makedirs("clips", exist_ok=True)
os.makedirs("tts", exist_ok=True)


# ================= DOWNLOAD CLIP =================
def download_clip(term, i):

    url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={term}&per_page=3"
    data = requests.get(url).json()

    if not data["hits"]:
        return None

    video_url = data["hits"][0]["videos"]["medium"]["url"]

    raw = f"clips/raw_{i}.mp4"
    clip = f"clips/clip_{i}.mp4"

    r = requests.get(video_url)

    with open(raw, "wb") as f:
        f.write(r.content)

    # Convert to vertical Shorts format
    subprocess.run([
        "ffmpeg", "-y",
        "-i", raw,
        "-t", str(CLIP_DURATION),
        "-vf", "scale=720:-1,pad=720:1280:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264",
        "-c:a", "aac",
        clip
    ], check=True)

    return clip


# ================= TEXT TO SPEECH =================
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


# ================= CONCAT VIDEOS =================
def concat_videos(files):

    listfile = "clips/list.txt"

    with open(listfile, "w") as f:
        for clip in files:
            f.write(f"file '{os.path.abspath(clip)}'\n")

    out = "temp_video.mp4"

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", listfile,
        "-c:v", "libx264",
        "-c:a", "aac",
        out
    ], check=True)

    return out


# ================= ADD HOOK TEXT =================
def add_text_overlay(video):

    out = "text_video.mp4"

    draw = (
        "drawtext=text='{}':"
        "fontcolor=white:fontsize=70:"
        "x=(w-text_w)/2:y=120:"
        "box=1:boxcolor=black@0.6:boxborderw=20"
    ).format(HOOK_TEXT)

    subprocess.run([
        "ffmpeg", "-y",
        "-i", video,
        "-vf", draw,
        "-c:v", "libx264",
        "-c:a", "copy",
        out
    ], check=True)

    return out


# ================= MERGE VIDEO + AUDIO =================
def merge_video_audio(video, audio):

    subprocess.run([
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", video,
        "-i", audio,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
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

    # 🎙️ Generate narration
    audio_files = []

    for i in range(len(clips)):

        file = f"tts/voice_{i}.mp3"
        await generate_voice(LINES[i % len(LINES)], file)
        audio_files.append(file)

    final_audio = merge_audio(audio_files, "tts/final.mp3")

    video = concat_videos(clips)

    video_with_text = add_text_overlay(video)

    merge_video_audio(video_with_text, final_audio)

    print("🔥 VIRAL VIDEO READY:", FINAL_VIDEO)


if __name__ == "__main__":
    asyncio.run(main())