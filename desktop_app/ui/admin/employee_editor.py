from PyQt6.QtWidgets import QLineEdit, QVBoxLayout, QLabel, QDialogButtonBox, QDialog
from PyQt6.QtCore import QDate

class EmployeeEditorDialog(QDialog):
    def __init__(self, employee_data, parent=None):
        super().__init__(parent)
        self.employee_data = employee_data

        self.setWindowTitle("Редакция на служител")

        # ------------------- Layout -------------------
        layout = QVBoxLayout(self)

        self.name_input = QLineEdit(self.employee_data["name"])
        layout.addWidget(QLabel("Име:"))
        layout.addWidget(self.name_input)

        self.start_date_input = QLineEdit(str(self.employee_data.get("active_from", "1")))
        layout.addWidget(QLabel("Активен от ден:"))
        layout.addWidget(self.start_date_input)

        # ------------------- Buttons -------------------
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(buttons)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "active_from": int(self.start_date_input.text())  # Assuming the day is an integer
        }



