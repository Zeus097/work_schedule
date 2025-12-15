from pathlib import Path
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

COUNT_AS_WORKED = {"Д", "В", "Н", "А", "О", "Б"}

def export_schedule_to_excel(
    filename: str,
    company: str,          # ТРАКИЯ ГЛАС
    department: str,       # КАНТАР
    city: str,             # ТЪРГОВИЩЕ
    month_name: str,       # МАРТ
    year: int,             # 2026
    employees: list[dict], # [{name, card_number?}]
    days: list[int],
    schedule: dict,
    weekends: list[int],
    holidays: list[int],
):
    wb = Workbook()
    ws = wb.active
    ws.title = "График"

    total_cols = len(days) + 4  # №, дни, име, изработени + карта

    # ===== HEADER BLOCK =====
    # ред 3 – общ ред за фирма / отдел / град

    # ТРАКИЯ ГЛАС – колона C (над имената)
    ws.merge_cells(start_row=3, start_column=3, end_row=3, end_column=10)
    cell = ws.cell(3, 3, company)
    cell.font = Font(size=14, bold=True)
    cell.alignment = Alignment(horizontal="center", vertical="center")

    # КАНТАР – център
    ws.merge_cells(start_row=3, start_column=11, end_row=3, end_column=22)
    cell = ws.cell(3, 11, department)
    cell.font = Font(size=15, bold=True)
    cell.alignment = Alignment(horizontal="center", vertical="center")

    # ТЪРГОВИЩЕ – вдясно
    ws.merge_cells(start_row=3, start_column=23, end_row=3, end_column=total_cols)
    cell = ws.cell(3, 23, city)
    cell.font = Font(size=14, bold=True)
    cell.alignment = Alignment(horizontal="center", vertical="center")

    # ред 4 – месец и година (централно)
    ws.merge_cells(start_row=4, start_column=1, end_row=4, end_column=total_cols)
    cell = ws.cell(4, 1, f"{month_name} {year} г.")
    cell.font = Font(size=12, bold=True)
    cell.alignment = Alignment(horizontal="center", vertical="center")

    # ===== TABLE HEADER =====
    headers = ["№", "Изр.", "Име, Презиме, Фамилия"]
    for col, text in enumerate(headers, start=1):
        c = ws.cell(row=5, column=col, value=text)
        c.fill = HEADER_FILL
        c.border = THIN_BORDER
        c.alignment = Alignment(horizontal="center")

    for i, day in enumerate(days, start=4):
        c = ws.cell(row=5, column=i, value=day)
        c.fill = HEADER_FILL
        c.border = THIN_BORDER
        c.alignment = Alignment(horizontal="center")

    last_col = 4 + len(days)
    ws.cell(row=5, column=last_col, value="Служебен номер")
    ws.cell(row=5, column=last_col).fill = HEADER_FILL
    ws.cell(row=5, column=last_col).border = THIN_BORDER
    ws.cell(row=5, column=last_col).alignment = Alignment(horizontal="center")

    # ===== BODY =====
    for idx, emp in enumerate(employees, start=1):
        row = 5 + idx
        name = emp["name"]
        card = emp.get("card_number", "")

        emp_days = schedule.get(name, {})

        worked_days = sum(
            1 for d in days if emp_days.get(d, "") in COUNT_AS_WORKED
        )

        ws.cell(row=row, column=1, value=idx).border = THIN_BORDER
        ws.cell(row=row, column=2, value=worked_days).border = THIN_BORDER
        ws.cell(row=row, column=3, value=name).border = THIN_BORDER

        for i, day in enumerate(days, start=4):
            val = emp_days.get(day, "")
            c = ws.cell(row=row, column=i, value=val)
            c.alignment = Alignment(horizontal="center")
            c.border = THIN_BORDER

            if day in weekends or day in holidays:
                c.fill = DARK_FILL

        ws.cell(row=row, column=last_col, value=card).border = THIN_BORDER

    # ===== WIDTHS =====
    ws.column_dimensions["A"].width = 5
    ws.column_dimensions["B"].width = 6
    ws.column_dimensions["C"].width = 30

    for col in range(4, last_col):
        ws.column_dimensions[get_column_letter(col)].width = 4

    ws.column_dimensions[get_column_letter(last_col)].width = 14

    wb.save(filename)






