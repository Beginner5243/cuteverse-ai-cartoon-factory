from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _resolve_font_path(language: str = "en") -> str:
    by_lang = {
        "hi": [
            "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        ],
        "gu": [
            "/usr/share/fonts/truetype/noto/NotoSansGujarati-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        ],
        "en": [
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        ],
    }
    for candidate in by_lang.get(language, by_lang["en"]):
        if Path(candidate).exists():
            return candidate
    for fallback in (
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansGujarati-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    ):
        if Path(fallback).exists():
            return fallback
    return ""


def _load_pil_font(size: int, language: str = "en") -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_path = _resolve_font_path(language)
    if font_path:
        try:
            return ImageFont.truetype(font_path, size=size)
        except Exception:
            pass
    return ImageFont.load_default()


def render_scene_clip(
    frame_paths: list[Path],
    audio_wav_path: Path,
    clip_mp4_path: Path,
    duration_sec: float,
    fps: int = 30,
) -> Path:
    clip_mp4_path.parent.mkdir(parents=True, exist_ok=True)
    frames_dir = frame_paths[0].parent
    pattern = str(frames_dir / "frame_%04d.png")

    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", pattern,
        "-i", str(audio_wav_path),
        "-t", f"{duration_sec:.3f}",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        "-c:a", "aac",
        "-b:a", "128k",
        str(clip_mp4_path),
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True)
    return clip_mp4_path


def concatenate_and_burn_subtitles(
    clip_paths: list[Path],
    mixed_audio_path: Path,
    srt_path: Path,
    final_mp4_path: Path,
    total_duration_sec: float,
    language: str = "en",
    width: int = 1080,
    height: int = 1920,
    fps: int = 30,
) -> Path:
    """
    Concatenates scene clips with smooth crossfade transitions, syncs mixed audio,
    and burns wrapped Unicode subtitles without distorting character proportions.
    """
    final_mp4_path.parent.mkdir(parents=True, exist_ok=True)
    concat_video = final_mp4_path.parent / "stitched_raw.mp4"

    if len(clip_paths) >= 2:
        # Build smooth 0.25s crossfade chain across clips while holding exact total duration
        fade_dur = 0.25
        inputs_args: list[str] = []
        for cp in clip_paths:
            inputs_args.extend(["-i", str(cp)])

        filter_parts: list[str] = []
        for idx in range(len(clip_paths)):
            filter_parts.append(
                f"[{idx}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,fps={fps},format=yuv420p[v{idx}]"
            )

        prev_label = "v0"
        elapsed = 0.0
        for idx in range(1, len(clip_paths)):
            clip_dur = total_duration_sec / len(clip_paths)
            elapsed += max(0.5, clip_dur - fade_dur)
            out_label = f"vx{idx}"
            filter_parts.append(
                f"[{prev_label}][v{idx}]xfade=transition=fade:duration={fade_dur:.2f}:offset={elapsed:.2f}[{out_label}]"
            )
            prev_label = out_label

        filter_parts.append(f"[{prev_label}]trim=duration={total_duration_sec:.3f},setpts=PTS-STARTPTS[vout]")
        subprocess.run(
            [
                "ffmpeg", "-y",
                *inputs_args,
                "-filter_complex", ";".join(filter_parts),
                "-map", "[vout]",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps),
                str(concat_video),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    else:
        list_file = final_mp4_path.parent / "clips.txt"
        with list_file.open("w", encoding="utf-8") as f:
            for cp in clip_paths:
                f.write(f"file '{cp.resolve()}'\n")
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", str(list_file),
                "-t", f"{total_duration_sec:.3f}",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps),
                str(concat_video),
            ],
            capture_output=True,
            text=True,
            check=True,
        )

    font_name_map = {
        "hi": "Noto Sans Devanagari",
        "gu": "Noto Sans Gujarati",
        "en": "Noto Sans",
    }
    font_name = font_name_map.get(language, "Noto Sans")
    escaped_srt = str(srt_path.resolve()).replace("\\", "/").replace(":", "\\:")
    force_style = (
        f"FontName={font_name},FontSize=18,PrimaryColour=&H00FFFFFF,"
        f"OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=3,Outline=2,Shadow=1,MarginV=160"
    )
    vf_chain = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
        f"subtitles='{escaped_srt}':fontsdir=/usr/share/fonts/truetype/noto:force_style='{force_style}'"
    )

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(concat_video),
            "-i", str(mixed_audio_path),
            "-vf", vf_chain,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-t", f"{total_duration_sec:.3f}",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", str(fps),
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            str(final_mp4_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return final_mp4_path


def generate_thumbnail(
    sample_frame: Path,
    title: str,
    thumb_path: Path,
    language: str = "en",
    width: int = 1080,
    height: int = 1920,
) -> Path:
    thumb_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(sample_frame).convert("RGB").resize((width, height), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)
    font = _load_pil_font(size=36, language=language)
    wrapped = textwrap.fill(title, width=28)
    draw.rounded_rectangle([70, 140, width - 70, 260], radius=24, fill="#23122E", outline="#FF7B00", width=4)
    draw.text((100, 175), wrapped, fill="#FFF8E1", font=font)
    img.save(thumb_path, format="JPEG", quality=92)
    return thumb_path
    
