"""Start Streamlit as a separate process and probe its HTTP endpoints."""

from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen


PROJECT = Path(__file__).resolve().parents[2]


def free_local_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def test_web_server_starts_and_serves_homepage(tmp_path):
    port = free_local_port()
    command = [
        sys.executable, "-m", "streamlit", "run", "week7/app.py",
        "--server.address", "127.0.0.1", "--server.port", str(port),
        "--server.headless", "true", "--browser.gatherUsageStats", "false",
    ]
    with (tmp_path / "server.log").open("w", encoding="utf-8") as log:
        server = subprocess.Popen(command, cwd=PROJECT, stdout=log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if server.poll() is not None:
                    raise AssertionError(f"Streamlit exited with code {server.returncode}")
                try:
                    with urlopen(f"http://127.0.0.1:{port}/_stcore/health", timeout=2) as response:
                        if response.status == 200:
                            break
                except (OSError, URLError):
                    time.sleep(0.2)
            else:
                raise AssertionError("Streamlit health endpoint did not become ready")

            with urlopen(f"http://127.0.0.1:{port}/", timeout=5) as response:
                html = response.read().decode("utf-8")
                assert response.status == 200
                assert "streamlit" in html.lower()
        finally:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)
