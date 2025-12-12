import calendar
import time

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QComboBox, QLabel, QGridLayout, QDialog, QScrollArea
)
from PyQt6.QtCore import Qt

from api_client import APIClient
from calendar_widget import CalendarWidget
from employees_widget import EmployeesWidget


MONTH_NAMES = {
    1: "Януари", 2: "Февруари", 3: "Март",
    4: "Април", 5: "Май", 6: "Юни",
    7: "Юли", 8: "Август", 9: "Септември",
    10: "Октомври", 11: "Ноември", 12: "Декември"
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.client = APIClient()

        self.setWindowTitle("Мениджър на работни графици")

        self.employees = self.client.get_employees()
        self.emp_widget = None

        self.build_ui()

    def build_ui(self):
        main_layout = QVBoxLayout()
        grid = QGridLayout()

        # Labels
        grid.addWidget(QLabel("Година:"), 0, 0)
        grid.addWidget(QLabel("Месец:"), 0, 1)

        # Year select
        self.year_select = QComboBox()
        for y in self.client.get_years():
            self.year_select.addItem(str(y))
        grid.addWidget(self.year_select, 1, 0)

        # Month select
        self.month_select = QComboBox()
        for m in range(1, 13):
            self.month_select.addItem(str(m))
        grid.addWidget(self.month_select, 1, 1)

        # Default selections
        if self.year_select.count():
            self.year_select.setCurrentIndex(0)
        if self.month_select.count():
            self.month_select.setCurrentIndex(0)

        # Load button
        load_btn = QPushButton("Зареди месец")
        load_btn.clicked.connect(self.reload_calendar)
        grid.addWidget(load_btn, 1, 2)

        # Employees button
        employees_btn = QPushButton("Служители")
        employees_btn.clicked.connect(self.open_employees)
        grid.addWidget(employees_btn, 2, 0)

        main_layout.addLayout(grid)

        # Titles
        self.section_title = QLabel("КАНТАР")
        self.section_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.section_title.setStyleSheet("font-size: 22px; font-weight: bold;")
        main_layout.addWidget(self.section_title)

        self.month_title = QLabel("")
        self.month_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.month_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(self.month_title)

        # Scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        main_layout.addWidget(self.scroll)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # React to changes
        self.year_select.currentIndexChanged.connect(self.reload_calendar)
        self.month_select.currentIndexChanged.connect(self.reload_calendar)

        self.reload_calendar()

    def reload_calendar(self):
        year_text = self.year_select.currentText()
        month_text = self.month_select.currentText()

        if not year_text or not month_text:
            return

        year = int(year_text)
        month = int(month_text)

        self.month_title.setText(MONTH_NAMES.get(month, ""))

        month_info = self.client.get_month_info(year, month)
        days = list(range(1, month_info["days"] + 1))
        weekends = month_info.get("weekends", [])
        holidays = month_info.get("holidays", [])

        try:
            data = self.client.get_schedule(year, month)
        except FileNotFoundError:
            self.client.generate_month(year, month)
            time.sleep(0.2)
            data = self.client.get_schedule(year, month)

        schedule = data.get("schedule", {})


        ordered_names = [emp["full_name"] for emp in self.employees]

        calendar_widget = CalendarWidget()
        calendar_widget.cell_clicked.connect(self.on_override_requested)

        calendar_widget.setup(
            ordered_names,
            days,
            schedule,
            weekends,
            holidays
        )


        calendar_widget.apply_schedule(schedule)

        self.scroll.setWidget(calendar_widget)
        self.calendar = calendar_widget

    def on_override_requested(self, day, payload):
        employee_name, new_shift = payload.split(":")

        emp_id = None
        for emp in self.employees:
            if emp["full_name"] == employee_name:
                emp_id = emp["id"]
                break

        if emp_id is None:
            print(f"ГРЕШКА: няма такъв служител в БД → {employee_name}")
            return

        year = int(self.year_select.currentText())
        month = int(self.month_select.currentText())

        try:
            self.client.post_override(year, month, {
                "employee_id": emp_id,
                "day": day,
                "shift": new_shift
            })
        except Exception as e:
            print("ГРЕШКА при override:", e)
            return

        self.reload_calendar()

    def open_employees(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Управление на служители")

        layout = QVBoxLayout(dialog)

        self.emp_widget = EmployeesWidget(self.employees)
        layout.addWidget(self.emp_widget)

        self.emp_widget.employee_added.connect(self.on_add_employee)
        self.emp_widget.employee_updated.connect(self.on_update_employee)
        self.emp_widget.employee_deleted.connect(self.on_delete_employee)

        dialog.exec()
        self.emp_widget = None

    def on_add_employee(self, data):
        self.client.add_employee(data)
        self.employees = self.client.get_employees()
        self.reload_calendar()

    def on_update_employee(self, data):
        self.client.update_employee(data["id"], data)
        self.employees = self.client.get_employees()
        self.reload_calendar()

    def on_delete_employee(self, emp_id):
        self.client.delete_employee(emp_id)
        self.employees = self.client.get_employees()
        self.reload_calendar()






