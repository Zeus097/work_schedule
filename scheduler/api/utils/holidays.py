from datetime import date, timedelta


FIXED_HOLIDAYS = [
    (1, 1),    # Нова година
    (3, 3),    # Освобождение
    (5, 1),    # Ден на труда
    (5, 6),    # Гергьовден
    (5, 24),   # Ден на азбуката
    (9, 6),    # Съединение
    (9, 22),   # Независимост
    (12, 24),  # Бъдни вечер
    (12, 25),  # Коледа
    (12, 26),  # Коледа
]



def orthodox_easter(year):

    a = year % 4
    b = year % 7
    c = year % 19
    d = (19 * c + 15) % 30
    e = (2 * a + 4 * b - d + 34) % 7
    month = (d + e + 114) // 31
    day = ((d + e + 114) % 31) + 1


    easter_julian = date(year, month, day)
    easter_gregorian = easter_julian + timedelta(days=13)

    return easter_gregorian


def easter_holidays(year):

    easter = orthodox_easter(year)

    good_friday = easter - timedelta(days=2)
    holy_saturday = easter - timedelta(days=1)
    easter_sunday = easter
    bright_monday = easter + timedelta(days=1)

    return [
        good_friday,
        holy_saturday,
        easter_sunday,
        bright_monday,
    ]

def get_holidays_for_month(year, month):
    holidays = []


    for m, d in FIXED_HOLIDAYS:
        if m == month:
            holidays.append(date(year, month, d))


    for easter_day in easter_holidays(year):
        if easter_day.month == month:
            holidays.append(easter_day)


    return sorted([d.day for d in holidays])



