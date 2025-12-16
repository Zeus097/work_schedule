from pathlib import Path
from datetime import date
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

from scheduler.api.utils.holidays import get_holidays_for_month


# === FILLS ===
RED_FILL = PatternFill("solid", fgColor="FF6666")     # уикенд / празник
GREEN_FILL = PatternFill("solid", fgColor="99CC66")  # работен ден
HEADER_FILL = PatternFill("solid", fgColor="E6E6E6")

EMPLOYEE_ROW_FILLS = [
    PatternFill("solid", fgColor="FFD966"),
    PatternFill("solid", fgColor="F4B084"),
    PatternFill("solid", fgColor="9BC2E6"),
    PatternFill("solid", fgColor="A9D18E"),
    PatternFill("solid", fgColor="C5E0B4"),
]

THIN_BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)

COUNT_AS_WORKED = {"Д", "В", "Н", "А", "О", "Б"}


def export_schedule_to_excel(
    filename: str,
    company: str,
    department: str,
    city: str,
    month_name: str,
    month: int,            # ⬅️ ВАЖНО
    year: int,
    employees: list[dict],
    days: list[int],
    schedule: dict,
):
    wb = Workbook()
    ws = wb.active
    ws.title = "График"

    holidays = set(get_holidays_for_month(year, month))

    first_day_col = 4
    last_day_col = first_day_col + len(days) - 1
    service_col = last_day_col + 1

    # ===== HEADER =====
    ws.merge_cells(start_row=3, start_column=3, end_row=3, end_column=10)
    ws.cell(3, 3, company).font = Font(size=14, bold=True)
    ws.cell(3, 3).alignment = Alignment(horizontal="center")

    ws.merge_cells(start_row=3, start_column=11, end_row=3, end_column=22)
    ws.cell(3, 11, department).font = Font(size=16, bold=True)
    ws.cell(3, 11).alignment = Alignment(horizontal="center")

    ws.merge_cells(start_row=3, start_column=23, end_row=3, end_column=service_col)
    ws.cell(3, 23, city).font = Font(size=14, bold=True)
    ws.cell(3, 23).alignment = Alignment(horizontal="center")

    ws.merge_cells(start_row=4, start_column=1, end_row=4, end_column=service_col)
    ws.cell(4, 1, f"{month_name} {year} г.").font = Font(size=12, bold=True)
    ws.cell(4, 1).alignment = Alignment(horizontal="center")

    # ===== TABLE HEADER =====
    headers = ["№", "Изр.", "Име, Презиме, Фамилия"]
    for col, text in enumerate(headers, start=1):
        c = ws.cell(row=5, column=col, value=text)
        c.fill = HEADER_FILL
        c.border = THIN_BORDER
        c.alignment = Alignment(horizontal="center")

    # === ЦИФРИТЕ НА ДНИТЕ (САМО ТЕ СА ОЦВЕТЕНИ) ===
    for idx, day in enumerate(days):
        col = first_day_col + idx
        c = ws.cell(row=5, column=col, value=day)
        c.border = THIN_BORDER
        c.alignment = Alignment(horizontal="center")

        weekday = date(year, month, day).weekday()  # 0=Понеделник
        if weekday >= 5 or day in holidays:
            c.fill = RED_FILL
        else:
            c.fill = GREEN_FILL

    ws.cell(row=5, column=service_col, value="Служебен номер").fill = HEADER_FILL
    ws.cell(row=5, column=service_col).border = THIN_BORDER
    ws.cell(row=5, column=service_col).alignment = Alignment(horizontal="center")

    # ===== BODY =====
    for idx, emp in enumerate(employees):
        row = 6 + idx
        name = emp["name"]
        card = emp.get("card_number", "")
        emp_days = schedule.get(name, {})

        worked_days = sum(1 for d in days if emp_days.get(d, "") in COUNT_AS_WORKED)
        fill = EMPLOYEE_ROW_FILLS[idx % len(EMPLOYEE_ROW_FILLS)]

        ws.cell(row=row, column=1, value=idx + 1).border = THIN_BORDER
        ws.cell(row=row, column=2, value=worked_days).border = THIN_BORDER
        ws.cell(row=row, column=3, value=name).border = THIN_BORDER
        ws.cell(row=row, column=3).fill = fill

        for i, day in enumerate(days):
            col = first_day_col + i
            val = emp_days.get(day, "")
            c = ws.cell(row=row, column=col, value=val)
            c.border = THIN_BORDER
            c.alignment = Alignment(horizontal="center")

        ws.cell(row=row, column=service_col, value=card).border = THIN_BORDER

    # ===== LEGEND =====
    legend_row = row + 3
    ws.cell(legend_row, 3, "ЛЕГЕНДА:").font = Font(bold=True)

    legend = [
        "Д – ДНЕВНА СМЯНА (08:00 – 16:00)",
        "В – ВТОРА СМЯНА (16:00 – 24:00)",
        "Н – НОЩНА СМЯНА (00:00 – 08:00)",
        "ПРАЗЕН КВАДРАТ – ПОЧИВЕН ДЕН",
        "О – ОТПУСК",
        "Б – БОЛНИЧЕН",
    ]

    for i, text in enumerate(legend, start=1):
        ws.cell(legend_row + i, 3, text)

    # ===== WIDTHS =====
    ws.column_dimensions["A"].width = 5
    ws.column_dimensions["B"].width = 6
    ws.column_dimensions["C"].width = 32

    for col in range(first_day_col, service_col):
        ws.column_dimensions[get_column_letter(col)].width = 4

    ws.column_dimensions[get_column_letter(service_col)].width = 16

    wb.save(filename)






