from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QPushButton, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction


class CalendarWidget(QWidget):

    cell_clicked = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.day_buttons = {}  # (row, col): QPushButton

    # ---------------------------------------------------
    def clear(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.day_buttons.clear()

    # ---------------------------------------------------
    def build(self, schedule_data):
        """
        schedule_data = {
            "employees": [ "John", "Maria" ],
            "days": [1..31],
            "schedule": { "John": {"1":"Д", "2":"Н"} ... }
        }
        """

        self.clear()

        employees = schedule_data["employees"]
        days = schedule_data["days"]
        schedule = schedule_data["schedule"]

        # ----- Header row with days -----
        for col, day in enumerate(days):
            lbl = QLabel(str(day))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout.addWidget(lbl, 0, col + 1)

        # ----- Rows: employees -----
        for row, emp in enumerate(employees, start=1):

            emp_lbl = QLabel(emp)
            self.layout.addWidget(emp_lbl, row, 0)

            # Cells for each day
            for col, day in enumerate(days):
                shift_value = schedule.get(emp, {}).get(str(day), "")

                btn = QPushButton(shift_value)
                btn.setProperty("day", day)
                btn.setProperty("employee", emp)

                # bind ALL values correctly
                btn.clicked.connect(
                    lambda _, d=day, e=emp: self.on_cell_click(d, e)
                )

                self.layout.addWidget(btn, row, col + 1)
                self.day_buttons[(row, col)] = btn

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

        # showing the menu
        menu.exec(self.mapToGlobal(self.cursor().pos()))
