import os
import subprocess

def create_voice(text, name):
    output = f"{name}.mp3"

        command = [
                "edge-tts",
                        "--voice", "en-US-GuyNeural",
                                "--text", text,
                                        "--write-media", output
                                            ]

                                                subprocess.run(command)
                                                    return output