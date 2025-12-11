from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QLabel, QGridLayout
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


        self.employees = self.client.get_employees()

        self.build_ui()

    def build_ui(self):
        main_layout = QVBoxLayout()

        # --- Grid layout for labels + fields ---
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
        self.calendar = CalendarWidget()
        self.calendar.cell_clicked.connect(self.on_override_requested)  # <<< ВАЖНО
        main_layout.addWidget(self.calendar)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Load initial month
        self.reload_calendar()




    # ---------------------------------------------
    # RELOAD SCHEDULE AND REBUILD CALENDAR
    # ---------------------------------------------
    def reload_calendar(self):
        year = int(self.year_select.currentText())
        month = int(self.month_select.currentText())

        # --- Get schedule from API ---
        data = self.client.get_schedule(year, month)
        schedule = data.get("schedule", {})

        # Ordered list of employee names
        ordered_names = [emp["full_name"] for emp in self.employees]

        # Build calendar input format
        schedule_data = {
            "employees": ordered_names,
            "days": list(range(1, 32)),
            "schedule": schedule
        }

        # Replace calendar widget
        self.calendar.setParent(None)
        self.calendar = CalendarWidget()
        self.calendar.cell_clicked.connect(self.on_override_requested)
        self.calendar.build(schedule_data)

        # Re-add to layout
        self.centralWidget().layout().addWidget(self.calendar)






    # ---------------------------------------------
    # HANDLE OVERRIDE CLICK
    # ---------------------------------------------
    def on_override_requested(self, day, payload):
        employee, new_shift = payload.split(":")

        if not new_shift:
            new_shift = ""  # празна смяна

        year = int(self.year_select.currentText())
        month = int(self.month_select.currentText())

        data = {
            "employee": employee,
            "day": day,
            "new_shift": new_shift
        }

        try:
            response = self.client.post_override(year, month, data)
            print("Override OK:", response)
            self.reload_calendar()  # 🔄 reloading UI
        except Exception as e:
            print("Override error:", e)






