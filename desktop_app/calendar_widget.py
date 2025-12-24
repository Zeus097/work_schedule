from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QComboBox, QSizePolicy, QHeaderView, QMessageBox
)

SHIFT_OPTIONS = ["", "Д", "В", "Н", "А", "О", "Б"]
COUNT_AS_WORKED: Set[str] = {"Д", "В", "Н", "А", "О", "Б"}

DAY_GREEN = QColor(160, 215, 140)
DAY_RED = QColor(235, 120, 120)
NAME_BG = QColor(210, 210, 210)
GRID_BG = QColor(45, 45, 45)
CELL_BG = QColor(55, 55, 55)
TEXT_LIGHT = QColor(240, 240, 240)
TEXT_DARK = QColor(0, 0, 0)


@dataclass
class EmpRow:
    full_name: str
    emp_id: int
    card_number: str


class CalendarWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.client = None
        self.year: Optional[int] = None
        self.month: Optional[int] = None

        self._read_only = True
        self._override_mode = False

        self._employees: List[EmpRow] = []
        self._schedule: Dict[str, Dict[int, str]] = {}
        self._days: List[int] = []
        self._weekends: Set[int] = set()
        self._holidays: Set[int] = set()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
        self.table.setStyleSheet("QTableWidget { background-color: #2d2d2d; }")

        layout.addWidget(self.table)

        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    # =====================================================
    def set_context(self, client, year: int, month: int):
        self.client = client
        self.year = year
        self.month = month

    def set_read_only(self, read_only: bool):
        self._read_only = read_only
        self._render()

    def set_override_mode(self, enabled: bool):
        self._override_mode = enabled
        self._render()

    # =====================================================
    def load(self, data: dict):
        if not self.client:
            return


        raw = sorted(self.client.get_employees(), key=lambda x: x["full_name"])

        self._employees = [
            EmpRow(
                full_name=e["full_name"],
                emp_id=str(e["id"]),
                card_number=str(e.get("card_number") or "")
            )
            for e in raw
        ]

        valid_ids = {e.emp_id for e in self._employees}


        raw_schedule = data.get("schedule", {}) or {}

        self._schedule = {
            emp_id: days
            for emp_id, days in raw_schedule.items()
            if str(emp_id) in valid_ids
        }


        info = self.client.get_month_info(self.year, self.month)
        self._days = list(range(1, int(info["days"]) + 1))
        self._weekends = set(info.get("weekends", []))
        self._holidays = set(info.get("holidays", []))

        self._render()

    # =====================================================
    def _render(self):
        rows = len(self._employees)
        cols = 3 + len(self._days) + 1

        self.table.clear()
        self.table.setRowCount(rows + 1)
        self.table.setColumnCount(cols)

        headers = ["№", "Бр.", "Служител"] + [str(d) for d in self._days] + ["Служебен №"]
        self.table.setHorizontalHeaderLabels(headers)

        self._paint_day_header()

        for i, emp in enumerate(self._employees):
            r = i + 1

            self._cell(r, 0, str(i + 1), center=True)
            self._cell(r, 1, str(self._count_worked(str(emp.emp_id))), center=True)
            self._cell(r, 2, emp.full_name, bg=NAME_BG, fg=TEXT_DARK, bold=True)

            for j, day in enumerate(self._days):
                col = 3 + j
                val = self._schedule.get(str(emp.emp_id), {}).get(day, "")

                if self._override_mode and not self._read_only:
                    self.table.setCellWidget(r, col, self._combo(emp, day, val))
                else:
                    self._cell(r, col, val, center=True)

            self._cell(r, cols - 1, emp.card_number, center=True)

        header = self.table.horizontalHeader()

        # №
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        # Бр.
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        # Служител → ВАЖНО
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(2, 240)  # ⬅️ тук контролираш четимостта

        # Дните → разтягаме
        for col in range(3, self.table.columnCount() - 1):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)

        # Служебен №
        header.setSectionResizeMode(self.table.columnCount() - 1, QHeaderView.ResizeMode.ResizeToContents)

        header.setMinimumSectionSize(28)

    # =====================================================
    def _paint_day_header(self):
        for col in range(self.table.columnCount()):
            it = QTableWidgetItem("")
            it.setFlags(Qt.ItemFlag.ItemIsEnabled)

            if 3 <= col < self.table.columnCount() - 1:
                day = int(self.table.horizontalHeaderItem(col).text())
                it.setBackground(QBrush(DAY_RED if day in self._weekends or day in self._holidays else DAY_GREEN))
            else:
                it.setBackground(QBrush(GRID_BG))

            self.table.setItem(0, col, it)

    # =====================================================
    def _combo(self, emp: EmpRow, day: int, current: str) -> QComboBox:
        cb = QComboBox()
        cb.setMinimumWidth(48)
        cb.view().setMinimumWidth(48)

        cb.setStyleSheet("""
        QComboBox {
            background-color: #373737;
            color: #f0f0f0;
            border: none;
            padding-left: 6px;
            min-width: 22px;
        }
        QComboBox::drop-down {
            width: 0px;
            border: none;
        }
        QComboBox::down-arrow {
            image: none;
        }
        QComboBox QAbstractItemView {
            background-color: #2d2d2d;
            color: #f0f0f0;
            selection-background-color: #5a8dee;
        }
        """)

        cb.addItems(SHIFT_OPTIONS)

        cb.blockSignals(True)
        cb.setCurrentText(current)
        cb.blockSignals(False)

        old_value = current  # ✅ ЗАПАЗВАМЕ СТАРАТА СТОЙНОСТ

        def on_change():
            new = cb.currentText()
            if new == old_value:
                return

            try:
                self.client.post_override(
                    self.year,
                    self.month,
                    {
                        "employee_id": emp.emp_id,
                        "day": day,
                        "new_shift": new,
                    },
                )

                # ✅ запис само ако API каже OK
                self._schedule.setdefault(str(emp.emp_id), {})[day] = new
                self._cell(
                    self._row(emp.full_name),
                    1,
                    str(self._count_worked(str(emp.emp_id))),
                    center=True,
                )

            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Невалидна корекция",
                    str(e),
                )
                cb.blockSignals(True)
                cb.setCurrentText(old_value)  # ✅ връщаме старата
                cb.blockSignals(False)

        cb.currentIndexChanged.connect(lambda _: on_change())
        return cb

    # =====================================================
    def _row(self, name: str) -> int:
        for i, e in enumerate(self._employees):
            if e.full_name == name:
                return i + 1
        return 1

    def _count_worked(self, emp_id: str) -> int:
        days = self._schedule.get(str(emp_id), {})
        return sum(1 for d in self._days if days.get(d) in COUNT_AS_WORKED)

    def _cell(self, r, c, text, bg=None, fg=None, bold=False, center=False):
        it = QTableWidgetItem(str(text))
        it.setFlags(Qt.ItemFlag.ItemIsEnabled)
        if center:
            it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if bold:
            f = it.font()
            f.setBold(True)
            it.setFont(f)
        it.setBackground(QBrush(bg or CELL_BG))
        it.setForeground(QBrush(fg or TEXT_LIGHT))
        self.table.setItem(r, c, it)

    def clear(self):
        self._schedule = {}
        self._employees = []
        self._days = []
        self._weekends = set()
        self._holidays = set()
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
