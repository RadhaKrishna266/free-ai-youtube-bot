import subprocess
from stock import download_stock

def make_short(audio_file):
    stock = download_stock("short")
    output = "short_video.mp4"

    cmd = [
        "ffmpeg", "-y",
        "-i", stock,
        "-i", audio_file,
        "-vf",
        "scale=1080:1920,zoompan=z='min(zoom+0.0006,1.1)':d=1",
        "-shortest",
        output
    ]

    subprocess.run(cmd)
    return output