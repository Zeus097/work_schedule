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

        self.current_year = None
        self.current_month = None
        self.current_schedule = {}

        self.build_ui()

    # =====================================================
    # UI
    # =====================================================
    def build_ui(self):
        main_layout = QVBoxLayout()
        grid = QGridLayout()

        grid.addWidget(QLabel("Година:"), 0, 0)
        grid.addWidget(QLabel("Месец:"), 0, 1)

        # -------- YEAR --------
        self.year_select = QComboBox()

        years = self.client.get_years()
        if not years:
            # fallback – UI никога не остава празен
            years = [2025, 2026, 2027]

        for y in years:
            self.year_select.addItem(str(y))

        grid.addWidget(self.year_select, 1, 0)

        # -------- MONTH --------
        self.month_select = QComboBox()
        for m in range(1, 13):
            self.month_select.addItem(str(m))

        grid.addWidget(self.month_select, 1, 1)

        load_btn = QPushButton("Зареди месец")
        load_btn.clicked.connect(self.load_month)
        grid.addWidget(load_btn, 1, 2)

        employees_btn = QPushButton("Служители")
        employees_btn.clicked.connect(self.open_employees)
        grid.addWidget(employees_btn, 2, 0)

        main_layout.addLayout(grid)

        # -------- TITLES --------
        self.section_title = QLabel("КАНТАР")
        self.section_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.section_title.setStyleSheet("font-size: 22px; font-weight: bold;")
        main_layout.addWidget(self.section_title)

        self.month_title = QLabel("")
        self.month_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.month_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(self.month_title)

        # -------- CALENDAR --------
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        main_layout.addWidget(self.scroll)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.init_defaults()

    # =====================================================
    # DEFAULTS
    # =====================================================
    def init_defaults(self):
        # default year = first available
        if self.year_select.count() > 0:
            self.year_select.setCurrentIndex(0)

        # default month = December
        if self.month_select.count() > 0:
            self.month_select.setCurrentIndex(11)

        self.load_month()

    # =====================================================
    # LOAD MONTH
    # =====================================================
    def load_month(self):
        if not self.year_select.currentText():
            return
        if not self.month_select.currentText():
            return

        year = int(self.year_select.currentText())
        month = int(self.month_select.currentText())

        self.current_year = year
        self.current_month = month

        self.month_title.setText(MONTH_NAMES.get(month, ""))

        month_info = self.client.get_month_info(year, month)
        days = list(range(1, month_info["days"] + 1))
        weekends = month_info.get("weekends", [])
        holidays = month_info.get("holidays", [])

        try:
            data = self.client.get_schedule(year, month)
        except FileNotFoundError:
            self.client.generate_month(year, month)
            time.sleep(0.1)
            data = self.client.get_schedule(year, month)

        self.current_schedule = data.get("schedule", {})
        if not self.current_schedule:
            return

        ordered_names = list(self.current_schedule.keys())

        self.calendar = CalendarWidget()
        self.calendar.cell_clicked.connect(self.on_override_requested)

        self.calendar.setup(
            ordered_names,
            days,
            self.current_schedule,
            weekends,
            holidays
        )

        self.calendar.apply_schedule(self.current_schedule)
        self.scroll.setWidget(self.calendar)

    # =====================================================
    # OVERRIDES
    # =====================================================
    def on_override_requested(self, day, payload):
        employee_name, new_shift = payload.split(":")

        emp_id = None
        for emp in self.employees:
            if emp["full_name"] == employee_name:
                emp_id = emp["id"]
                break

        if emp_id is None:
            return

        self.client.post_override(
            self.current_year,
            self.current_month,
            {
                "employee_id": emp_id,
                "day": day,
                "shift": new_shift
            }
        )

        emp_schedule = self.current_schedule.setdefault(employee_name, {})
        emp_schedule[day] = new_shift

        self.calendar.apply_schedule(self.current_schedule)

    # =====================================================
    # EMPLOYEES
    # =====================================================
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
        self.load_month()

    def on_update_employee(self, data):
        self.client.update_employee(data["id"], data)
        self.employees = self.client.get_employees()
        self.load_month()

    def on_delete_employee(self, emp_id):
        self.client.delete_employee(emp_id)
        self.employees = self.client.get_employees()
        self.load_month()
