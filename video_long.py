import subprocess
from stock import get_stock_video

def make_long(audio):
    stock = get_stock_video()
    output = "long_video.mp4"

    cmd = [
        "ffmpeg", "-y",
        "-i", stock,
        "-i", audio,
        "-vf",
        "scale=1280:720,zoompan=z='min(zoom+0.0004,1.05)':d=1",
        "-shortest",
        output
    ]

    subprocess.run(cmd)
    return output