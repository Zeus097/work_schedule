from django.core.management.base import BaseCommand, CommandError
from scheduler.models import MonthRecord
from scheduler.logic.generator.generator import generate_new_month
from scheduler.services.employee_service import EmployeeService
from scheduler.logic.json_help_functions import load_json_file, write_json_file




class Command(BaseCommand):
    help = "Генерира нов месец и го записва в MonthRecord"

    def add_arguments(self, parser):
        parser.add_argument("year", type=int, help="Година, напр. 2026")
        parser.add_argument("month", type=int, help="Месец 1–12")

    def handle(self, *args, **options):
        year = options["year"]
        month = options["month"]


        if month < 1 or month > 12:
            raise CommandError("Месецът трябва да е между 1 и 12.")

        self.stdout.write(self.style.WARNING(f"👉 Генерирам {year}-{month:02d} ..."))

        employees = EmployeeService.get_active_employees_for_month(year, month)

        if not employees:
            raise CommandError("Няма активни служители за този месец!")

        config = load_json_file("config")

        config["employees"] = [{"name": emp} for emp in employees]

        write_json_file(config, "config")

        result = generate_new_month(year, month)

        if not isinstance(result, dict):
            raise CommandError("Грешка: generate_new_month трябва да върне dict.")


        record, created = MonthRecord.objects.update_or_create(
            year=year,
            month=month,
            defaults={"data": result},
        )

        if created:
            msg = f"✔ Създаден е нов запис за {year}-{month:02d}"
        else:
            msg = f"✔ Обновен е съществуващ запис за {year}-{month:02d}"

        self.stdout.write(self.style.SUCCESS(msg))
        self.stdout.write(self.style.SUCCESS("Графикът е записан успешно!"))
