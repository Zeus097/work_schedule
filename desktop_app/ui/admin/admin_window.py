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


def extract_last_shifts(schedule: dict, days_in_month: int) -> dict:
    """
    schedule е по employee_id:
    { "57": { "1":"Д", "2":"", ...}, ... }
    """
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
            "Избери администратор (само един) и последна смяна за всеки служител.\n"
            "Изборът на администратор важи за следващите месеци."
        )
        layout.addWidget(desc)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Админ", "Служител", "Последна смяна"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.preview_btn = QPushButton("Преглед (зареди данните)")
        self.preview_btn.clicked.connect(self.load_data)
        layout.addWidget(self.preview_btn)

        self.lock_btn = QPushButton("Запис (заключи месеца)")
        self.lock_btn.clicked.connect(self.confirm_and_lock)
        layout.addWidget(self.lock_btn)

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
            combo = QComboBox()
            combo.addItems(ALLOWED_SHIFTS)
            combo.setCurrentText(last_shifts.get(emp_id, ""))
            self.table.setCellWidget(row, 2, combo)

    # =====================================================
    def _collect_last_shifts_from_table(self) -> dict:
        """
        Връща:
        { employee_id: "Д/В/Н/..." }
        """
        result = {}
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 1)
            combo = self.table.cellWidget(row, 2)

            if not name_item:
                continue

            emp_id = name_item.data(Qt.ItemDataRole.UserRole)
            shift = combo.currentText().strip() if isinstance(combo, QComboBox) else ""
            result[str(emp_id)] = shift

        return result

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

        # 1️⃣ Администратор (по ID)
        try:
            # Ако backend очаква "name", а ти пращаш ID -> оправи APIClient.set_admin да праща "id"
            # или направи SetAdminView да приема и "id".
            self.client.set_admin(admin_id)
        except Exception as e:
            QMessageBox.critical(self, "Грешка", f"Неуспешна смяна на админ:\n{e}")
            return

        # 2️⃣ Последни смени (по ID)
        last_shifts = self._collect_last_shifts_from_table()

        # 3️⃣ Заключване
        try:
            self.client.lock_month(year, month, last_shifts=last_shifts)
        except Exception as e:
            QMessageBox.critical(self, "Грешка при заключване", str(e))
            return

        # 4️⃣ AUTO: следващ месец (зареди ако има, иначе генерирай и зареди)
        ny, nm = next_year_month(year, month)

        try:
            self.client.get_schedule(ny, nm)
        except FileNotFoundError:
            try:
                # трябва да имаш това в APIClient -> POST /api/schedule/generate/
                self.client.generate_month(ny, nm)
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Заключено, но без нов месец",
                    f"Месецът е заключен успешно.\n"
                    f"Но следващият месец ({nm:02d}.{ny}) не успя да се генерира:\n{e}"
                )

        # 5️⃣ Превключи UI към следващия месец и зареди
        try:
            self.main_window.year_select.setCurrentText(str(ny))
            self.main_window.month_select.setCurrentIndex(nm - 1)
        except Exception:
            # ако селекторите са различни при теб, поне зареди по текущите стойности
            pass

        QMessageBox.information(self, "Заключено", "Месецът е успешно заключен.")
        self.main_window.load_month()
        self.close()
