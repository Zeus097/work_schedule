import subprocess
import sys
import os
import time
import signal


class DjangoBackend:
    def __init__(self):
        self.process = None

    def start(self):
        if self.process:
            return

        cmd = [
            sys.executable,
            "manage.py",
            "runserver",
            "127.0.0.1:8000",
        ]

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=self._project_root(),
            start_new_session=True,
        )

        self._wait_until_ready()

    def stop(self):
        if not self.process:
            return

        try:
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
        except Exception:
            pass

        self.process = None

    def _wait_until_ready(self, timeout=10):
        start = time.time()
        while time.time() - start < timeout:
            time.sleep(0.3)

    def _project_root(self):
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

