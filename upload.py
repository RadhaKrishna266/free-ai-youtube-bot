import os
import requests
import subprocess
import random
import asyncio
import edge_tts
from pydub import AudioSegment

# ================= CONFIG =================
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")

SEARCH_TERMS = ["temple", "meditation", "nature", "india", "spiritual"]
NUM_CLIPS = 5
CLIP_DURATION = 8   # ⭐ seconds per clip (viral length)
FINAL_VIDEO = "final_video_episode_1.mp4"

os.makedirs("clips", exist_ok=True)
os.makedirs("tts", exist_ok=True)

# ================= STEP 1: Download + Trim Clip =================
def download_clip(search_term, index):
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={search_term}&per_page=5"

    response = requests.get(url)
    data = response.json()
    hits = data.get("hits", [])

    if not hits:
        print("❌ No clips found")
        return None

    video_url = hits[0]["videos"]["medium"]["url"]
    raw_file = f"clips/raw_{index}.mp4"
    trimmed_file = f"clips/clip_{index}.mp4"

    # Download
    with requests.get(video_url, stream=True) as r:
        with open(raw_file, "wb") as f:
            for chunk in r.iter_content(1024 * 1024):
                f.write(chunk)

    # Trim to fixed duration ⭐
    subprocess.run([
        "ffmpeg", "-y",
        "-i", raw_file,
        "-t", str(CLIP_DURATION),
        "-c:v", "libx264",
        "-c:a", "aac",
        trimmed_file
    ], check=True)

    print(f"⬇️ Clip ready: {trimmed_file}")
    return trimmed_file


# ================= STEP 2: Generate TTS =================
async def generate_tts(text, output_file):
    communicate = edge_tts.Communicate(text, "hi-IN-SwaraNeural")
    await communicate.save(output_file)
    print(f"🎤 TTS created: {output_file}")


# ================= STEP 3: Merge Audio =================
def merge_audio(audio_files, output_file):
    combined = AudioSegment.empty()

    for file in audio_files:
        combined += AudioSegment.from_file(file)

    combined.export(output_file, format="mp3")
    print("✅ Audio merged")
    return output_file


# ================= STEP 4: Concatenate Clips =================
def concat_clips(clip_files, output_file="clips/concat.mp4"):
    list_file = "clips/list.txt"

    with open(list_file, "w") as f:
        for clip in clip_files:
            f.write(f"file '{os.path.abspath(clip)}'\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_file,
        "-c", "copy",
        output_file
    ], check=True)

    print("✅ Video clips combined")
    return output_file


# ================= STEP 5: Merge Video + Audio (SYNCED) =================
def merge_video_audio(video_file, audio_file, output_file):
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video_file,
        "-i", audio_file,
        "-map", "0:v",
        "-map", "1:a",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",   # ⭐ IMPORTANT FIX
        output_file
    ], check=True)

    print(f"🎬 Final video created: {output_file}")


# ================= MAIN =================
async def main():

    # 1️⃣ Download clips
    clip_files = []

    for i in range(NUM_CLIPS):
        term = random.choice(SEARCH_TERMS)
        clip = download_clip(term, i + 1)

        if clip:
            clip_files.append(clip)

    if not clip_files:
        print("❌ No clips downloaded")
        return

    # 2️⃣ Create captions
    captions = [
        "भगवान की कृपा से सब संभव है",
        "सकारात्मक ऊर्जा आपके साथ है",
        "विश्वास रखिए, चमत्कार होगा",
        "ध्यान से मन शांत होता है",
        "ईश्वर हमेशा साथ हैं"
    ]

    audio_files = []

    for i in range(len(clip_files)):
        text = random.choice(captions)
        file = f"tts/audio_{i}.mp3"
        await generate_tts(text, file)
        audio_files.append(file)

    # 3️⃣ Merge audio
    final_audio = "tts/final_audio.mp3"
    merge_audio(audio_files, final_audio)

    # 4️⃣ Combine clips
    video_concat = concat_clips(clip_files)

    # 5️⃣ Merge video + audio (SYNCED)
    merge_video_audio(video_concat, final_audio, FINAL_VIDEO)


# ================= RUN =================
if __name__ == "__main__":
    asyncio.run(main())