from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger("cuteverse.video_generator")


def attempt_remote_video_generation(
    scene: dict[str, Any],
    ref_image_path: Path,
    output_mp4: Path,
    remote_cfg: dict[str, Any],
) -> Path | None:
    """
    Optional hook for external free cloud video services.
    Never blocks or fails the pipeline if no remote API is configured or reachable.
    """
    if not remote_cfg.get("enabled", False):
        return None

    max_retries = int(remote_cfg.get("max_retries", 2))
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                "Remote video hook attempt %d/%d for scene %s (provider=%s)",
                attempt,
                max_retries,
                scene["scene_number"],
                remote_cfg.get("provider", "none"),
            )
            # Intentionally no hardcoded paid/unverified endpoint; returns None to trigger
            # the deterministic free fallback engine cleanly.
            return None
        except Exception as exc:
            logger.warning("Remote video attempt %d failed: %s", attempt, exc)
            time.sleep(1)

    return None
  
