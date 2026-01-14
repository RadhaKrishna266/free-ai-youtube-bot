import random

def get_topic():
    files = ["topics/history.txt", "topics/tech.txt"]
    chosen_file = random.choice(files)

    with open(chosen_file, "r") as f:
        topics = f.readlines()

    return random.choice(topics).strip()