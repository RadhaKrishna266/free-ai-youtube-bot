import subprocess
from stock import download_stock

def make_long(audio_file):
    stock = download_stock("technology", "stock.mp4")
    output = "long_video.mp4"

    if stock:
        cmd = [
            "ffmpeg", "-y",
            "-i", stock,
            "-i", audio_file,
            "-vf",
            "scale=1280:720,zoompan=z='min(zoom+0.0003,1.05)':d=1",
            "-shortest",
            output
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "color=c=black:s=1280x720:d=300",
            "-i", audio_file,
            "-shortest",
            output
        ]

    subprocess.run(cmd)
    return output