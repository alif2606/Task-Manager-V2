"""
main.py
-------
Entry point. Nothing else lives here.
Run with:  python main.py
"""

from ui import TaskWidget


def main() -> None:
    app = TaskWidget()
    app.mainloop()


if __name__ == "__main__":
    main()