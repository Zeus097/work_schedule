from django.core.management.base import BaseCommand, CommandError
from scheduler.models import MonthRecord
from scheduler.logic.generator.generator import generate_new_month


class Command(BaseCommand):
    """
        Django management command for generating and storing a monthly schedule.
        Invokes the schedule generator for a given year and month and
        creates or updates the corresponding MonthRecord entry.
    """

    help = "Генерира нов месец и го записва в MonthRecord"

    def add_arguments(self, parser):
        parser.add_argument("year", type=int, help="Година, напр. 2026")
        parser.add_argument("month", type=int, help="Месец 1–12")

    def handle(self, *args, **options):
        year = options["year"]
        month = options["month"]

        if month < 1 or month > 12:
            raise CommandError("Месецът трябва да е между 1 и 12.")

        self.stdout.write(
            self.style.WARNING(f"👉 Генерирам {year}-{month:02d} ...")
        )

        result = generate_new_month(year, month)

        if not isinstance(result, dict):
            raise CommandError("Грешка: generate_new_month трябва да върне dict.")

        record, created = MonthRecord.objects.update_or_create(
            year=year,
            month=month,
            defaults={"data": result},
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f"✔ Създаден е нов запис за {year}-{month:02d}")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"✔ Обновен е съществуващ запис за {year}-{month:02d}")
            )

        self.stdout.write(self.style.SUCCESS("Графикът е записан успешно!"))
