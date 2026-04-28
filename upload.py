import os
import random
from gtts import gTTS
from moviepy.editor import *

# =========================
# SETUP
# =========================
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# =========================
# STORY DATA (COMEDY)
# =========================
HOOKS = [
    "गांव में एक मजेदार चुड़ैल रहती थी...",
    "एक दांती चुड़ैल बहुत फेमस थी..."
]

SETUPS = [
    "कोई उससे डरता नहीं था, सब उसका मजाक उड़ाते थे...",
    "पूरा गांव उसे देखकर हंसता था..."
]

TWISTS = [
    "एक दिन उसने बोला — अब मैं शादी करूँगी!",
    "एक दिन उसने नौकरी के लिए apply किया!"
]

PUNCHLINES = [
    "लड़का बोला — बाल नहीं हैं तो shampoo का खर्चा बचेगा! 😂",
    "इंटरव्यू में बोली — मैं डराती नहीं, हंसाती हूं! 😂"
]

CTA = [
    "Follow करो ऐसी funny videos के लिए 😄"
]

# =========================
# GENERATE STORY
# =========================
def generate_story():
    lines = [
        random.choice(HOOKS),
        random.choice(SETUPS),
        random.choice(TWISTS),
        random.choice(PUNCHLINES),
        random.choice(CTA)
    ]
    return lines


# =========================
# VOICE
# =========================
def create_voice(text):
    path = os.path.join(OUTPUT_DIR, "voice.mp3")
    tts = gTTS(text=text, lang='hi')
    tts.save(path)
    return path


# =========================
# VIDEO CREATION
# =========================
def create_video(lines, audio_file):
    audio = AudioFileClip(audio_file)
    duration = audio.duration / len(lines)

    clips = []

    for line in lines:
        bg = ColorClip(size=(1080, 1920), color=(10, 10, 10)).set_duration(duration)

        txt = TextClip(
            line,
            fontsize=70,
            color='white',
            stroke_color='black',
            stroke_width=2,
            method='caption',
            size=(900, None)
        ).set_position(("center", "center")).set_duration(duration)

        clip = CompositeVideoClip([bg, txt])
        clips.append(clip)

    video = concatenate_videoclips(clips)
    video = video.set_audio(audio)

    output_path = os.path.join(OUTPUT_DIR, "final.mp4")
    video.write_videofile(output_path, fps=24)

    return output_path


# =========================
# MAIN
# =========================
def run():
    print("😂 Generating Funny Video...")

    lines = generate_story()
    full_text = " ".join(lines)

    for l in lines:
        print("👉", l)

    audio = create_voice(full_text)
    print("🎤 Voice created")

    video = create_video(lines, audio)
    print("🎬 Video created:", video)

    print("\n✅ DONE!")


if __name__ == "__main__":
    run()