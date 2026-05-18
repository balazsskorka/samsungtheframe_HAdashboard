"""Overlay compositor for Samsung Frame Art integration."""
from __future__ import annotations

import io
import os
import re
import logging
from datetime import date, datetime

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

# Regex to strip emoji and other non-Latin symbols that DejaVu can't render
# Weather condition → simple text symbol (no emoji, DejaVu safe)
CONDITION_LABEL = {
    "clear-night":          "Clear",
    "cloudy":               "Cloudy",
    "exceptional":          "Special",
    "fog":                  "Fog",
    "hail":                 "Hail",
    "lightning":            "Storm",
    "lightning-rainy":      "T-Storm",
    "partlycloudy":         "Partly Cloudy",
    "pouring":              "Pouring",
    "rainy":                "Rain",
    "snowy":                "Snow",
    "snowy-rainy":          "Sleet",
    "sunny":                "Sunny",
    "windy":                "Windy",
    "windy-variant":        "Windy",
    "exceptional":          "Special",
}

_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F700-\U0001F77F"  # alchemical
    "\U0001F780-\U0001F7FF"  # geometric extended
    "\U0001F800-\U0001F8FF"  # supplemental arrows
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U0001FA00-\U0001FA6F"  # chess symbols
    "\U0001FA70-\U0001FAFF"  # symbols extended-A
    "\U00002702-\U000027B0"  # dingbats
    "\U000024C2-\U0001F251"  # enclosed chars
    "\U0000200D"             # ZWJ
    "\U0000FE0F"             # variation selector
    "]+",
    flags=re.UNICODE,
)


def _strip_emoji(text: str) -> str:
    return _EMOJI_RE.sub("", text).strip()


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
    _LOGGER.warning("Font not found — text will render tiny")
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


def _format_event_time(ev: dict, lang: str) -> str:
    """Return a time string for the event, or empty string for all-day events."""
    if ev.get("all_day"):
        return ""
    start = ev.get("start")
    end = ev.get("end")
    if not isinstance(start, datetime):
        return ""
    time_str = start.strftime("%H:%M")
    if end and isinstance(end, datetime):
        time_str += f" – {end.strftime('%H:%M')}"
    return time_str


