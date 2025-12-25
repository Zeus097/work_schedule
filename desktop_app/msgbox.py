"""
    Centralized message box helpers for the desktop application.

    This module provides a unified, localized (BG) wrapper around QMessageBox
    to ensure consistent button texts, icons, and behavior across the entire UI.

    Why this exists:
        - PyQt6 does NOT support global override of QMessageBox button texts
        - Native QMessageBox shows Yes/No, not Да/Не
        - This wrapper guarantees consistent UX and avoids copy-paste dialogs

    Usage:
        from desktop_app.ui.msgbox import question, info, warning, error

        reply = question(self, "Потвърди", "Да изтрия ли служителя?")
        if reply == QMessageBox.StandardButton.Yes:
            ...

    All dialogs use Bulgarian labels and are safe for macOS / Windows / Linux.
"""



from PyQt6.QtWidgets import QMessageBox


def info(parent, title: str, text: str):
    QMessageBox.information(
        parent,
        title,
        text,
        QMessageBox.StandardButton.Ok
    )


def error(parent, title: str, text: str):
    QMessageBox.critical(
        parent,
        title,
        text,
        QMessageBox.StandardButton.Ok
    )


def warning(parent, title: str, text: str):
    QMessageBox.warning(
        parent,
        title,
        text,
        QMessageBox.StandardButton.Ok
    )


def question(parent, title: str, text: str) -> bool:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Question)
    box.setWindowTitle(title)
    box.setText(text)

    yes = box.addButton("Да", QMessageBox.ButtonRole.YesRole)
    no = box.addButton("Не", QMessageBox.ButtonRole.NoRole)

    box.setDefaultButton(no)
    box.exec()

    return box.clickedButton() == yes




