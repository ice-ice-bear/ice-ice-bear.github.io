#!/usr/bin/env python3
"""Generate English cover images for all EN posts that currently share Korean covers."""

import re
import sys
from pathlib import Path

# Add log-blog to path for image_handler
sys.path.insert(0, str(Path.home() / "Documents/github/log-blog/src"))

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
EN_POSTS = REPO / "content" / "en" / "posts"
STATIC_IMAGES = REPO / "static" / "images" / "posts"

COVER_WIDTH = 1200
COVER_HEIGHT = 630

TAG_COLOR_SCHEMES = {
    "python": ((53, 114, 165), (30, 75, 120), (255, 212, 59)),
    "javascript": ((247, 223, 30), (200, 180, 20), (50, 50, 50)),
    "typescript": ((49, 120, 198), (30, 80, 150), (180, 210, 255)),
    "react": ((97, 218, 251), (50, 150, 200), (40, 40, 50)),
    "fastapi": ((0, 150, 136), (0, 100, 90), (200, 255, 240)),
    "docker": ((36, 150, 237), (20, 100, 180), (180, 220, 255)),
    "kubernetes": ((50, 108, 229), (30, 70, 170), (180, 200, 255)),
    "claude-code": ((204, 120, 50), (150, 80, 30), (255, 220, 180)),
    "anthropic": ((204, 120, 50), (150, 80, 30), (255, 220, 180)),
    "vibe-coding": ((139, 92, 246), (100, 60, 200), (220, 200, 255)),
    "mcp": ((124, 58, 237), (91, 33, 182), (196, 181, 253)),
    "ai-coding": ((139, 92, 246), (100, 60, 200), (220, 200, 255)),
    "openai": ((0, 0, 0), (30, 30, 30), (0, 200, 83)),
    "gemini": ((66, 133, 244), (25, 95, 200), (180, 210, 255)),
    "skills": ((139, 92, 246), (100, 60, 200), (220, 200, 255)),
    "llm": ((100, 50, 150), (60, 30, 100), (210, 180, 255)),
    "multi-agent": ((100, 50, 150), (60, 30, 100), (210, 180, 255)),
    "developer-tools": ((50, 50, 50), (30, 30, 30), (180, 255, 180)),
    "security": ((220, 50, 50), (150, 30, 30), (255, 180, 180)),
    "devops": ((36, 150, 237), (20, 100, 180), (180, 220, 255)),
    "hugo": ((255, 79, 100), (200, 50, 70), (255, 180, 190)),
    "trading": ((34, 139, 34), (20, 100, 20), (144, 238, 144)),
    "machine-learning": ((100, 50, 150), (60, 30, 100), (210, 180, 255)),
    "deep-learning": ((100, 50, 150), (60, 30, 100), (210, 180, 255)),
    "notebooklm": ((66, 133, 244), (25, 95, 200), (180, 210, 255)),
    "backend": ((0, 150, 136), (0, 100, 90), (200, 255, 240)),
    "fintech": ((34, 139, 34), (20, 100, 20), (144, 238, 144)),
}

DEFAULT_PALETTE = ((99, 102, 106), (55, 58, 64), (180, 185, 190))


def pick_palette(tags):
    for tag in tags:
        key = tag.lower()
        if key in TAG_COLOR_SCHEMES:
            return TAG_COLOR_SCHEMES[key]
    return DEFAULT_PALETTE


def darken(color, factor=0.28):
    return (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))