def compose_overlay(
    image_path: str,
    lang: str,
    events: list[dict],
    opacity: int = 50,
    font_size: int = 100,
    show_date: bool = True,
    show_calendar: bool = True,
    show_weather: bool = True,
    forecast: list[dict] | None = None,
) -> bytes:
    """Compose image with overlay. opacity: 0-100, font_size: 50-200 (percent)."""
    img = Image.open(image_path).convert("RGBA")
    img = img.resize((3840, 2160), Image.LANCZOS)
    w, h = img.size

    bold_path    = _find_font(FONT_PATHS_BOLD)
    regular_path = _find_font(FONT_PATHS_REGULAR)

    alpha = int(opacity / 100 * 255)
    scale = font_size / 100.0

    # ── Font sizes scaled by user preference ─────────────────────────────────
    fs_day_name    = int(160 * scale)
    fs_date_big    = int(320 * scale)
    fs_month_year  = int(130 * scale)
    fs_event_label = int(90  * scale)
    fs_event_title = int(120 * scale)

    font_day_name    = _font(regular_path, fs_day_name)
    font_date_big    = _font(bold_path,    fs_date_big)
    font_month_year  = _font(regular_path, fs_month_year)
    font_event_label = _font(regular_path, fs_event_label)
    font_event_title = _font(bold_path,    fs_event_title)
    fs_weather_cond  = int(70  * scale)
    fs_weather_temp  = int(80  * scale)
    font_weather_cond = _font(regular_path, fs_weather_cond)
    font_weather_temp = _font(bold_path,    fs_weather_temp)

    # ── Panel geometry ────────────────────────────────────────────────────────
    margin   = 80
    gap      = 60
    radius   = 50

    left_w       = int(w * 0.38)
    left_panel_h = int(h * 0.40) if not (show_weather and forecast) else int(h * 0.62)
    left_x       = margin
    left_y       = margin

    right_x = left_x + left_w + gap
    right_w = w - right_x - margin
    right_y = margin
    right_h = h - margin * 2

    if show_date:
        left_panel = _rounded_frosted_panel(img, left_x, left_y, left_w, left_panel_h, radius, alpha)
        img.paste(left_panel, (left_x, left_y), left_panel)

    if show_calendar:
        right_panel = _rounded_frosted_panel(img, right_x, right_y, right_w, right_h, radius, alpha)
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

    if show_date:
        tw, _ = _text_size(draw, day_name_str, font_day_name)
        draw.text((left_cx - tw // 2, ty), day_name_str, font=font_day_name, fill=WHITE_DIM)

        ty += fs_day_name + 20
        tw, _ = _text_size(draw, day_num_str, font_date_big)
        draw.text((left_cx - tw // 2, ty), day_num_str, font=font_date_big, fill=WHITE)

        ty += fs_date_big + 20
        tw, _ = _text_size(draw, month_yr_str, font_month_year)
        draw.text((left_cx - tw // 2, ty), month_yr_str, font=font_month_year, fill=WHITE_DIM)

    # ── Weather forecast (below date in left panel) ─────────────────────────
    if show_date and show_weather and forecast:
        # Separator line
        sep_y = left_y + int(left_panel_h * 0.48)
        draw.line([(left_x + 40, sep_y), (left_x + left_w - 40, sep_y)], fill=WHITE_FAINT, width=2)

        fc_y = sep_y + int(h * 0.02)
        fc_col_w = left_w // max(len(forecast), 1)

        for i, fc in enumerate(forecast):
            if i >= 5:
                break
            col_x = left_x + i * fc_col_w + fc_col_w // 2

            # Date label
            try:
                from datetime import datetime as _dt
                dt_str = fc.get("datetime", "")
                dt_obj = _dt.fromisoformat(dt_str.replace("Z", "+00:00")).replace(tzinfo=None)
                fc_label = DAYS.get(lang, DAYS["en"])[dt_obj.weekday()][:3].upper()
            except Exception:
                fc_label = f"D{i+1}"

            tw, _ = _text_size(draw, fc_label, font_weather_cond)
            draw.text((col_x - tw // 2, fc_y), fc_label, font=font_weather_cond, fill=WHITE_DIM)

            # Condition
            cond = CONDITION_LABEL.get(fc.get("condition", ""), fc.get("condition", "").replace("-", " ").title())
            cond = cond[:10]
            tw, _ = _text_size(draw, cond, font_weather_cond)
            draw.text((col_x - tw // 2, fc_y + fs_weather_cond + 8), cond, font=font_weather_cond, fill=WHITE_DIM)

            # Temperature
            temp_hi = fc.get("temperature")
            temp_lo = fc.get("templow")
            if temp_hi is not None:
                temp_str = f"{int(round(temp_hi))}°"
                if temp_lo is not None:
                    temp_str += f" / {int(round(temp_lo))}°"
                tw, _ = _text_size(draw, temp_str, font_weather_temp)
                draw.text((col_x - tw // 2, fc_y + fs_weather_cond * 2 + 16), temp_str, font=font_weather_temp, fill=WHITE)

            # Precipitation probability
            precip = fc.get("precipitation_probability")
            if precip is not None:
                precip_str = f"{int(precip)}%"
                tw, _ = _text_size(draw, precip_str, font_weather_cond)
                draw.text((col_x - tw // 2, fc_y + fs_weather_cond * 2 + 16 + fs_weather_temp + 8), precip_str, font=font_weather_cond, fill=WHITE_DIM)

    # ── RIGHT: Events ─────────────────────────────────────────────────────────
    if show_calendar:
        ev_pad    = 80
        ev_x      = right_x + ev_pad
        ev_y      = right_y + ev_pad
        ev_max_x  = right_x + right_w - ev_pad
        ev_bottom = right_y + right_h - ev_pad
        block_h   = fs_event_label + 14 + fs_event_title
        row_gap   = int(50 * scale)

        if not events:
            no_ev = NO_EVENTS_LABEL.get(lang, "No upcoming events")
            draw.text((ev_x, right_y + right_h // 2), no_ev, font=font_event_label, fill=WHITE_DIM)
        else:
            max_chars = int((ev_max_x - ev_x - 60) / (fs_event_title * 0.52))
            for i, ev in enumerate(events):
                if ev_y + block_h > ev_bottom:
                    break

                start   = ev.get("start")
                ev_date = start.date() if hasattr(start, "date") else start
                label   = _format_event_label(ev_date, lang).upper()
                summary = _strip_emoji(ev.get("summary", ""))
                if len(summary) > max_chars:
                    summary = summary[:max_chars - 1] + "…"

                # Dot accent
                dot_x = ev_x - 40
                dot_y = ev_y + fs_event_label + 14 + fs_event_title // 2
                draw.ellipse([(dot_x - 10, dot_y - 10), (dot_x + 10, dot_y + 10)], fill=WHITE_DIM)

                # Label row: date label left, time right
                draw.text((ev_x, ev_y), label, font=font_event_label, fill=WHITE_DIM)
                time_str = _format_event_time(ev, lang)
                if time_str:
                    tw_t, _ = _text_size(draw, time_str, font_event_label)
                    draw.text((ev_max_x - tw_t, ev_y), time_str, font=font_event_label, fill=WHITE_DIM)

                draw.text((ev_x, ev_y + fs_event_label + 14), summary, font=font_event_title, fill=WHITE)

                ev_y += block_h + row_gap
                if i < len(events) - 1 and ev_y + block_h <= ev_bottom:
                    draw.line([(ev_x, ev_y), (ev_max_x, ev_y)], fill=WHITE_FAINT, width=2)
                    ev_y += row_gap


    out = io.BytesIO()
    img.convert("RGB").save(out, format="JPEG", quality=88, optimize=True)
    return out.getvalue()
