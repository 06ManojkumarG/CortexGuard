
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

# Add the CortexGuard repository root to Python's search path.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.main_window import CortexGuardWindow


def main():
    app = QApplication(sys.argv)
    window = CortexGuardWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
