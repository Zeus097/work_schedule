from __future__ import annotations

from PyQt6.QtCore import Qt, QRegularExpression, pyqtSignal
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox,
    QRadioButton, QButtonGroup
)
from desktop_app.msgbox import question, warning, error, info




class EmployeesWidget(QWidget):
    admin_changed = pyqtSignal()

    """
        UI widget for managing employees.
            - Displays all active employees in a tabular view
            - Supports creating, updating, and deleting employees
            - Syncs employee data with the backend API
            - Acts as the entry point for selecting the monthly administrator
            - Remains accessible even when no schedule is generated
        """

    def __init__(self, client, year: int, month: int):
        super().__init__()
        self.client = client
        self.year = year
        self.month = month

        self.employees = []

        self.admin_group = QButtonGroup(self)
        self.admin_group.setExclusive(True)
        self.current_month_admin_id = None

        self._build_ui()
        self.reload()


    def _build_ui(self):
        """
            Builds the employees management UI.
                - Renders the employees table (ID, full name, card number)
                - Provides input fields for adding and editing employees
                - Adds action buttons for create, update, and delete
                - Handles row selection and form synchronization
                - Serves as the base UI for assigning roles (incl. monthly admin)
        """

        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setMinimumWidth(680)
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 260)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 140)

        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Име", "Служебен №", "Администратор"]
        )
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
        """
            Reloads the employees list from the backend.
                - Fetches all employees via the API
                - Sorts them alphabetically by full name
                - Rebuilds the table rows and admin radio buttons
                - Preserves the current monthly administrator selection
                - Refreshes column sizing and clears invalid selections
        """

        try:
            self.current_month_admin_id = self.client.get_month_admin(
                year=self.year,
                month=self.month
            )
        except Exception:
            self.current_month_admin_id = None

        try:
            self.employees = self.client.get_employees()
        except Exception as e:
            QMessageBox.critical(self, "Грешка", f"Не мога да заредя служители:\n{e}")
            self.employees = []

        self.employees = sorted(self.employees, key=lambda x: (x.get("full_name") or ""))
        self.table.setRowCount(len(self.employees))
        self.admin_group = QButtonGroup(self)
        self.admin_group.setExclusive(True)

        self.table.setRowCount(len(self.employees))

        for r, emp in enumerate(self.employees):
            emp_id = str(emp.get("id", ""))
            name = str(emp.get("full_name", ""))
            card = str(emp.get("card_number") or "")

            # ID
            it_id = QTableWidgetItem(emp_id)
            it_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 0, it_id)

            # Name
            it_name = QTableWidgetItem(name)
            it_name.setTextAlignment(Qt.AlignmentFlag.AlignLeft)
            self.table.setItem(r, 1, it_name)

            # Card
            it_card = QTableWidgetItem(card)
            it_card.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 2, it_card)

            # Admin radio
            radio = QRadioButton()
            self.admin_group.addButton(radio)
            cell = QWidget()
            lay = QHBoxLayout(cell)
            lay.addWidget(radio)
            lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(r, 3, cell)

            if emp_id == self.current_month_admin_id:
                radio.setChecked(True)

            radio.toggled.connect(
                lambda checked, eid=emp_id: self._on_admin_selected(eid, checked)
            )

        self.table.setColumnHidden(0, True)

        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(1, 260)

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
            warning(self, "Липсва име", "Въведи име.")
            return

        try:
            self.client.add_employee({
                "full_name": name,
                "card_number": card or None
            })
        except Exception as e:
            error(self, "Грешка", f"Не успях да добавя:\n{e}")
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
            warning(self, "Няма избор", "Избери служител от списъка.")
            return

        emp_id = emp["id"]
        name = emp.get("full_name", "")

        if not question(self, "Потвърди", f"Да изтрия ли:\n{name}?"):
            return

        try:
            admin_id = self.client.get_month_admin(self.year, self.month)
        except Exception:
            admin_id = None

        if admin_id and str(emp_id) == str(admin_id):
            warning(
                self,
                "Администратор",
                "Не можеш да изтриеш администратора за текущия месец."
            )
            return

        try:
            self.client.delete_employee(emp_id)
        except Exception as e:
            error(self, "Грешка", f"Не успях да изтрия:\n{e}")
            return

        self.name_in.clear()
        self.card_in.clear()
        self.reload()


    def _on_admin_selected(self, emp_id: str, checked: bool):
        if not checked:
            return

        self.current_month_admin_id = emp_id

        try:
            self.client.set_month_admin(
                self.year,
                self.month,
                emp_id
            )

            self.admin_changed.emit()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Грешка",
                f"Неуспешно задаване на администратор:\n{e}"
            )






