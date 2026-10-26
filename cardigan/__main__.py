import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from .theme import NoAltMenuStyle
from .window import Window


def main():
    app = QApplication(sys.argv)
    app.setStyle(NoAltMenuStyle(app.style().objectName()))
    win = Window(Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