def load_font(size):
    candidates = [
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        sep = " " if current else ""
        test = f"{current}{sep}{word}"
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    if len(lines) > 3:
        lines = lines[:3]
        last = lines[-1]
        while len(last) > 1:
            candidate = last + "..."
            bbox = draw.textbbox((0, 0), candidate, font=font)
            if bbox[2] - bbox[0] <= max_width:
                lines[-1] = candidate
                break
            last = last[:-1]
    return lines or [text[:50]]


def generate_cover(title, tags, slug):
    grad_start, grad_end, accent = pick_palette(tags)
    dark_start = darken(grad_start, 0.28)
    dark_end = darken(grad_end, 0.28)

    # Gradient
    img = Image.new("RGB", (COVER_WIDTH, COVER_HEIGHT))
    pixels = img.load()
    for y in range(COVER_HEIGHT):
        for x in range(COVER_WIDTH):
            t = x / COVER_WIDTH * 0.6 + y / COVER_HEIGHT * 0.4
            r = int(dark_start[0] + (dark_end[0] - dark_start[0]) * t)
            g = int(dark_start[1] + (dark_end[1] - dark_start[1]) * t)
            b = int(dark_start[2] + (dark_end[2] - dark_start[2]) * t)
            pixels[x, y] = (r, g, b)

    # Grid
    draw_obj = ImageDraw.Draw(img)
    grid_color = darken(grad_start, 0.38)
    for gx in range(0, COVER_WIDTH, 60):
        draw_obj.line([(gx, 0), (gx, COVER_HEIGHT)], fill=grid_color, width=1)
    for gy in range(0, COVER_HEIGHT, 60):
        draw_obj.line([(0, gy), (COVER_WIDTH, gy)], fill=grid_color, width=1)

    # Text
    title_font = load_font(52)
    subtitle_font = load_font(26)
    meta_font = load_font(18)

    left_pad = 40
    max_text_width = COVER_WIDTH - left_pad - 80

    if " — " in title:
        display_title, subtitle = title.split(" — ", 1)
    elif " - " in title:
        display_title, subtitle = title.split(" - ", 1)
    else:
        display_title = title
        subtitle = " + ".join(t.replace("-", " ").title() for t in tags[:3])

    lines = wrap_text(draw_obj, display_title, title_font, max_text_width)
    date_str = slug[:10] if len(slug) >= 10 else ""
    meta_line = f"{date_str}  |  Tech Log" if date_str else ""

    y = int(COVER_HEIGHT * 0.32)
    draw_obj.line([(left_pad, y), (left_pad + 150, y)], fill=accent, width=4)
    y += 14

    for line in lines:
        draw_obj.text((left_pad + 2, y + 2), line, fill=(0, 0, 0), font=title_font)
        draw_obj.text((left_pad, y), line, fill=(255, 255, 255), font=title_font)
        y += 64

    y += 4
    if subtitle:
        draw_obj.text((left_pad, y), subtitle, fill=(200, 200, 210), font=subtitle_font)
        y += 38
    if meta_line:
        draw_obj.text((left_pad, y), meta_line, fill=(160, 160, 170), font=meta_font)

    return img


def parse_frontmatter(text):
    m = re.match(r'^---\n(.*?)\n---', text, re.DOTALL)
    if not m:
        return {}, text
    fm_text = m.group(1)
    title = ""
    tags = []
    for line in fm_text.split("\n"):
        if line.startswith("title:"):
            title = line.split(":", 1)[1].strip().strip('"').strip("'")
        if line.startswith("tags:"):
            tags_str = line.split(":", 1)[1].strip()
            tags = [t.strip().strip('"').strip("'") for t in tags_str.strip("[]").split(",")]
    return {"title": title, "tags": tags}, text


def main():
    posts = sorted(EN_POSTS.glob("2026-*.md"))
    print(f"Found {len(posts)} EN posts to process")

    generated = 0
    skipped = 0

    for post_path in posts:
        slug = post_path.stem
        text = post_path.read_text(encoding="utf-8")
        fm, _ = parse_frontmatter(text)

        title = fm.get("title", "")
        tags = fm.get("tags", [])
        if not title:
            print(f"  SKIP {slug}: no title")
            skipped += 1
            continue

        # Check if image frontmatter exists
        if 'image:' not in text:
            print(f"  SKIP {slug}: no image field")
            skipped += 1
            continue

        dest_dir = STATIC_IMAGES / slug
        dest = dest_dir / "cover-en.jpg"

        if dest.exists():
            # Still update frontmatter even if image exists
            pass
        else:
            dest_dir.mkdir(parents=True, exist_ok=True)
            img = generate_cover(title, tags, slug)
            img.save(str(dest), "JPEG", quality=90)

        # Update frontmatter: cover.jpg -> cover-en.jpg
        old_image = f'/images/posts/{slug}/cover.jpg'
        new_image = f'/images/posts/{slug}/cover-en.jpg'
        if old_image in text:
            text = text.replace(old_image, new_image)
            post_path.write_text(text, encoding="utf-8")

        generated += 1
        if generated % 10 == 0:
            print(f"  ... processed {generated}/{len(posts)}")

    print(f"\nDone: {generated} generated, {skipped} skipped")


if __name__ == "__main__":
    main()
