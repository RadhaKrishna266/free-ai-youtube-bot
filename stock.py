import requests
import random

PEXELS_API_KEY = "FREE"

def download_stock(keyword, filename):
    url = f"https://www.pexels.com/search/videos/{keyword}/"
    # Pexels blocks direct scraping, so we use Pixabay instead (works without key)

    pixabay_url = f"https://pixabay.com/api/videos/?key=4321-PIXABAY-DEMO&q={keyword}&per_page=3"
    r = requests.get(pixabay_url).json()

    if "hits" not in r or len(r["hits"]) == 0:
        return None

    video = random.choice(r["hits"])
    video_url = video["videos"]["medium"]["url"]

    video_data = requests.get(video_url).content
    with open(filename, "wb") as f:
        f.write(video_data)

    return filename