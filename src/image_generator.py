from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter


def generate_scene_backdrop(
    scene: dict[str, Any],
    output_path: Path,
    width: int = 1080,
    height: int = 1920,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (width, height), "#FFF4E0")
    draw = ImageDraw.Draw(img)

    # Soft sky/wall gradient bands
    top_colors = [(255, 243, 214), (242, 232, 255), (224, 247, 250)]
    band_color = top_colors[(scene["scene_number"] - 1) % len(top_colors)]
    draw.rectangle([0, 0, width, int(height * 0.68)], fill=band_color)

    # Decorative background shapes
    draw.ellipse([80, 140, 260, 320], fill="#FFE082")
    draw.ellipse([width - 240, 220, width - 60, 400], fill="#FFCCBC")

    # Floor
    floor_y = int(height * 0.68)
    draw.rectangle([0, floor_y, width, height], fill="#A3D977")
    draw.line([(0, floor_y), (width, floor_y)], fill="#558B2F", width=8)

    img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
    img.save(output_path, format="PNG")
    return output_path
  
