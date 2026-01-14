import subprocess

def make_long(audio_file):
    output = "long.mp4"

        command = [
                "ffmpeg",
                        "-loop", "1",
                                "-f", "lavfi",
                                        "-i", "color=c=black:s=1280x720:d=600",
                                                "-i", audio_file,
                                                        "-shortest",
                                                                "-c:v", "libx264",
                                                                        "-c:a", "aac",
                                                                                "-pix_fmt", "yuv420p",
                                                                                        output
                                                                                            ]

                                                                                                subprocess.run(command)
                                                                                                    return output