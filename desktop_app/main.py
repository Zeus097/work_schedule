import sys
from PyQt6.QtWidgets import QApplication
from desktop_app.main_window import MainWindow



def main():
    """ App entry point. """

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
