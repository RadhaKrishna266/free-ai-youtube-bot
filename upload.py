import os
import subprocess
import json
import math
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from moviepy.editor import AudioFileClip

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

VIDEO_FILE = "final.mp4"
TITLE = "Mystery of Stonehenge"
DESCRIPTION = "AI generated educational documentary"
TAGS = ["history", "documentary", "AI video"]
CATEGORY_ID = "27"  # Education

def generate_script():
    text = """Stonehenge is one of the greatest mysteries in human history.
For thousands of years, massive stones stood aligned with the sun.
Scholars still debate how ancient people moved them.
This documentary explores theories, science, and legends.
""" * 40  # makes ~6–8 min
    with open("script.txt", "w") as f:
        f.write(text)

def generate_voice():
    subprocess.run([
        "edge-tts",
        "--voice", "en-IN-PrabhatNeural",
        "--file", "script.txt",
        "--write-media", "voice.mp3"
    ], check=True)

def get_audio_duration():
    audio = AudioFileClip("voice.mp3")
    return audio.duration

def generate_images():
    os.makedirs("images", exist_ok=True)
    for i in range(1, 11):
        subprocess.run([
            "ffmpeg", "-f", "lavfi",
            "-i", "color=c=black:s=1920x1080",
            "-frames:v", "1",
            f"images/img{i}.png"
        ])

def generate_video(audio_duration):
    per_image = audio_duration / 10
    with open("images.txt", "w") as f:
        for i in range(1, 11):
            f.write(f"file 'images/img{i}.png'\n")
            f.write(f"duration {per_image}\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "images.txt",
        "-vf", "scale=1920:1080,format=yuv420p",
        "-r", "25",
        "video.mp4"
    ], check=True)

    subprocess.run([
        "ffmpeg", "-y",
        "-i", "video.mp4",
        "-i", "voice.mp3",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        VIDEO_FILE
    ], check=True)

def get_authenticated_service():
    secret_json = os.environ["YOUTUBE_CLIENT_SECRET"]
    with open("client_secret.json", "w") as f:
        f.write(secret_json)

    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secret.json", SCOPES
    )
    creds = flow.run_console()
    return build("youtube", "v3", credentials=creds)

def