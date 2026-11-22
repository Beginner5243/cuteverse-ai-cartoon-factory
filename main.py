from __future__ import annotations

import argparse
import json
import logging
import shutil
from pathlib import Path

from src.animation_engine import render_animated_scene_frames
from src.audio_mixer import mix_episode_audio
from src.character_manager import ensure_character_references, load_characters
from src.image_generator import generate_scene_backdrop
from src.quality_checker import run_quality_checks
from src.story_generator import generate_episode_package, write_script_and_storyboard
from src.subtitle_generator import generate_srt_subtitles
from src.video_generator import attempt_remote_video_generation
from src.video_renderer import concatenate_and_burn_subtitles, generate_thumbnail, render_scene_clip
from src.voice_generator import generate_scene_voice


def main() -> int:
    parser = argparse.ArgumentParser(description="CuteVerse AI Cartoon Factory Runner")
    parser.add_argument("--episode", type=int, default=1)
    parser.add_argument("--language", type=str, default="en", choices=["en", "hi", "gu"])
    parser.add_argument("--duration", type=int, default=30)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent
    log_dir = repo_root / "output" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"ep_{args.episode:03d}_{args.language}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler()],
    )
    logger = logging.getLogger("cuteverse.main")

    try:
        settings = json.loads((repo_root / "config" / "settings.json").read_text(encoding="utf-8"))
        characters = load_characters(repo_root / "config" / "characters.json")

        allowed_durations = settings["video"]["allowed_durations_sec"]
        default_duration = settings["video"]["default_duration_sec"]
        duration = args.duration if args.duration in allowed_durations else default_duration
        width = int(settings["video"]["width"])
        height = int(settings["video"]["height"])
        fps = int(settings["video"]["fps"])

        pkg = generate_episode_package(
            episode_id=args.episode,
            language=args.language,
            duration_sec=duration,
            characters_data=characters,
        )
        write_script_and_storyboard(
            pkg,
            repo_root / "episodes" / "scripts",
            repo_root / "episodes" / "storyboards",
        )
        ref_images = ensure_character_references(characters, repo_root)

        work_dir = repo_root / "output" / "work" / f"ep_{args.episode:03d}_{args.language}"
        if work_dir.exists():
            shutil.rmtree(work_dir)
        work_dir.mkdir(parents=True, exist_ok=True)

        lang_cfg = settings["languages"][args.language]
        clip_paths: list[Path] = []
        voice_wavs: list[Path] = []
        first_frame: Path | None = None
        fallback_thumb_source: Path | None = None

        for sc in pkg["scenes"]:
            s_num = sc["scene_number"]
            speaker_id = sc["speaker_id"]
            voice_name = lang_cfg["voice_char_a"] if speaker_id == "char_a" else lang_cfg["voice_char_b"]

            voice_wav = generate_scene_voice(
                text=sc["dialogue"],
                voice=voice_name,
                output_wav=work_dir / f"voice_{s_num:02d}.wav",
                duration_sec=float(sc["duration_sec"]),
                speaker_id=speaker_id,
            )
            voice_wavs.append(voice_wav)

            backdrop = generate_scene_backdrop(
                scene=sc,
                output_path=work_dir / f"bg_{s_num:02d}.png",
                width=width,
                height=height,
            )
            if fallback_thumb_source is None:
                fallback_thumb_source = backdrop

            remote_clip = attempt_remote_video_generation(
                scene=sc,
                ref_image_path=ref_images[speaker_id],
                output_mp4=work_dir / f"remote_{s_num:02d}.mp4",
                remote_cfg=settings.get("remote_video", {}),
            )

            if remote_clip and remote_clip.exists():
                clip_paths.append(remote_clip)
            else:
                frames = render_animated_scene_frames(
                    scene=sc,
                    backdrop_path=backdrop,
                    ref_images=ref_images,
                    audio_wav_path=voice_wav,
                    frames_dir=work_dir / f"frames_{s_num:02d}",
                    width=width,
                    height=height,
                    fps=fps,
                )
                if first_frame is None and frames:
                    first_frame = frames[0]
                clip_mp4 = render_scene_clip(
                    frame_paths=frames,
                    audio_wav_path=voice_wav,
                    clip_mp4_path=work_dir / f"clip_{s_num:02d}.mp4",
                    fps=fps,
                )
                clip_paths.append(clip_mp4)

        mixed_audio = mix_episode_audio(
            scenes=pkg["scenes"],
            voice_wavs=voice_wavs,
            output_audio_path=work_dir / "mixed_audio.m4a",
            total_duration_sec=float(duration),
        )

        stem = f"ep_{args.episode:03d}_{args.language}"
        srt_path = generate_srt_subtitles(
            pkg["scenes"],
            repo_root / "output" / "subtitles" / f"{stem}.srt",
        )
        final_mp4 = concatenate_and_burn_subtitles(
            clip_paths=clip_paths,
            mixed_audio_path=mixed_audio,
            srt_path=srt_path,
            final_mp4_path=repo_root / "output" / "videos" / f"{stem}.mp4",
            width=width,
            height=height,
            fps=fps,
        )

        thumb_source = first_frame or fallback_thumb_source
        thumb_path = repo_root / "output" / "thumbnails" / f"{stem}.jpg"
        if thumb_source:
            generate_thumbnail(thumb_source, pkg["title"], thumb_path, width=width, height=height)

        report_path = repo_root / "output" / "reports" / f"{stem}_quality.json"
        report = run_quality_checks(
            mp4_path=final_mp4,
            srt_path=srt_path,
            thumb_path=thumb_path,
            expected_duration_sec=float(duration),
            expected_width=width,
            expected_height=height,
            report_path=report_path,
        )
        logger.info("Quality report: %s", json.dumps(report))
        if not report["passed"]:
            raise RuntimeError(f"Episode failed quality checks: {report}")

        logger.info("Episode completed successfully: %s", final_mp4)
        return 0
    except Exception as exc:
        logger.exception("Pipeline error: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
        
