from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any


STORY_TEMPLATES: list[dict[str, Any]] = [
    {
        "title": "Sheru and Potato's Bouncing Laddoo Mix-Up",
        "setting": "kitchen_room",
        "hook_en": "Hey! That giant laddoo is rolling right toward us!",
        "hook_hi": "अरे! वो बड़ा लड्डू सीधा हमारी तरफ लुढ़क रहा है!",
        "hook_gu": "અરે! એ મોટો લાડુ સીધો આપણી તરફ ગબડી રહ્યો છે!",
        "twist_en": "Twist! Potato caught it, tripped on a cushion, and bounced Sheru into a giggle!",
        "twist_hi": "ट्विस्ट! पोटैटो ने लपक लिया, कुशन से फिसला और शेरू हँसते-हँसते उछल पड़ा!",
        "twist_gu": "ટ્વિસ્ટ! પોટેટોએ ઝીલી લીધો, ગાદી પર લપસ્યો અને શેરુ હસતાં-હસતાં ઉછળી પડ્યો!",
        "ending_en": "Best snack teamwork ever—who laughed louder, Sheru or Potato?",
        "ending_hi": "सबसे मज़ेदार टीमवर्क—कौन ज़्यादा हँसा, शेरू या पोटैटो?",
        "ending_gu": "સૌથી મજેદાર ટીમવર્ક—કોણ વધુ હસ્યું, શેરુ કે પોટેટો?",
        "beats": [
            ("hook_entrance", "char_a", "surprised", "walk_together", "pass_object",
             "Look Potato! A giant laddoo just rolled in!",
             "देखो पोटैटो! एक बड़ा लड्डू अंदर आ गया!",
             "જુઓ પોટેટો! એક મોટો લાડુ અંદર આવી ગયો!"),
            ("dialogue_exchange", "char_b", "happy", "talk_face_to_face", "hold_object",
             "Careful Sheru, pass it gently—don't drop my treat!",
             "संभाल के शेरू, धीरे से दो—मेरी मिठाई गिराना मत!",
             "સંભાળીને શેરુ, ધીમેથી આપ—મારી મીઠાઈ પાડતો નહીં!"),
            ("misunderstanding", "char_a", "innocent", "pass_object", "catch_object",
             "I passed it! Why did you duck like a ninja?",
             "मैंने तो दे दिया! तुम निंजा की तरह क्यों झुके?",
             "મેં તો આપી દીધો! તું નિન્જાની જેમ કેમ ઝૂક્યો?"),
            ("physical_comedy", "char_b", "angry", "run_and_fall", "drop_object",
             "Whoa—my sprout headband slipped and I tumbled!",
             "ओह—मेरा हेडबैंड खिसका और मैं लड़खड़ा गया!",
             "ઓહ—મારું હેડબેન્ડ સરક્યું અને હું ગબડી પડ્યો!"),
            ("twist_ending", "char_a", "laughing", "laugh_together", "share_object",
             "Haha! Soft cushion landing! Let's share half and half!",
             "हाहा! कुशन पर मज़ेदार लैंडिंग! आधा-आधा बाँटते हैं!",
             "હાહા! ગાદી પર મજેદાર લેન્ડિંગ! અડધો-અડધો વહેંચીએ!")
        ],
    },
    {
        "title": "The Golden Mango Toss",
        "setting": "sunny_garden",
        "hook_en": "Catch! A shiny golden mango just flew over the fence!",
        "hook_hi": "पकड़ो! बाड़ के ऊपर से चमकता सुनहरा आम आया!",
        "hook_gu": "પકડો! વાડ ઉપરથી ચમકતી સોનેરી કેરી આવી!",
        "twist_en": "Twist! It wasn't a heavy rock—it was a bouncy ball that boinged both buddies!",
        "twist_hi": "ट्विस्ट! वो भारी पत्थर नहीं, उछलती गेंद थी जिसने दोनों को उछाल दिया!",
        "twist_gu": "ટ્વિસ્ટ! એ ભારે પથ્થર નહીં, ઉછળતો દડો હતો જેણે બંનેને ઉછાળી દીધા!",
        "ending_en": "Silly garden surprise—would you catch it or dodge it?",
        "ending_hi": "गार्डन का मज़ेदार सरप्राइज़—आप पकड़ते या बचते?",
        "ending_gu": "ગાર્ડનની રમુજી સરપ્રાઈઝ—તમે પકડત કે બચત?",
        "beats": [
            ("hook_entrance", "char_b", "surprised", "walk_together", "pass_object",
             "Sheru! Quick! Catch this golden mango!",
             "शेरू! जल्दी! इस सुनहरे आम को पकड़ो!",
             "શેરુ! જલ્દી! આ સોનેરી કેરી પકડો!"),
            ("dialogue_exchange", "char_a", "happy", "talk_face_to_face", "catch_object",
             "Got it! Wait—why does this mango bounce like rubber?",
             "पकड़ लिया! रुको—ये आम रबर जैसा क्यों उछल रहा है?",
             "પકડી લીધી! રોકાઓ—આ કેરી રબર જેવી કેમ ઉછળે છે?"),
            ("misunderstanding", "char_b", "innocent", "pass_object", "catch_object",
             "Maybe mangoes do yoga in the afternoon sun!",
             "शायद दोपहर की धूप में आम भी योग करते हैं!",
             "કદાચ બપોરના તડકામાં કેરી પણ યોગ કરે છે!"),
            ("physical_comedy", "char_a", "surprised", "run_and_fall", "drop_object",
             "Boing! Too bouncy—I'm doing a cartoon flip!",
             "बोइंग! ज़्यादा उछल गया—मैं तो पलटी खा गया!",
             "બોઇંગ! વધુ ઉછળી ગઈ—હું તો ગબડી પડ્યો!"),
            ("twist_ending", "char_b", "laughing", "laugh_together", "share_object",
             "Haha! Real sweet mangoes are waiting in the basket!",
             "हाहा! टोकरी में असली मीठे आम रखे हैं!",
             "હાહા! ટોપલીમાં અસલી મીઠી કેરીઓ રાખી છે!")
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
    rng = random.Random(seed if seed is not None else episode_id * 131 + len(lang))
    template = STORY_TEMPLATES[(episode_id - 1) % len(STORY_TEMPLATES)]

    beats = template["beats"]
    num_scenes = len(beats)
    base_len = duration_sec / num_scenes

    hook_key = f"hook_{lang}"
    twist_key = f"twist_{lang}"
    ending_key = f"ending_{lang}"
    line_idx = {"en": 5, "hi": 6, "gu": 7}[lang]

    scenes: list[dict[str, Any]] = []
    current_t = 0.0

    for idx, beat in enumerate(beats, start=1):
        beat_name, speaker_id, expression, action, prop_action, *_ = beat
        dialogue_text = beat[line_idx]
        if idx == 1:
            dialogue_text = template[hook_key]
        elif idx == num_scenes:
            dialogue_text = template[ending_key]

        scene_dur = round(base_len if idx < num_scenes else max(2.0, duration_sec - current_t), 2)
        speaker_name = characters_data[speaker_id]["name"]
        listener_id = "char_b" if speaker_id == "char_a" else "char_a"
        listener_name = characters_data[listener_id]["name"]

        scenes.append({
            "scene_number": idx,
            "beat": beat_name,
            "setting": template["setting"],
            "start_sec": round(current_t, 2),
            "duration_sec": scene_dur,
            "speaker_id": speaker_id,
            "speaker_name": speaker_name,
            "listener_id": listener_id,
            "listener_name": listener_name,
            "expression": expression,
            "action": action,
            "prop_action": prop_action,
            "dialogue": dialogue_text,
            "camera_move": rng.choice(["zoom_in", "pan_right", "pan_left", "gentle_bounce"]),
        })
        current_t += scene_dur

    script_lines = [
        f"TITLE: {template['title']} (Episode {episode_id})",
        f"LANGUAGE: {lang.upper()}",
        f"SETTING: {template['setting']}",
        f"TARGET DURATION: {duration_sec}s",
        f"HOOK: {template[hook_key]}",
        f"TWIST: {template[twist_key]}",
        f"ENDING: {template[ending_key]}",
        "=" * 48,
    ]
    for sc in scenes:
        script_lines.append(
            f"[Scene {sc['scene_number']} | {sc['start_sec']}s - "
            f"{round(sc['start_sec'] + sc['duration_sec'], 2)}s | action={sc['action']} | "
            f"prop={sc['prop_action']} | expr={sc['expression']}]\n"
            f"{sc['speaker_name']}: {sc['dialogue']}\n"
        )

    return {
        "episode_id": episode_id,
        "title": template["title"],
        "setting": template["setting"],
        "language": lang,
        "duration_sec": duration_sec,
        "hook": template[hook_key],
        "twist": template[twist_key],
        "ending": template[ending_key],
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
    
