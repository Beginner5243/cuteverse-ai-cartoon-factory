from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageStat


def _check_alpha_transparency(ref_paths: list[Path]) -> dict[str, bool]:
    results: dict[str, bool] = {}
    for p in ref_paths:
        if not p.exists():
            results[p.name] = False
            continue
        im = Image.open(p).convert("RGBA")
        alpha = im.getchannel("A")
        extrema = alpha.getextrema()
        # Must contain both transparent (0) and opaque (> 200) pixels
        results[p.name] = (extrema[0] == 0 and extrema[1] >= 200)
    return results


def _sample_video_frames(mp4_path: Path, sample_dir: Path, count: int = 4) -> list[Path]:
    sample_dir.mkdir(parents=True, exist_ok=True)
    out_pattern = str(sample_dir / "sample_%02d.png")
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(mp4_path),
            "-vf", f"fps=0.2,scale=540:960",
            "-frames:v", str(count),
            out_pattern,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return sorted(sample_dir.glob("sample_*.png"))


def _check_frame_variety_and_not_blank(frames: list[Path]) -> tuple[bool, bool]:
    if not frames:
        return False, False
    not_blank = True
    means: list[float] = []
    for fp in frames:
        st = ImageStat.Stat(Image.open(fp).convert("RGB"))
        # Blank/flat frame check via standard deviation
        if max(st.stddev) < 4.0:
            not_blank = False
        means.append(sum(st.mean) / 3.0)
    has_variation = (max(means) - min(means)) >= 1.5 if len(means) >= 2 else True
    return not_blank, has_variation


def _check_audio_not_silent(mp4_path: Path) -> bool:
    probe = subprocess.run(
        [
            "ffmpeg", "-v", "info",
            "-i", str(mp4_path),
            "-af", "volumedetect",
            "-f", "null", "-",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    stderr = probe.stderr or ""
    for line in stderr.splitlines():
        if "max_volume:" in line:
            try:
                val_str = line.split("max_volume:")[1].split("dB")[0].strip()
                if val_str == "-inf" or float(val_str) < -55.0:
                    return False
                return True
            except Exception:
                return True
    return True


def run_quality_checks(
    mp4_path: Path,
    srt_path: Path,
    thumb_path: Path,
    expected_duration_sec: float,
    expected_width: int,
    expected_height: int,
    report_path: Path,
    ref_images: list[Path] | None = None,
    tts_records: list[dict[str, Any]] | None = None,
    preview_dir: Path | None = None,
) -> dict[str, Any]:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    srt_text = srt_path.read_text(encoding="utf-8") if srt_path.exists() else ""
    alpha_map = _check_alpha_transparency(ref_images or [])

    sampled = _sample_video_frames(mp4_path, preview_dir or (report_path.parent / "previews")) if mp4_path.exists() else []
    frames_not_blank, scene_variation_ok = _check_frame_variety_and_not_blank(sampled)
    audio_not_silent = _check_audio_not_silent(mp4_path) if mp4_path.exists() else False

    tts_failures = [r for r in (tts_records or []) if not r.get("voiced_ok", False)]
    fonts_present = any(
        Path(p).exists()
        for p in (
            "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansGujarati-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        )
    )

    checks: dict[str, bool] = {
        "mp4_exists": mp4_path.exists() and mp4_path.stat().st_size > 10_000,
        "srt_unicode_valid": len(srt_text.strip()) > 30 and "-->" in srt_text,
        "thumbnail_exists": thumb_path.exists() and thumb_path.stat().st_size > 2_000,
        "alpha_transparency_valid": all(alpha_map.values()) if alpha_map else True,
        "fonts_available": fonts_present,
        "frames_not_blank": frames_not_blank,
        "scene_variation_ok": scene_variation_ok,
        "audio_not_silent": audio_not_silent,
        "tts_all_voiced": len(tts_failures) == 0,
        "duration_synced": False,
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
            checks["duration_synced"] = abs(fmt_dur - expected_duration_sec) <= 0.75

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
        "alpha_by_asset": alpha_map,
        "tts_failures": tts_failures,
        "preview_frames": [str(p) for p in sampled],
        "measured_duration_sec": round(measured_duration, 2),
        "expected_duration_sec": expected_duration_sec,
        "resolution": f"{width}x{height}",
        "expected_resolution": f"{expected_width}x{expected_height}",
    }
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report
    
