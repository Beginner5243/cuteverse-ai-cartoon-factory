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
    """
    Procedural cartoon background illustration (never claimed to be AI-generated artwork).
    Adapts environment by scene beat/setting so shots have distinct cartoon places.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    setting = scene.get("setting", "sunny_garden")
    img = Image.new("RGB", (width, height), "#FFF5E4")
    draw = ImageDraw.Draw(img)

    if setting == "kitchen_room":
        # Warm indoor room wall, wainscot paneling, window, and wooden floor
        draw.rectangle([0, 0, width, int(height * 0.66)], fill="#FDE8C8")
        draw.rectangle([0, int(height * 0.42), width, int(height * 0.66)], fill="#F4CFA0")
        draw.line([(0, int(height * 0.42)), (width, int(height * 0.42))], fill="#C9975B", width=6)
        # Window
        draw.rounded_rectangle([140, 180, 440, 460], radius=24, fill="#B3E5FC", outline="#795548", width=10)
        draw.line([(290, 180), (290, 460)], fill="#795548", width=8)
        draw.line([(140, 320), (440, 320)], fill="#795548", width=8)
        # Shelf & jar
        draw.rectangle([620, 290, 940, 322], fill="#8D6E63")
        draw.rounded_rectangle([680, 210, 760, 290], radius=14, fill="#FFE082", outline="#5D4037", width=4)
        # Floor
        floor_y = int(height * 0.66)
        draw.rectangle([0, floor_y, width, height], fill="#D7A86E")
        for y_stripe in range(floor_y, height, 70):
            draw.line([(0, y_stripe), (width, y_stripe)], fill="#B8864B", width=3)
    else:
        # Illustrated sunny garden / courtyard
        draw.rectangle([0, 0, width, int(height * 0.65)], fill="#CBEF62" if setting == "garden_path" else "#B8E8FF")
        # Distant hills
        draw.ellipse([-120, 680, 620, 1320], fill="#9CCC65")
        draw.ellipse([440, 720, 1220, 1340], fill="#8BC34A")
        # Sun
        draw.ellipse([820, 140, 970, 290], fill="#FFD54F")
        # Garden bushes
        for bx in range(60, width - 60, 220):
            draw.ellipse([bx, int(height * 0.57), bx + 180, int(height * 0.68)], fill="#4CAF50")
        # Foreground path & grass
        floor_y = int(height * 0.66)
        draw.rectangle([0, floor_y, width, height], fill="#7CB342")
        draw.polygon(
            [(340, floor_y), (740, floor_y), (960, height), (120, height)],
            fill="#F3D59B",
        )

    img = img.filter(ImageFilter.GaussianBlur(radius=1.0))
    img.save(output_path, format="PNG")
    return output_path
    
