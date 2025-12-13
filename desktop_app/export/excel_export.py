from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter


DARK_FILL = PatternFill("solid", fgColor="B0B0B0")
HEADER_FILL = PatternFill("solid", fgColor="E6E6E6")

THIN_BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)


def export_schedule_to_excel(
    filename: str,
    title: str,
    month_label: str,
    employees: list[str],
    days: list[int],
    schedule: dict,
    weekends: list[int],
    holidays: list[int],
):
    wb = Workbook()
    ws = wb.active
    ws.title = "График"

    total_cols = len(days) + 1

    # ===== TITLE =====
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=total_cols)
    cell = ws.cell(row=1, column=1, value=title)
    cell.font = Font(size=16, bold=True)
    cell.alignment = Alignment(horizontal="center")

    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=total_cols)
    cell = ws.cell(row=2, column=1, value=month_label)
    cell.font = Font(size=13, bold=True)
    cell.alignment = Alignment(horizontal="center")

    # ===== HEADER =====
    h = ws.cell(row=4, column=1, value="Служител")
    h.fill = HEADER_FILL
    h.border = THIN_BORDER

    for col, day in enumerate(days, start=2):
        c = ws.cell(row=4, column=col, value=day)
        c.alignment = Alignment(horizontal="center")
        c.fill = HEADER_FILL
        c.border = THIN_BORDER

    # ===== BODY =====
    for row, name in enumerate(employees, start=5):
        ws.cell(row=row, column=1, value=name).border = THIN_BORDER

        emp_days = schedule.get(name, {})
        for col, day in enumerate(days, start=2):
            val = emp_days.get(day, "")
            cell = ws.cell(row=row, column=col, value=val)
            cell.alignment = Alignment(horizontal="center")
            cell.border = THIN_BORDER

            if day in weekends or day in holidays:
                cell.fill = DARK_FILL

    # ===== SIZES =====
    ws.column_dimensions["A"].width = 28
    for col in range(2, total_cols + 1):
        ws.column_dimensions[get_column_letter(col)].width = 4

    wb.save(filename)
