from __future__ import annotations

import asyncio
import logging
import subprocess
import wave
from pathlib import Path
from typing import Any

import edge_tts

logger = logging.getLogger("cuteverse.voice_generator")


def _probe_wav_duration(wav_path: Path) -> float:
    if not wav_path.exists():
        return 0.0
    try:
        with wave.open(str(wav_path), "rb") as wf:
            fr = wf.getframerate()
            nf = wf.getnframes()
            return (nf / fr) if fr > 0 else 0.0
    except Exception:
        return 0.0


def _write_silent_wav(wav_path: Path, duration_sec: float) -> Path:
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 24000
    n_samples = max(1, int(sample_rate * max(0.5, duration_sec)))
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * n_samples)
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
) -> dict[str, Any]:
    """
    Synthesizes speech via edge-tts and converts MP3 -> PCM WAV.
    Never claims voiced success when TTS fails; explicitly reports status and reason.
    """
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    mp3_temp = output_wav.with_suffix(".mp3")

    try:
        asyncio.run(_synthesize_edge_tts(text, voice, mp3_temp))
        if not mp3_temp.exists() or mp3_temp.stat().st_size == 0:
            raise RuntimeError("edge-tts returned empty MP3 file")

        conv = subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(mp3_temp),
                "-ar", "24000",
                "-ac", "1",
                "-c:a", "pcm_s16le",
                str(output_wav),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        mp3_temp.unlink(missing_ok=True)

        if conv.returncode != 0 or not output_wav.exists() or output_wav.stat().st_size <= 44:
            raise RuntimeError(f"FFmpeg MP3->WAV conversion failed: {conv.stderr.strip()}")

        spoken_dur = _probe_wav_duration(output_wav)
        return {
            "wav_path": output_wav,
            "voiced_ok": True,
            "fallback_used": False,
            "voice": voice,
            "speaker_id": speaker_id,
            "spoken_duration_sec": round(spoken_dur, 3),
            "target_duration_sec": round(duration_sec, 3),
            "error": None,
        }
    except Exception as exc:
        mp3_temp.unlink(missing_ok=True)
        err_msg = f"TTS failed for speaker={speaker_id} voice={voice}: {exc}"
        logger.warning(err_msg)
        _write_silent_wav(output_wav, duration_sec)
        return {
            "wav_path": output_wav,
            "voiced_ok": False,
            "fallback_used": True,
            "voice": voice,
            "speaker_id": speaker_id,
            "spoken_duration_sec": 0.0,
            "target_duration_sec": round(duration_sec, 3),
            "error": err_msg,
        }
        
