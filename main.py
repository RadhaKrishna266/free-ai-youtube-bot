import os
import random
import requests
import shutil
from gtts import gTTS
from moviepy.editor import *

# ================== CONFIG ==================
PEXELS_API_KEY = "YOUR_API_KEY"

# ================== TOPIC ==================
def get_topic():
    topics = [
        "peaceful village life in india",
        "simple village life india",
        "indian village morning routine",
        "real happiness village life india",
        "rural india lifestyle"
    ]
    return random.choice(topics)

# ================== SCRIPT ==================
def generate_scripts(topic):
    hooks = [
        "This is what real happiness looks like...",
        "No stress. No noise. Just peace.",
        "City life is busy… but this is life."
    ]

    scenes = [
        "Sun rising over green fields",
        "Birds chirping in silence",
        "Grandmother cooking on chulha",
        "Farmers working peacefully",
        "Children playing freely",
        "Fresh air and slow life"
    ]

    endings = [
        "Would you live here?",
        "Follow for more peaceful life",
        "This is real happiness ❤️"
    ]

    hook = random.choice(hooks)

    short = f"{hook} {random.choice(scenes)}. {random.choice(endings)}"
    long = f"{hook} {' '.join(random.sample(scenes, 5))}. {random.choice(endings)}"

    return short, long

# ================== VOICE ==================
def create_voice(text, name):
    file = f"{name}.mp3"
    tts = gTTS(text=text, lang='en', slow=True)
    tts.save(file)
    return file

# ================== FETCH CLIPS ==================
def clean_clips():
    if os.path.exists("clips"):
        shutil.rmtree("clips")

def fetch_clips(query):
    clean_clips()
    os.makedirs("clips", exist_ok=True)

    headers = {"Authorization": PEXELS_API_KEY}
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=6"

    data = requests.get(url, headers=headers).json()

    paths = []

    for i, vid in enumerate(data.get("videos", [])):
        files = vid.get("video_files", [])
        if not files:
            continue

        link = files[0]["link"]
        path = f"clips/clip_{i}.mp4"

        print(f"⬇️ Downloading clip {i+1}")
        content = requests.get(link).content

        with open(path, "wb") as f:
            f.write(content)

        paths.append(path)

    return paths

# ================== VIDEO ==================
def make_video(audio_file, topic, output, vertical=True):
    audio = AudioFileClip(audio_file)
    clip_files = fetch_clips(topic)

    clips = []
    duration_per_clip = audio.duration / max(len(clip_files), 1)

    for file in clip_files:
        clip = VideoFileClip(file)
        clip = clip.subclip(0, min(duration_per_clip, clip.duration))
        clips.append(clip)

    video = concatenate_videoclips(clips).set_audio(audio)

    if vertical:
        video = video.resize(height=1920)
    else:
        video = video.resize(height=1080)

    # Background music (optional)
    if os.path.exists("bg.mp3"):
        bg = AudioFileClip("bg.mp3").volumex(0.15)
        final_audio = CompositeAudioClip([audio, bg])
        video = video.set_audio(final_audio)

    video.write_videofile(output, fps=24)
    return output

# ================== SUBTITLES ==================
def add_subtitles(video_path, text):
    video = VideoFileClip(video_path)

    words = text.split()
    chunk_size = 4
    duration = video.duration / (len(words)//chunk_size + 1)

    subs = []

    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])

        txt = TextClip(
            chunk,
            fontsize=60,
            color='white',
            stroke_color='black',
            stroke_width=2,
            method='caption',
            size=(video.w*0.9, None)
        ).set_position(("center", "bottom"))

        txt = txt.set_duration(duration)
        txt = txt.set_start((i//chunk_size)*duration)

        subs.append(txt)

    final = CompositeVideoClip([video, *subs])

    output = "final_" + video_path
    final.write_videofile(output, fps=24)

    return output

# ================== UPLOAD (PLACEHOLDER) ==================
def upload_video(file, topic, is_short):
    if is_short:
        title = f"Village Life 🌾 | {topic} #shorts"
    else:
        title = f"Peaceful Village Life 🌿 | {topic}"

    print(f"📤 Uploading: {title}")
    print(f"File: {file}")

# ================== MAIN ==================
def run():
    print("🚀 Starting Viral Video System...\n")

    topic = get_topic()
    print(f"📌 Topic: {topic}")

    short_script, long_script = generate_scripts(topic)

    short_audio = create_voice(short_script, "short")
    long_audio = create_voice(long_script, "long")

    short_video = make_video(short_audio, topic, "short.mp4", True)
    long_video = make_video(long_audio, topic, "long.mp4", False)

    short_final = add_subtitles(short_video, short_script)
    long_final = add_subtitles(long_video, long_script)

    upload_video(short_final, topic, True)
    upload_video(long_final, topic, False)

    print("\n✅ DONE! Videos created successfully")

if __name__ == "__main__":
    run()