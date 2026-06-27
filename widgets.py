"""
widgets.py
----------
Reusable UI primitives:
  - rounded_rect()   : draws a smooth rounded rectangle on a Canvas
  - hex_to_rgb()     : colour math helper
  - blend_colours()  : linear interpolation between two hex colours
  - CheckBox         : custom drawn checkbox widget
  - TaskRow          : one complete task row (checkbox + label + delete btn)
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable

import config
from models import Priority, Task


# ── Colour helpers ────────────────────────────────────────────────────────────
def hex_to_rgb(hex_colour: str) -> tuple[int, int, int]:
    h = hex_colour.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def blend_colours(c1: str, c2: str, t: float) -> str:
    """
    Linearly interpolate between hex colours c1 and c2.
    t=0 -> c1,  t=1 -> c2
    """
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


# ── Canvas helper ─────────────────────────────────────────────────────────────
def rounded_rect(
    canvas: tk.Canvas,
    x1: int, y1: int,
    x2: int, y2: int,
    r: int,
    **kwargs,
) -> int:
    """
    Draw a smooth rounded rectangle and return its canvas item id.
    Uses a polygon with smooth=True so it works on every platform.
    """
    pts = [
        x1+r, y1,    x2-r, y1,
        x2,   y1,    x2,   y1+r,
        x2,   y2-r,  x2,   y2,
        x2-r, y2,    x1+r, y2,
        x1,   y2,    x1,   y2-r,
        x1,   y1+r,  x1,   y1,
        x1+r, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kwargs)


# ── Checkbox ──────────────────────────────────────────────────────────────────
class CheckBox(tk.Canvas):
    """
    A tiny custom-drawn checkbox.
    Calls on_toggle(checked: bool) when clicked.
    """

    SIZE = 18

    def __init__(
        self,
        parent: tk.Widget,
        checked: bool = False,
        on_toggle: Callable[[bool], None] = lambda _: None,
        bg: str = config.BG_CARD,
    ) -> None:
        super().__init__(
            parent,
            width=self.SIZE,
            height=self.SIZE,
            bg=bg,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )
        self._checked   = checked
        self._on_toggle = on_toggle
        self._bg        = bg
        self._redraw()
        self.bind("<Button-1>", self._click)

    def _redraw(self) -> None:
        self.delete("all")
        colour = config.CHK_ON  if self._checked else config.CHK_OFF
        fill   = config.CHK_ON  if self._checked else self._bg
        self.create_rectangle(
            1, 1, self.SIZE - 1, self.SIZE - 1,
            outline=colour,
            width=1.5,
            fill=fill,
        )
        if self._checked:
            self.create_line(
                4,  9, 8, 13,
                fill="white", width=2,
                capstyle="round", joinstyle="round",
            )
            self.create_line(
                8, 13, 14, 5,
                fill="white", width=2,
                capstyle="round", joinstyle="round",
            )

    def _click(self, _event: tk.Event) -> None:
        self._checked = not self._checked
        self._redraw()
        self._on_toggle(self._checked)

    def set_bg(self, colour: str) -> None:
        """Update background without toggling state (used by hover)."""
        self._bg = colour
        self.configure(bg=colour)
        self._redraw()

    @property
    def checked(self) -> bool:
        return self._checked


# ── Priority dot colour map ───────────────────────────────────────────────────
_PRIORITY_COLOUR: dict[Priority, str] = {
    Priority.HIGH  : config.PRIORITY_HIGH,
    Priority.MEDIUM: config.PRIORITY_MEDIUM,
    Priority.LOW   : config.PRIORITY_LOW,
    Priority.NONE  : config.BG_CARD,   # invisible when no priority set
}


# ── Task row ──────────────────────────────────────────────────────────────────
class TaskRow(tk.Frame):
    """
    One task displayed as:
      [priority dot] [checkbox] [task text] [✕]

    Callbacks
    ---------
    on_delete(row)  called after the fade-out animation completes
    on_toggle(row)  called immediately when the checkbox is clicked
    """

    def __init__(
        self,
        parent    : tk.Widget,
        task      : Task,
        on_delete : Callable[["TaskRow"], None],
        on_toggle : Callable[["TaskRow"], None],
        wrap_width: int = 170,
    ) -> None:
        super().__init__(
            parent,
            bg=config.BG_CARD,
            bd=0,
            highlightthickness=0,
        )
        self.task        = task
        self._on_delete  = on_delete
        self._on_toggle  = on_toggle
        self._wrap_width = wrap_width

        self._build()
        self._bind_hover()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build(self) -> None:
        # Priority colour strip (3 px wide)
        dot_colour = _PRIORITY_COLOUR.get(self.task.priority, config.BG_CARD)
        self._dot = tk.Frame(self, width=3, bg=dot_colour)
        self._dot.pack(side="left", fill="y", padx=(2, 4))

        # Checkbox
        self._checkbox = CheckBox(
            self,
            checked   = self.task.done,
            on_toggle = self._on_checkbox,
            bg        = config.BG_CARD,
        )
        self._checkbox.pack(side="left", padx=(0, 6), pady=5)

        # Task label
        self._label = tk.Label(
            self,
            text       = self.task.text,
            bg         = config.BG_CARD,
            fg         = config.DONE_CLR if self.task.done else config.TEXT_CLR,
            font       = config.FONT_STRIKE if self.task.done else config.FONT_BODY,
            anchor     = "w",
            justify    = "left",
            wraplength = self._wrap_width,
        )
        self._label.pack(side="left", fill="x", expand=True)

        # Clicking the label also toggles the checkbox
        self._label.bind(
            "<Button-1>", lambda _: self._checkbox._click(None)
        )

        # Delete button
        self._del_btn = tk.Label(
            self,
            text   = "✕",
            bg     = config.BG_CARD,
            fg     = config.DEL_CLR,
            font   = ("Segoe UI", 9, "bold"),
            cursor = "hand2",
            padx   = 4,
        )
        self._del_btn.pack(side="right", padx=(0, 4))
        self._del_btn.bind("<Button-1>", lambda _: self._begin_fade())
        self._del_btn.bind(
            "<Enter>", lambda _: self._del_btn.config(fg=config.DEL_HOVER))
        self._del_btn.bind(
            "<Leave>", lambda _: self._del_btn.config(fg=config.DEL_CLR))

        # Separator line — packed by pack_row(), not by _build()
        self._separator = tk.Frame(
            self.master,
            bg=config.DIVIDER,
            height=1,
        )

    def _bind_hover(self) -> None:
        for widget in (self, self._label, self._dot):
            widget.bind("<Enter>", self._hover_in)
            widget.bind("<Leave>", self._hover_out)

    # ── Checkbox callback ──────────────────────────────────────────────────────
    def _on_checkbox(self, checked: bool) -> None:
        self.task.done = checked
        self._label.config(
            font = config.FONT_STRIKE if checked else config.FONT_BODY,
            fg   = config.DONE_CLR   if checked else config.TEXT_CLR,
        )
        self._on_toggle(self)

    # ── Hover ──────────────────────────────────────────────────────────────────
    def _set_bg(self, colour: str) -> None:
        self.config(bg=colour)
        self._label.config(bg=colour)
        self._del_btn.config(bg=colour)
        self._checkbox.set_bg(colour)

    def _hover_in(self, _event: tk.Event) -> None:
        self._set_bg(config.BG_ROW_HOVER)

    def _hover_out(self, _event: tk.Event) -> None:
        self._set_bg(config.BG_CARD)

    # ── Delete fade animation ──────────────────────────────────────────────────
    def _begin_fade(self, step: int = 0) -> None:
        if step <= config.FADE_STEPS:
            t        = step / config.FADE_STEPS
            src_text = config.DONE_CLR if self.task.done else config.TEXT_CLR
            self._label.config(
                fg=blend_colours(src_text, config.BG_CARD, t)
            )
            self._del_btn.config(
                fg=blend_colours(config.DEL_CLR, config.BG_CARD, t)
            )
            self.after(
                config.FADE_DELAY,
                lambda: self._begin_fade(step + 1),
            )
        else:
            self._on_delete(self)

    # ── Pack helpers ───────────────────────────────────────────────────────────
    def pack_row(self, **kwargs) -> None:
        """Pack this row and its separator into the parent container."""
        self.pack(fill="x", padx=4, pady=(2, 0), **kwargs)
        self._separator.pack(fill="x", padx=config.PADDING)

    def remove(self) -> None:
        """Destroy this row and its separator widget."""
        self._separator.destroy()
        self.destroy()

    def update_wrap(self, width: int) -> None:
        self._wrap_width = width
        self._label.config(wraplength=width)