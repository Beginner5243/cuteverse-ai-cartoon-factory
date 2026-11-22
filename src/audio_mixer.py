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
    notes = [261.63, 329.63, 392.00, 329.63]
    with wave.open(str(bgm_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(n_samples):
            t = i / sample_rate
            freq = notes[int(t * 2) % len(notes)]
            val = int(950 * math.sin(2 * math.pi * freq * t))
            frames.extend(struct.pack("<h", max(-32767, min(32767, val))))
        wf.writeframes(bytes(frames))
    return bgm_path


def create_pop_sfx_wav(sfx_path: Path, duration_sec: float = 0.14) -> Path:
    sfx_path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 24000
    n_samples = max(1, int(sample_rate * duration_sec))
    with wave.open(str(sfx_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(n_samples):
            t = i / sample_rate
            env = max(0.0, 1.0 - (t / duration_sec))
            freq = 320.0 + 420.0 * (t / duration_sec)
            val = int(3200 * env * math.sin(2 * math.pi * freq * t))
            frames.extend(struct.pack("<h", max(-32767, min(32767, val))))
        wf.writeframes(bytes(frames))
    return sfx_path


def fit_wav_to_duration(input_wav: Path, target_sec: float, out_wav: Path) -> Path:
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_wav),
        "-af", f"apad=whole_dur={target_sec:.3f},atrim=duration={target_sec:.3f}",
        "-ar", "24000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        str(out_wav),
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True)
    return out_wav


def mix_episode_audio(
    scenes: list[dict[str, Any]],
    voice_wavs: list[Path],
    output_audio_path: Path,
    total_duration_sec: float,
) -> Path:
    output_audio_path.parent.mkdir(parents=True, exist_ok=True)
    bgm_path = create_bgm_wav(output_audio_path.parent / "bgm_loop.wav", total_duration_sec)
    sfx_path = create_pop_sfx_wav(output_audio_path.parent / "sfx_pop.wav", 0.14)

    fitted_wavs: list[Path] = []
    for idx, (sc, raw_wav) in enumerate(zip(scenes, voice_wavs), start=1):
        fitted = fit_wav_to_duration(
            raw_wav,
            float(sc["duration_sec"]),
            output_audio_path.parent / f"fitted_voice_{idx:02d}.wav",
        )
        fitted_wavs.append(fitted)

    full_voice_path = output_audio_path.parent / "full_voice.wav"
    concat_list = output_audio_path.parent / "concat_voices.txt"
    with concat_list.open("w", encoding="utf-8") as f:
        for w in fitted_wavs:
            f.write(f"file '{w.resolve()}'\n")

    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_list),
            "-t", f"{total_duration_sec:.3f}",
            "-c:a", "pcm_s16le", "-ar", "24000", "-ac", "1",
            str(full_voice_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(full_voice_path),
            "-i", str(bgm_path),
            "-i", str(sfx_path),
            "-filter_complex",
            f"[0:a]volume=1.35[v];[1:a]volume=0.16[m];[2:a]volume=0.25[s];[v][m][s]amix=inputs=3:duration=longest,atrim=duration={total_duration_sec:.3f}[aout]",
            "-map", "[aout]",
            "-c:a", "aac", "-b:a", "128k",
            str(output_audio_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return output_audio_path
    1
