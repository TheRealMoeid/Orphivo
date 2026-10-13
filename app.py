"""Local Persian speech-to-text desktop application."""
from src.ui import PersianSTTApp


def main() -> None:
    app = PersianSTTApp()
    app.mainloop()


if __name__ == "__main__":
    main()
