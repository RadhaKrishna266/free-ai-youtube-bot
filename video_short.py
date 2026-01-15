import subprocess
from stock import download_stock

def make_short(audio_file):
    stock = download_stock("history", "short_stock.mp4")
    output = "short_video.mp4"

    if stock:
        cmd = [
            "ffmpeg", "-y",
            "-i", stock,
            "-i", audio_file,
            "-vf",
            "scale=1080:1920,zoompan=z='min(zoom+0.0008,1.1)':d=1",
            "-shortest",
            output
        ]
    else:
        cmd = [
            "ffmpeg", "-y",