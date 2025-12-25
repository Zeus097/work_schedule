from datetime import date, timedelta


FIXED_HOLIDAYS = [
    (1, 1),    # New Year
    (3, 3),    # Liberation
    (5, 1),    # Labor Day
    (5, 6),    # St. George's Day
    (5, 24),   # Alphabet Day
    (9, 6),    # Union Day
    (9, 22),   # Independence Day
    (12, 24),  # Christmas Eve
    (12, 25),  # Christmas
    (12, 26),  # Christmas
]



def orthodox_easter(year):
    """
        Calculates the date of Orthodox Easter for a given year.
        Computes the Julian calendar Easter date and converts it
        to the Gregorian calendar.
    """

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
    """
        Returns Orthodox Easter-related holiday dates for a given year.
        Includes Good Friday, Holy Saturday, Easter Sunday,
        and Bright Monday.
    """

    easter = orthodox_easter(year)
    good_friday = easter - timedelta(days=2)
    holy_saturday = easter - timedelta(days=1)
    easter_sunday = easter
    bright_monday = easter + timedelta(days=1)
    return [good_friday, holy_saturday, easter_sunday, bright_monday,]


def get_holidays_for_month(year, month):
    """
        Returns all official holidays for a given month.
        Combines fixed-date holidays and Orthodox Easter-related holidays
        and returns the list of day numbers within the month.
    """

    holidays = []

    for m, d in FIXED_HOLIDAYS:
        if m == month:
            holidays.append(date(year, month, d))

    for easter_day in easter_holidays(year):
        if easter_day.month == month:
            holidays.append(easter_day)

    return sorted([d.day for d in holidays])



