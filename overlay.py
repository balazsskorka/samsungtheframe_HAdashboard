"""Overlay compositor for Samsung Frame Art integration."""
from __future__ import annotations

import io
import os
import logging
from datetime import date, timedelta, datetime

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .const import (
    DAYS,
    MONTHS,
    TODAY_LABEL,
    TOMORROW_LABEL,
    NO_EVENTS_LABEL,
)

_LOGGER = logging.getLogger(__name__)

_FONTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

FONT_PATHS_BOLD = [
    os.path.join(_FONTS_DIR, "DejaVuSans-Bold.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]

FONT_PATHS_REGULAR = [
    os.path.join(_FONTS_DIR, "DejaVuSans.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]


def _find_font(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return None


def _font(path, size):
    if path:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    _LOGGER.warning("Font not found, falling back to default — text will be tiny!")
    return ImageFont.load_default()


def _text_size(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0], bb[3] - bb[1]


def _rounded_frosted_panel(img, x, y, pw, ph, radius, alpha):
    region = img.crop((x, y, x + pw, y + ph))
    blurred = region.filter(ImageFilter.GaussianBlur(radius=50))
    tint = Image.new("RGBA", (pw, ph), (0, 0, 0, alpha))
    frosted = Image.alpha_composite(blurred.convert("RGBA"), tint)
    mask = Image.new("L", (pw, ph), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, pw, ph], radius=radius, fill=255)
    result = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    result.paste(frosted, mask=mask)
    return result


def _format_event_label(d: date, lang: str) -> str:
    today = date.today()
    delta = (d - today).days
    if delta == 0:
        return TODAY_LABEL.get(lang, "Today")
    if delta == 1:
        return TOMORROW_LABEL.get(lang, "Tomorrow")
    day_names = DAYS.get(lang, DAYS["en"])
    month_names = MONTHS.get(lang, MONTHS["en"])
    if lang == "hu":
        return f"{month_names[d.month-1]} {d.day}. {day_names[d.weekday()]}"
    return f"{day_names[d.weekday()]}, {month_names[d.month-1]} {d.day}"


def compose_overlay(
    image_path: str,
    lang: str,
    events: list[dict],
    opacity: int = 50,
) -> bytes:
    img = Image.open(image_path).convert("RGBA")
    img = img.resize((3840, 2160), Image.LANCZOS)
    w, h = img.size

    bold_path    = _find_font(FONT_PATHS_BOLD)
    regular_path = _find_font(FONT_PATHS_REGULAR)

    _LOGGER.info("Using bold font: %s", bold_path)
    _LOGGER.info("Using regular font: %s", regular_path)

    alpha = int(opacity / 100 * 255)

    # ── Font sizes — large enough to read from 3+ metres ─────────────────────
    fs_day_name    = 160   # "SATURDAY"
    fs_date_big    = 320   # "17"
    fs_month_year  = 130   # "May 2026"
    fs_event_label = 90    # "TODAY" / "TOMORROW"
    fs_event_title = 120   # event summary

    font_day_name    = _font(regular_path, fs_day_name)
    font_date_big    = _font(bold_path,    fs_date_big)
    font_month_year  = _font(regular_path, fs_month_year)
    font_event_label = _font(regular_path, fs_event_label)
    font_event_title = _font(bold_path,    fs_event_title)

    # ── Panel geometry ────────────────────────────────────────────────────────
    margin   = 80
    gap      = 60
    radius   = 50

    left_w       = int(w * 0.38)
    left_panel_h = int(h * 0.40)   # ~40% height for date block
    left_x       = margin
    left_y       = margin

    right_x = left_x + left_w + gap
    right_w = w - right_x - margin
    right_y = margin
    right_h = h - margin * 2

    # ── Draw panels ───────────────────────────────────────────────────────────
    left_panel  = _rounded_frosted_panel(img, left_x, left_y, left_w, left_panel_h, radius, alpha)
    right_panel = _rounded_frosted_panel(img, right_x, right_y, right_w, right_h, radius, alpha)

    img.paste(left_panel,  (left_x, left_y),   left_panel)
    img.paste(right_panel, (right_x, right_y), right_panel)

    draw = ImageDraw.Draw(img)

    WHITE       = (255, 255, 255, 255)
    WHITE_DIM   = (255, 255, 255, 180)
    WHITE_FAINT = (255, 255, 255, 90)

    # ── LEFT: Date ────────────────────────────────────────────────────────────
    today = date.today()
    day_names   = DAYS.get(lang, DAYS["en"])
    month_names = MONTHS.get(lang, MONTHS["en"])

    day_name_str = day_names[today.weekday()].upper()
    day_num_str  = str(today.day)
    month_yr_str = f"{month_names[today.month - 1]} {today.year}"

    left_cx = left_x + left_w // 2
    total_h = fs_day_name + 20 + fs_date_big + 20 + fs_month_year
    ty = left_y + (left_panel_h - total_h) // 2

    tw, _ = _text_size(draw, day_name_str, font_day_name)
    draw.text((left_cx - tw // 2, ty), day_name_str, font=font_day_name, fill=WHITE_DIM)

    ty += fs_day_name + 20
    tw, _ = _text_size(draw, day_num_str, font_date_big)
    draw.text((left_cx - tw // 2, ty), day_num_str, font=font_date_big, fill=WHITE)

    ty += fs_date_big + 20
    tw, _ = _text_size(draw, month_yr_str, font_month_year)
    draw.text((left_cx - tw // 2, ty), month_yr_str, font=font_month_year, fill=WHITE_DIM)

    # ── RIGHT: Events ─────────────────────────────────────────────────────────
    ev_pad    = 80
    ev_x      = right_x + ev_pad
    ev_y      = right_y + ev_pad
    ev_max_x  = right_x + right_w - ev_pad
    ev_bottom = right_y + right_h - ev_pad
    block_h   = fs_event_label + 14 + fs_event_title
    row_gap   = 50

    if not events:
        no_ev = NO_EVENTS_LABEL.get(lang, "No upcoming events")
        draw.text((ev_x, right_y + right_h // 2), no_ev, font=font_event_label, fill=WHITE_DIM)
    else:
        max_chars = int((ev_max_x - ev_x - 60) / (fs_event_title * 0.52))
        for i, ev in enumerate(events):
            if ev_y + block_h > ev_bottom:
                break
            start  = ev.get("start")
            ev_date = start.date() if hasattr(start, "date") else start
            label   = _format_event_label(ev_date, lang).upper()
            summary = ev.get("summary", "")
            if len(summary) > max_chars:
                summary = summary[:max_chars - 1] + "…"

            # Dot
            dot_x = ev_x - 40
            dot_y = ev_y + fs_event_label + 14 + fs_event_title // 2
            draw.ellipse([(dot_x - 10, dot_y - 10), (dot_x + 10, dot_y + 10)], fill=WHITE_DIM)

            draw.text((ev_x, ev_y), label, font=font_event_label, fill=WHITE_DIM)
            draw.text((ev_x, ev_y + fs_event_label + 14), summary, font=font_event_title, fill=WHITE)

            ev_y += block_h + row_gap
            if i < len(events) - 1 and ev_y + block_h <= ev_bottom:
                draw.line([(ev_x, ev_y), (ev_max_x, ev_y)], fill=WHITE_FAINT, width=2)
                ev_y += row_gap

    out = io.BytesIO()
    img.convert("RGB").save(out, format="JPEG", quality=88, optimize=True)
    _LOGGER.debug("Overlay JPEG: %d bytes", out.tell())
    return out.getvalue()
