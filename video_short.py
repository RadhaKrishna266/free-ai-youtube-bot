import subprocess
from stock import get_stock_video

def make_short(audio):
    stock = get_stock_video()
    output = "short_video.mp4"

    cmd = [
        "ffmpeg", "-y",
        "-i", stock,
        "-i", audio,
        "-vf",
        "scale=1080:1920,zoompan=z='min(zoom+0.0006,1.1)':d=1",
        "-shortest",
        output
    ]

    subprocess.run(cmd)
    return output