import time
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QComboBox, QLabel, QGridLayout, QDialog, QScrollArea,
    QFileDialog, QMessageBox, QHBoxLayout
)
from PyQt6.QtCore import Qt

from api_client import APIClient
from calendar_widget import CalendarWidget
from employees_widget import EmployeesWidget
from desktop_app.ui.admin.admin_window import AdminWindow
from export.excel_export import export_schedule_to_excel


# ===== PATHS =====
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
LAST_STATE_FILE = DATA_DIR / "last_state.json"


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
        years = self.client.get_years() or [2025, 2026, 2027]
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

        admin_btn = QPushButton("Администрация")
        admin_btn.clicked.connect(self.open_admin)
        grid.addWidget(admin_btn, 2, 1)

        main_layout.addLayout(grid)

        # -------- EXPORT BUTTON --------
        export_layout = QHBoxLayout()
        export_layout.addStretch()

        export_btn = QPushButton("Експорт в Excel")
        export_btn.clicked.connect(self.export_to_excel)
        export_btn.setStyleSheet("""
        QPushButton {
            background-color: #e6e6e6;
            color: #000000;
            border: 1px solid #555;
            padding: 6px 16px;
            font-weight: bold;
        }
        QPushButton:hover { background-color: #dcdcdc; }
        QPushButton:pressed { background-color: #cfcfcf; }
        """)
        export_layout.addWidget(export_btn)
        main_layout.addLayout(export_layout)

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
    def init_defaults(self):
        if self.year_select.count():
            self.year_select.setCurrentIndex(0)
        if self.month_select.count():
            self.month_select.setCurrentIndex(11)
        self.load_month()

    # =====================================================
    def load_month(self):
        year = int(self.year_select.currentText())
        month = int(self.month_select.currentText())

        self.current_year = year
        self.current_month = month
        self.month_title.setText(MONTH_NAMES[month])

        month_info = self.client.get_month_info(year, month)
        days = list(range(1, month_info["days"] + 1))

        try:
            data = self.client.get_schedule(year, month)
        except FileNotFoundError:
            self.client.generate_month(year, month)
            time.sleep(0.1)
            data = self.client.get_schedule(year, month)

        self.current_schedule = data.get("schedule", {})
        if not self.current_schedule:
            return

        self.calendar = CalendarWidget()
        self.calendar.setup(
            list(self.current_schedule.keys()),
            days,
            self.current_schedule,
            month_info.get("weekends", []),
            month_info.get("holidays", [])
        )
        self.scroll.setWidget(self.calendar)

    # =====================================================
    # ADMIN
    # =====================================================
    def open_admin(self):
        self.admin_window = AdminWindow(self)
        self.admin_window.current_schedule = self.current_schedule
        self.admin_window.days_in_month = len(self.calendar.days)
        self.admin_window.show()

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
        try:
            self.client.add_employee(data)
        except Exception:
            pass
        self._refresh_after_employee_change()

    def on_update_employee(self, data):
        try:
            self.client.update_employee(data["id"], data)
        except Exception:
            pass
        self._refresh_after_employee_change()

    def on_delete_employee(self, emp_id):
        try:
            self.client.delete_employee(emp_id)
        except Exception:
            pass
        self._refresh_after_employee_change()

    def _refresh_after_employee_change(self):
        self.employees = self.client.get_employees()
        if self.current_year and self.current_month:
            self.load_month()

    # =====================================================
    # EXPORT
    # =====================================================
    def export_to_excel(self):
        if not LAST_STATE_FILE.exists():
            QMessageBox.warning(
                self,
                "Експортът е блокиран",
                "Първо трябва да заключиш месеца.\n\n"
                "Администрация → „Запис (заключи месеца)“"
            )
            return

        if not self.current_schedule:
            QMessageBox.warning(
                self,
                "Няма данни",
                "Няма зареден график за експорт."
            )
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Запази графика",
            f"График_{self.current_year}_{self.current_month}.xlsx",
            "Excel файлове (*.xlsx)"
        )
        if not filename:
            return

        try:
            month_info = self.client.get_month_info(self.current_year, self.current_month)

            export_schedule_to_excel(
                filename=filename,
                title="КАНТАР",
                month_label=f"{MONTH_NAMES[self.current_month]} {self.current_year} г.",
                employees=list(self.current_schedule.keys()),
                days=list(range(1, month_info["days"] + 1)),
                schedule=self.current_schedule,
                weekends=month_info.get("weekends", []),
                holidays=month_info.get("holidays", []),
            )

            QMessageBox.information(
                self,
                "Успешен експорт",
                "Excel файлът е създаден успешно и може да се редактира."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Грешка при експорт",
                f"Възникна грешка при създаване на файла:\n{e}"
            )



