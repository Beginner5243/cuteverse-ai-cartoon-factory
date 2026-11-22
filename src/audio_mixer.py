from __future__ import annotations

import math
import struct
import subprocess
import wave
from pathlib import Path
from typing import Any


def create_bgm_wav(bgm_path: Path, total_duration_sec: float) -> Path:
    bgm_path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 24000
    n_samples = max(1, int(sample_rate * total_duration_sec))
    notes = [261.63, 329.63, 392.00, 329.63]  # C4, E4, G4, E4 gentle loop
    with wave.open(str(bgm_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(n_samples):
            t = i / sample_rate
            freq = notes[int(t * 2) % len(notes)]
            val = int(1100 * math.sin(2 * math.pi * freq * t))
            frames.extend(struct.pack("<h", max(-32767, min(32767, val))))
        wf.writeframes(bytes(frames))
    return bgm_path


def mix_episode_audio(
    scenes: list[dict[str, Any]],
    voice_wavs: list[Path],
    output_audio_path: Path,
    total_duration_sec: float,
) -> Path:
    output_audio_path.parent.mkdir(parents=True, exist_ok=True)
    bgm_path = create_bgm_wav(output_audio_path.parent / "bgm_loop.wav", total_duration_sec)

    # Build full voice track by concatenating/padding each scene's voice
    full_voice_path = output_audio_path.parent / "full_voice.wav"
    concat_list = output_audio_path.parent / "concat_voices.txt"
    with concat_list.open("w", encoding="utf-8") as f:
        for w in voice_wavs:
            f.write(f"file '{w.resolve()}'\n")

    cmd_concat = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list), "-c:a", "pcm_s16le", "-ar", "24000", "-ac", "1",
        str(full_voice_path),
    ]
    subprocess.run(cmd_concat, capture_output=True, text=True, check=True)

    # Mix voice + soft background music + subtle pop SFX on scene starts
    sfx_path = create_bgm_wav(output_audio_path.parent / "sfx_pop.wav", 0.12)
    cmd_mix = [
        "ffmpeg", "-y",
        "-i", str(full_voice_path),
        "-i", str(bgm_path),
        "-i", str(sfx_path),
        "-filter_complex",
        "[0:a]volume=1.3[v];[1:a]volume=0.22[m];[2:a]volume=0.35[s];[v][m][s]amix=inputs=3:duration=first[aout]",
        "-map", "[aout]",
        "-c:a", "aac", "-b:a", "128k",
        str(output_audio_path),
    ]
    subprocess.run(cmd_mix, capture_output=True, text=True, check=True)
    return output_audio_path
  
