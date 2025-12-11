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

        year_label = QLabel("Година:")
        month_label = QLabel("Месец:")

        grid.addWidget(year_label, 0, 0)
        grid.addWidget(month_label, 0, 1)

        self.year_select = QComboBox()
        for y in self.client.get_years():
            self.year_select.addItem(str(y))

        self.month_select = QComboBox()
        for m in range(1, 13):
            self.month_select.addItem(str(m))

        grid.addWidget(self.year_select, 1, 0)
        grid.addWidget(self.month_select, 1, 1)

        load_btn = QPushButton("Зареди месец")
        load_btn.clicked.connect(self.reload_calendar)
        grid.addWidget(load_btn, 1, 2)

        employees_btn = QPushButton("Служители")
        employees_btn.clicked.connect(self.open_employees)
        grid.addWidget(employees_btn, 2, 0)

        main_layout.addLayout(grid)

        self.section_title = QLabel("КАНТАР")
        self.section_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.section_title.setStyleSheet("font-size: 22px; font-weight: bold;")
        main_layout.addWidget(self.section_title)

        self.month_title = QLabel("")
        self.month_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.month_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(self.month_title)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        main_layout.addWidget(self.scroll)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)


        self.month_select.currentIndexChanged.connect(self.reload_calendar)
        self.year_select.currentIndexChanged.connect(self.reload_calendar)

        self.reload_calendar()


    def reload_calendar(self):
        year = int(self.year_select.currentText())
        month = int(self.month_select.currentText())

        self.month_title.setText(MONTH_NAMES.get(month, ""))

        month_info = self.client.get_month_info(year, month)
        days_count = month_info.get("days", 31)
        holidays = month_info.get("holidays", [])
        days = list(range(1, days_count + 1))

        weekends = [
            d for d in days if calendar.weekday(year, month, d) in (5, 6)
        ]


        try:
            data = self.client.get_schedule(year, month)
        except FileNotFoundError:
            print(f"Месецът не съществува → генерираме: {year} {month}")
            self.client.generate_month(year, month)

            time.sleep(0.1)
            for _ in range(5):
                try:
                    data = self.client.get_schedule(year, month)
                    break
                except FileNotFoundError:
                    time.sleep(0.1)
            else:
                raise RuntimeError("Файлът не се появи след генериране!")

        schedule = data.get("schedule", {})
        ordered_names = [emp["full_name"] for emp in self.employees]


        self.calendar = CalendarWidget()
        self.calendar.cell_clicked.connect(self.on_override_requested)

        self.calendar.setup(
            ordered_names,
            days,
            schedule,
            weekends,
            holidays
        )


        self.calendar.apply_schedule(schedule)

        self.scroll.setWidget(self.calendar)

    def on_override_requested(self, day, payload):
        employee, new_shift = payload.split(":")
        if not new_shift:
            new_shift = ""

        year = int(self.year_select.currentText())
        month = int(self.month_select.currentText())

        self.client.post_override(year, month, {
            "employee": employee,
            "day": day,
            "new_shift": new_shift
        })


        self.reload_calendar()


    def open_employees(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Управление на служители")

        layout = QVBoxLayout()
        dialog.setLayout(layout)

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
        if self.emp_widget:
            self.emp_widget.reload_list(self.employees)
        self.reload_calendar()

    def on_update_employee(self, data):
        self.client.update_employee(data["id"], data)
        self.employees = self.client.get_employees()
        if self.emp_widget:
            self.emp_widget.reload_list(self.employees)
        self.reload_calendar()

    def on_delete_employee(self, emp_id):
        self.client.delete_employee(emp_id)
        self.employees = self.client.get_employees()
        if self.emp_widget:
            self.emp_widget.reload_list(self.employees)
        self.reload_calendar()



