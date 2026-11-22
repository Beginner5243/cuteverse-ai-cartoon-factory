from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any


STORY_TEMPLATES: list[dict[str, Any]] = [
    {
        "title": "The Vanishing Laddoo Trap",
        "hook_en": "Wait—where did my giant laddoo go?!",
        "hook_hi": "रुको—मेरा बड़ा लड्डू कहाँ गया?!",
        "hook_gu": "રોકાઓ—મારો મોટો લાડુ ક્યાં ગયો?!",
        "twist_en": "Plot twist: the spring-loaded cushion launched BOTH of them!",
        "twist_hi": "ट्विस्ट: स्प्रिंग वाले कुशन ने दोनों को हवा में उछाल दिया!",
        "twist_gu": "ટ્વિસ્ટ: સ્પ્રિંગવાળા ગાદીએ બંનેને હવામાં ઉછાળી દીધા!",
        "ending_en": "Moral: share snacks, or get bounced into next week!",
        "ending_hi": "सीख: स्नैक्स बाँटो, वरना सीधे हवा में उछलोगे!",
        "ending_gu": "શીખ: નાસ્તો વહેંચો, નહીંતર સીધા હવામાં ઉછળશો!",
        "question_en": "Who was more dramatic—Momo or Tofu-ji?",
        "question_hi": "सबसे ज़्यादा ड्रामेबाज़ कौन था—मोमो या टोफू-जी?",
        "question_gu": "સૌથી વધુ ડ્રામેબાઝ કોણ હતું—મોમો કે ટોફૂ-જી?",
        "beats": [
            ("hook", "char_b", "surprised", "walk_in",
             "Hey! My giant laddoo just vanished!",
             "अरे! मेरा बड़ा लड्डू अभी-अभी गायब हो गया!",
             "અરે! મારો મોટો લાડુ હમણાં જ ગાયબ થઈ ગયો!"),
            ("misunderstanding", "char_a", "innocent", "blink_hop",
             "Laddoo? What laddoo? I was just counting clouds!",
             "लड्डू? कौन सा लड्डू? मैं तो बस बादल गिन रहा था!",
             "લાડુ? કયો લાડુ? હું તો બસ વાદળ ગણતો હતો!"),
            ("angry_reaction", "char_b", "angry", "dance_stomp",
             "Your nose has sugar on it, Momo!",
             "मोमो, तुम्हारी नाक पर शक्कर लगी है!",
             "મોમો, તારા નાક પર ખાંડ લાગી છે!"),
            ("trap_setup", "char_b", "happy", "run_bounce",
             "Time for a super-secret bouncy cushion trap!",
             "अब चलेगा एक सुपर-सीक्रेट बाउंसी ट्रैप!",
             "હવે ચાલશે એક સુપર-સિક્રેટ બાઉન્સી ટ્રેપ!"),
            ("twist_ending", "char_a", "laughing", "jump_spin",
             "Wheee! Best trampoline ever!",
             "हीही! ये तो सबसे मज़ेदार ट्रैंपोलिन है!",
             "હીહી! આ તો સૌથી મજેદાર ટ્રેમ્પોલિન છે!")
        ],
    },
    {
        "title": "The Great Mango Mistake",
        "hook_en": "Who painted a yellow rock to look like a mango?!",
        "hook_hi": "आम जैसा दिखने वाला पीला पत्थर किसने रखा?!",
        "hook_gu": "કેરી જેવો દેખાતો પીળો પથ્થર કોણે મૂક્યો?!",
        "twist_en": "The 'mango' rolled down and bonked Tofu-ji's own helmet!",
        "twist_hi": "वो 'आम' लुढ़का और टोफू-जी के ही सिर से टकराया!",
        "twist_gu": "એ 'કેરી' ગબડી અને ટોફૂ-જીના જ માથા સાથે અથડાઈ!",
        "ending_en": "Funny ending: real mangoes won the day!",
        "ending_hi": "मज़ेदार अंत: असली आम ने बाज़ी मार ली!",
        "ending_gu": "રમુજી અંત: અસલી કેરીએ બાજી મારી લીધી!",
        "question_en": "Would you fall for Tofu-ji's prank?",
        "question_hi": "क्या आप टोफू-जी के मज़ाक में फँस जाते?",
        "question_gu": "શું તમે ટોફૂ-જીની મજાકમાં ફસાઈ જાત?",
        "beats": [
            ("hook", "char_a", "surprised", "jump_spin",
             "Whoa! A super shiny golden mango!",
             "वाह! एक एकदम चमकता सुनहरा आम!",
             "વાહ! એકદમ ચમકતી સોનેરી કેરી!"),
            ("misunderstanding", "char_b", "angry", "walk_in",
             "That is my lucky paperweight, not a mango!",
             "वो मेरा लकी पेपरवेट है, आम नहीं!",
             "એ મારું લકી પેપરવેટ છે, કેરી નહીં!"),
            ("angry_reaction", "char_a", "crying", "blink_hop",
             "My teeth almost chipped! So unfair!",
             "मेरे दाँत टूटते-टूटते बचे! ये गलत है!",
             "મારા દાંત તૂટતા-તૂટતા બચ્યા! આ ખોટું છે!"),
            ("trap_setup", "char_b", "laughing", "run_bounce",
             "Watch this silly rolling decoy trick!",
             "देखो ये मज़ेदार लुढ़कने वाली चाल!",
             "જુઓ આ રમુજી ગબડતી ચાલ!"),
            ("twist_ending", "char_a", "happy", "dance_stomp",
             "Surprise! Real mangoes for everyone!",
             "सरप्राइज़! सबके लिए असली आम!",
             "સરપ્રાઈઝ! બધા માટે અસલી કેરી!")
        ],
    },
]


