# Starts the real server once for the whole E2E session and stops it afterwards.
# The `page` fixture used by the tests comes from the pytest-playwright plugin.
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

PORT = 8100
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def server(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("e2e") / "app.db"
    env = {**os.environ, "PORT": str(PORT), "APP_DB_PATH": str(db_path)}
    proc = subprocess.Popen([sys.executable, "-m", "app"], cwd=PROJECT_ROOT, env=env)
    url = f"http://localhost:{PORT}"

    deadline = time.time() + 15
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            break
        except (urllib.error.URLError, ConnectionError):
            time.sleep(0.2)
    else:
        proc.kill()
        pytest.fail(f"server did not start on {url}")

    yield url

    proc.terminate()
    proc.wait(timeout=5)
