import os
import random
from gtts import gTTS

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# =========================
# CHARACTER BASE (CONSISTENT)
# =========================
CHARACTER = "funny indian cartoon chudail, big eyes, silly face, 2D animation, colorful, not scary"

# =========================
# STORY DATA (COMEDY)
# =========================
HOOKS = [
    "एक मजेदार चुड़ैल गांव में रहती थी...",
    "यह चुड़ैल डराती नहीं, हंसाती थी...",
]

SETUPS = [
    "पूरा गांव उसका मजाक उड़ाता था...",
    "कोई उससे डरता नहीं था...",
]

TWISTS = [
    "एक दिन उसने शादी करने का फैसला किया...",
    "एक दिन उसने दुकान खोल ली...",
]

PUNCHLINES = [
    "लड़का बोला — बाल नहीं हैं तो shampoo का खर्चा बचेगा 😂",
    "उसकी दुकान में कोई नहीं आया, तो उसने खुद ही सामान खरीद लिया 😂",
]

CTA = [
    "Follow करो ऐसी funny videos के लिए 😄"
]

# =========================
# GENERATE STORY
# =========================
def generate_story():
    story = [
        random.choice(HOOKS),
        random.choice(SETUPS),
        random.choice(TWISTS),
        random.choice(PUNCHLINES),
        random.choice(CTA)
    ]
    return story


# =========================
# VOICE
# =========================
def create_voice(text):
    path = os.path.join(OUTPUT_DIR, "voice.mp3")
    tts = gTTS(text=text, lang='hi', slow=False)
    tts.save(path)
    return path


# =========================
# CREATE ANIMATION PROMPTS
# =========================
def create_prompts(story_lines):
    prompts = []

    for line in story_lines:
        prompt = f"{CHARACTER}, indian village background, funny scene, {line}, cartoon animation, bright colors"
        prompts.append(prompt)

    return prompts


# =========================
# SAVE FILES
# =========================
def save_file(filename, data):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(item + "\n")
    return path


# =========================
# MAIN
# =========================
def run():
    print("😂 Cartoon Chudail Animation Generator\n")

    story_lines = generate_story()
    full_text = " ".join(story_lines)

    # Voice
    voice = create_voice(full_text)
    print("🎤 Voice:", voice)

    # Prompts
    prompts = create_prompts(story_lines)
    prompt_file = save_file("prompts.txt", prompts)
    print("🎨 Prompts:", prompt_file)

    # Scene Plan
    plan = [f"Scene {i+1}: {line}" for i, line in enumerate(story_lines)]
    plan_file = save_file("scene_plan.txt", plan)
    print("📝 Plan:", plan_file)

    print("\n🎬 NEXT STEP:")
    print("1. Use prompts in AI animation tools")
    print("2. Generate 2–3 sec clips per scene")
    print("3. Combine with voice in editor")

    print("\n✅ DONE - Ready for viral cartoon videos")


if __name__ == "__main__":
    run()