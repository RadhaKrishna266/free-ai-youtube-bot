import subprocess

def make_short(audio_file):
    output = "short_video.mp4"

    cmd = [
        "ffmpeg",
        "-y",
        "-stream_loop", "1",
        "-f", "lavfi",
        "-i", "color=c=black:s=1080x1920:d=30",
        "-i", audio_file,
        "-t", "30",
        "-vf",
        "drawtext=text='Did You Know?':fontcolor=white:fontsize=70:x=(w-text_w)/2:y=200",
        "-shortest",
        output
    ]

    subprocess.run(cmd, check=True)
    return output