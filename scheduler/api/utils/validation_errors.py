def humanize_validation_error(employee, day, raw_message):
    """
    Превръща вътрешна грешка от валидатора
    в човешко, UI-приятелско съобщение.
    """

    # --- Покритие ---
    if employee == "ПОКРИТИЕ":
        if "Д" in raw_message:
            return {
                "day": day,
                "employee": None,
                "message": "Липсва или има повече от една дневна смяна (Д).",
                "hint": "Трябва да има точно 1× Д смяна за деня."
            }
        if "В" in raw_message:
            return {
                "day": day,
                "employee": None,
                "message": "Липсва или има повече от една вечерна смяна (В).",
                "hint": "Трябва да има точно 1× В смяна за деня."
            }
        if "Н" in raw_message:
            return {
                "day": day,
                "employee": None,
                "message": "Липсва или има повече от една нощна смяна (Н).",
                "hint": "Трябва да има точно 1× Н смяна за деня."
            }

    # --- Ротация ---
    if "Невалидна ротация" in raw_message:
        return {
            "day": day,
            "employee": employee,
            "message": "Невалидна последователност на смените.",
            "hint": "Провери почивките между смените (след Н – 2 дни почивка)."
        }

    # --- Администратор ---
    if "Администратор" in raw_message:
        return {
            "day": day,
            "employee": employee,
            "message": "Администраторът не може да работи в този ден.",
            "hint": "Администраторът работи само делнични дни със смяна А."
        }

    # --- Fallback ---
    return {
        "day": day,
        "employee": employee,
        "message": "Невалидна смяна.",
        "hint": "Провери ротациите и покритието за деня."
    }
