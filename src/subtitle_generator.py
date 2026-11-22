from __future__ import annotations

from pathlib import Path
from typing import Any


def _format_srt_time(seconds: float) -> str:
    ms_total = max(0, int(round(seconds * 1000)))
    hours = ms_total // 3_600_000
    rem = ms_total % 3_600_000
    minutes = rem // 60_000
    rem %= 60_000
    secs = rem // 1000
    millis = rem % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_srt_subtitles(scenes: list[dict[str, Any]], srt_path: Path) -> Path:
    srt_path.parent.mkdir(parents=True, exist_ok=True)
    blocks: list[str] = []
    for idx, sc in enumerate(scenes, start=1):
        start_str = _format_srt_time(float(sc["start_sec"]))
        end_str = _format_srt_time(float(sc["start_sec"]) + float(sc["duration_sec"]))
        line = f"{sc['speaker_name']}: {sc['dialogue']}"
        blocks.append(f"{idx}\n{start_str} --> {end_str}\n{line}\n")

    srt_path.write_text("\n".join(blocks), encoding="utf-8")
    return srt_path
  
