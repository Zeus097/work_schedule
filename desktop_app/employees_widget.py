from __future__ import annotations

from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox
)


class EmployeesWidget(QWidget):
    """
    Управление на служители:
    - full_name
    - card_number (незадължително)
    """

    def __init__(self, client):
        super().__init__()
        self.client = client
        self.employees = []  # list[dict]

        self._build_ui()
        self.reload()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Име", "Служебен №"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        form = QHBoxLayout()
        form.addWidget(QLabel("Име:"))
        self.name_in = QLineEdit()
        form.addWidget(self.name_in)

        form.addWidget(QLabel("Служебен №:"))
        self.card_in = QLineEdit()
        self.card_in.setPlaceholderText("цифрите на пропуска")
        # ✅ само цифри (може да е празно)
        self.card_in.setValidator(QRegularExpressionValidator(QRegularExpression(r"^\d*$")))
        form.addWidget(self.card_in)

        layout.addLayout(form)

        btns = QHBoxLayout()
        self.add_btn = QPushButton("Добави")
        self.upd_btn = QPushButton("Обнови")
        self.del_btn = QPushButton("Изтрий")

        self.add_btn.clicked.connect(self.add_employee)
        self.upd_btn.clicked.connect(self.update_employee)
        self.del_btn.clicked.connect(self.delete_employee)

        btns.addWidget(self.add_btn)
        btns.addWidget(self.upd_btn)
        btns.addWidget(self.del_btn)
        btns.addStretch()
        layout.addLayout(btns)

        self.table.itemSelectionChanged.connect(self._on_select)

    def reload(self):
        try:
            self.employees = self.client.get_employees()
        except Exception as e:
            QMessageBox.critical(self, "Грешка", f"Не мога да заредя служители:\n{e}")
            self.employees = []

        self.employees = sorted(self.employees, key=lambda x: (x.get("full_name") or ""))

        self.table.setRowCount(len(self.employees))
        for r, emp in enumerate(self.employees):
            emp_id = str(emp.get("id", ""))
            name = str(emp.get("full_name", ""))
            card = str(emp.get("card_number") or "")

            for c, val in enumerate([emp_id, name, card]):
                it = QTableWidgetItem(val)
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter if c != 1 else Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(r, c, it)

        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(1, 280)

    def _selected_emp(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.employees):
            return None
        return self.employees[row]

    def _on_select(self):
        emp = self._selected_emp()
        if not emp:
            return
        self.name_in.setText(emp.get("full_name") or "")
        self.card_in.setText(emp.get("card_number") or "")

    def add_employee(self):
        name = self.name_in.text().strip()
        card = self.card_in.text().strip()

        if not name:
            QMessageBox.warning(self, "Липсва име", "Въведи име.")
            return

        try:
            self.client.add_employee({
                "full_name": name,
                "card_number": card or None
            })
        except Exception as e:
            QMessageBox.critical(self, "Грешка", f"Не успях да добавя:\n{e}")
            return

        self.name_in.clear()
        self.card_in.clear()
        self.reload()

    def update_employee(self):
        emp = self._selected_emp()
        if not emp:
            QMessageBox.warning(self, "Няма избор", "Избери служител от списъка.")
            return

        emp_id = emp["id"]
        name = self.name_in.text().strip()
        card = self.card_in.text().strip()

        if not name:
            QMessageBox.warning(self, "Липсва име", "Името не може да е празно.")
            return

        try:
            self.client.update_employee(emp_id, {
                "full_name": name,
                "card_number": card or None
            })
        except Exception as e:
            QMessageBox.critical(self, "Грешка", f"Не успях да обновя:\n{e}")
            return

        self.reload()

    def delete_employee(self):
        emp = self._selected_emp()
        if not emp:
            QMessageBox.warning(self, "Няма избор", "Избери служител от списъка.")
            return

        emp_id = emp["id"]
        name = emp.get("full_name", "")

        ok = QMessageBox.question(self, "Потвърди", f"Да изтрия ли:\n{name} ?")
        if ok != QMessageBox.StandardButton.Yes:
            return

        try:
            self.client.delete_employee(emp_id)
        except Exception as e:
            QMessageBox.critical(self, "Грешка", f"Не успях да изтрия:\n{e}")
            return

        self.name_in.clear()
        self.card_in.clear()
        self.reload()
