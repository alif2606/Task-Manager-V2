"""
storage.py
----------
All disk I/O lives here and nowhere else.
Callers never touch file paths or JSON directly.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Optional

from models import Task


def _get_base_dir() -> str:
    """
    Return the folder where data should be stored.

    When running as a PyInstaller .exe, files must be saved
    BESIDE the .exe — not inside the temporary _MEIPASS folder
    which gets deleted when the program exits.

    When running as a normal .py script, save next to the script.
    """
    if getattr(sys, "frozen", False):
        # Running inside a PyInstaller bundle → use the exe's folder
        return os.path.dirname(sys.executable)
    else:
        # Running as a normal Python script → use the script's folder
        return os.path.dirname(os.path.abspath(__file__))


_BASE_DIR  = _get_base_dir()
_DATA_DIR  = os.path.join(_BASE_DIR, "data")
TASKS_FILE = os.path.join(_DATA_DIR, "tasks.json")
CFG_FILE   = os.path.join(_DATA_DIR, "settings.json")


def _ensure_data_dir() -> None:
    """Create data/ if it does not exist yet."""
    os.makedirs(_DATA_DIR, exist_ok=True)


# ── Tasks ─────────────────────────────────────────────────────────────────────
def load_tasks() -> list[Task]:
    """
    Read tasks from disk.
    Returns an empty list when the file is absent or corrupt —
    never raises an exception to the caller.
    """
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        if isinstance(raw, list):
            return [Task.from_dict(item) for item in raw]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass
    return []


def save_tasks(tasks: list[Task]) -> None:
    """
    Write tasks to disk.
    Active tasks are stored first so the file is human-readable.
    Silently skips if the file is locked (e.g. antivirus scan).
    """
    _ensure_data_dir()
    active    = [t for t in tasks if not t.done]
    completed = [t for t in tasks if t.done]
    ordered   = active + completed
    try:
        with open(TASKS_FILE, "w", encoding="utf-8") as fh:
            json.dump([t.to_dict() for t in ordered], fh,
                      indent=2, ensure_ascii=False)
    except OSError:
        pass


# ── Settings / window geometry ────────────────────────────────────────────────
def load_settings() -> dict:
    """
    Return the persisted settings dict.
    Always returns a dict (possibly empty) — never raises.
    """
    try:
        with open(CFG_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return {}


def save_settings(settings: dict) -> None:
    """Persist arbitrary settings. Merges with existing file."""
    _ensure_data_dir()
    current = load_settings()
    current.update(settings)
    try:
        with open(CFG_FILE, "w", encoding="utf-8") as fh:
            json.dump(current, fh, indent=2)
    except OSError:
        pass