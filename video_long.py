import subprocess
from stock import download_stock

def make_long(audio_file):
    stock = download_stock("long")
    output = "long_video.mp4"

    cmd = [
        "ffmpeg", "-y",
        "-i", stock,
        "-i", audio_file,
        "-vf",
        "scale=1280:720,zoompan=z='min(zoom+0.0003,1.05)':d=1",
        "-shortest",
        output
    ]

    subprocess.run(cmd)
    return output