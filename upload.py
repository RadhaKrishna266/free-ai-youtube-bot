import os, subprocess, random, textwrap, json, math
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

BASE = Path(".")
IMG_DIR = BASE / "images"
IMG_DIR.mkdir(exist_ok=True)

VIDEO = "final.mp4"
AUDIO = "voice.m4a"

# ------------------ FACT ENGINE ------------------

FACT_POOLS = {
    "science": [
        "Octopuses have three hearts and blue blood",
        "There are more possible chess games than atoms in the universe",
        "Bananas are naturally radioactive",
        "Your brain can power a small light bulb",
    ],
    "space": [
        "A day on Venus is longer than a year on Venus",
        "There are planets made of diamonds",
        "Neutron stars are so dense a spoon weighs billions of tons",
    ],
    "human": [
        "Humans glow faintly due to bioluminescence",
        "Your stomach gets a new lining every 3 days",
        "Your bones are stronger than steel by weight",
    ],
}

def generate_facts(n=6):
    facts = []
    used = set()
    while len(facts) < n:
        cat = random.choice(list(FACT_POOLS))
        fact = random.choice(FACT_POOLS[cat])
        if fact not in used:
            used.add(fact)
            facts.append(fact)
    return facts

# ------------------ AUDIO ------------------

def create_audio(text):
    script = " ".join(text)
    subprocess.run([
        "ffmpeg","-y",
        "-f","lavfi",
        "-i","sine=frequency=440",
        "-t",str(len(text)*6),
        "-c:a","aac","-b:a","128k",AUDIO
    ], check=True)

# ------------------ AI FACE ------------------

def create_face():
    subprocess.run([
        "ffmpeg","-y",
        "-f","lavfi",
        "-i","color=c=#202020:s=1024x1024",
        "-vf","drawtext=text='AI FACT FACE':fontsize=72:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
        str(IMG_DIR / "face.jpg")
    ], check=True)

# ------------------ ANIMATED TALKING FACE ------------------

def create_video():
    cmd = [
        "ffmpeg","-y",
        "-loop","1","-i",str(IMG_DIR / "face.jpg"),
        "-i",AUDIO,
        "-filter_complex",
        (
            "zoompan=z='1+0.0008*sin(2*PI*t)':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            "d=1:fps=30,"
            "scale=1280:720"
        ),
        "-c:v","libx264",
        "-pix_fmt","yuv420p",
        "-c:a","aac",
        "-shortest",
        VIDEO
    ]
    subprocess.run(cmd, check=True)

# ------------------ YOUTUBE ------------------

def upload_video(title, description):
    creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/youtube.upload"])
    yt = build("youtube","v3",credentials=creds)

    request = yt.videos().insert(
        part="snippet,status",
        body={
            "snippet":{
                "title": title,
                "description": description,
                "tags":["facts","unknown facts","ai video","mind blowing"],
                "categoryId":"27"
            },
            "status":{"privacyStatus":"public"}
        },
        media_body=MediaFileUpload(VIDEO, chunksize=-1, resumable=True)
    )
    request.execute()

# ------------------ MAIN ------------------

def main():
    print("🚀 Starting AI Talking Face Video Bot")

    facts = generate_facts()
    create_audio(facts)
    create_face()
    create_video()

    title = "AI Reveals Unknown Facts You Were Never Taught"
    description = "\n".join(f"• {f}" for f in facts)

    try:
        upload_video(title, description)
    except Exception as e:
        print("⚠️ Upload skipped:", e)

    print("✅ Video ready:", VIDEO)

if __name__ == "__main__":
    main()