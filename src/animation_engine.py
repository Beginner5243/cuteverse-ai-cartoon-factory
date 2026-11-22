from __future__ import annotations

import math
import wave
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from src.character_manager import extract_articulated_parts


def _get_audio_amplitudes(wav_path: Path, fps: int, total_frames: int) -> list[float]:
    if not wav_path.exists():
        return [0.0] * total_frames
    try:
        with wave.open(str(wav_path), "rb") as wf:
            n_frames = wf.getnframes()
            n_channels = max(1, wf.getnchannels())
            sampwidth = wf.getsampwidth()
            raw = wf.readframes(n_frames)
        if n_frames == 0 or sampwidth != 2:
            return [0.0] * total_frames
        samples = [
            int.from_bytes(raw[i:i + 2], byteorder="little", signed=True)
            for i in range(0, len(raw), 2 * n_channels)
        ]
        peak = max((abs(s) for s in samples), default=1) or 1
        amps: list[float] = []
        samples_per_frame = max(1, len(samples) // max(1, total_frames))
        for f in range(total_frames):
            chunk = samples[f * samples_per_frame:(f + 1) * samples_per_frame]
            avg = (sum(abs(x) for x in chunk) / max(1, len(chunk))) / peak
            amps.append(min(1.0, avg * 2.4))
        return amps
    except Exception:
        return [0.0] * total_frames


def _draw_articulated_character(
    canvas: Image.Image,
    parts: dict[str, Image.Image],
    x: int,
    y: int,
    scale: float,
    phase: float,
    head_tilt: float,
    mouth_open_amount: float,
    expression: str,
    blink: bool,
    is_speaker: bool,
) -> tuple[int, int, int, int]:
    """
    Renders separated legs, arms, body, and head with articulation,
    dialogue timing + amplitude mouth motion, and expression overlays.
    Returns bounding box (x0, y0, x1, y1).
    """
    stride = math.sin(phase * math.pi * 4)
    leg_swing_l = 18 * stride
    leg_swing_r = -18 * stride
    arm_swing_l = -22 * stride if is_speaker else -10 * stride
    arm_swing_r = 22 * stride if is_speaker else 10 * stride
    bob_y = -abs(math.cos(phase * math.pi * 4)) * 14

    def resize_part(name: str, w_base: int, h_base: int) -> Image.Image:
        return parts[name].resize(
            (max(1, int(w_base * scale)), max(1, int(h_base * scale))),
            Image.Resampling.LANCZOS,
        )

    leg_l = resize_part("left_leg", 68, 66).rotate(leg_swing_l, expand=True, resample=Image.BICUBIC)
    leg_r = resize_part("right_leg", 68, 66).rotate(leg_swing_r, expand=True, resample=Image.BICUBIC)
    arm_l = resize_part("left_arm", 68, 72).rotate(arm_swing_l, expand=True, resample=Image.BICUBIC)
    arm_r = resize_part("right_arm", 68, 72).rotate(arm_swing_r, expand=True, resample=Image.BICUBIC)
    body = resize_part("body", 165, 112)
    head = resize_part("head", 220, 205).rotate(head_tilt, expand=True, resample=Image.BICUBIC)

    cur_y = int(y + bob_y)
    body_x = x + int(28 * scale)
    body_y = cur_y + int(155 * scale)
    leg_y = body_y + int(82 * scale)

    canvas.alpha_composite(leg_l, (body_x + int(8 * scale), leg_y))
    canvas.alpha_composite(leg_r, (body_x + int(82 * scale), leg_y))
    canvas.alpha_composite(arm_l, (body_x - int(36 * scale), body_y + int(8 * scale)))
    canvas.alpha_composite(arm_r, (body_x + int(132 * scale), body_y + int(8 * scale)))
    canvas.alpha_composite(body, (body_x, body_y))

    head_x = x + int(4 * scale) + int(head_tilt * 0.6)
    head_y = cur_y
    canvas.alpha_composite(head, (head_x, head_y))

    draw = ImageDraw.Draw(canvas)
    h_cx = head_x + head.width // 2
    h_cy = head_y + head.height // 2

    # Brows & emotion cues on head
    for side in (-1, 1):
        ex = h_cx + side * int(34 * scale)
        ey = h_cy - int(12 * scale)
        if blink:
            draw.line([(ex - 14, ey), (ex + 14, ey)], fill="#1A1A1A", width=3)
        elif expression == "angry":
            draw.line([(ex - 16, ey - 22), (ex + 12, ey - 12)], fill="#B71C1C", width=4)
        elif expression == "surprised":
            draw.arc([ex - 14, ey - 30, ex + 14, ey - 14], start=180, end=360, fill="#1A1A1A", width=3)
        elif expression == "crying":
            draw.ellipse([ex - 4, ey + 14, ex + 4, ey + 26], fill="#29B6F6")

    # Mouth driven by dialogue timing envelope + speech amplitude
    mouth_y = h_cy + int(34 * scale)
    m_open = int(4 + mouth_open_amount * 20)
    if mouth_open_amount > 0.14 or expression in ("surprised", "laughing"):
        draw.ellipse(
            [h_cx - int(18 * scale), mouth_y - m_open // 2, h_cx + int(18 * scale), mouth_y + m_open // 2],
            fill="#C62828",
            outline="#1A1A1A",
            width=3,
        )
    else:
        draw.arc(
            [h_cx - int(20 * scale), mouth_y - 6, h_cx + int(20 * scale), mouth_y + 10],
            start=12,
            end=168,
            fill="#1A1A1A",
            width=3,
        )

    x1 = max(x + body_x - int(36 * scale), x)
    y1 = leg_y + leg_l.height
    return (min(x, body_x - int(36 * scale)), head_y, max(head_x + head.width, body_x + int(132 * scale) + arm_r.width), y1)


def _draw_prop(
    canvas: Image.Image,
    setting: str,
    prop_action: str,
    progress: float,
    ax: int,
    bx: int,
    y_base: int,
) -> None:
    if prop_action == "drop_object" and progress > 0.45:
        return
    draw = ImageDraw.Draw(canvas)
    t_arc = math.sin(progress * math.pi)
    px = int(ax + (bx - ax) * progress)
    py = int(y_base + 120 - t_arc * 160)
    if prop_action == "share_object":
        px = (ax + bx) // 2 + 60
        py = y_base + 140

    if setting == "sunny_garden":
        # Golden mango prop
        draw.ellipse([px - 28, py - 22, px + 28, py + 24], fill="#FFB300", outline="#E65100", width=3)
        draw.polygon([(px, py - 22), (px + 14, py - 34), (px + 18, py - 18)], fill="#43A047")
    else:
        # Sweet laddoo prop
        draw.ellipse([px - 26, py - 26, px + 26, py + 26], fill="#FFA000", outline="#795548", width=3)
        draw.point([(px - 6, py - 5), (px + 7, py + 4), (px + 4, py - 8)], fill="#FFF8E1")


def render_animated_scene_frames(
    scene: dict[str, Any],
    backdrop_path: Path,
    ref_images: dict[str, Path],
    audio_wav_path: Path,
    frames_dir: Path,
    width: int = 1080,
    height: int = 1920,
    fps: int = 30,
    spoken_duration_sec: float | None = None,
) -> list[Path]:
    frames_dir.mkdir(parents=True, exist_ok=True)
    duration_sec = float(scene["duration_sec"])
    total_frames = max(15, int(round(duration_sec * fps)))
    amplitudes = _get_audio_amplitudes(audio_wav_path, fps, total_frames)

    parts_a = extract_articulated_parts(ref_images["char_a"])
    parts_b = extract_articulated_parts(ref_images["char_b"])
    base_bg = Image.open(backdrop_path).convert("RGB").resize((width, height), Image.Resampling.LANCZOS)

    action = scene.get("action", "walk_together")
    expression = scene.get("expression", "happy")
    speaker_id = scene.get("speaker_id", "char_a")
    setting = scene.get("setting", "kitchen_room")
    prop_action = scene.get("prop_action", "pass_object")
    margin = 60
    active_speech_end = spoken_duration_sec if spoken_duration_sec and spoken_duration_sec > 0 else duration_sec * 0.85

    frame_paths: list[Path] = []
    for f_idx in range(total_frames):
        t_sec = f_idx / fps
        progress = f_idx / max(1, total_frames - 1)
        frame = base_bg.copy()

        cam_move = scene.get("camera_move", "zoom_in")
        if cam_move == "zoom_in":
            zoom = 1.0 + 0.035 * progress
            zw, zh = int(width * zoom), int(height * zoom)
            zoomed = frame.resize((zw, zh), Image.Resampling.BILINEAR)
            frame = zoomed.crop(((zw - width) // 2, (zh - height) // 2, (zw - width) // 2 + width, (zh - height) // 2 + height))

        canvas = frame.convert("RGBA")

        if action == "walk_together":
            ax = int(margin + 140 * progress)
            bx = int(520 + 110 * progress)
            ay = 1130
            by = 1140
        elif action == "talk_face_to_face":
            ax = 210
            bx = 610
            ay = 1130
            by = 1140
        elif action in ("pass_object", "catch_object", "share_object"):
            ax = 190
            bx = 620
            ay = 1130
            by = 1140
        elif action == "run_and_fall":
            ax = int(170 + 180 * min(1.0, progress * 1.3))
            bx = int(580 + 140 * min(1.0, progress * 1.3))
            fall_drop = int(90 * max(0.0, (progress - 0.55) / 0.45))
            ay = 1130 + fall_drop
            by = 1140 + (fall_drop if speaker_id == "char_b" else 0)
        else:  # laugh_together
            ax = 200 + int(18 * math.sin(progress * math.pi * 6))
            bx = 600 - int(18 * math.sin(progress * math.pi * 6))
            ay = 1130
            by = 1140

        ax = max(margin, min(width - 280 - margin, ax))
        bx = max(margin, min(width - 280 - margin, bx))

        # Dialogue timing window + speech amplitude for mouth animation
        in_dialogue = t_sec <= active_speech_end
        timing_cadence = (0.55 + 0.45 * math.sin(t_sec * 18.0)) if in_dialogue else 0.0
        amp = amplitudes[f_idx] if f_idx < len(amplitudes) else 0.0

        mouth_a = max(amp, timing_cadence * 0.55) if (speaker_id == "char_a" and in_dialogue) else amp * 0.2
        mouth_b = max(amp, timing_cadence * 0.55) if (speaker_id == "char_b" and in_dialogue) else amp * 0.2

        head_tilt_a = 10 * math.sin(progress * math.pi * 4) if speaker_id == "char_a" else -4 * math.cos(progress * math.pi * 2)
        head_tilt_b = -10 * math.sin(progress * math.pi * 4) if speaker_id == "char_b" else 4 * math.cos(progress * math.pi * 2)
        blink = (f_idx % (fps * 3)) < 3

        _draw_articulated_character(
            canvas=canvas,
            parts=parts_a,
            x=ax,
            y=ay,
            scale=1.05,
            phase=progress,
            head_tilt=head_tilt_a,
            mouth_open_amount=mouth_a,
            expression=expression if speaker_id == "char_a" else "happy",
            blink=blink,
            is_speaker=(speaker_id == "char_a"),
        )
        _draw_articulated_character(
            canvas=canvas,
            parts=parts_b,
            x=bx,
            y=by,
            scale=1.02,
            phase=progress + 0.15,
            head_tilt=head_tilt_b,
            mouth_open_amount=mouth_b,
            expression=expression if speaker_id == "char_b" else "happy",
            blink=blink,
            is_speaker=(speaker_id == "char_b"),
        )

        _draw_prop(canvas, setting=setting, prop_action=prop_action, progress=progress, ax=ax + 120, bx=bx + 90, y_base=1150)

        out_frame = frames_dir / f"frame_{f_idx:04d}.png"
        canvas.convert("RGB").save(out_frame, format="PNG")
        frame_paths.append(out_frame)

    return frame_paths
    
