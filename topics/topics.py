import random

def get_topic():
    history_topics = [
        "The lost city of Mohenjo-daro",
        "The real reason the Roman Empire collapsed",
        "How ancient Egyptians built the pyramids",
        "The mystery of the Indus Valley Civilization",
        "The most shocking events in world history"
    ]

    tech_topics = [
        "How the internet works",
        "What is artificial intelligence explained simply",
        "How smartphones actually work",
        "What happens inside a computer chip",
        "How technology will change the future"
    ]

    category = random.choice(["history", "tech"])

    if category == "history":
        topic = random.choice(history_topics)
    else:
        topic = random.choice(tech_topics)

    return category, topic


if __name__ == "__main__":
    cat, top = get_topic()
    print(cat, ":", top)