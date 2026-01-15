import subprocess

def make_short(audio_file):
    output = "short_video.mp4"

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", "color=c=black:s=1080x1920:d=60",
        "-i", audio_file,
        "-vf", "zoompan=z='min(zoom+0.0005,1.1)':d=1",
        "-shortest",
        output
    ]

    subprocess.run(cmd, check=True)
    return output