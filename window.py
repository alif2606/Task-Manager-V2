"""
window.py
---------
Frameless transparent window + Windows API desktop-widget behaviour.
"""

from __future__ import annotations

import ctypes
import tkinter as tk
from typing import Optional

import config
from storage import load_settings, save_settings


# ── Windows API ───────────────────────────────────────────────────────────────
_user32         = ctypes.windll.user32
_SetWindowPos   = _user32.SetWindowPos
_SetWindowLongW = _user32.SetWindowLongW
_GetWindowLongW = _user32.GetWindowLongW


def _push_to_bottom(hwnd: int) -> None:
    _SetWindowPos(
        hwnd,
        config.HWND_BOTTOM,
        0, 0, 0, 0,
        config.SWP_NOMOVE     |
        config.SWP_NOSIZE     |
        config.SWP_NOACTIVATE |
        config.SWP_NOOWNERZORDER,
    )


def _apply_toolwindow_style(hwnd: int) -> None:
    style = _GetWindowLongW(hwnd, config.GWL_EXSTYLE)
    _SetWindowLongW(
        hwnd,
        config.GWL_EXSTYLE,
        style | config.WS_EX_TOOLWINDOW | config.WS_EX_NOACTIVATE,
    )


# ── Base window ───────────────────────────────────────────────────────────────
class BaseWindow(tk.Tk):

    def __init__(self) -> None:
        super().__init__()

        self._hwnd             : Optional[int] = None
        self._drag_x           : int  = 0
        self._drag_y           : int  = 0
        self._resize_start_x   : int  = 0
        self._resize_start_y   : int  = 0
        self._resize_start_w   : int  = 0
        self._resize_start_h   : int  = 0
        self._geo_save_pending : bool = False

        self._configure_window()
        self._restore_geometry()

        self.bind("<FocusIn>", self._on_focus_in)
        self.after(300, self._init_win32)

    def _configure_window(self) -> None:
        self.overrideredirect(True)
        self.attributes("-alpha", config.WINDOW_ALPHA)
        self.attributes("-topmost", False)
        self.configure(bg=config.BG_OUTER)
        self.wm_attributes("-transparentcolor", config.BG_OUTER)
        self.minsize(config.MIN_WIDTH, config.MIN_HEIGHT)

    def _restore_geometry(self) -> None:
        settings = load_settings()
        geo      = settings.get("geometry")
        if geo:
            try:
                self.geometry(geo)
                return
            except Exception:
                pass
        self._centre_window()

    def _centre_window(self) -> None:
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = (sw - config.DEFAULT_WIDTH)  // 2
        y  = (sh - config.DEFAULT_HEIGHT) // 2
        self.geometry(
            f"{config.DEFAULT_WIDTH}x{config.DEFAULT_HEIGHT}+{x}+{y}"
        )

    def save_geometry_debounced(self) -> None:
        if self._geo_save_pending:
            return
        self._geo_save_pending = True
        self.after(400, self._flush_geometry)

    def _flush_geometry(self) -> None:
        self._geo_save_pending = False
        try:
            save_settings({"geometry": self.geometry()})
        except Exception:
            pass

    def _init_win32(self) -> None:
        try:
            raw = self.frame()
            if not raw:
                return
            self._hwnd = int(raw, 16)
            _apply_toolwindow_style(self._hwnd)
            _push_to_bottom(self._hwnd)
        except Exception:
            pass

    def _on_focus_in(self, _event: tk.Event) -> None:
        if self._hwnd:
            try:
                _push_to_bottom(self._hwnd)
            except Exception:
                pass

    def start_drag(self, event: tk.Event) -> None:
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()

    def do_drag(self, event: tk.Event) -> None:
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.geometry(f"+{x}+{y}")

    def start_resize(self, event: tk.Event) -> None:
        self._resize_start_x = event.x_root
        self._resize_start_y = event.y_root
        self._resize_start_w = self.winfo_width()
        self._resize_start_h = self.winfo_height()

    def do_resize(self, event: tk.Event) -> None:
        dw = event.x_root - self._resize_start_x
        dh = event.y_root - self._resize_start_y
        nw = max(config.MIN_WIDTH,  self._resize_start_w + dw)
        nh = max(config.MIN_HEIGHT, self._resize_start_h + dh)
        self.geometry(f"{nw}x{nh}")

    def quit_app(self) -> None:
        try:
            save_settings({"geometry": self.geometry()})
        except Exception:
            pass
        self.destroy()