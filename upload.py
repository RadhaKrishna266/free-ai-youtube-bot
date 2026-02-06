import os
import requests
import subprocess
import random
import asyncio
import edge_tts

# ================= CONFIG =================
PIXABAY_API_KEY = "YOUR_PIXABAY_API_KEY"  # Free account
SEARCH_TERMS = ["funny", "animals", "nature", "amazing", "weird", "technology"]
NUM_CLIPS = 5                # Number of clips per video
CLIP_DURATION = 20            # Seconds per clip
FINAL_VIDEO = "compilation_video.mp4"
BACKGROUND_MUSIC = "background.mp3"  # Optional, put your own music here
os.makedirs("clips", exist_ok=True)
os.makedirs("tts", exist_ok=True)

# ================= STEP 1: Download Pixabay Clip =================
def download_pixabay_clip(search_term, index):
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={search_term}&per_page=3"
    response = requests.get(url).json()
    hits = response.get("hits", [])
    if not hits:
        print(f"❌ No videos found for {search_term}")
        return None
    video_url = hits[0]["videos"]["medium"]["url"]
    local_file = f"clips/clip_{index}.mp4"
    with requests.get(video_url, stream=True) as r:
        with open(local_file, "wb") as f:
            for chunk in r.iter_content(1024*1024):
                if chunk:
                    f.write(chunk)
    print(f"⬇️ Clip downloaded: {local_file}")
    return local_file

# ================= STEP 2: Generate TTS Caption =================
async def generate_tts(text, output_file):
    communicate = edge_tts.Communicate(text, "hi-IN-SwaraNeural")
    await communicate.save(output_file)
    print(f"🎤 TTS generated: {output_file}")

# ================= STEP 3: Merge Audio Clips =================
def merge_audio_files(audio_files, output_file):
    from pydub import AudioSegment
    combined = AudioSegment.empty()
    for file in audio_files:
        combined += AudioSegment.from_file(file)
    combined.export(output_file, format="mp3")
    print(f"✅ Merged audio: {output_file}")
    return output_file

# ================= STEP 4: Concatenate Video Clips =================
def concatenate_clips(clip_files, output_file="clips/concat.mp4"):
    concat_list = "clips/concat_list.txt"
    with open(concat_list, "w") as f:
        for clip in clip_files:
            f.write(f"file '{os.path.abspath(clip)}'\n")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-c", "copy", output_file
    ], check=True)
    print(f"✅ Clips concatenated: {output_file}")
    return output_file

# ================= STEP 5: Merge Video + Audio =================
def merge_video_audio(video_file, audio_file, output_file):
    command = [
        "ffmpeg", "-y",
        "-i", video_file,
        "-i", audio_file,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_file
    ]
    subprocess.run(command, check=True)
    print(f"🎥 Final compilation video created: {output_file}")

# ================= MAIN =================
async def main():
    # 1️⃣ Download random clips
    clip_files = []
    for i in range(NUM_CLIPS):
        term = random.choice(SEARCH_TERMS)
        clip = download_pixabay_clip(term, i+1)
        if clip:
            clip_files.append(clip)

    if not clip_files:
        print("❌ No clips downloaded. Exiting.")
        return

    # 2️⃣ Generate random captions for each clip (optional)
    captions = [
        "देखिए ये अद्भुत दृश्य!",
        "क्या आप ये देखकर हँसेंगे?",
        "ये मजेदार है ना?",
        "ये विज्ञान से भरा है!",
        "अविश्वसनीय दृश्य!"
    ]
    audio_files = []
    for idx, _ in enumerate(clip_files, 1):
        caption = random.choice(captions)
        tts_file = f"tts/caption_{idx}.mp3"
        await generate_tts(caption, tts_file)
        audio_files.append(tts_file)

    # 3️⃣ Merge all TTS audios into one
    final_audio = "tts/final_audio.mp3"
    merge_audio_files(audio_files, final_audio)

    # 4️⃣ Optionally merge background music
    if os.path.exists(BACKGROUND_MUSIC):
        from pydub import AudioSegment
        bg = AudioSegment.from_file(BACKGROUND_MUSIC)
        fg = AudioSegment.from_file(final_audio)
        # Loop background music if shorter
        while len(bg) < len(fg):
            bg += bg
        mixed = bg[:len(fg)].overlay(fg)
        mixed.export(final_audio, format="mp3")
        print("🎵 Background music added")

    # 5️⃣ Concatenate clips
    video_concat = concatenate_clips(clip_files)

    # 6️⃣ Merge final audio with video
    merge_video_audio(video_concat, final_audio, FINAL_VIDEO)

# ================= RUN SCRIPT =================
if __name__ == "__main__":
    asyncio.run(main())