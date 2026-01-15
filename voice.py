import subprocess

def create_voice(text, name):
    output_file = f"{name}.mp3"

    command = [
        "edge-tts",
        "--voice",
        "en-US-GuyNeural",
        "--text",
        text,
        "--write-media",
        output_file
    ]

    subprocess.run(command, timeout=120)
    return output_file