def generate_episode_package(
    episode_id: int,
    language: str,
    duration_sec: int,
    characters_data: dict[str, Any],
    seed: int | None = None,
) -> dict[str, Any]:
    lang = language if language in ("en", "hi", "gu") else "en"
    rng = random.Random(seed if seed is not None else episode_id * 97 + len(lang))
    template = STORY_TEMPLATES[(episode_id - 1) % len(STORY_TEMPLATES)]

    beats = template["beats"]
    num_scenes = len(beats)
    base_len = duration_sec / num_scenes

    hook_key = f"hook_{lang}"
    twist_key = f"twist_{lang}"
    ending_key = f"ending_{lang}"
    question_key = f"question_{lang}"
    line_idx = {"en": 4, "hi": 5, "gu": 6}[lang]

    scenes: list[dict[str, Any]] = []
    current_t = 0.0

    for idx, beat in enumerate(beats, start=1):
        beat_name, speaker_id, expression, motion, *_ = beat
        dialogue_text = beat[line_idx]
        if idx == 1:
            dialogue_text = template[hook_key]
        elif idx == num_scenes:
            dialogue_text = f"{template[ending_key]} {template[question_key]}"

        scene_dur = round(base_len if idx < num_scenes else max(2.0, duration_sec - current_t), 2)
        speaker_name = characters_data[speaker_id]["name"]
        other_id = "char_b" if speaker_id == "char_a" else "char_a"
        other_name = characters_data[other_id]["name"]

        scenes.append({
            "scene_number": idx,
            "beat": beat_name,
            "start_sec": round(current_t, 2),
            "duration_sec": scene_dur,
            "speaker_id": speaker_id,
            "speaker_name": speaker_name,
            "listener_id": other_id,
            "listener_name": other_name,
            "expression": expression,
            "motion": motion,
            "dialogue": dialogue_text,
            "visual_prompt": (
                f"Cute expressive 3D cartoon style, {speaker_name} and {other_name} in a bright "
                f"playful room, {beat_name} moment, {expression} reaction, {motion} action, "
                f"consistent character design, vibrant lighting, no watermark."
            ),
            "camera_move": rng.choice(["zoom_in", "pan_right", "pan_left", "gentle_bounce"]),
        })
        current_t += scene_dur

    script_lines = [
        f"TITLE: {template['title']} (Episode {episode_id})",
        f"LANGUAGE: {lang.upper()}",
        f"TARGET DURATION: {duration_sec}s",
        f"OPENING HOOK: {template[hook_key]}",
        f"TWIST: {template[twist_key]}",
        "-" * 48,
    ]
    for sc in scenes:
        script_lines.append(
            f"[Scene {sc['scene_number']} | {sc['start_sec']}s - "
            f"{round(sc['start_sec'] + sc['duration_sec'], 2)}s | {sc['motion']} | {sc['expression']}]\n"
            f"{sc['speaker_name']}: {sc['dialogue']}\n"
        )

    return {
        "episode_id": episode_id,
        "title": template["title"],
        "language": lang,
        "duration_sec": duration_sec,
        "hook": template[hook_key],
        "twist": template[twist_key],
        "ending": template[ending_key],
        "engagement_question": template[question_key],
        "scenes": scenes,
        "script_text": "\n".join(script_lines),
    }


def write_script_and_storyboard(
    package: dict[str, Any],
    scripts_dir: Path,
    storyboards_dir: Path,
) -> tuple[Path, Path]:
    scripts_dir.mkdir(parents=True, exist_ok=True)
    storyboards_dir.mkdir(parents=True, exist_ok=True)

    stem = f"ep_{package['episode_id']:03d}_{package['language']}"
    script_path = scripts_dir / f"{stem}_script.txt"
    storyboard_path = storyboards_dir / f"{stem}_storyboard.json"

    script_path.write_text(package["script_text"], encoding="utf-8")
    storyboard_path.write_text(json.dumps(package, indent=2, ensure_ascii=False), encoding="utf-8")
    return script_path, storyboard_path
  
