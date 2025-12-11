from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QLineEdit, QLabel
)
from PyQt6.QtCore import pyqtSignal


class EmployeesWidget(QWidget):
    employee_added = pyqtSignal(dict)
    employee_updated = pyqtSignal(dict)
    employee_deleted = pyqtSignal(int)

    def __init__(self, employees, parent=None):
        super().__init__(parent)

        self.employees = employees

        layout = QVBoxLayout()
        self.setLayout(layout)

        # --- LIST ---
        self.list = QListWidget()
        layout.addWidget(self.list)

        for emp in employees:
            self.list.addItem(f"{emp['id']} — {emp['full_name']}")

        # --- FORM ---
        form = QHBoxLayout()

        self.name_input = QLineEdit()
        form.addWidget(QLabel("Име:"))
        form.addWidget(self.name_input)

        layout.addLayout(form)

        # --- BUTTONS ---
        btn_row = QHBoxLayout()

        add_btn = QPushButton("Добави")
        add_btn.clicked.connect(self.add_employee)
        btn_row.addWidget(add_btn)

        update_btn = QPushButton("Обнови")
        update_btn.clicked.connect(self.update_employee)
        btn_row.addWidget(update_btn)

        delete_btn = QPushButton("Изтрий")
        delete_btn.clicked.connect(self.delete_employee)
        btn_row.addWidget(delete_btn)

        layout.addLayout(btn_row)

        # select → load name
        self.list.itemClicked.connect(self.load_to_input)

    # ---------------------------------------------------------
    def reload_list(self, employees):
        """Обновява списъка визуално + локално."""
        self.employees = employees
        self.list.clear()

        for emp in employees:
            self.list.addItem(f"{emp['id']} — {emp['full_name']}")

        # чисти input-а, за да няма грешки
        self.name_input.clear()

    # ---------------------------------------------------------
    def load_to_input(self, item):
        emp_id = int(item.text().split(" — ")[0])
        emp = next(e for e in self.employees if e["id"] == emp_id)
        self.name_input.setText(emp["full_name"])

    # ---------------------------------------------------------
    def add_employee(self):
        name = self.name_input.text().strip()
        if not name:
            return

        self.employee_added.emit({"full_name": name})
        self.name_input.clear()

    # ---------------------------------------------------------
    def update_employee(self):
        selected = self.list.currentItem()
        if not selected:
            return

        emp_id = int(selected.text().split(" — ")[0])
        name = self.name_input.text().strip()
        if not name:
            return

        self.employee_updated.emit({"id": emp_id, "full_name": name})

    # ---------------------------------------------------------
    def delete_employee(self):
        selected = self.list.currentItem()
        if not selected:
            return

        emp_id = int(selected.text().split(" — ")[0])
        self.employee_deleted.emit(emp_id)



