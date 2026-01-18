import os
import subprocess
import textwrap
import random
import requests
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

VOICE = "en-IN-PrabhatNeural"
IMAGE_COUNT = 40
IMAGE_DURATION = 8
FPS = 30
VIDEO_SIZE = "1280x720"

def get_topic():
    return random.choice([
        "How ancient Egyptians built pyramids",
        "Secrets of the Roman Colosseum",
        "The mystery of Stonehenge",
        "How Vikings navigated the oceans"
    ])

def generate_script(topic):
    print("Generating script...")
    text = []
    for i in range(20):
        text.append(
            f"{topic}. This section explains the history, engineering methods, "
            f"scientific theories, cultural importance, and modern discoveries "
            f"in simple language."
        )
    script = "\n\n".join(text)
    open("script.txt", "w", encoding="utf-8").write(script)
    return script

def split_script(script, max_chars=2500):
    chunks = []
    current = ""
    for line in script.split("\n"):
        if len(current) + len(line) < max_chars:
            current += line + " "
        else:
            chunks.append(current.strip())
            current = line + " "
    if current:
        chunks.append(current.strip())
    return chunks

def generate_voice(script):
    print("Generating voice safely...")
    os.makedirs("audio", exist_ok=True)
    chunks = split_script(script)

    audio_files = []
    for i, chunk in enumerate(chunks):
        txt = f"audio/part_{i}.txt"
        mp3 = f"audio/part_{i}.mp3"
        open(txt, "w", encoding="utf-8").write(chunk)

        subprocess.run([
            "edge-tts",
            "--voice", VOICE,
            "--file", txt,
            "--write-media", mp3
        ], check=True)

        audio_files.append(mp3)

    with open("audio_list.txt", "w") as f:
        for a in audio_files:
            f.write(f"file '{a}'\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "audio_list.txt",
        "-c", "copy",
        "voice.mp3"
    ], check=True)

def download_images(topic):
    print("Downloading images...")
    os.makedirs("images", exist_ok=True)
    count = 0

    while count < IMAGE_COUNT:
        try:
            url = f"https://source.unsplash.com/1600x900/?{topic.replace(' ', ',')}"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                open(f"images/img_{count}.jpg", "wb").write(r.content)
                count += 1
        except:
            pass

def create_video():
    print("Creating animated video...")
    with open("list.txt", "w") as f:
        for img in sorted(os.listdir("images")):
            f.write(f"file 'images/{img}'\n")
            f.write(f"duration {IMAGE_DURATION}\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", "list.txt",
        "-vf",
        f"scale={VIDEO_SIZE},zoompan=z='zoom+0.0006':d={IMAGE_DURATION*FPS}",
        "-pix_fmt", "yuv420p",
        "video.mp4"
    ], check=True)

def merge_audio():
    subprocess.run([
        "ffmpeg", "-y",
        "-i", "video.mp4",
        "-i", "voice.mp3",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        "final.mp4"
    ], check=True)

def upload_to_youtube(topic):
    print("Uploading to YouTube...")
    creds = Credentials.from_authorized_user_file(
        "token.json",
        ["https://www.googleapis.com/auth/youtube.upload"]
    )

    youtube = build("youtube", "v3", credentials=creds)

    youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": topic,
                "description": topic + "\n\nAuto-generated educational video",
                "categoryId": "27",
                "tags": ["history", "facts", "education"]
            },
            "status": {"privacyStatus": "public"}
        },
        media_body=MediaFileUpload("final.mp4")
    ).execute()

def main():
    print("Starting auto video pipeline...")
    topic = get_topic()
    print("Topic:", topic)

    script = generate_script(topic)
    generate_voice(script)
    download_images(topic)
    create_video()
    merge_audio()
    upload_to_youtube(topic)

if __name__ == "__main__":
    main()