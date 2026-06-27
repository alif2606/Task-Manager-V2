"""
config.py
---------
Single source of truth for every constant in the application.
No magic numbers anywhere else in the codebase.
"""

from __future__ import annotations

# ── Application metadata ──────────────────────────────────────────────────────
APP_NAME    = "TaskList V2"
APP_VERSION = "1.0.0"

# ── Window defaults ───────────────────────────────────────────────────────────
DEFAULT_WIDTH  : int = 320
DEFAULT_HEIGHT : int = 480
MIN_WIDTH      : int = 260
MIN_HEIGHT     : int = 260
WINDOW_ALPHA   : float = 0.95      # 0.0 = invisible, 1.0 = solid

# ── Layout constants ──────────────────────────────────────────────────────────
PADDING        : int = 14          # outer card padding
RADIUS         : int = 16          # card corner radius
BORDER_WIDTH   : int = 1

# ── Colour palette — dark glassmorphism ───────────────────────────────────────
# Backgrounds
BG_OUTER       = "#0f1117"         # transparent-keyed outer window colour
BG_CARD        = "#1a1d2e"         # main card
BG_INPUT       = "#13152a"         # text entry background
BG_ROW_HOVER   = "#1e2240"         # task row on mouse-enter

# Borders / dividers
BORDER_CLR     = "#3b4068"
INPUT_FOCUS    = "#4e5580"
DIVIDER        = "#2a2f4a"

# Text
TITLE_CLR      = "#c0c8f0"
TEXT_CLR       = "#cdd6f4"
DONE_CLR       = "#44476a"         # struck-through task text
MUTED_CLR      = "#585b80"         # placeholder / empty state
HINT_CLR       = "#44476a"         # input placeholder

# Accents
ACCENT         = "#7c85d4"
BTN_BG         = "#2e3460"
BTN_HOVER      = "#3d4480"
BTN_FG         = "#a0aaee"

# Delete button
DEL_CLR        = "#e06c75"
DEL_HOVER      = "#ff8891"

# Checkbox
CHK_ON         = "#7c85d4"
CHK_OFF        = "#3b4068"

# Priority colours
PRIORITY_HIGH   = "#e06c75"        # red
PRIORITY_MEDIUM = "#e5c07b"        # amber
PRIORITY_LOW    = "#98c379"        # green
PRIORITY_NONE   = MUTED_CLR

# ── Typography ────────────────────────────────────────────────────────────────
FONT_TITLE   = ("Segoe UI", 11, "bold")
FONT_BODY    = ("Segoe UI", 10)
FONT_STRIKE  = ("Segoe UI", 10, "overstrike")
FONT_SMALL   = ("Segoe UI", 9)
FONT_BOLD    = ("Segoe UI", 10, "bold")
FONT_BTN     = ("Segoe UI", 10, "bold")
FONT_MONO    = ("Consolas",  9)

# ── Animation ─────────────────────────────────────────────────────────────────
FADE_STEPS : int = 14
FADE_DELAY : int = 16              # milliseconds per step

# ── Persistence ───────────────────────────────────────────────────────────────
SAVE_DEBOUNCE_MS : int = 200       # delay before flushing to disk

# ── Windows API constants ─────────────────────────────────────────────────────
HWND_BOTTOM       = 1
SWP_NOMOVE        = 0x0002
SWP_NOSIZE        = 0x0001
SWP_NOACTIVATE    = 0x0010
SWP_NOOWNERZORDER = 0x0200
WS_EX_TOOLWINDOW  = 0x00000080
WS_EX_NOACTIVATE  = 0x08000000
GWL_EXSTYLE       = -20

# Sink interval — how often we re-push the window below others (ms)
SINK_INTERVAL_MS : int = 3000