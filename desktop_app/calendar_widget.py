from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QMenu, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QMouseEvent


class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class CalendarWidget(QWidget):
    cell_clicked = pyqtSignal(int, str)

    BUTTON_SIZE = 34
    NAME_COL_WIDTH = 180

    def __init__(self, parent=None):
        super().__init__(parent)

        self.root_layout = QVBoxLayout()
        self.root_layout.setContentsMargins(10, 10, 10, 10)
        self.root_layout.setSpacing(4)
        self.setLayout(self.root_layout)

        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

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
        self.days = []
        self.employees = []

    def setup(self, employees, days, schedule, weekends, holidays):
        self.clear()
        self.employees = employees
        self.days = days
        self.weekends = weekends
        self.holidays = holidays

        header_layout = QHBoxLayout()
        header_layout.setSpacing(2)

        name_spacer = QLabel("")
        name_spacer.setFixedWidth(self.NAME_COL_WIDTH)
        header_layout.addWidget(name_spacer)

        for day in self.days:
            lbl = QLabel(str(day))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedSize(self.BUTTON_SIZE, self.BUTTON_SIZE)
            lbl.setStyleSheet("color: white;")
            header_layout.addWidget(lbl)

        self.root_layout.addLayout(header_layout)

        for row_idx, emp in enumerate(self.employees):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(2)

            name_lbl = QLabel(emp)
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            name_lbl.setFixedSize(self.NAME_COL_WIDTH, self.BUTTON_SIZE)
            name_lbl.setStyleSheet("color: white;")
            row_layout.addWidget(name_lbl)

            emp_schedule = schedule.get(emp, {})

            for col_idx, day in enumerate(self.days):
                shift_value = emp_schedule.get(str(day), "")

                cell = ClickableLabel(shift_value)
                cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setFixedSize(self.BUTTON_SIZE, self.BUTTON_SIZE)

                if day in self.holidays:
                    cell.setStyleSheet(
                        "background-color: #add8ff; border: 1px solid #6aa0d6; color: black;"
                    )
                elif day in self.weekends:
                    cell.setStyleSheet(
                        "background-color: #ff6b6b; border: 1px solid #a83232; color: black;"
                    )
                else:
                    cell.setStyleSheet(
                        "background-color: #3a3a3a; border: 1px solid #555; color: white;"
                    )

                cell.clicked.connect(
                    lambda _, d=day, e=emp: self.on_cell_click(d, e)
                )

                row_layout.addWidget(cell)
                self.day_cells[(row_idx, col_idx)] = cell

            self.root_layout.addLayout(row_layout)

        total_width = self.NAME_COL_WIDTH + len(self.days) * (self.BUTTON_SIZE + 2) + 40
        total_height = (len(self.employees) + 1) * (self.BUTTON_SIZE + 6) + 40

        self.setMinimumSize(total_width, total_height)

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



