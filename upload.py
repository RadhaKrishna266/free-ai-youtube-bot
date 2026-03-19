import os
import requests
import subprocess
import asyncio
import edge_tts
from pydub import AudioSegment

# ================= CONFIG =================
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")
FINAL_VIDEO = "final_video_episode_1.mp4"
VOICE = "en-US-GuyNeural"

if not PIXABAY_API_KEY:
    raise ValueError("PIXABAY_API_KEY not found!")

os.makedirs("clips", exist_ok=True)
os.makedirs("tts", exist_ok=True)

# ================= SCENES =================
SCENES = [
    ("If the Sun suddenly disappeared", "sun space"),
    ("Earth would not notice for 8 minutes", "earth space sunlight"),
    ("Then total darkness would cover the planet", "earth dark space"),
    ("Temperatures would drop rapidly", "frozen landscape"),
    ("Oceans would begin to freeze", "frozen ocean"),
    ("Humanity would struggle to survive", "abandoned city"),
    ("Within a year Earth becomes an ice world", "ice planet"),
    ("But the Sun returns", "sunrise earth space"),
    ("Nothing would ever be the same again", "earth from space dramatic")
]

# ================= DOWNLOAD CLIP =================
def download_clip(term, i):

    url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={term}&per_page=3"

    response = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    if response.status_code != 200:
        print("API Error:", response.text)
        return None

    try:
        data = response.json()
    except:
        print("Invalid JSON:", response.text)
        return None

    hits = data.get("hits", [])
    if not hits:
        print("No clip found for:", term)
        return None

    video_url = hits[0]["videos"]["medium"]["url"]
    filename = f"clips/clip_{i}.mp4"

    r = requests.get(video_url, stream=True)
    with open(filename, "wb") as f:
        for chunk in r.iter_content(1024 * 1024):
            f.write(chunk)

    return filename

# ================= TTS =================
async def generate_tts(text, output):
    tts = edge_tts.Communicate(text, VOICE)
    await tts.save(output)

# ================= CONCAT VIDEO =================
def concat_videos(video_list):

    list_file = "clips/list.txt"
    with open(list_file, "w") as f:
        for v in video_list:
            f.write(f"file '{os.path.abspath(v)}'\n")

    subprocess.run([
        "ffmpeg","-y","-f","concat","-safe","0",
        "-i",list_file,
        "-c","copy",
        "clips/concat.mp4"
    ], check=True)

    return "clips/concat.mp4"

# ================= MERGE AUDIO =================
def merge_audio(audio_files, output):

    combined = AudioSegment.empty()
    for f in audio_files:
        combined += AudioSegment.from_file(f)

    combined.export(output, format="mp3")
    return output

# ================= FINAL MERGE =================
def merge_video_audio(video, audio):

    subprocess.run([
        "ffmpeg","-y",
        "-i",video,
        "-i",audio,
        "-c:v","copy",
        "-c:a","aac",
        "-shortest",
        FINAL_VIDEO
    ], check=True)

# ================= MAIN =================
async def main():

    video_files = []
    audio_files = []

    for i, (text, term) in enumerate(SCENES, 1):

        clip = download_clip(term, i)
        if clip:
            video_files.append(clip)

        audio_file = f"tts/scene_{i}.mp3"
        await generate_tts(text, audio_file)
        audio_files.append(audio_file)

    if not video_files:
        raise RuntimeError("No video clips downloaded!")

    narration = "tts/narration.mp3"
    merge_audio(audio_files, narration)

    video = concat_videos(video_files)
    merge_video_audio(video, narration)

    print("🎬 VIDEO CREATED:", FINAL_VIDEO)

# ================= RUN =================
if __name__ == "__main__":
    asyncio.run(main())