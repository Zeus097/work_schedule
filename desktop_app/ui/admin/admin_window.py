from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QRadioButton,
    QButtonGroup, QMessageBox
)
from PyQt6.QtCore import Qt

from desktop_app.api_client import APIClient
from desktop_app.msgbox import question, warning, error, info



ALLOWED_SHIFTS = ["", "Д", "В", "Н", "А", "О", "Б"]


def _get_employee_name_map(self) -> dict:
    return {
        str(e["id"]): e["full_name"]
        for e in self.client.get_employees()
    }


def extract_last_shifts(schedule: dict, days_in_month: int) -> dict:
    result = {}
    for emp_id, days in schedule.items():
        for day in range(days_in_month, 0, -1):
            shift = days.get(str(day), days.get(day))
            if shift and str(shift).strip():
                result[str(emp_id)] = str(shift).strip()
                break
        else:
            result[str(emp_id)] = ""
    return result


def next_year_month(year: int, month: int) -> tuple[int, int]:
    if month == 12:
        return year + 1, 1
    return year, month + 1


class AdminWindow(QWidget):
    """
       Administrative panel for finalizing a monthly schedule.

       Allows selecting a single administrator, previewing last shifts per employee,
       locking the current month, validating coverage constraints, and preparing
       the next month. Also supports accepting the current month as a new generation
       baseline for future schedules.
       Relies on the main window for the active year/month and schedule data,
       and communicates with the backend via APIClient.
    """

    def __init__(self, main_window):
        """
            Initializes the admin window and binds it to the main application window.
            Sets up API access, stores a reference to the main window,
            initializes internal state, and builds the UI.
        """

        super().__init__()

        self.client = APIClient()
        self.main_window = main_window

        self.setWindowTitle("Администраторски панел")
        self.resize(620, 420)

        self.current_schedule = {}
        self.days_in_month = 0

        self.admin_group = QButtonGroup(self)
        self.admin_group.setExclusive(True)

        self.build_ui()


    def build_ui(self):
        """
            Constructs the admin panel UI layout and widgets.
            Creates labels, table, and action buttons, and connects
            user interactions to their corresponding handlers.
        """

        layout = QVBoxLayout(self)

        title = QLabel("Администрация")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        desc = QLabel(
            "Избери администратор.\nПоследната смяна е информативна и идва от графика."
            "Изборът на администратор важи за следващите месеци."
        )
        layout.addWidget(desc)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Админ", "Служител", "Последна работна смяна"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.preview_btn = QPushButton("Преглед (зареди данните)")
        self.preview_btn.clicked.connect(self.load_data)
        layout.addWidget(self.preview_btn)

        self.lock_btn = QPushButton("Запис (заключи месеца)")
        self.lock_btn.clicked.connect(self.confirm_and_lock)
        layout.addWidget(self.lock_btn)

        self.accept_btn = QPushButton("♻️ Приеми текущия месец като начало")
        self.accept_btn.clicked.connect(self.accept_as_start)
        layout.addWidget(self.accept_btn)


    def load_data(self):
        """
           Loads schedule data from the main window into the admin table.
           Derives the number of days in the month, extracts each employee’s
           last worked shift, populates the table, and resets admin selection.
        """

        if not self.main_window.current_schedule:
            warning(
                self,
                "Няма данни",
                "Първо зареди месец от главния екран."
            )
            return

        self.current_schedule = self.main_window.current_schedule

        all_days = set()
        for emp_days in self.current_schedule.values():
            for k in emp_days.keys():
                try:
                    all_days.add(int(k))
                except Exception:
                    pass

        self.days_in_month = max(all_days) if all_days else 0
        last_shifts = extract_last_shifts(self.current_schedule, self.days_in_month)

        employees = {
            str(e["id"]): e["full_name"]
            for e in self.client.get_employees()
        }

        self.table.setRowCount(0)
        self.admin_group = QButtonGroup(self)
        self.admin_group.setExclusive(True)

        for emp_id, full_name in employees.items():
            row = self.table.rowCount()
            self.table.insertRow(row)


            radio = QRadioButton()
            self.admin_group.addButton(radio)
            self.table.setCellWidget(row, 0, radio)


            name_item = QTableWidgetItem(full_name)
            name_item.setData(Qt.ItemDataRole.UserRole, emp_id)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, name_item)


            last_shift = last_shifts.get(emp_id, "")

            item = QTableWidgetItem(last_shift if last_shift else "—")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.table.setItem(row, 2, item)


    def _get_selected_admin(self) -> str | None:
        """
            Returns employee_id to the choosen administrator.
        """

        for row, btn in enumerate(self.admin_group.buttons()):
            if btn.isChecked():
                item = self.table.item(row, 1)
                return str(item.data(Qt.ItemDataRole.UserRole))
        return None


    def confirm_and_lock(self):
        if self.table.rowCount() == 0:
            warning(self, "Няма данни", "Първо направи преглед.")
            return

        admin_id = self._get_selected_admin()
        if not admin_id:
            warning(self, "Липсва администратор", "Избери администратор.")
            return

        reply = QMessageBox.question(
            self,
            "Потвърждение",
            "Сигурен ли си?\nСлед заключване графикът не може да се променя.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        year = int(self.main_window.current_year)
        month = int(self.main_window.current_month)

        try:
            self.client.set_month_admin(year, month, int(admin_id))
            result = self.client.lock_month(year, month)

        except Exception as e:
            error(self, "Грешка", str(e))
            return

        if not result.get("ok"):
            QMessageBox.warning(
                self,
                "Неуспешно",
                result.get("message", "Месецът не може да бъде заключен.")
            )
            return

        QMessageBox.information(self, "Успешно", "Графикът беше успешно заключен.")

        self.main_window.load_month()
        self.close()


    def _summarize_lock_errors(self, errors: list[dict]) -> str:
        """
            Aggregates and formats lock validation errors for user display.
            Groups errors by employee (one per employee), converts employee IDs
            to names, and produces a concise, human-readable summary with hints.
        """

        id_to_name = {
            str(e["id"]): e["full_name"]
            for e in self.client.get_employees()
        }

        first_error_per_employee = {}

        for err in errors:
            raw_employee = err.get("employee")
            employee = (
                id_to_name.get(str(raw_employee), raw_employee)
                if raw_employee else "Покритие за деня"
            )

            if employee not in first_error_per_employee:
                first_error_per_employee[employee] = err

        lines = []

        for employee, err in first_error_per_employee.items():
            day = err.get("day")
            message = err.get("message", "")
            hint = err.get("hint", "")

            if employee == "Покритие за деня":
                lines.append(
                    f"⚠️ Ден {day}: {message}"
                )
            else:
                lines.append(
                    f"👤 {employee} – ден {day}: {message}"
                )

            if hint:
                lines.append(f"   → {hint}")

        lines.append(
            "\nℹ️ Натисни „Прекрати заключването“, за да се върнеш и коригираш смените."
        )

        return "\n".join(lines)


    def _show_lock_errors_dialog(self, summary_text: str):
        """
            Displays a warning dialog with lock validation error details.
            Shows a summarized explanation of why the month cannot be locked
            and instructs the user to return and correct the schedule.
        """

        dialog = QMessageBox(self)
        dialog.setWindowTitle("Месецът не може да бъде заключен")
        dialog.setIcon(QMessageBox.Icon.Warning)

        dialog.setText("Има проблеми в графика:")
        dialog.setInformativeText(summary_text)

        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        dialog.button(QMessageBox.StandardButton.Ok).setText(
            "Прекрати заключването и се върни за корекции"
        )

        dialog.exec()


    def accept_as_start(self):
        """
            Marks the current month as the new generation baseline.
            Confirms user intent and updates backend state so future schedules
            are generated starting from this month.
        """

        reply = QMessageBox.question(
            self,
            "Потвърждение",
            "Сигурен ли си?\nТекущият месец ще бъде използван като начало за следващия.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        year = int(self.main_window.current_year)
        month = int(self.main_window.current_month)

        try:
            self.client.accept_month_as_start(year, month)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Грешка",
                f"Операцията не беше успешна:\n{e}"
            )
            return

        QMessageBox.information(
            self,
            "Готово",
            "Текущият месец е приет като ново начало.\n"
            "Следващите месеци ще се генерират от него."
        )


    def update_ui_state(self):
        self.reload_month()
        self.lock_btn.setDisabled(True)
        self.accept_btn.setDisabled(True)



