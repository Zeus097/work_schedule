import os
from waitress import serve
from django.core.wsgi import get_wsgi_application


def start_server():
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "weight_department_schedule.settings"
    )

    application = get_wsgi_application()

    serve(
        application,
        host="127.0.0.1",
        port=8000,
        threads=4
    )

