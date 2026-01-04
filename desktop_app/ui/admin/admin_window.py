from datetime import date
import calendar

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QRadioButton,
    QButtonGroup,
    QMessageBox
)
from PyQt6.QtCore import Qt

from desktop_app.msgbox import warning, error
from scheduler.logic.cycle_state import save_last_cycle_state
from scheduler.logic.generator.generator import CYCLE, CYCLE_LEN


ALLOWED_SHIFTS = ["", "Д", "В", "Н", "А", "О", "Б"]


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


class AdminWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()

        self.client = main_window.client
        self.main_window = main_window

        self.setWindowTitle("Администраторски панел")
        self.resize(620, 420)

        self.current_schedule = {}
        self.days_in_month = 0

        self.admin_group = QButtonGroup(self)
        self.admin_group.setExclusive(True)

        self.build_ui()


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
        self.table.setHorizontalHeaderLabels(
            ["Админ", "Служител", "Последна работна смяна"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.preview_btn = QPushButton("Преглед (зареди данните)")
        self.preview_btn.clicked.connect(self.load_data)
        layout.addWidget(self.preview_btn)

        self.lock_btn = QPushButton("Запис (заключи месеца)")
        self.lock_btn.clicked.connect(self.confirm_and_lock)
        layout.addWidget(self.lock_btn)


    def load_data(self):
        if not self.main_window.current_schedule:
            warning(self, "Няма данни", "Първо зареди месец от главния екран.")
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


    def accept_as_start(self):
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
            data = self.client.get_schedule(year, month)
            schedule = data["schedule"]
            admin_id = data.get("month_admin_id")

            last_day = date(year, month, calendar.monthrange(year, month)[1])

            state = {}

            for emp_id, days in schedule.items():
                if str(emp_id) == str(admin_id):
                    continue

                last_shift = None
                for day in sorted(days.keys(), key=int):
                    if days[day] in ("Д", "Н", "В"):
                        last_shift = days[day]

                if last_shift is None:
                    cycle_index = 0
                else:
                    cycle_index = max(
                        i for i, s in enumerate(CYCLE) if s == last_shift
                    ) + 1

                state[str(emp_id)] = {
                    "cycle_index": cycle_index % CYCLE_LEN
                }

            save_last_cycle_state(state, last_day)
            self.main_window.load_month()

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


