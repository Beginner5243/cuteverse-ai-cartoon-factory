from __future__ import annotations

import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def render_scene_clip(
    frame_paths: list[Path],
    audio_wav_path: Path,
    clip_mp4_path: Path,
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
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        str(clip_mp4_path),
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True)
    return clip_mp4_path


def concatenate_and_burn_subtitles(
    clip_paths: list[Path],
    mixed_audio_path: Path,
    srt_path: Path,
    final_mp4_path: Path,
    width: int = 1080,
    height: int = 1920,
    fps: int = 30,
) -> Path:
    final_mp4_path.parent.mkdir(parents=True, exist_ok=True)
    list_file = final_mp4_path.parent / "clips.txt"
    with list_file.open("w", encoding="utf-8") as f:
        for cp in clip_paths:
            f.write(f"file '{cp.resolve()}'\n")

    concat_video = final_mp4_path.parent / "stitched_raw.mp4"
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps),
            str(concat_video),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    escaped_srt = str(srt_path.resolve()).replace("\\", "/").replace(":", "\\:")
    vf_chain = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
        f"subtitles='{escaped_srt}':force_style='FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,MarginV=140'"
    )

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(concat_video),
            "-i", str(mixed_audio_path),
            "-vf", vf_chain,
            "-map", "0:v:0",
            "-map", "1:a:0",
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
    width: int = 1080,
    height: int = 1920,
) -> Path:
    thumb_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(sample_frame).convert("RGB").resize((width, height))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    draw.rounded_rectangle([80, 220, width - 80, 360], radius=24, fill="#FF7B00")
    draw.text((120, 275), f"CUTEVERSE • {title.upper()}", fill="#FFFFFF", font=font)
    img.save(thumb_path, format="JPEG", quality=90)
    return thumb_path
  
