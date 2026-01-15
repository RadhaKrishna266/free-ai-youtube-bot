import subprocess
from stock import download_stock

def make_long(audio_file):
    stock = download_stock("technology")
    output = "long_video.mp4"

    cmd = [
        "ffmpeg", "-y",
        "-i", stock,
        "-i", audio_file,
        "-vf", "zoompan=z='min(zoom+0.0004,1.08)':d=1",
        "-shortest",
        output
    ]

    subprocess.run(cmd)
    return output