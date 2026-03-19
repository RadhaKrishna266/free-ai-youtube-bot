import os
import requests
import subprocess
import asyncio
import edge_tts
from pydub import AudioSegment

# ================= CONFIG =================
PIXABAY_API_KEY = "YOUR_PIXABAY_API_KEY"
FINAL_VIDEO = "viral_space_video.mp4"
BACKGROUND_MUSIC = "background.mp3"  # optional
VOICE = "en-US-GuyNeural"  # cinematic voice

os.makedirs("clips", exist_ok=True)
os.makedirs("tts", exist_ok=True)

# ================= SCENE SCRIPT =================
SCENES = [
    ("If the Sun suddenly disappeared", "sun space"),
    ("Earth wouldn’t notice immediately", "earth from space day"),
    ("For 8 minutes everything would seem normal", "earth sunlight space"),
    ("Then suddenly total darkness", "earth dark space"),
    ("Temperatures would drop rapidly", "frozen landscape"),
    ("Plants would stop producing oxygen", "dead plants"),
    ("Within days the surface would freeze", "ice wasteland"),
    ("Humanity would not survive long", "abandoned city"),
    ("But the Sun would return", "sunrise earth space"),
    ("And nothing would ever be the same again", "earth from space dramatic")
]

# ================= DOWNLOAD CLIP =================
def download_clip(search_term, index):
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={search_term}&per_page=3"
    data = requests.get(url).json()
    hits = data.get("hits", [])
    if not hits:
        print("No clip for", search_term)
        return None

    video_url = hits[0]["videos"]["medium"]["url"]
    filename = f"clips/clip_{index}.mp4"

    r = requests.get(video_url, stream=True)
    with open(filename, "wb") as f:
        for chunk in r.iter_content(1024 * 1024):
            if chunk:
                f.write(chunk)

    return filename

# ================= TTS =================
async def generate_tts(text, output):
    tts = edge_tts.Communicate(text, VOICE)
    await tts.save(output)

# ================= CONCAT VIDEO =================
def concat_videos(video_list, output="clips/concat.mp4"):
    list_file = "clips/list.txt"
    with open(list_file, "w") as f:
        for v in video_list:
            f.write(f"file '{os.path.abspath(v)}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_file, "-c", "copy", output
    ], check=True)

    return output

# ================= MERGE AUDIO =================
def merge_audio(audio_files, output):
    combined = AudioSegment.empty()
    for a in audio_files:
        combined += AudioSegment.from_file(a)
    combined.export(output, format="mp3")
    return output

# ================= FINAL MERGE =================
def merge_video_audio(video, audio, output):
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video,
        "-i", audio,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        output
    ], check=True)

# ================= MAIN =================
async def main():

    video_files = []
    audio_files = []

    for i, (text, term) in enumerate(SCENES, 1):

        # Download matching clip
        clip = download_clip(term, i)
        if clip:
            video_files.append(clip)

        # Generate voice
        tts_file = f"tts/scene_{i}.mp3"
        await generate_tts(text, tts_file)
        audio_files.append(tts_file)

    # Merge audio narration
    narration = "tts/narration.mp3"
    merge_audio(audio_files, narration)

    # Add background music (optional)
    if os.path.exists(BACKGROUND_MUSIC):
        bg = AudioSegment.from_file(BACKGROUND_MUSIC)
        fg = AudioSegment.from_file(narration)

        while len(bg) < len(fg):
            bg += bg

        mixed = bg[:len(fg)].overlay(fg - 5)
        mixed.export(narration, format="mp3")

    # Concatenate video clips
    video_concat = concat_videos(video_files)

    # Final merge
    merge_video_audio(video_concat, narration, FINAL_VIDEO)

    print("🎬 VIRAL VIDEO CREATED:", FINAL_VIDEO)

# ================= RUN =================
if __name__ == "__main__":
    asyncio.run(main())