from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QLabel, QGridLayout, QDialog, QScrollArea,
    QFileDialog, QPushButton
)
from PyQt6.QtCore import Qt

from desktop_app.services.app_service import AppService
from desktop_app.calendar_widget import CalendarWidget
from desktop_app.employees_widget import EmployeesWidget
from desktop_app.ui.admin.admin_window import AdminWindow
from desktop_app.export.excel_export import export_schedule_to_excel
from desktop_app.msgbox import question, error, show_info, warning

MONTH_NAMES = {
    1: "Януари", 2: "Февруари", 3: "Март",
    4: "Април", 5: "Май", 6: "Юни",
    7: "Юли", 8: "Август", 9: "Септември",
    10: "Октомври", 11: "Ноември", 12: "Декември"
}


class MainWindow(QMainWindow):
    """
        Main application window for the work schedule manager.
            - Coordinates year and month selection
            - Controls schedule generation and regeneration flow
            - Manages manual override mode and locking workflow
            - Provides access to employee and monthly admin management
            - Acts as the central UI controller between widgets and the backend API
            - Handles validation, user feedback, and export operations
    """

    def __init__(self):
        super().__init__()

        self.client = AppService()
        self.setWindowTitle("Мениджър на работни графици")

        self.current_year = None
        self.current_month = None
        self.current_schedule = {}
        self.is_locked = False
        self.override_enabled = False
        self._generation_error_shown = False

        self._ui_ready = False

        self.calendar_widget = CalendarWidget()

        self.build_ui()

        self._backend_ready = False
        self.init_defaults()

        self._backend_ready = True
        self.safe_load_month()


    def build_ui(self):
        """
            Builds the main application UI layout.
            Creates month/year selectors, action buttons, status indicators,
            calendar container, and export controls, and wires all UI events.
        """

        main_layout = QVBoxLayout()
        grid = QGridLayout()

        grid.addWidget(QLabel("Година:"), 0, 0)
        grid.addWidget(QLabel("Месец:"), 0, 1)

        self.validation_label = QLabel("")
        self.validation_label.setStyleSheet("color: red; font-weight: bold;")
        self.validation_label.hide()
        main_layout.addWidget(self.validation_label)

        self.year_select = QComboBox()
        now_year = datetime.now().year
        for y in (now_year - 1, now_year, now_year + 1):
            self.year_select.addItem(str(y), y)
        grid.addWidget(self.year_select, 1, 0)

        self.month_select = QComboBox()
        for m in range(1, 13):
            self.month_select.addItem(MONTH_NAMES[m], m)
        grid.addWidget(self.month_select, 1, 1)

        self.employees_btn = QPushButton("Служители")
        self.employees_btn.clicked.connect(self.open_employees)
        grid.addWidget(self.employees_btn, 2, 0)

        self.admin_btn = QPushButton("Администрация")
        self.admin_btn.clicked.connect(self.open_admin)
        grid.addWidget(self.admin_btn, 2, 1)

        self.lock_status_label = QLabel("")
        self.lock_status_label.setStyleSheet("font-weight: bold;")
        grid.addWidget(self.lock_status_label, 2, 2)

        main_layout.addLayout(grid)
        tools = QHBoxLayout()
        left_tools = QVBoxLayout()

        self.override_btn = QPushButton("✏️ Ръчни корекции")
        self.override_btn.setCheckable(True)
        self.override_btn.clicked.connect(self.toggle_override)
        left_tools.addWidget(self.override_btn)

        self.clear_btn = QPushButton("🧹 Изчисти графика")
        self.clear_btn.clicked.connect(self.clear_schedule)
        self.clear_btn.setEnabled(False)
        left_tools.addWidget(self.clear_btn)

        left_tools.addStretch()
        tools.addLayout(left_tools)

        tools.addStretch()
        main_layout.addLayout(tools)

        export_layout = QHBoxLayout()
        export_layout.addStretch()
        export_btn = QPushButton("Експорт в Excel")
        export_btn.clicked.connect(self.export_to_excel)
        export_layout.addWidget(export_btn)
        main_layout.addLayout(export_layout)

        self.section_title = QLabel("КАНТАР")
        self.section_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.section_title.setStyleSheet("font-size: 22px; font-weight: bold;")
        main_layout.addWidget(self.section_title)

        self.month_title = QLabel("")
        self.month_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.month_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(self.month_title)

        self.validation_label = QLabel("")
        self.validation_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.validation_label.setStyleSheet("color: red; font-weight: bold;")
        self.validation_label.hide()
        main_layout.addWidget(self.validation_label)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.calendar_widget)
        main_layout.addWidget(self.scroll)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.year_select.currentIndexChanged.connect(self.safe_load_month)
        self.month_select.currentIndexChanged.connect(self.safe_load_month)

        self.generate_btn = QPushButton("⚙️ Генерирай месец")
        self.generate_btn.clicked.connect(self.generate_month)
        self.generate_btn.setEnabled(False)
        tools.addWidget(self.generate_btn)


    def init_defaults(self):
        now = datetime.now()

        self.year_select.setCurrentIndex(
            self.year_select.findData(now.year)
        )
        self.month_select.setCurrentIndex(
            self.month_select.findData(now.month)
        )

        self._ui_ready = True
        self.load_month()


    def load_month(self):
        """
            Loads or initializes the selected month.
            Safe against backend-not-ready state.
        """

        if not self._ui_ready:
            return

        year = self.year_select.currentData()
        month = self.month_select.currentData()

        if year is None or month is None:
            return

        year = int(year)
        month = int(month)

        try:
            data = self.client.get_schedule(year, month)

        except FileNotFoundError:
            self._backend_ready = True

            self.current_year = year
            self.current_month = month
            self.current_schedule = {}
            self.is_locked = False

            self.calendar_widget.clear()

            self.month_title.setText(f"{MONTH_NAMES[month]} {year} г.")
            self.lock_status_label.setText("🆕 Нов месец (не е генериран)")
            self.lock_status_label.setStyleSheet("color: orange; font-weight: bold;")

            self.override_btn.setEnabled(False)

            self.employees_btn.setEnabled(True)
            self.admin_btn.setEnabled(True)

            self._update_lock_ui()

            self.validate_before_generate()
            return


        except Exception:
            return

        self._backend_ready = True

        self.current_year = year
        self.current_month = month
        self.current_schedule = data["schedule"]
        self.is_locked = bool(data.get("ui_locked", False))

        # 🔒 Generator freeze
        if data.get("generator_locked"):
            reason = data.get("freeze_reason")

            if reason == "MIN_EMPLOYEES":
                msg = "❗ Минимум 4 служители + 1 администратор са нужни за генериране."
            elif reason == "NO_ADMIN":
                msg = "❗ Няма избран администратор за текущия месец."
            else:
                msg = "ℹ️ Месецът вече е генериран."

            self.lock_status_label.setText(msg)
            self.lock_status_label.setStyleSheet(
                "color: red; font-weight: bold;"
            )

            self.generate_btn.setEnabled(False)

            self.override_btn.setEnabled(not self.is_locked)
            self.clear_btn.setEnabled(not self.is_locked)
            self.employees_btn.setEnabled(not self.is_locked)
            self.admin_btn.setEnabled(not self.is_locked)

            self.calendar_widget.set_context(self.client, year, month)
            self.calendar_widget.set_read_only(self.is_locked)
            self.calendar_widget.load(data)

            self.month_title.setText(f"{MONTH_NAMES[month]} {year} г.")


        self.override_enabled = False
        self.override_btn.setChecked(False)
        self.override_btn.setText("✏️ Ръчни корекции")

        self.calendar_widget.set_context(self.client, year, month)
        self.calendar_widget.set_read_only(self.is_locked)
        self.calendar_widget.set_override_mode(False)
        self.calendar_widget.load(data)

        self._update_lock_ui()
        self.month_title.setText(f"{MONTH_NAMES[month]} {year} г.")

        has_any_shift = any(
            (str(shift).strip() for emp_days in self.current_schedule.values() for shift in emp_days.values())
        ) if self.current_schedule else False

        self.generate_btn.setEnabled(not self.is_locked and not has_any_shift)
        self.validate_before_generate()


    def toggle_override(self):
        """
            Toggles manual override mode for the current month.
            Enables or disables inline shift editing, reloads the schedule,
            and updates the UI state based on lock and edit mode.
        """

        if not self.current_schedule:
            warning(self, "Няма график", "Месецът няма график за редакция.")
            self.override_btn.setChecked(False)
            return

        if self.is_locked:
            warning(self, "Заключен месец", "Месецът е заключен.")
            self.override_btn.setChecked(False)
            return

        self.override_enabled = self.override_btn.isChecked()
        self.calendar_widget.set_override_mode(self.override_enabled)

        if self.override_enabled:
            data = self.client.get_schedule(self.current_year, self.current_month)
            self.calendar_widget.load(data)
            self.calendar_widget.set_read_only(False)
            self.override_btn.setText("✅ Приключи редакция")
        else:
            self.load_month()
            self.override_btn.setText("✏️ Ръчни корекции")


    def _update_lock_ui(self):
        """
            Updates UI elements based on the month lock state.
            Adjusts status labels and enables or disables actions
            depending on whether the current month is locked.
        """

        if self.is_locked:
            self.lock_status_label.setText("🔒 Месецът е ЗАКЛЮЧЕН")
            self.lock_status_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.lock_status_label.setText("🔓 Месецът е ОТВОРЕН")
            self.lock_status_label.setStyleSheet("color: green; font-weight: bold;")

        self.employees_btn.setEnabled(not self.is_locked)
        self.admin_btn.setEnabled(not self.is_locked)
        self.override_btn.setEnabled(not self.is_locked)

        self.clear_btn.setEnabled(not self.is_locked and bool(self.current_schedule))


    def open_admin(self):
        """
            Opens the administration panel for the current month.
            Prevents access if the month is locked and passes the
            current schedule context to the admin window.
        """

        if self.is_locked:
            show_info(self, "Заключен месец", "Администрацията не е достъпна.")
            return

        if not hasattr(self, "admin_window") or self.admin_window is None:
            self.admin_window = AdminWindow(self)
            self.admin_window.current_schedule = self.current_schedule

        self.admin_window.show()
        self.admin_window.raise_()
        self.admin_window.activateWindow()


    def open_employees(self):
        if self.is_locked:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Управление на служители")
        dialog.setMinimumWidth(720)
        dialog.setMinimumHeight(420)

        layout = QVBoxLayout(dialog)

        widget = EmployeesWidget(
            client=self.client,
            year=self.current_year,
            month=self.current_month
        )
        widget.admin_changed.connect(self.validate_before_generate)
        layout.addWidget(widget)
        dialog.exec()
        self.validate_before_generate()

        if self.current_year and self.current_month:
            try:
                self.client.get_schedule(self.current_year, self.current_month)
                self.load_month()
            except FileNotFoundError:
                pass


    def export_to_excel(self):
        """
            Exports the locked monthly schedule to an Excel file.
            Prompts for a file location, gathers required data,
            and generates a formatted Excel schedule.
        """

        if not self.is_locked:
            warning(self, "Експортът е блокиран", "Първо заключи месеца.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Запази графика",
            f"График_{self.current_year}_{self.current_month}.xlsx",
            "Excel (*.xlsx)"
        )
        if not filename:
            return

        month_info = self.client.get_month_info(self.current_year, self.current_month)
        employees = self.client.get_employees()

        export_schedule_to_excel(
            filename=filename,
            company="КАНТАР",
            department="ТРАКИЯ ГЛАС",
            city="ТЪРГОВИЩЕ",
            month_name=MONTH_NAMES[self.current_month],
            month=self.current_month,
            year=self.current_year,
            employees=employees,
            days=list(range(1, int(month_info["days"]) + 1)),
            schedule=self.current_schedule,
        )

        show_info(self, "Готово", "Excel файлът е създаден.")


    def generate_month(self):
        """
            Triggers generation of the current month’s schedule
            after validating required preconditions in the UI.
        """

        if not self.validate_before_generate():
            return

        employees = self.client.get_employees()
        if len(employees) < 5:
            warning(
                self,
                "Недостатъчен брой служители",
                "За генериране са нужни минимум:\n"
                "• 4 ротационни служители\n"
                "• 1 администратор"
            )

            return

        try:
            data = self.client.get_schedule(self.current_year, self.current_month)
            month_admin_id = data.get("month_admin_id")
        except Exception:
            month_admin_id = None

        if not month_admin_id:
            warning(
                self,
                "Липсва администратор",
                "Избери администратор за текущия месец\n"
                "от меню „Служители“."
            )

            return

        try:
            self.client.generate_month(self.current_year, self.current_month)
        except Exception as e:
            error(self, "Грешка", str(e))
            return

        show_info(self, "Готово", "Месецът е генериран.")
        self.load_month()


    def clear_schedule(self):
        """
            Clears all shifts for the current month.
            Confirms user intent, resets the schedule via the backend,
            and reloads the month in an unlocked state.
        """

        if not question(
                self,
                "Изчистване на графика",
                "Сигурен ли си, че искаш да изчистиш целия график за месеца?\n\n"
                "Всички смени ще бъдат премахнати и месецът ще остане отворен."
        ):
            return

        year = int(self.current_year)
        month = int(self.current_month)

        try:
            self.client.clear_month(year, month)
        except Exception as e:
            error(
                self,
                "Грешка",
                f"Неуспешно изчистване на графика:\n{e}"
            )
            return

        show_info(
            self,
            "Готово",
            "Графикът е изчистен успешно.\n"
            "Можеш да генерираш нов или да въведеш смените ръчно."
        )

        self.load_month()


    def validate_before_generate(self):
        employees = self.client.get_employees()
        admin_id = self.client.get_month_admin(
            self.current_year,
            self.current_month
        )

        if len(employees) < 4:
            self.validation_label.setText(
                "❌ Минимум 4 служители са необходими за генериране на график."
            )
            self.validation_label.show()
            self.generate_btn.setEnabled(False)
            return False

        if not admin_id:
            self.validation_label.setText(
                "❌ Избери администратор за текущия месец."
            )
            self.validation_label.show()
            self.generate_btn.setEnabled(False)
            return False

        self.validation_label.hide()
        self.generate_btn.setEnabled(True)
        return True


    def safe_load_month(self):
        if not self._backend_ready:
            return

        try:
            self.load_month()
        except Exception:
            pass


    def closeEvent(self, event):
        event.accept()


