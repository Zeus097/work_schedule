from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox,
    QTableWidget, QTableWidgetItem, QComboBox
)
from PyQt6.QtCore import Qt

from .month_close import extract_last_shifts, save_last_state


class AdminWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Администраторски панел")
        self.setMinimumSize(520, 360)
        self.setWindowFlag(Qt.WindowType.Window)
        self.setAutoFillBackground(True)
        self.setStyleSheet("background-color: #f2f2f2;")

        self.current_schedule = None
        self.days_in_month = None

        layout = QVBoxLayout(self)

        title = QLabel("Администрация")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        info = QLabel("Коригирай последната смяна при нужда, после запиши.")
        layout.addWidget(info)

        # TABLE
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Служител", "Последна смяна"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        # BUTTONS
        self.preview_btn = QPushButton("Преглед (зареди данните)")
        self.preview_btn.clicked.connect(self.load_preview)
        layout.addWidget(self.preview_btn)

        self.save_btn = QPushButton("Запис (заключи месеца)")
        self.save_btn.clicked.connect(self.save_locked_month)
        layout.addWidget(self.save_btn)

        layout.addStretch()

        self.setStyleSheet("""
        QComboBox {
            color: black;
            background-color: white;
        }
        QComboBox QAbstractItemView {
            color: black;
            background-color: white;
            selection-background-color: #cce4ff;
            selection-color: black;
        }
        """)

    # =========================
    # PREVIEW (editable)
    # =========================
    def load_preview(self):
        if not self.current_schedule or not self.days_in_month:
            QMessageBox.warning(self, "Няма данни", "Първо зареди месец от главния екран.")
            return

        snapshot = extract_last_shifts(self.current_schedule, self.days_in_month)
        if not snapshot:
            QMessageBox.warning(self, "Грешка", "Не бяха открити валидни смени.")
            return

        self.table.setRowCount(0)

        for row, (name, shift) in enumerate(snapshot.items()):
            self.table.insertRow(row)

            name_item = QTableWidgetItem(name)
            self.table.setItem(row, 0, name_item)

            combo = QComboBox()
            combo.addItems(["", "Д", "В", "Н", "А", "О", "Б"])
            combo.setCurrentText(shift if shift in ["", "Д", "В", "Н", "А", "О", "Б"] else "")

            self.table.setCellWidget(row, 1, combo)

    # =========================
    # SAVE (uses edited values)
    # =========================
    def save_locked_month(self):
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "Няма данни", "Първо направи предварителен преглед.")
            return

        snapshot = {}
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 0).text()
            combo = self.table.cellWidget(row, 1)
            snapshot[name] = combo.currentText()

        save_last_state(
            self.parent().current_year,
            self.parent().current_month,
            snapshot
        )

        QMessageBox.information(
            self,
            "Готово",
            "Месецът е заключен.\nМожеш да генерираш следващия."
        )

        # 🔄 позволи продължаване на работа в main window
        parent = self.parent()
        if parent:
            parent.year_select.setEnabled(True)
            parent.month_select.setEnabled(True)
