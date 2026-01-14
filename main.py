from topic import get_topic
from script import generate_scripts
from voice_edge import create_voice
from video_short import create_short_video
from video_long import create_long_video
from upload import upload_video

def main():
    topic = get_topic()
        short_script, long_script = generate_scripts(topic)

            short_audio = create_voice(short_script, "short")
                long_audio = create_voice(long_script, "long")

                    short_video = create_short_video(short_audio, short_script)
                        long_video = create_long_video(long_audio, long_script)

                            upload_video(short_video, "short", topic)
                                upload_video(long_video, "long", topic)

                                if __name__ == "__main__":
                                    main()