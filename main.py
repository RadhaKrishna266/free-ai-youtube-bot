from topic import get_topic
from script import generate_scripts
from voice import create_voice
from video_long import make_long
from video_short import make_short
from upload import upload_video

def run():
    topic = get_topic()
    script = generate_scripts(topic)

    short_audio = create_voice(script, name="short")
    long_audio = create_voice(script, name="long")

    short_video = make_short(short_audio, short=True)
    long_video = make_long(long_audio, short=False)

    upload_video(short_video, topic, is_short=True)
    upload_video(long_video, topic, is_short=False)

if __name__ == "__main__":
    run()