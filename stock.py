import subprocess

def download_stock(keyword):
    output = "stock.mp4"
    url = f"https://pixabay.com/videos/search/{keyword}/"
    
    subprocess.run([
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", "testsrc=size=1280x720:rate=30",
        "-t", "10",
        output
    ])
    return output