from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


def load_characters(config_path: Path) -> dict[str, Any]:
    return json.loads(config_path.read_text(encoding="utf-8"))


def _draw_char_a(draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float = 1.0) -> None:
    r = int(115 * scale)
    # Ears
    draw.ellipse([cx - int(110 * scale), cy - int(135 * scale), cx - int(35 * scale), cy - int(35 * scale)],
                 fill="#B86B35", outline="#2B1E16", width=5)
    draw.ellipse([cx + int(35 * scale), cy - int(135 * scale), cx + int(110 * scale), cy - int(35 * scale)],
                 fill="#B86B35", outline="#2B1E16", width=5)
    # Body
    draw.ellipse([cx - int(95 * scale), cy + int(55 * scale), cx + int(95 * scale), cy + int(225 * scale)],
                 fill="#F6E7D8", outline="#2B1E16", width=5)
    # Blue scarf
    draw.rounded_rectangle([cx - int(85 * scale), cy + int(50 * scale), cx + int(85 * scale), cy + int(92 * scale)],
                           radius=18, fill="#4EA8DE", outline="#1D3557", width=4)
    # Head
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#F6E7D8", outline="#2B1E16", width=5)
    # Eye patches
    draw.ellipse([cx - int(72 * scale), cy - int(35 * scale), cx - int(12 * scale), cy + int(32 * scale)],
                 fill="#B86B35")
    draw.ellipse([cx + int(12 * scale), cy - int(35 * scale), cx + int(72 * scale), cy + int(32 * scale)],
                 fill="#B86B35")
    # Eyes
    for ex in (-42, 42):
        ox = cx + int(ex * scale)
        oy = cy - int(2 * scale)
        er = int(20 * scale)
        draw.ellipse([ox - er, oy - er, ox + er, oy + er], fill="#FFFFFF", outline="#111111", width=3)
        pr = int(11 * scale)
        draw.ellipse([ox - pr, oy - pr, ox + pr, oy + pr], fill="#111111")
        draw.ellipse([ox - int(5 * scale), oy - int(8 * scale), ox + int(2 * scale), oy - int(1 * scale)],
                     fill="#FFFFFF")
    # Nose & smile
    draw.ellipse([cx - int(14 * scale), cy + int(24 * scale), cx + int(14 * scale), cy + int(44 * scale)],
                 fill="#2B1E16")
    draw.arc([cx - int(32 * scale), cy + int(42 * scale), cx + int(32 * scale), cy + int(76 * scale)],
             start=10, end=170, fill="#2B1E16", width=4)


def _draw_char_b(draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float = 1.0) -> None:
    # Green leaf sprout on top
    draw.polygon([
        (cx, cy - int(105 * scale)),
        (cx - int(45 * scale), cy - int(155 * scale)),
        (cx - int(10 * scale), cy - int(125 * scale)),
    ], fill="#4CAF50", outline="#1B5E20", width=4)
    draw.polygon([
        (cx, cy - int(105 * scale)),
        (cx + int(45 * scale), cy - int(155 * scale)),
        (cx + int(10 * scale), cy - int(125 * scale)),
    ], fill="#66BB6A", outline="#1B5E20", width=4)
    # Round veggie body (purple top + cream bottom)
    r = int(110 * scale)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#7B4B94", outline="#24142E", width=5)
    draw.chord([cx - r, cy - r, cx + r, cy + r], start=10, end=170, fill="#F7F3E9", outline="#24142E", width=4)
    # Orange headband
    draw.rectangle([cx - r + 4, cy - int(55 * scale), cx + r - 4, cy - int(28 * scale)],
                   fill="#FF7B00", outline="#7C3A00", width=3)
    # Eyes
    for ex in (-38, 38):
        ox = cx + int(ex * scale)
        oy = cy - int(5 * scale)
        er = int(22 * scale)
        draw.ellipse([ox - er, oy - er, ox + er, oy + er], fill="#FFFFFF", outline="#111111", width=3)
        pr = int(10 * scale)
        draw.ellipse([ox - pr, oy - pr, ox + pr, oy + pr], fill="#111111")
    # Mischievous grin
    draw.arc([cx - int(36 * scale), cy + int(22 * scale), cx + int(36 * scale), cy + int(58 * scale)],
             start=10, end=170, fill="#24142E", width=4)
    # Tiny arms & legs
    draw.line([(cx - r, cy + int(20 * scale)), (cx - r - int(35 * scale), cy + int(5 * scale))],
              fill="#24142E", width=7)
    draw.line([(cx + r, cy + int(20 * scale)), (cx + r + int(35 * scale), cy + int(5 * scale))],
              fill="#24142E", width=7)
    draw.line([(cx - int(40 * scale), cy + r), (cx - int(45 * scale), cy + r + int(45 * scale))],
              fill="#24142E", width=8)
    draw.line([(cx + int(40 * scale), cy + r), (cx + int(45 * scale), cy + r + int(45 * scale))],
              fill="#24142E", width=8)


def ensure_character_references(characters_data: dict[str, Any], repo_root: Path) -> dict[str, Path]:
    refs: dict[str, Path] = {}
    for char_id, info in characters_data.items():
        ref_path = repo_root / info["reference_image"]
        ref_path.parent.mkdir(parents=True, exist_ok=True)
        if not ref_path.exists():
            img = Image.new("RGBA", (600, 600), (255, 249, 238, 255))
            draw = ImageDraw.Draw(img)
            if char_id == "char_a":
                _draw_char_a(draw, 300, 290, scale=1.0)
            else:
                _draw_char_b(draw, 300, 300, scale=1.0)
            img.save(ref_path, format="PNG")
        refs[char_id] = ref_path
    return refs
  
