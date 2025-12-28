import subprocess
import sys
import time
import requests
from pathlib import Path


class DjangoBackend:
    def __init__(self):
        self.process = None
        self.base_url = "http://127.0.0.1:8000"

    def start(self):
        if self.process:
            return

        project_root = self._project_root()

        cmd = [
            sys.executable,
            "-m",
            "waitress",
            "--listen=127.0.0.1:8000",
            "weight_department_schedule.wsgi:application",
        ]

        self.process = subprocess.Popen(
            cmd,
            cwd=str(project_root),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        self._wait_until_ready()

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process = None

    def _wait_until_ready(self, timeout=20):
        start = time.time()
        while time.time() - start < timeout:
            try:
                r = requests.get(f"{self.base_url}/api/meta/years/", timeout=0.5)
                if r.status_code == 200:
                    return
            except Exception:
                pass
            time.sleep(0.3)

        raise RuntimeError("Django backend did not start")

    def _project_root(self) -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys._MEIPASS)
        return Path(__file__).resolve().parents[2]
