from desktop_app.backend_runner import DjangoBackend
import sys
from PyQt6.QtWidgets import QApplication
from desktop_app.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    backend = DjangoBackend()
    backend.start()

    window = MainWindow()
    window.show()

    exit_code = app.exec()

    backend.stop()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
