from __future__ import annotations

import math
import wave
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


def _get_audio_amplitudes(wav_path: Path, fps: int, total_frames: int) -> list[float]:
    if not wav_path.exists():
        return [0.3 if (i % 10 < 5) else 0.05 for i in range(total_frames)]
    try:
        with wave.open(str(wav_path), "rb") as wf:
            n_frames = wf.getnframes()
            sample_rate = wf.getframerate()
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            raw = wf.readframes(n_frames)
        if n_frames == 0 or sample_rate == 0 or sampwidth != 2:
            return [0.2] * total_frames
        samples = [
            int.from_bytes(raw[i:i + 2], byteorder="little", signed=True)
            for i in range(0, len(raw), 2 * max(1, n_channels))
        ]
        peak = max((abs(s) for s in samples), default=1) or 1
        amps: list[float] = []
        samples_per_frame = max(1, len(samples) // max(1, total_frames))
        for f in range(total_frames):
            chunk = samples[f * samples_per_frame:(f + 1) * samples_per_frame]
            avg = (sum(abs(x) for x in chunk) / max(1, len(chunk))) / peak
            amps.append(min(1.0, avg * 2.2))
        return amps
    except Exception:
        return [0.25 if (i % 12 < 6) else 0.05 for i in range(total_frames)]


def _draw_expression_and_mouth(
    draw: ImageDraw.ImageDraw,
    cx: int,
    mouth_y: int,
    expression: str,
    mouth_open: float,
    blink: bool,
    eye_y: int,
    eye_offset_x: int,
) -> None:
    # Blinking or expression eyes
    for side in (-1, 1):
        ex = cx + side * eye_offset_x
        if blink:
            draw.line([(ex - 18, eye_y), (ex + 18, eye_y)], fill="#111111", width=4)
        elif expression == "angry":
            draw.line([(ex - 20, eye_y - 14), (ex + 16, eye_y - 2)], fill="#B71C1C", width=5)
        elif expression == "crying":
            draw.ellipse([ex - 6, eye_y + 18, ex + 6, eye_y + 34], fill="#29B6F6")

    # Mouth driven by speech amplitude + expression
    open_h = int(6 + mouth_open * 26)
    if expression == "crying":
        draw.arc([cx - 26, mouth_y, cx + 26, mouth_y + 28], start=180, end=360, fill="#222222", width=4)
    elif open_h > 9 or expression in ("surprised", "laughing"):
        draw.ellipse([cx - 22, mouth_y - open_h // 2, cx + 22, mouth_y + open_h // 2],
                     fill="#D32F2F", outline="#222222", width=3)
    else:
        draw.arc([cx - 24, mouth_y - 8, cx + 24, mouth_y + 12], start=15, end=165, fill="#222222", width=4)


def render_animated_scene_frames(
    scene: dict[str, Any],
    backdrop_path: Path,
    ref_images: dict[str, Path],
    audio_wav_path: Path,
    frames_dir: Path,
    width: int = 1080,
    height: int = 1920,
    fps: int = 30,
) -> list[Path]:
    frames_dir.mkdir(parents=True, exist_ok=True)
    total_frames = max(15, int(round(scene["duration_sec"] * fps)))
    amplitudes = _get_audio_amplitudes(audio_wav_path, fps, total_frames)

    base_bg = Image.open(backdrop_path).convert("RGB").resize((width, height))
    char_a_sprite = Image.open(ref_images["char_a"]).convert("RGBA").resize((360, 360))
    char_b_sprite = Image.open(ref_images["char_b"]).convert("RGBA").resize((340, 340))

    font = ImageFont.load_default()
    frame_paths: list[Path] = []
    motion = scene.get("motion", "walk_in")
    expression = scene.get("expression", "happy")
    speaker_id = scene.get("speaker_id", "char_a")

    for f_idx in range(total_frames):
        progress = f_idx / max(1, total_frames - 1)
        frame = base_bg.copy()

        # Camera movement
        cam_move = scene.get("camera_move", "zoom_in")
        if cam_move == "zoom_in":
            zoom = 1.0 + 0.06 * progress
            zw, zh = int(width * zoom), int(height * zoom)
            zoomed = frame.resize((zw, zh))
            left = (zw - width) // 2
            top = (zh - height) // 2
            frame = zoomed.crop((left, top, left + width, top + height))
        elif cam_move == "pan_right":
            shift = int(40 * progress)
            frame = frame.transform((width, height), Image.AFFINE, (1, 0, shift, 0, 1, 0))

        canvas = frame.convert("RGBA")
        draw = ImageDraw.Draw(canvas)

        # Motion trajectories
        bounce = abs(math.sin(progress * math.pi * 4)) * 38
        hop = abs(math.sin(progress * math.pi * 6)) * 55
        if motion == "walk_in":
            ax = int(-120 + 420 * min(1.0, progress * 1.4))
            ay = int(1120 - bounce * 0.5)
            bx = 640
            by = int(1140 - bounce * 0.3)
        elif motion == "jump_spin":
            ax = 240 + int(60 * math.sin(progress * math.pi * 2))
            ay = int(1120 - hop)
            bx = 650
            by = int(1140 - bounce * 0.4)
        elif motion == "run_bounce":
            ax = 230
            ay = int(1120 - bounce * 0.6)
            bx = int(920 - 280 * min(1.0, progress * 1.3))
            by = int(1140 - hop * 0.8)
        elif motion == "dance_stomp":
            ax = 230 + int(25 * math.sin(progress * math.pi * 6))
            ay = int(1120 - bounce * 0.7)
            bx = 650 - int(25 * math.sin(progress * math.pi * 6))
            by = int(1140 - bounce * 0.7)
        else:
            ax = 230
            ay = int(1120 - bounce * 0.4)
            bx = 650
            by = int(1140 - bounce * 0.4)

        # Head tilt / rotation
        tilt_a = 8 * math.sin(progress * math.pi * 4) if speaker_id == "char_a" else 0
        tilt_b = 8 * math.sin(progress * math.pi * 4) if speaker_id == "char_b" else 0
        rot_a = char_a_sprite.rotate(tilt_a, expand=True, resample=Image.BICUBIC)
        rot_b = char_b_sprite.rotate(tilt_b, expand=True, resample=Image.BICUBIC)

        canvas.alpha_composite(rot_a, (ax, ay))
        canvas.alpha_composite(rot_b, (bx, by))

        # Blink every ~3 seconds
        blink = (f_idx % (fps * 3)) < 3
        amp = amplitudes[f_idx] if f_idx < len(amplitudes) else 0.0

        # Expressive mouth & eye overlay on active speaker
        if speaker_id == "char_a":
            _draw_expression_and_mouth(
                draw,
                cx=ax + rot_a.width // 2,
                mouth_y=ay + 195,
                expression=expression,
                mouth_open=amp,
                blink=blink,
                eye_y=ay + 145,
                eye_offset_x=42,
            )
        else:
            _draw_expression_and_mouth(
                draw,
                cx=bx + rot_b.width // 2,
                mouth_y=by + 190,
                expression=expression,
                mouth_open=amp,
                blink=blink,
                eye_y=by + 140,
                eye_offset_x=38,
            )

        # Subtle scene badge at top
        draw.rounded_rectangle([40, 70, 340, 125], radius=16, fill=(255, 255, 255, 210))
        draw.text((62, 88), f"SCENE {scene['scene_number']} • {motion.upper()}", fill="#1A1A1A", font=font)

        out_frame = frames_dir / f"frame_{f_idx:04d}.png"
        canvas.convert("RGB").save(out_frame, format="PNG")
        frame_paths.append(out_frame)

    return frame_paths
  
