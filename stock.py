import random
import subprocess

PIXABAY_VIDEOS = [
    "https://cdn.pixabay.com/vimeo/458199130/ai-38530.mp4",
    "https://cdn.pixabay.com/vimeo/452033518/technology-30377.mp4",
    "https://cdn.pixabay.com/vimeo/447645493/history-29441.mp4"
]

def download_stock(name):
    url = random.choice(PIXABAY_VIDEOS)
    output = f"{name}_stock.mp4"
    subprocess.run(["wget", "-O", output, url])
    return output