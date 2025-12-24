from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QComboBox,
    QRadioButton,
    QButtonGroup
)
from PyQt6.QtCore import Qt

from desktop_app.api_client import APIClient


ALLOWED_SHIFTS = ["", "Д", "В", "Н", "А", "О", "Б"]


def _get_employee_name_map(self) -> dict:
    return {
        str(e["id"]): e["full_name"]
        for e in self.client.get_employees()
    }


def extract_last_shifts(schedule: dict, days_in_month: int) -> dict:
    result = {}
    for emp_id, days in schedule.items():
        # days е dict с ключове "1","2"... или 1,2...
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
    def __init__(self, main_window):
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

    # =====================================================
    def build_ui(self):
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

    # =====================================================
    def load_data(self):
        if not self.main_window.current_schedule:
            QMessageBox.warning(
                self,
                "Няма данни",
                "Първо зареди месец от главния екран."
            )
            return

        self.current_schedule = self.main_window.current_schedule

        # дни в месеца
        all_days = set()
        for emp_days in self.current_schedule.values():
            # emp_days ключовете може да са "1","2"... или 1,2...
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

            # --- Админ радио ---
            radio = QRadioButton()
            self.admin_group.addButton(radio)
            self.table.setCellWidget(row, 0, radio)

            # --- Име (показваме име, пазим ID) ---
            name_item = QTableWidgetItem(full_name)
            name_item.setData(Qt.ItemDataRole.UserRole, emp_id)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, name_item)

            # --- Последна смяна ---
            last_shift = last_shifts.get(emp_id, "")

            item = QTableWidgetItem(last_shift if last_shift else "—")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.table.setItem(row, 2, item)

    # =====================================================
    def _get_selected_admin(self) -> str | None:
        """
        Връща employee_id на избрания администратор
        """
        for row, btn in enumerate(self.admin_group.buttons()):
            if btn.isChecked():
                item = self.table.item(row, 1)
                return str(item.data(Qt.ItemDataRole.UserRole))
        return None

    # =====================================================
    def confirm_and_lock(self):
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "Няма данни", "Първо направи преглед.")
            return

        admin_id = self._get_selected_admin()
        if not admin_id:
            QMessageBox.warning(self, "Липсва админ", "Избери администратор.")
            return

        reply = QMessageBox.question(
            self,
            "Потвърждение",
            "Сигурен ли си?\nСлед заключване графикът не може да се променя.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        year = int(self.main_window.current_year)
        month = int(self.main_window.current_month)


        try:
            self.client.set_admin(admin_id)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Грешка",
                f"Неуспешна смяна на администратор:\n{e}"
            )
            return

        result = self.client.lock_month(year, month)


        if not result.get("ok", True):
            summary = self._summarize_lock_errors(result.get("errors"))
            self._show_lock_errors_dialog(summary)
            return


        ny, nm = next_year_month(year, month)

        try:
            try:
                self.client.get_schedule(ny, nm)
            except FileNotFoundError:
                self.client.generate_month(ny, nm, strict=False)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Заключването е отказано",
                f"Следващият месец ({nm:02d}.{ny}) не може да бъде подготвен.\n\n"
                f"Причина:\n{e}\n\n"
                f"Коригирай текущия месец и опитай отново."
            )



        try:
            self.main_window.year_select.setCurrentText(str(ny))
            self.main_window.month_select.setCurrentIndex(nm - 1)
        except Exception:
            pass

        QMessageBox.information(
            self,
            "Заключено",
            "Месецът е успешно заключен."
        )

        self.main_window.load_month()
        self.close()

    def _summarize_lock_errors(self, errors: list[dict]) -> str:
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
        reply = QMessageBox.question(
            self,
            "Потвърждение",
            "Сигурен ли си?\nТози месец ще стане новото начало за всички следващи графици.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
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


