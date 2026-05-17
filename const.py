"""Constants for Samsung Frame Art integration."""

DOMAIN = "samsung_frame"

# Config keys
CONF_TV_IP = "tv_ip"
CONF_MEDIA_FOLDER = "media_folder"
CONF_TOKEN_FILE = "token_file"
CONF_CALENDAR_ENTITY = "calendar_entity"
CONF_LANGUAGE = "language"
CONF_UPCOMING_DAYS = "upcoming_days"
CONF_MATTE_COLOR = "matte_color"
CONF_OVERLAY_OPACITY = "overlay_opacity"
CONF_DEBUG_SAVE = "debug_save"

# Defaults
DEFAULT_MEDIA_FOLDER = "/media/frame"
DEFAULT_TOKEN_FILE = "/config/samsung_frame_token.txt"
DEFAULT_UPCOMING_DAYS = 5
DEFAULT_MATTE_COLOR = "modern_apricot"
DEFAULT_OVERLAY_OPACITY = 50  # percent 0-100
DEFAULT_DEBUG_SAVE = False
DEFAULT_LANGUAGE = "en"

# Supported languages
LANGUAGES = {
    "en": "English",
    "de": "Deutsch",
    "hu": "Magyar",
}

# Matte options (samsungtvws style)
MATTE_OPTIONS = [
    "none",
    "modern_apricot",
    "modern_warm",
    "modern_neutral",
    "modernthin_apricot",
    "shadowbox_apricot",
]

# Service names
SERVICE_UPDATE = "update"

# Overlay layout
OVERLAY_HEIGHT_RATIO = 0.30   # bottom 30% of image
OVERLAY_BLUR_RADIUS = 40
OVERLAY_BG_ALPHA = 180        # 0-255

# Font sizes (relative to image height)
FONT_SIZE_DATE = 0.055
FONT_SIZE_DAY = 0.038
FONT_SIZE_EVENT = 0.028
FONT_SIZE_EVENT_DATE = 0.022

# Day/month translations
DAYS = {
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    "de": ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"],
    "hu": ["Hétfő", "Kedd", "Szerda", "Csütörtök", "Péntek", "Szombat", "Vasárnap"],
}

MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"],
    "de": ["Januar", "Februar", "März", "April", "Mai", "Juni",
           "Juli", "August", "September", "Oktober", "November", "Dezember"],
    "hu": ["Január", "Február", "Március", "Április", "Május", "Június",
           "Július", "Augusztus", "Szeptember", "Október", "November", "December"],
}

TODAY_LABEL = {
    "en": "Today",
    "de": "Heute",
    "hu": "Ma",
}

TOMORROW_LABEL = {
    "en": "Tomorrow",
    "de": "Morgen",
    "hu": "Holnap",
}

NO_EVENTS_LABEL = {
    "en": "No upcoming events",
    "de": "Keine bevorstehenden Termine",
    "hu": "Nincsenek közelgő események",
}
