import random

def get_topic():
    with open("topics/history.txt", "r") as h:
            history = h.readlines()

                with open("topics/tech.txt", "r") as t:
                        tech = t.readlines()

                            all_topics = history + tech
                                return random.choice(all_topics).strip()