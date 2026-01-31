# upload.py
import os
import time
import random
from pathlib import Path
from gtts import gTTS
from moviepy.editor import AudioFileClip, ImageClip, CompositeAudioClip, concatenate_videoclips
from huggingface_hub import InferenceClient

# ========== CONFIG ==========
SCRIPT_FILE = "script.txt"
OUTPUT_VIDEO = "final_video.mp4"
BACKGROUND_MUSIC = "audio/tanpura.mp3"
IMAGE_DIR = "generated_images"
AUDIO_DIR = "generated_audio"

HF_API_KEY = os.environ.get("HF_API_KEY")

# ========== FOLDERS ==========
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

# ========== FUNCTIONS ==========

def load_script(script_file):
    with open(script_file, "r", encoding="utf-8") as f:
        blocks = [b.strip() for b in f.read().split("\n\n") if b.strip()]
    return blocks

def generate_audio(text, filename):
    tts = gTTS(text=text, lang="hi")
    tts.save(filename)
    return filename

def generate_hf_image(prompt, filename, retries=3):
    client = InferenceClient(token=HF_API_KEY)
    for attempt in range(1, retries + 1):
        try:
            print(f"🎨 Generating image for prompt [{prompt[:50]}...] (attempt {attempt})")
            result = client.text_to_image(prompt, height=720, width=1280)
            with open(filename, "wb") as f:
                f.write(result)
            return filename
        except Exception as e:
            print(f"⚠ HF image generation failed: {e}, retrying...")
            time.sleep(5)
    raise RuntimeError("❌ AI image generation failed completely")

def create_video(script_blocks):
    clips = []

    for i, block in enumerate(script_blocks):
        # Generate audio
        audio_file = f"{AUDIO_DIR}/{i:03d}.mp3"
        generate_audio(block, audio_file)
        audio_clip = AudioFileClip(audio_file)

        # Generate image
        img_file = f"{IMAGE_DIR}/{i:03d}.png"
        prompt = f"Divine Lord Vishnu, glowing, serene, traditional Indian style, HD"
        generate_hf_image(prompt, img_file)

        # Create clip
        img_clip = ImageClip(img_file).set_duration(audio_clip.duration).set_fps(24)
        img_clip = img_clip.set_audio(audio_clip)
        clips.append(img_clip)

    # Concatenate all clips
    final_video = concatenate_videoclips(clips, method="compose")

    # Add background music
    if os.path.exists(BACKGROUND_MUSIC):
        bg_music = AudioFileClip(BACKGROUND_MUSIC).volumex(0.2)
        final_audio = CompositeAudioClip([final_video.audio, bg_music.set_duration(final_video.duration)])
        final_video = final_video.set_audio(final_audio)

    # Write video
    final_video.write_videofile(OUTPUT_VIDEO, fps=24)

# ========== MAIN ==========
def main():
    print("📖 Loading script...")
    blocks = load_script(SCRIPT_FILE)

    print("🎬 Generating video with AI images and narration...")
    create_video(blocks)

    print(f"✅ FINAL VIDEO READY: {OUTPUT_VIDEO}")

if __name__ == "__main__":
    main()