import subprocess
import shlex

def create_voice(text, name):
    output_file = f"{name}.mp3"

    # Clean text (important for CLI safety)
    safe_text = text.replace('"', "'").replace("\n", " ")

    command = f'''
    edge-tts
    --voice en-US-GuyNeural
    --text "{safe_text}"
    --write-media {output_file}
    '''

    try:
        subprocess.run(
            shlex.split(command),
            timeout=180,
            check=True
        )
    except subprocess.TimeoutExpired:
        raise Exception("Voice generation timed out")
    except subprocess.CalledProcessError:
        raise Exception("Edge TTS failed")

    return output_file