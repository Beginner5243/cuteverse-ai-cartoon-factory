from __future__ import annotations

import asyncio
import math
import struct
import wave
from pathlib import Path
from typing import Any

import edge_tts


def _generate_fallback_tone_wav(wav_path: Path, duration_sec: float, pitch_hz: float = 240.0) -> Path:
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 24000
    n_samples = max(1, int(sample_rate * duration_sec))
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(n_samples):
            t = i / sample_rate
            # Syllabic modulation so mouth animation still moves if TTS falls back
            syllable_env = 0.5 + 0.5 * math.sin(2 * math.pi * 4.5 * t)
            val = int(4500 * syllable_env * math.sin(2 * math.pi * pitch_hz * t))
            frames.extend(struct.pack("<h", max(-32767, min(32767, val))))
        wf.writeframes(bytes(frames))
    return wav_path


async def _synthesize_edge_tts(text: str, voice: str, out_file: Path) -> None:
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(str(out_file))


def generate_scene_voice(
    text: str,
    voice: str,
    output_wav: Path,
    duration_sec: float,
    speaker_id: str,
) -> Path:
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    mp3_temp = output_wav.with_suffix(".mp3")
    try:
        asyncio.run(_synthesize_edge_tts(text, voice, mp3_temp))
        if mp3_temp.exists() and mp3_temp.stat().st_size > 0:
            # Convert to standard PCM WAV via ffmpeg if available, else keep mp3 rename
            import subprocess
            res = subprocess.run(
                ["ffmpeg", "-y", "-i", str(mp3_temp), "-ar", "24000", "-ac", "1", str(output_wav)],
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0 and output_wav.exists() and output_wav.stat().st_size > 0:
                mp3_temp.unlink(missing_ok=True)
                return output_wav
    except Exception:
        pass

    pitch = 290.0 if speaker_id == "char_a" else 195.0
    return _generate_fallback_tone_wav(output_wav, duration_sec=duration_sec, pitch_hz=pitch)
  
