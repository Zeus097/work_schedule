from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QLabel
)
from api_client import APIClient
from calendar_widget import CalendarWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.client = APIClient()

        self.setWindowTitle("Мениджър на работни графици")

        self.current_year = 2025
        self.current_month = 1

        self.employees = self.client.get_employees()  # нужно за подредбата на смените

        self.build_ui()

    def build_ui(self):
        main_layout = QVBoxLayout()

        # --- Grid layout for labels + fields ---
        from PyQt6.QtWidgets import QGridLayout
        grid = QGridLayout()

        # Labels
        year_label = QLabel("Година:")
        year_label.setStyleSheet("color: #ccc; font-size: 12px;")

        month_label = QLabel("Месец:")
        month_label.setStyleSheet("color: #ccc; font-size: 12px;")

        grid.addWidget(year_label, 0, 0)
        grid.addWidget(month_label, 0, 1)

        # Combo boxes
        self.year_select = QComboBox()
        for y in self.client.get_years():
            self.year_select.addItem(str(y))

        self.month_select = QComboBox()
        for m in range(1, 13):
            self.month_select.addItem(str(m))

        grid.addWidget(self.year_select, 1, 0)
        grid.addWidget(self.month_select, 1, 1)

        # Button
        load_btn = QPushButton("Зареди месец")
        load_btn.clicked.connect(self.reload_calendar)
        grid.addWidget(load_btn, 1, 2)

        main_layout.addLayout(grid)

        # --- Calendar ---
        self.calendar = CalendarWidget(self.current_year, self.current_month)
        main_layout.addWidget(self.calendar)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)


    def reload_calendar(self):
        year = int(self.year_select.currentText())
        month = int(self.month_select.currentText())

        # --- Get schedule from API ---
        data = self.client.get_schedule(year, month)

        shifts = {}
        schedule = data.get("schedule", {})

        # Ordered list of employee names
        ordered_names = [emp["full_name"] for emp in self.employees]

        for name in ordered_names:
            days = schedule.get(name, {})
            for day_str, sm in days.items():
                day = int(day_str)
                shifts.setdefault(day, []).append(sm)

        # Replace calendar in UI
        self.calendar.setParent(None)
        self.calendar = CalendarWidget(year, month)
        self.calendar.set_day_shifts(shifts)

        self.centralWidget().layout().addWidget(self.calendar)


