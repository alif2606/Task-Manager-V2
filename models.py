"""
models.py
---------
Pure data structures. No tkinter, no file I/O.
A Task is just a dataclass — easy to test, easy to serialise.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time


class Priority(str, Enum):
    NONE   = "none"
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"


@dataclass
class Task:
    text     : str
    done     : bool          = False
    priority : Priority      = Priority.NONE
    created  : float         = field(default_factory=time.time)
    # Unique id so the UI layer can track rows reliably
    task_id  : str           = field(default_factory=lambda: str(time.time_ns()))

    # ── Serialisation ──────────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "task_id" : self.task_id,
            "text"    : self.text,
            "done"    : self.done,
            "priority": self.priority.value,
            "created" : self.created,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            task_id  = data.get("task_id", str(time.time_ns())),
            text     = data.get("text", ""),
            done     = data.get("done", False),
            priority = Priority(data.get("priority", "none")),
            created  = data.get("created", time.time()),
        )

    def __repr__(self) -> str:
        status = "✓" if self.done else "○"
        return f"Task({status} [{self.priority.value}] {self.text!r})"