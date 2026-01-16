# main.py
import os
from topic import get_topic
from script import generate_scripts
from voice import create_voice
from video_long import make_long
from video_short import make_short

def run():
    topic = get_topic()

    short_script, long_script = generate_scripts(topic)

    short_audio = create_voice(short_script, name="short")
    long_audio = create_voice(long_script, name="long")

    short_video = make_short(short_audio)
    long_video = make_long(long_audio)

    # ✅ Upload ONLY when NOT running in GitHub Actions
    if os.environ.get("GITHUB_ACTIONS") != "true":
        from upload import upload_video
        upload_video(short_video, topic, is_short=True)
        upload_video(long_video, topic, is_short=False)
    else:
        print("⚠️ CI detected — skipping upload step")

if __name__ == "__main__":
    run()