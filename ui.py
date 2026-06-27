"""
ui.py
-----
TaskWidget — main application UI.

Flicker fix
-----------
The card background is drawn ONCE on startup and never redrawn
unless the window is actually resized by the user via the grip.

Placeholder fix
---------------
On frameless (overrideredirect) windows, FocusIn does not fire
reliably on Windows. A <Key> binding now clears the placeholder
on the first real keypress as a guaranteed fallback.
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional

import config
from models import Task
from storage import load_tasks, save_tasks
from widgets import TaskRow, rounded_rect
from window import BaseWindow


class TaskWidget(BaseWindow):
    PLACEHOLDER = "Add a task…"

    def __init__(self) -> None:
        super().__init__()

        self._task_rows    : list[TaskRow] = []
        self._save_pending : bool = False
        self._resize_job   : Optional[str] = None

        # Track actual window size so we can ignore position-only events
        self._last_w : int = config.DEFAULT_WIDTH
        self._last_h : int = config.DEFAULT_HEIGHT

        self._build_canvas()
        self._build_input_row()
        self._build_task_list()
        self._build_resize_grip()
        self._build_context_menu()

        # Bind <Configure> only after everything is built
        self.after(500, self._enable_configure_binding)

        # Load saved tasks after window is fully visible
        self.after(600, self._load_tasks)

    # ══════════════════════════════════════════════════════════════════════════
    # Startup
    # ══════════════════════════════════════════════════════════════════════════

    def _enable_configure_binding(self) -> None:
        self.bind("<Configure>", self._on_window_configure)

    # ══════════════════════════════════════════════════════════════════════════
    # Canvas + card
    # ══════════════════════════════════════════════════════════════════════════

    def _build_canvas(self) -> None:
        self._canvas = tk.Canvas(
            self,
            bg=config.BG_OUTER,
            highlightthickness=0,
            bd=0,
        )
        self._canvas.pack(fill="both", expand=True)

        self._draw_card(config.DEFAULT_WIDTH, config.DEFAULT_HEIGHT)

        self._title = tk.Label(
            self._canvas,
            text=config.APP_NAME.upper(),
            bg=config.BG_CARD,
            fg=config.TITLE_CLR,
            font=config.FONT_TITLE,
        )
        self._canvas.create_window(
            config.PADDING + config.RADIUS // 2, 18,
            window=self._title,
            anchor="nw",
            tags="title",
        )

        self._canvas.bind("<ButtonPress-1>", self.start_drag)
        self._canvas.bind("<B1-Motion>",     self.do_drag)

    def _draw_card(self, w: int, h: int) -> None:
        self._canvas.delete("card")
        r = config.RADIUS

        rounded_rect(
            self._canvas,
            r, r, w - r, h - r, r,
            fill    = config.BG_CARD,
            outline = config.BORDER_CLR,
            width   = config.BORDER_WIDTH,
            tags    = "card",
        )
        self._canvas.create_rectangle(
            config.PADDING + r // 2, 50,
            w - config.PADDING - r // 2, 51,
            fill=config.DIVIDER, outline="",
            tags="card",
        )
        self._canvas.create_rectangle(
            config.PADDING + r // 2, 100,
            w - config.PADDING - r // 2, 101,
            fill=config.DIVIDER, outline="",
            tags="card",
        )
        self._canvas.tag_lower("card")

    # ══════════════════════════════════════════════════════════════════════════
    # Input row
    # ══════════════════════════════════════════════════════════════════════════

    def _build_input_row(self) -> None:
        self._input_frame = tk.Frame(
            self._canvas,
            bg=config.BG_CARD,
            bd=0,
            highlightthickness=0,
        )
        self._canvas.create_window(
            config.PADDING, 58,
            window=self._input_frame,
            anchor="nw",
            tags="input_frame",
        )

        self._entry_var = tk.StringVar()
        self._entry = tk.Entry(
            self._input_frame,
            textvariable       = self._entry_var,
            bg                 = config.BG_INPUT,
            fg                 = config.HINT_CLR,
            insertbackground   = config.TEXT_CLR,
            relief             = "flat",
            bd                 = 4,
            font               = config.FONT_BODY,
            highlightthickness = 1,
            highlightbackground= config.BORDER_CLR,
            highlightcolor     = config.INPUT_FOCUS,
        )
        self._entry.pack(side="left", fill="x", expand=True, ipady=4)
        self._entry.insert(0, self.PLACEHOLDER)

        # Placeholder handling — multiple bindings for reliability
        self._entry.bind("<FocusIn>",      self._entry_focus_in)
        self._entry.bind("<FocusOut>",     self._entry_focus_out)
        self._entry.bind("<Return>",       lambda _: self._add_task())
        self._entry.bind("<Key>",          self._entry_on_key)
        self._entry.bind("<Button-1>",     self._entry_on_click)

        self._add_btn = tk.Button(
            self._input_frame,
            text             = "+ Add",
            bg               = config.BTN_BG,
            fg               = config.BTN_FG,
            activebackground = config.BTN_HOVER,
            activeforeground = config.BTN_FG,
            relief           = "flat",
            bd               = 0,
            font             = config.FONT_BTN,
            cursor           = "hand2",
            padx             = 8,
            pady             = 4,
            command          = self._add_task,
        )
        self._add_btn.pack(side="left", padx=(6, 0))
        self._add_btn.bind(
            "<Enter>", lambda _: self._add_btn.config(bg=config.BTN_HOVER))
        self._add_btn.bind(
            "<Leave>", lambda _: self._add_btn.config(bg=config.BTN_BG))

    # ══════════════════════════════════════════════════════════════════════════
    # Task list
    # ══════════════════════════════════════════════════════════════════════════

    def _build_task_list(self) -> None:
        self._scroll_canvas = tk.Canvas(
            self._canvas,
            bg=config.BG_CARD,
            bd=0,
            highlightthickness=0,
        )
        self._scrollbar = tk.Scrollbar(
            self._canvas,
            orient      = "vertical",
            command     = self._scroll_canvas.yview,
            width       = 6,
            troughcolor = config.BG_CARD,
            bg          = config.MUTED_CLR,
        )
        self._scroll_canvas.configure(
            yscrollcommand=self._scrollbar.set
        )

        w = config.DEFAULT_WIDTH
        h = config.DEFAULT_HEIGHT

        self._canvas.create_window(
            config.PADDING, 108,
            window=self._scroll_canvas,
            anchor="nw",
            tags="scroll_canvas",
        )
        self._canvas.create_window(
            w - config.PADDING // 2, 108,
            window=self._scrollbar,
            anchor="nw",
            tags="scrollbar",
        )

        self._task_container = tk.Frame(
            self._scroll_canvas,
            bg=config.BG_CARD,
            bd=0,
            highlightthickness=0,
        )
        self._scroll_canvas.create_window(
            0, 0,
            window=self._task_container,
            anchor="nw",
        )

        self._task_container.bind("<Configure>", self._update_scroll_region)
        self._scroll_canvas.bind("<MouseWheel>",  self._on_mousewheel)
        self._task_container.bind("<MouseWheel>", self._on_mousewheel)

        self._empty_label = tk.Label(
            self._task_container,
            text    = "No tasks yet — add one above!",
            bg      = config.BG_CARD,
            fg      = config.MUTED_CLR,
            font    = config.FONT_SMALL,
            justify = "left",
        )
        self._empty_label.pack(anchor="w", padx=8, pady=10)

        self._update_list_size(w, h)

    # ══════════════════════════════════════════════════════════════════════════
    # Resize grip
    # ══════════════════════════════════════════════════════════════════════════

    def _build_resize_grip(self) -> None:
        self._grip = tk.Label(
            self._canvas,
            text   = "⠿",
            bg     = config.BG_CARD,
            fg     = config.MUTED_CLR,
            cursor = "size_nw_se",
            font   = ("Segoe UI", 9),
        )
        self._canvas.create_window(
            config.DEFAULT_WIDTH - 6,
            config.DEFAULT_HEIGHT - 6,
            window=self._grip,
            anchor="se",
            tags="grip",
        )
        self._grip.bind("<ButtonPress-1>", self.start_resize)
        self._grip.bind("<B1-Motion>",     self.do_resize)

    # ══════════════════════════════════════════════════════════════════════════
    # Context menu
    # ══════════════════════════════════════════════════════════════════════════

    def _build_context_menu(self) -> None:
        self._menu = tk.Menu(
            self,
            tearoff=0,
            bg              = "#1e2235",
            fg              = config.TEXT_CLR,
            activebackground= "#2e3355",
            activeforeground= config.TEXT_CLR,
            bd=0, relief="flat",
            font=config.FONT_BODY,
        )
        self._menu.add_command(
            label="Clear completed",
            command=self._clear_completed,
        )
        self._menu.add_separator()
        self._menu.add_command(label="Quit", command=self.quit_app)
        self._canvas.bind("<Button-3>", self._show_context_menu)

    # ══════════════════════════════════════════════════════════════════════════
    # Configure handler
    # ══════════════════════════════════════════════════════════════════════════

    def _on_window_configure(self, _event: tk.Event) -> None:
        w = self.winfo_width()
        h = self.winfo_height()

        if w == self._last_w and h == self._last_h:
            return

        self._last_w = w
        self._last_h = h

        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(80, self._apply_layout)

    def _apply_layout(self) -> None:
        self._resize_job = None
        w = self._last_w
        h = self._last_h

        self._canvas.config(width=w, height=h)
        self._draw_card(w, h)

        self._canvas.coords("scrollbar", w - config.PADDING // 2, 108)
        self._canvas.coords("grip",      w - 6, h - 6)

        self._input_frame.config(width=w - config.PADDING * 2)
        self._update_list_size(w, h)

        wrap = self._current_wrap_width()
        for row in self._task_rows:
            row.update_wrap(wrap)

        self.save_geometry_debounced()

    # ══════════════════════════════════════════════════════════════════════════
    # Task CRUD
    # ══════════════════════════════════════════════════════════════════════════

    def _add_task(self) -> None:
        text = self._entry.get().strip()

        # Reject empty input and accidental placeholder submission
        if not text or text == self.PLACEHOLDER:
            self._reset_placeholder()
            return

        # Clear the entry and restore placeholder appearance
        self._reset_placeholder()

        task = Task(text=text)
        self._create_row(task)
        self._schedule_save()

    def _create_row(self, task: Task) -> None:
        if self._empty_label.winfo_ismapped():
            self._empty_label.pack_forget()

        wrap = self._current_wrap_width()
        row  = TaskRow(
            parent     = self._task_container,
            task       = task,
            on_delete  = self._handle_delete,
            on_toggle  = self._handle_toggle,
            wrap_width = wrap,
        )
        self._task_rows.append(row)
        self._repack_rows()

    def _handle_delete(self, row: TaskRow) -> None:
        if row in self._task_rows:
            self._task_rows.remove(row)
        row.remove()
        if not self._task_rows:
            self._empty_label.pack(anchor="w", padx=8, pady=10)
        self._schedule_save()

    def _handle_toggle(self, row: TaskRow) -> None:
        self._repack_rows()
        self._schedule_save()

    def _clear_completed(self) -> None:
        completed = [r for r in self._task_rows if r.task.done]
        for row in completed:
            self._task_rows.remove(row)
            row.remove()
        if not self._task_rows:
            self._empty_label.pack(anchor="w", padx=8, pady=10)
        self._schedule_save()

    def _repack_rows(self) -> None:
        active    = [r for r in self._task_rows if not r.task.done]
        completed = [r for r in self._task_rows if r.task.done]

        for row in self._task_rows:
            row.pack_forget()
            row._separator.pack_forget()

        for row in active + completed:
            row.pack_row()

    # ══════════════════════════════════════════════════════════════════════════
    # Persistence
    # ══════════════════════════════════════════════════════════════════════════

    def _load_tasks(self) -> None:
        tasks = load_tasks()
        for task in tasks:
            self._create_row(task)
        if not self._task_rows:
            self._empty_label.pack(anchor="w", padx=8, pady=10)

    def _schedule_save(self) -> None:
        if not self._save_pending:
            self._save_pending = True
            self.after(config.SAVE_DEBOUNCE_MS, self._flush_save)

    def _flush_save(self) -> None:
        self._save_pending = False
        save_tasks([row.task for row in self._task_rows])

    def quit_app(self) -> None:
        self._flush_save()
        super().quit_app()

    # ══════════════════════════════════════════════════════════════════════════
    # Scroll
    # ══════════════════════════════════════════════════════════════════════════

    def _update_scroll_region(self, _event: tk.Event = None) -> None:
        self._scroll_canvas.configure(
            scrollregion=self._scroll_canvas.bbox("all")
        )

    def _on_mousewheel(self, event: tk.Event) -> None:
        self._scroll_canvas.yview_scroll(
            int(-1 * (event.delta / 120)), "units"
        )

    def _update_list_size(self, w: int, h: int) -> None:
        area_h = max(40, h - 108 - 20)
        area_w = max(60, w - config.PADDING * 2 - 10)
        self._scroll_canvas.config(width=area_w, height=area_h)
        self._task_container.config(width=area_w)

    def _current_wrap_width(self) -> int:
        w = self.winfo_width() or config.DEFAULT_WIDTH
        return max(80, w - config.PADDING * 2 - 70)

    # ══════════════════════════════════════════════════════════════════════════
    # Entry placeholder — robust handling for frameless windows
    # ══════════════════════════════════════════════════════════════════════════

    def _is_placeholder_showing(self) -> bool:
        """True when the entry currently shows the greyed placeholder."""
        return (
            self._entry.get() == self.PLACEHOLDER
            and str(self._entry.cget("fg")) == config.HINT_CLR
        )

    def _clear_placeholder(self) -> None:
        """Remove the placeholder and switch to normal text colour."""
        if self._is_placeholder_showing():
            self._entry.delete(0, "end")
            self._entry.config(fg=config.TEXT_CLR)

    def _reset_placeholder(self) -> None:
        """Empty the entry and show the greyed placeholder again."""
        self._entry.delete(0, "end")
        self._entry.insert(0, self.PLACEHOLDER)
        self._entry.config(fg=config.HINT_CLR)

    def _entry_focus_in(self, _event) -> None:
        self._clear_placeholder()
        # Force keyboard focus — needed on overrideredirect windows
        self._entry.focus_force()

    def _entry_focus_out(self, _event) -> None:
        if not self._entry.get().strip():
            self._reset_placeholder()

    def _entry_on_click(self, _event) -> None:
        """Clicking the entry should always grab focus and clear placeholder."""
        self._entry.focus_force()
        self._clear_placeholder()

    def _entry_on_key(self, event) -> None:
        """
        Guaranteed placeholder clear on the first real keypress.
        Needed because FocusIn is unreliable on frameless Windows.
        """
        ignored = {
            "Shift_L", "Shift_R",
            "Control_L", "Control_R",
            "Alt_L", "Alt_R",
            "Tab", "Caps_Lock",
            "Win_L", "Win_R",
            "Return", "Escape",
        }
        if event.keysym in ignored:
            return
        self._clear_placeholder()

    # ══════════════════════════════════════════════════════════════════════════
    # Context menu
    # ══════════════════════════════════════════════════════════════════════════

    def _show_context_menu(self, event: tk.Event) -> None:
        self._menu.tk_popup(event.x_root, event.y_root)