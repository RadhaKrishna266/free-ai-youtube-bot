import subprocess

def make_long(audio_file):
    output = "long_video.mp4"

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", "color=c=black:s=1280x720:d=360",
        "-i", audio_file,
        "-vf", "zoompan=z='min(zoom+0.0003,1.05)':d=1",
        "-shortest",
        output
    ]

    subprocess.run(cmd, check=True)
    return output