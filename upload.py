import os
from gtts import gTTS

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# =========================
# FULL STORY
# =========================
def get_story():
    return [
        "यह कहानी आपकी सोच बदल देगी...",
        "एक गरीब किसान अपने खेत में काम कर रहा था...",
        "तभी उसे मिट्टी के अंदर कुछ सख्त चीज महसूस हुई...",
        "उसने खोदकर देखा तो एक पुराना घड़ा मिला...",
        "पहले उसने सोचा यह बेकार होगा...",
        "लेकिन जब उसने घड़ा खोला...",
        "अंदर सोना नहीं था...",
        "बल्कि एक पुरानी चिट्ठी थी...",
        "जिसमें लिखा था — जो मेहनत करता है वही असली खजाना पाता है...",
        "उस दिन किसान समझ गया कि मेहनत ही असली दौलत है...",
        "और वही उसे सफल बना सकती है...",
        "यही असली खुशी है ❤️"
    ]


# =========================
# VOICE
# =========================
def create_voice(text):
    path = os.path.join(OUTPUT_DIR, "voice.mp3")
    tts = gTTS(text=text, lang='hi', slow=True)
    tts.save(path)
    return path


# =========================
# CHARACTER PROMPTS (VERY IMPORTANT)
# =========================
def create_scene_prompts(story_lines):
    base_character = "same indian farmer, 2D cartoon style, consistent face, village background"

    prompts = []

    for line in story_lines:
        prompt = f"{base_character}, emotional scene, {line}, cinematic lighting, animation style"
        prompts.append(prompt)

    return prompts


# =========================
# SAVE PROMPTS
# =========================
def save_prompts(prompts):
    path = os.path.join(OUTPUT_DIR, "scene_prompts.txt")
    with open(path, "w", encoding="utf-8") as f:
        for p in prompts:
            f.write(p + "\n")
    return path


# =========================
# SAVE EDIT PLAN
# =========================
def save_edit_plan(story_lines):
    path = os.path.join(OUTPUT_DIR, "edit_plan.txt")

    with open(path, "w", encoding="utf-8") as f:
        for i, line in enumerate(story_lines):
            f.write(f"Scene {i+1}: {line}\n")
            f.write("Duration: 2-3 seconds\n\n")

    return path


# =========================
# MAIN
# =========================
def run():
    print("🚀 Character Animation Video System\n")

    story_lines = get_story()
    full_text = " ".join(story_lines)

    # Voice
    voice = create_voice(full_text)
    print("🎤 Voice created:", voice)

    # Prompts
    prompts = create_scene_prompts(story_lines)
    prompt_file = save_prompts(prompts)
    print("🎨 Scene prompts ready:", prompt_file)

    # Edit plan
    plan = save_edit_plan(story_lines)
    print("📝 Edit plan ready:", plan)

    print("\n🎬 NEXT STEPS (IMPORTANT):")
    print("1. Open AI tool like Runway or Pika")
    print("2. Paste each prompt → generate 2–3 sec animation")
    print("3. Download clips")
    print("4. Combine clips + voice in CapCut")

    print("\n✅ DONE! This is how viral animated videos are made")


if __name__ == "__main__":
    run()