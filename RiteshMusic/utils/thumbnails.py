# ⟶̽ जय श्री ༢།म > 𝟑🙏🚩
import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from youtubesearchpython.__future__ import VideosSearch
from config import YOUTUBE_IMG_URL

# Constants / paths
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Canvas
CANVAS_W, CANVAS_H = 1280, 720
LEFT_W = CANVAS_W // 2       # 640px
RIGHT_W = CANVAS_W - LEFT_W  # 640px

RIGHT_X = LEFT_W
RIGHT_Y = 0

LEFT_X = 0
LEFT_Y = 0

# Shadow & effect parameters
SHADOW_BLUR = 20  # S1 subtle outer blur
EDGE_TINT_ALPHA = 28  # 0-255 (very low -> subtle)

# Safe font loader
def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

title_font = load_font("RiteshMusic/assets/thumb/font2.ttf", 40)
meta_font = load_font("RiteshMusic/assets/thumb/font.ttf", 20)
duration_font = load_font("RiteshMusic/assets/thumb/font2.ttf", 28)

def clean_text(t):
    return re.sub(r"\s+", " ", (t or "")).strip()

def _linear_gradient(w, h, left_color, right_color):
    """
    Horizontal gradient image from left_color -> right_color (RGBA tuples).
    """
    base = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for x in range(w):
        # interpolation factor
        f = x / max(w - 1, 1)
        r = int(left_color[0] + (right_color[0] - left_color[0]) * f)
        g = int(left_color[1] + (right_color[1] - left_color[1]) * f)
        b = int(left_color[2] + (right_color[2] - left_color[2]) * f)
        a = int(left_color[3] + (right_color[3] - left_color[3]) * f)
        Image.Draw = ImageDraw.Draw  # harmless reference to avoid linter issues
        col_strip = Image.new("RGBA", (1, h), (r, g, b, a))
        base.paste(col_strip, (x, 0))
    return base

