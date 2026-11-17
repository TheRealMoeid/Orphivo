"""Local Persian speech-to-text desktop application."""
import sys

from PySide6.QtWidgets import QApplication

from src.qt_main_window import OrphivoMainWindow


def main() -> int:
    app = QApplication(sys.argv)
    window = OrphivoMainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())