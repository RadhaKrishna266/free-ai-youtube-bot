import requests
import random
import os

PIXABAY_VIDEOS = [
    "https://cdn.pixabay.com/video/2020/03/11/33569-401138047_large.mp4",
    "https://cdn.pixabay.com/video/2023/01/10/146360-787462594_large.mp4",
    "https://cdn.pixabay.com/video/2019/09/24/27369-363438373_large.mp4"
]

def get_stock_video():
    url = random.choice(PIXABAY_VIDEOS)
    filename = "stock.mp4"

    r = requests.get(url)
    with open(filename, "wb") as f:
        f.write(r.content)

    return filename