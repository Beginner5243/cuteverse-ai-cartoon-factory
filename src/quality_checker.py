from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def run_quality_checks(
    mp4_path: Path,
    srt_path: Path,
    thumb_path: Path,
    expected_duration_sec: float,
    expected_width: int,
    expected_height: int,
    report_path: Path,
) -> dict[str, Any]:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    checks: dict[str, bool] = {
        "mp4_exists": mp4_path.exists() and mp4_path.stat().st_size > 10_000,
        "srt_exists": srt_path.exists() and srt_path.stat().st_size > 20,
        "thumbnail_exists": thumb_path.exists() and thumb_path.stat().st_size > 2_000,
        "duration_valid": False,
        "audio_present": False,
        "resolution_valid": False,
        "frames_decodable": False,
    }

    measured_duration = 0.0
    width = 0
    height = 0

    if checks["mp4_exists"]:
        probe = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_streams", "-show_format",
                "-of", "json", str(mp4_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if probe.returncode == 0 and probe.stdout:
            info = json.loads(probe.stdout)
            streams = info.get("streams", [])
            v_streams = [s for s in streams if s.get("codec_type") == "video"]
            a_streams = [s for s in streams if s.get("codec_type") == "audio"]
            checks["audio_present"] = len(a_streams) > 0
            if v_streams:
                width = int(v_streams[0].get("width", 0))
                height = int(v_streams[0].get("height", 0))
                checks["resolution_valid"] = (width == expected_width and height == expected_height)
            fmt_dur = float(info.get("format", {}).get("duration", 0.0))
            measured_duration = fmt_dur
            checks["duration_valid"] = abs(fmt_dur - expected_duration_sec) <= max(3.0, expected_duration_sec * 0.25)

        # Decode check for corrupted frames
        decode_test = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", str(mp4_path), "-f", "null", "-"],
            capture_output=True,
            text=True,
            check=False,
        )
        checks["frames_decodable"] = (decode_test.returncode == 0 and decode_test.stderr.strip() == "")

    passed = all(checks.values())
    report = {
        "passed": passed,
        "checks": checks,
        "measured_duration_sec": round(measured_duration, 2),
        "expected_duration_sec": expected_duration_sec,
        "resolution": f"{width}x{height}",
        "expected_resolution": f"{expected_width}x{expected_height}",
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
  