async def get_thumb(videoid: str) -> str:
    out_path = os.path.join(CACHE_DIR, f"{videoid}_v6.png")
    if os.path.exists(out_path):
        return out_path

    # fetch youtube info
    try:
        results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        data = await results.next()
        info = data.get("result", [{}])[0]

        title = clean_text(info.get("title", "Unknown Title"))
        thumb = info.get("thumbnails", [{}])[0].get("url", YOUTUBE_IMG_URL)
        duration = info.get("duration")
        views = info.get("viewCount", {}).get("short", "Unknown Views")
        channel = info.get("channel", {}).get("name", "")
    except Exception:
        title = "Unknown Title"
        thumb = YOUTUBE_IMG_URL
        duration = None
        views = "Unknown Views"
        channel = ""

    is_live = not duration or str(duration).lower() in ["", "live", "live now"]
    duration_text = "LIVE" if is_live else (duration or "Unknown")

    # download thumbnail
    temp_thumb = os.path.join(CACHE_DIR, f"temp_{videoid}.png")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumb) as resp:
                if resp.status == 200:
                    async with aiofiles.open(temp_thumb, "wb") as f:
                        await f.write(await resp.read())
                else:
                    # fallback to config url
                    temp_thumb = None
    except Exception:
        temp_thumb = None

    # Build canvas
    base = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))

    # LEFT PANEL: gradient background (professional combination)
    # Color choice (navy -> teal) with subtle alpha for depth
    left_start = (12, 20, 35, 255)     # deep navy
    left_end   = (14, 163, 161, 255)   # teal-ish
    # Create gradient (left to right across left panel)
    left_panel = Image.new("RGBA", (LEFT_W, CANVAS_H), (0, 0, 0, 0))
    # Generate horizontal gradient efficiently
    for x in range(LEFT_W):
        f = x / max(LEFT_W - 1, 1)
        r = int(left_start[0] + (left_end[0] - left_start[0]) * f)
        g = int(left_start[1] + (left_end[1] - left_start[1]) * f)
        b = int(left_start[2] + (left_end[2] - left_start[2]) * f)
        a = int(255)
        col_strip = Image.new("RGBA", (1, CANVAS_H), (r, g, b, a))
        left_panel.paste(col_strip, (x, 0))
    # Slight vignette: darker near left edge
    vignette = Image.new("L", (LEFT_W, CANVAS_H), 0)
    vdraw = ImageDraw.Draw(vignette)
    # radial-ish fade from left edge
    for i in range(LEFT_W):
        alpha = int(40 * (1 - i / LEFT_W))  # subtle darkening
        vdraw.line([(i, 0), (i, CANVAS_H)], fill=alpha)
    left_panel.putalpha(255)
    base.paste(left_panel, (LEFT_X, LEFT_Y), left_panel)

    # RIGHT PANEL: thumbnail (resized to exactly RIGHT_W x CANVAS_H)
    if temp_thumb and os.path.exists(temp_thumb):
        try:
            right_img = Image.open(temp_thumb).convert("RGBA")
        except Exception:
            right_img = Image.new("RGBA", (RIGHT_W, CANVAS_H), (20, 20, 20, 255))
    else:
        # fallback blank if download failed
        right_img = Image.new("RGBA", (RIGHT_W, CANVAS_H), (30, 30, 30, 255))

    # preserve aspect ratio: center-crop then resize
    def fit_and_fill(im, target_w, target_h):
        iw, ih = im.size
        target_ratio = target_w / target_h
        img_ratio = iw / ih
        if img_ratio > target_ratio:
            # crop horizontally
            new_w = int(ih * target_ratio)
            left = (iw - new_w) // 2
            im = im.crop((left, 0, left + new_w, ih))
        else:
            # crop vertically
            new_h = int(iw / target_ratio)
            top = (ih - new_h) // 2
            im = im.crop((0, top, iw, top + new_h))
        return im.resize((target_w, target_h), Image.LANCZOS)

    right_img = fit_and_fill(right_img, RIGHT_W, CANVAS_H)
    base.paste(right_img, (RIGHT_X, RIGHT_Y), right_img)

    draw = ImageDraw.Draw(base)

    # Text content (Option C: premium)
    padding = 48
    text_x = LEFT_X + padding
    text_y = LEFT_Y + padding

    # Title (wrap if too long)
    # Simple wrap: break into lines to fit within LEFT_W - 2*padding
    max_w = LEFT_W - padding * 2
    words = title.split()
    lines = []
    cur = ""
    for w in words:
        test = (cur + " " + w).strip()
        tw, _ = draw.textsize(test, font=title_font)
        if tw <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    # limit to 3 lines
    lines = lines[:3]

    for i, line in enumerate(lines):
        draw.text((text_x, text_y), line, font=title_font, fill=(255, 255, 255, 255))
        text_y += title_font.getsize(line)[1] + 6

    text_y += 8
    # Channel (if present)
    if channel:
        draw.text((text_x, text_y), channel, font=meta_font, fill=(220, 235, 235, 220))
        text_y += 30

    # Views
    draw.text((text_x, text_y), f"Views: {views}", font=meta_font, fill=(200, 220, 220, 200))
    text_y += 34

    # Duration badge (premium aesthetic)
    dur_text = duration_text
    dur_w, dur_h = draw.textsize(dur_text, font=duration_font)
    badge_pad_x = 18
    badge_pad_y = 8
    bx1 = text_x
    by1 = text_y
    bx2 = bx1 + dur_w + badge_pad_x
    by2 = by1 + dur_h + badge_pad_y

    # Semi-transparent light badge for contrast
    badge = Image.new("RGBA", (bx2 - bx1, by2 - by1), (255, 255, 255, 30))
    bd_draw = ImageDraw.Draw(badge)
    bd_draw.rounded_rectangle((0, 0, bx2 - bx1, by2 - by1), radius=12, fill=(255, 255, 255, 30))
    base.paste(badge, (bx1, by1), badge)
    draw.text((bx1 + 10, by1 + 6), dur_text, font=duration_font, fill=(255, 255, 255, 230))

    # small gap
    text_y = by2 + 18

    # small horizontal accent line
    line_w = int(max_w * 0.6)
    draw.line((text_x, text_y, text_x + line_w, text_y), fill=(255, 255, 255, 18), width=2)
    text_y += 18

    # Additional info (kept minimal & professional)
    info_lines = [
        "High Quality Audio",
        "Auto-Played, Easy Controls",
    ]
    for info in info_lines:
        draw.text((text_x, text_y), info, font=meta_font, fill=(200, 220, 220, 190))
        text_y += 28

    # EDGE TINTS (subtle colored shadows on each side)
    # colors: top (purple), right (pink), bottom (teal), left (amber) with very low alpha
    edge_layer = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    ed = ImageDraw.Draw(edge_layer)

    # Top tint
    top_rect = (0, 0, CANVAS_W, 60)
    ed.rectangle(top_rect, fill=(124, 58, 237, EDGE_TINT_ALPHA))  # purple tint

    # Bottom tint
    bottom_rect = (0, CANVAS_H - 60, CANVAS_W, CANVAS_H)
    ed.rectangle(bottom_rect, fill=(6, 182, 212, EDGE_TINT_ALPHA))  # teal tint

    # Left tint
    left_rect = (0, 0, 40, CANVAS_H)
    ed.rectangle(left_rect, fill=(245, 158, 11, EDGE_TINT_ALPHA))  # amber tint

    # Right tint (subtle pink near right edge)
    right_rect = (CANVAS_W - 40, 0, CANVAS_W, CANVAS_H)
    ed.rectangle(right_rect, fill=(236, 72, 153, EDGE_TINT_ALPHA))  # pink tint

    # Blur the edge layer to create soft colored shadows
    edge_layer = edge_layer.filter(ImageFilter.GaussianBlur(18))
    base = Image.alpha_composite(base, edge_layer)

    # OUTER SOFT SHADOW (S1 style): make a blurred copy underneath
    shadow = base.copy().convert("RGBA").filter(ImageFilter.GaussianBlur(SHADOW_BLUR))
    final = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    final.alpha_composite(shadow, (0, 0))
    final.alpha_composite(base, (0, 0))

    # Save and cleanup
    try:
        final.save(out_path)
    except Exception:
        # fallback to saving without alpha if weird environment
        final.convert("RGB").save(out_path)

    try:
        if temp_thumb and os.path.exists(temp_thumb):
            os.remove(temp_thumb)
    except Exception:
        pass

    return out_path
