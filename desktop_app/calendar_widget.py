from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QMenu, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QMouseEvent


SHIFT_COLORS = {
    "Д": "background-color: #4da6ff; border: 1px solid #1f5f99; color: black;",
    "Н": "background-color: #b36bff; border: 1px solid #6b2fb3; color: black;",
    "В": "background-color: #ff6b6b; border: 1px solid #a83232; color: black;",
    "П": "background-color: #63d471; border: 1px solid #2b8a3e; color: black;",
    "":  "background-color: #3a3a3a; border: 1px solid #555; color: white;",
}


class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def set_shift(self, value: str, weekend=False, holiday=False):
        self.setText(value)

        if value == "":
            if holiday:
                self.setStyleSheet(
                    "background-color: #add8ff; border: 1px solid #6aa0d6; color: black;"
                )
                return
            if weekend:
                self.setStyleSheet(
                    "background-color: #ff9b9b; border: 1px solid #a83232; color: black;"
                )
                return

        self.setStyleSheet(SHIFT_COLORS.get(value, SHIFT_COLORS[""]))

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class CalendarWidget(QWidget):
    cell_clicked = pyqtSignal(int, str)  # day, "Employee:Shift"

    BUTTON_SIZE = 34
    NAME_COL_WIDTH = 180

    def __init__(self, parent=None):
        super().__init__(parent)

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(10, 10, 10, 10)
        self.root_layout.setSpacing(2)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.day_cells = {}
        self.days = []
        self.weekends = []
        self.holidays = []
        self.employees = []

    def clear(self):
        while self.root_layout.count():
            item = self.root_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.day_cells.clear()

    def setup(self, employees, days, schedule, weekends, holidays):
        self.clear()

        self.employees = employees
        self.days = days
        self.weekends = weekends
        self.holidays = holidays

        # HEADER
        header = QHBoxLayout()
        header.setSpacing(2)

        spacer = QLabel("")
        spacer.setFixedWidth(self.NAME_COL_WIDTH)
        header.addWidget(spacer)

        for day in days:
            lbl = QLabel(str(day))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedSize(self.BUTTON_SIZE, self.BUTTON_SIZE)
            lbl.setStyleSheet("color: white;")
            header.addWidget(lbl)

        self.root_layout.addLayout(header)

        # ROWS
        for emp in employees:
            row = QHBoxLayout()
            row.setSpacing(2)

            name_lbl = QLabel(emp)
            name_lbl.setFixedSize(self.NAME_COL_WIDTH, self.BUTTON_SIZE)
            name_lbl.setStyleSheet("color: white; padding-left: 6px;")
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            row.addWidget(name_lbl)

            emp_schedule = schedule.get(emp, {})

            for day in days:
                shift = emp_schedule.get(day, "")

                cell = ClickableLabel(shift)
                cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setFixedSize(self.BUTTON_SIZE, self.BUTTON_SIZE)

                cell.set_shift(
                    shift,
                    weekend=(day in weekends),
                    holiday=(day in holidays),
                )

                cell.clicked.connect(self._make_cell_click_handler(emp, day))

                self.day_cells[(emp, day)] = cell
                row.addWidget(cell)

            self.root_layout.addLayout(row)

        self.adjustSize()
        self.updateGeometry()

    def _make_cell_click_handler(self, employee, day):
        def handler():
            self._open_shift_menu(employee, day)
        return handler

    def _open_shift_menu(self, employee, day):
        cell = self.day_cells[(employee, day)]
        menu = QMenu(self)

        for code, label in {
            "": "—",
            "Д": "Дневна",
            "Н": "Нощна",
            "В": "Втора",
            "П": "Админ",
        }.items():
            action = QAction(label, self)
            action.triggered.connect(
                self._make_shift_handler(employee, day, code)
            )
            menu.addAction(action)

        menu.exec(cell.mapToGlobal(cell.rect().bottomLeft()))

    def _make_shift_handler(self, employee, day, shift_code):
        def handler():
            cell = self.day_cells[(employee, day)]

            cell.set_shift(
                shift_code,
                weekend=(day in self.weekends),
                holiday=(day in self.holidays),
            )

            # 🔧 FIX 3 — NO reload, ONLY notify
            self.cell_clicked.emit(day, f"{employee}:{shift_code}")

        return handler

    # 🔧 FIX 2 — TUP apply_schedule
    def apply_schedule(self, schedule: dict):
        for emp, days in schedule.items():
            for day, shift in days.items():
                cell = self.day_cells.get((emp, day))
                if cell:
                    cell.set_shift(
                        shift,
                        weekend=(day in self.weekends),
                        holiday=(day in self.holidays),
                    )








