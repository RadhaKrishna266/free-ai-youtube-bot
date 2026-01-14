import subprocess

def make_short(audio_file):
    output = "short.mp4"

        command = [
                "ffmpeg",
                        "-loop", "1",
                                "-f", "lavfi",
                                        "-i", "color=c=black:s=1080x1920:d=60",
                                                "-i", audio_file,
                                                        "-shortest",
                                                                "-c:v", "libx264",
                                                                        "-c:a", "aac",
                                                                                "-pix_fmt", "yuv420p",
                                                                                        output
                                                                                            ]

                                                                                                subprocess.run(command)
                                                                                                    return output