import subprocess

def make_short(audio_file):
    output = "short_video.mp4"

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "color=c=black:s=1080x1920:d=60",
        "-i", audio_file,
        "-vf",
        "drawtext=text='FACT YOU DID NOT KNOW':fontcolor=white:fontsize=80:x=(w-text_w)/2:y=300",
        "-shortest",
        output
    ]

    subprocess.run(cmd)
    return output