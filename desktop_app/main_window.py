from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox
)
from api_client import APIClient
from calendar_widget import CalendarWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.client = APIClient()

        self.setWindowTitle("Мениджър на работни графици")

        # default, current year/month
        self.current_year = 2025
        self.current_month = 1

        self.build_ui()

    def build_ui(self):
        main_layout = QVBoxLayout()

        # --- HEADER for choosing year/month ---
        header = QHBoxLayout()

        self.year_select = QComboBox()
        for y in self.client.get_years():
            self.year_select.addItem(str(y))

        self.month_select = QComboBox()
        for m in range(1, 13):
            self.month_select.addItem(str(m))


        load_btn: QPushButton = QPushButton("Зареди месец")
        load_btn.clicked.connect(self.reload_calendar)

        header.addWidget(self.year_select)
        header.addWidget(self.month_select)
        header.addWidget(load_btn)

        main_layout.addLayout(header)


        self.calendar = CalendarWidget(self.current_year, self.current_month)
        main_layout.addWidget(self.calendar)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)


    def reload_calendar(self):
        year = int(self.year_select.currentText())
        month = int(self.month_select.currentText())

        self.current_year = year
        self.current_month = month

        self.calendar.setParent(None)
        self.calendar = CalendarWidget(year, month)

        self.centralWidget().layout().addWidget(self.calendar)


