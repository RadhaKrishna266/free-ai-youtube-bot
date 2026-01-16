from topic import get_topic
from script import generate_scripts
from voice import generate_voice
from video import create_video
from upload import upload_video

def run():
    topic = get_topic()
    script = generate_scripts(topic)

    short_audio = generate_voice(script, short=True)
    long_audio = generate_voice(script, short=False)

    short_video = create_video(short_audio, short=True)
    long_video = create_video(long_audio, short=False)

    upload_video(short_video, topic, is_short=True)
    upload_video(long_video, topic, is_short=False)

if __name__ == "__main__":
    run()