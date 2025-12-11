from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QSizePolicy
)
from PyQt6.QtCore import Qt
import calendar


class CalendarWidget(QWidget):
    def __init__(self, year, month, parent=None):
        super().__init__(parent)

        self.year = year
        self.month = month

        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.build_calendar()

    def build_calendar(self):
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()


        week_days = ["Пон", "Вт", "Ср", "Чет", "Пет", "Съб", "Нед"]

        for col, day in enumerate(week_days):
            label = QLabel(day)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-weight: bold; color: white;")
            self.layout.addWidget(label, 0, col)


        cal = calendar.monthcalendar(self.year, self.month)

        for row_idx, week in enumerate(cal, start=1):
            for col_idx, day in enumerate(week):

                if day == 0:
                    cell = QLabel("")
                else:
                    cell = QLabel(str(day))

                cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setSizePolicy(QSizePolicy.Policy.Expanding,
                                   QSizePolicy.Policy.Expanding)


                cell.setStyleSheet("""
                    background: white;
                    color: black;
                    border: 1px solid #ccc;
                    padding: 4px;
                """)


                if col_idx >= 5:
                    cell.setStyleSheet("""
                        background: #444;
                        color: red;
                        border: 1px solid #ccc;
                        padding: 4px;
                        font-weight: bold;
                    """)

                self.layout.addWidget(cell, row_idx, col_idx)


