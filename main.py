# main.py
from topic import get_topic
from script import generate_scripts
from voice import create_voice
from video_long import make_long
from video_short import make_short
from upload import upload_video

def run():
    topic = get_topic()

    # 1. Generate scripts
    short_script, long_script = generate_scripts(topic)

    # 2. Generate audio
    short_audio = create_voice(short_script, name="short")
    long_audio = create_voice(long_script, name="long")

    # 3. Generate videos (NO FLAGS HERE)
    short_video = make_short(short_audio)
    long_video = make_long(long_audio)

    # 4. Upload (FLAG IS VALID HERE)
    upload_video(short_video, topic, is_short=True)
    upload_video(long_video, topic, is_short=False)

if __name__ == "__main__":
    run()