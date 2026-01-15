import subprocess

def make_long(audio_file):
    output = "long_video.mp4"

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", "color=c=black:s=1280x720:d=180",
        "-i", audio_file,
        "-t", "180",
        "-vf", "scale=1280:720",
        "-shortest",
        output
    ]

    subprocess.run(cmd, check=True)
    return output