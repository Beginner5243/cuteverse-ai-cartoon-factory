from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


def load_characters(config_path: Path) -> dict[str, Any]:
    return json.loads(config_path.read_text(encoding="utf-8"))


def _make_border_transparent(img: Image.Image, tolerance: int = 24) -> Image.Image:
    """
    Removes only background pixels connected to the image border that match
    the corner backdrop color, preserving interior white eyes and highlights.
    """
    rgba = img.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()
    bg_r, bg_g, bg_b, _ = px[0, 0]

    def matches_bg(x: int, y: int) -> bool:
        r, g, b, _ = px[x, y]
        return (
            abs(r - bg_r) <= tolerance
            and abs(g - bg_g) <= tolerance
            and abs(b - bg_b) <= tolerance
        )

    visited = [[False] * h for _ in range(w)]
    q: deque[tuple[int, int]] = deque()

    for x in range(w):
        for y in (0, h - 1):
            if matches_bg(x, y) and not visited[x][y]:
                visited[x][y] = True
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if matches_bg(x, y) and not visited[x][y]:
                visited[x][y] = True
                q.append((x, y))

    while q:
        cx, cy = q.popleft()
        px[cx, cy] = (bg_r, bg_g, bg_b, 0)
        for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
            if 0 <= nx < w and 0 <= ny < h and not visited[nx][ny] and matches_bg(nx, ny):
                visited[nx][ny] = True
                q.append((nx, ny))

    return rgba


def _draw_sheru_base(draw: ImageDraw.ImageDraw, cx: int = 300, cy: int = 290) -> None:
    # Brown ears
    draw.ellipse([cx - 115, cy - 135, cx - 35, cy - 35], fill="#8D5524", outline="#24160C", width=5)
    draw.ellipse([cx + 35, cy - 135, cx + 115, cy - 35], fill="#8D5524", outline="#24160C", width=5)
    # Cream body
    draw.ellipse([cx - 95, cy + 65, cx + 95, cy + 235], fill="#F7EBD9", outline="#24160C", width=5)
    # Small arms & legs
    draw.rounded_rectangle([cx - 128, cy + 85, cx - 78, cy + 145], radius=22, fill="#8D5524", outline="#24160C", width=4)
    draw.rounded_rectangle([cx + 78, cy + 85, cx + 128, cy + 145], radius=22, fill="#8D5524", outline="#24160C", width=4)
    draw.rounded_rectangle([cx - 72, cy + 205, cx - 22, cy + 255], radius=18, fill="#8D5524", outline="#24160C", width=4)
    draw.rounded_rectangle([cx + 22, cy + 205, cx + 72, cy + 255], radius=18, fill="#8D5524", outline="#24160C", width=4)
    # Cream head
    draw.ellipse([cx - 115, cy - 110, cx + 115, cy + 105], fill="#F7EBD9", outline="#24160C", width=5)
    # Brown eye patches & large expressive eyes
    for side in (-1, 1):
        px_x = cx + side * 44
        draw.ellipse([px_x - 32, cy - 36, px_x + 32, cy + 28], fill="#8D5524")
        draw.ellipse([px_x - 20, cy - 22, px_x + 20, cy + 18], fill="#FFFFFF", outline="#141414", width=3)
        draw.ellipse([px_x - 10, cy - 10, px_x + 10, cy + 10], fill="#141414")
        draw.ellipse([px_x - 7, cy - 9, px_x - 1, cy - 3], fill="#FFFFFF")
    # Nose & gentle smile
    draw.ellipse([cx - 14, cy + 24, cx + 14, cy + 42], fill="#24160C")
    draw.arc([cx - 32, cy + 44, cx + 32, cy + 74], start=10, end=170, fill="#24160C", width=4)


def _draw_potato_base(draw: ImageDraw.ImageDraw, cx: int = 300, cy: int = 305) -> None:
    # Green sprout hair
    draw.line([(cx, cy - 105), (cx, cy - 142)], fill="#2E7D32", width=7)
    draw.polygon([(cx, cy - 135), (cx - 46, cy - 165), (cx - 10, cy - 122)], fill="#4CAF50", outline="#1B5E20", width=4)
    draw.polygon([(cx, cy - 135), (cx + 46, cy - 165), (cx + 10, cy - 122)], fill="#66BB6A", outline="#1B5E20", width=4)
    # Round purple top + cream lower potato body
    draw.ellipse([cx - 112, cy - 108, cx + 112, cy + 108], fill="#7B4B94", outline="#23122E", width=5)
    draw.chord([cx - 112, cy - 108, cx + 112, cy + 108], start=12, end=168, fill="#F7F2E7", outline="#23122E", width=4)
    # Orange headband
    draw.rectangle([cx - 106, cy - 58, cx + 106, cy - 30], fill="#FF7B00", outline="#7C3A00", width=3)
    # Large expressive eyes
    for side in (-1, 1):
        ex = cx + side * 40
        draw.ellipse([ex - 23, cy - 22, ex + 23, cy + 24], fill="#FFFFFF", outline="#141414", width=3)
        draw.ellipse([ex - 11, cy - 8, ex + 11, cy + 12], fill="#141414")
        draw.ellipse([ex - 6, cy - 7, ex - 1, cy - 2], fill="#FFFFFF")
    # Grin
    draw.arc([cx - 34, cy + 28, cx + 34, cy + 62], start=12, end=168, fill="#23122E", width=4)
    # Small arms & legs
    draw.line([(cx - 110, cy + 20), (cx - 148, cy + 4)], fill="#23122E", width=8)
    draw.line([(cx + 110, cy + 20), (cx + 148, cy + 4)], fill="#23122E", width=8)
    draw.line([(cx - 42, cy + 106), (cx - 48, cy + 152)], fill="#23122E", width=9)
    draw.line([(cx + 42, cy + 106), (cx + 48, cy + 152)], fill="#23122E", width=9)


def ensure_character_references(characters_data: dict[str, Any], repo_root: Path) -> dict[str, Path]:
    refs: dict[str, Path] = {}
    for char_id, info in characters_data.items():
        ref_path = repo_root / info["reference_image"]
        ref_path.parent.mkdir(parents=True, exist_ok=True)
        canvas = Image.new("RGBA", (600, 600), (245, 238, 224, 255))
        draw = ImageDraw.Draw(canvas)
        if char_id == "char_a":
            _draw_sheru_base(draw)
        else:
            _draw_potato_base(draw)
        transparent = _make_border_transparent(canvas, tolerance=22)
        transparent.save(ref_path, format="PNG")
        refs[char_id] = ref_path
    return refs


def extract_articulated_parts(ref_path: Path) -> dict[str, Image.Image]:
    """
    Splits a 600x600 reference character sprite into head, torso, left_arm,
    right_arm, left_leg, and right_leg crops with preserved alpha.
    """
    img = Image.open(ref_path).convert("RGBA").resize((600, 600), Image.Resampling.LANCZOS)
    return {
        "head": img.crop((145, 110, 455, 405)),
        "body": img.crop((185, 355, 415, 510)),
        "left_arm": img.crop((130, 365, 225, 465)),
        "right_arm": img.crop((375, 365, 470, 465)),
        "left_leg": img.crop((200, 485, 295, 575)),
        "right_leg": img.crop((305, 485, 400, 575)),
    }
    
