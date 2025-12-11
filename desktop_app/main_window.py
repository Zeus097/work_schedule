from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
from api_client import APIClient

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.client = APIClient()

        self.setWindowTitle("Work Schedule Manager")

        layout = QVBoxLayout()

        years = self.client.get_years()
        label = QLabel(f"Налични години: {years}")

        layout.addWidget(label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)


