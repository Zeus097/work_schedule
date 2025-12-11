from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QMenu, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction


class CalendarWidget(QWidget):
    """
    Визуален календар:

    [име] [ [бутон ден1] [бутон ден2] ... ]
    """

    cell_clicked = pyqtSignal(int, str)  # day, "Employee:ShiftCode"

    BUTTON_SIZE = 34       # размер на клетките (квадрат)
    NAME_COL_WIDTH = 180   # ширина на колоната с името

    def __init__(self, parent=None):
        super().__init__(parent)

        self.root_layout = QVBoxLayout()
        self.root_layout.setContentsMargins(10, 10, 10, 10)
        self.root_layout.setSpacing(4)
        self.setLayout(self.root_layout)

        # целият widget да НЕ се разтяга произволно
        self.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed
        )

        self.day_buttons = {}  # (row_idx, day_idx) -> QPushButton
        self.days = []
        self.employees = []

    # ---------------------------------------------------
    def clear(self):
        while self.root_layout.count():
            item = self.root_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.day_buttons.clear()
        self.days = []
        self.employees = []

    # ---------------------------------------------------
    def build(self, schedule_data):
        """
        schedule_data = {
            "employees": ["John", "Maria"],
            "days": [1..31],
            "schedule": {
                "John": {"1": "Д", "2": "Н", ...},
                "Maria": {...}
            }
        }
        """
        self.clear()

        self.employees = schedule_data["employees"]
        self.days = schedule_data["days"]
        schedule = schedule_data["schedule"]

        # ---------- HEADER: days ----------
        header_layout = QHBoxLayout()
        header_layout.setSpacing(2)

        # празно място за колоната с имена
        name_spacer = QLabel("")
        name_spacer.setFixedWidth(self.NAME_COL_WIDTH)
        header_layout.addWidget(name_spacer)

        for day in self.days:
            lbl = QLabel(str(day))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedSize(self.BUTTON_SIZE, self.BUTTON_SIZE)
            lbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            header_layout.addWidget(lbl)

        self.root_layout.addLayout(header_layout)

        # ---------- ROWS: employees ----------
        for row_idx, emp in enumerate(self.employees):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(2)

            # име вляво, винаги на едно ниво с клетките
            name_lbl = QLabel(emp)
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            name_lbl.setFixedSize(self.NAME_COL_WIDTH, self.BUTTON_SIZE)
            name_lbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            row_layout.addWidget(name_lbl)

            emp_schedule = schedule.get(emp, {})

            for col_idx, day in enumerate(self.days):
                shift_value = emp_schedule.get(str(day), "")

                btn = QPushButton(shift_value)
                btn.setFixedSize(self.BUTTON_SIZE, self.BUTTON_SIZE)
                btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

                btn.clicked.connect(
                    lambda _, d=day, e=emp: self.on_cell_click(d, e)
                )

                row_layout.addWidget(btn)
                self.day_buttons[(row_idx, col_idx)] = btn

            self.root_layout.addLayout(row_layout)

        # ---------- фиксираме общия размер, за да не се раздува ----------
        total_width = self.NAME_COL_WIDTH + len(self.days) * (self.BUTTON_SIZE + 2) + 20
        total_height = (1 + len(self.employees)) * (self.BUTTON_SIZE + 4) + 20

        self.setMinimumSize(total_width, total_height)
        self.setMaximumSize(total_width, total_height)

    # ---------------------------------------------------
    def on_cell_click(self, day, employee):
        menu = QMenu(self)

        for code in ["", "Д", "Н", "П", "В"]:
            label = code if code else "—"
            action = QAction(label, self)

            action.triggered.connect(
                lambda _, d=day, e=employee, c=code:
                    self.cell_clicked.emit(d, f"{e}:{c}")
            )

            menu.addAction(action)

        menu.exec(self.mapToGlobal(self.cursor().pos()))
