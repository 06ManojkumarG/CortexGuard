import sys

from PySide6.QtWidgets import QApplication

from dashboard.main_window import CortexGuardWindow


def main():
    app = QApplication(sys.argv)

    window = CortexGuardWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()