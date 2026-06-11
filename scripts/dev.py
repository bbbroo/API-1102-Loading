from __future__ import annotations

import argparse
import os
import platform
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import venv
import webbrowser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT / "frontend"
VENV_DIR = ROOT / ".venv"
REQUIREMENTS = ROOT / "requirements.txt"
REQUIREMENTS_STAMP = VENV_DIR / ".requirements-installed"
BACKEND_URL = "http://127.0.0.1:8000/api/health"
FRONTEND_URL = "http://127.0.0.1:5173"
IS_WINDOWS = platform.system().lower().startswith("win")
shutdown_requested = threading.Event()


def venv_python() -> Path:
    if IS_WINDOWS:
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def npm_command() -> str:
    return "npm.cmd" if IS_WINDOWS else "npm"


def run_checked(command: list[str], cwd: Path, prefix: str) -> None:
    print(f"{prefix} {' '.join(command)}")
    subprocess.run(command, cwd=cwd, check=True)


def create_venv_if_needed() -> None:
    python = venv_python()
    if python.exists():
        return
    print("[setup] Creating .venv")
    venv.EnvBuilder(with_pip=True).create(VENV_DIR)


def requirements_need_install() -> bool:
    if not REQUIREMENTS.exists():
        return False
    if not REQUIREMENTS_STAMP.exists():
        return True
    return REQUIREMENTS.stat().st_mtime > REQUIREMENTS_STAMP.stat().st_mtime


def install_backend_dependencies_if_needed() -> None:
    if not requirements_need_install():
        return
    run_checked(
        [str(venv_python()), "-m", "pip", "install", "-r", str(REQUIREMENTS)],
        ROOT,
        "[setup]",
    )
    REQUIREMENTS_STAMP.write_text(str(time.time()), encoding="utf-8")


def install_frontend_dependencies_if_needed() -> None:
    if (FRONTEND_DIR / "node_modules").exists():
        return
    run_checked([npm_command(), "install"], FRONTEND_DIR, "[setup]")


def port_is_busy(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def check_ports() -> None:
    occupied = []
    if port_is_busy("127.0.0.1", 8000):
        occupied.append("Backend cannot start: 127.0.0.1:8000 is already in use.")
    if port_is_busy("127.0.0.1", 5173):
        occupied.append("Frontend cannot start: 127.0.0.1:5173 is already in use.")
    if occupied:
        for message in occupied:
            print(f"[error] {message}", file=sys.stderr)
        print("[error] Stop the process using the occupied port, then run python scripts/dev.py again.", file=sys.stderr)
        raise SystemExit(1)


def stream_output(process: subprocess.Popen[str], prefix: str) -> None:
    assert process.stdout is not None
    for line in process.stdout:
        print(f"{prefix} {line.rstrip()}", flush=True)


def start_process(command: list[str], cwd: Path, prefix: str) -> subprocess.Popen[str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    popen_kwargs: dict[str, object] = {}
    if IS_WINDOWS:
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs["start_new_session"] = True
    return subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
        **popen_kwargs,
    )


def wait_for_url(url: str, label: str, timeout: float = 45.0) -> None:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if 200 <= response.status < 500:
                    return
        except Exception as error:  # noqa: BLE001 - readiness polling should keep retrying.
            last_error = error
        time.sleep(0.5)
    raise RuntimeError(f"{label} did not become ready at {url}: {last_error}")


def stop_process(process: subprocess.Popen[str], label: str) -> None:
    if process.poll() is not None:
        return
    print(f"[dev] Stopping {label}...")
    if IS_WINDOWS:
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        process.kill()


def request_shutdown(signum: int, _frame: object) -> None:
    signal_name = "Ctrl+C" if signum == signal.SIGINT else "shutdown signal"
    print(f"\n[dev] {signal_name} received.")
    shutdown_requested.set()


def install_signal_handlers() -> None:
    signal.signal(signal.SIGINT, request_shutdown)
    if IS_WINDOWS and hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, request_shutdown)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the API RP 1102 backend and frontend dev servers.")
    parser.add_argument("--open", action="store_true", help="Open the frontend in the default browser after startup.")
    args = parser.parse_args()

    install_signal_handlers()
    check_ports()
    create_venv_if_needed()
    install_backend_dependencies_if_needed()
    install_frontend_dependencies_if_needed()
    check_ports()

    backend = start_process(
        [
            str(venv_python()),
            "-m",
            "uvicorn",
            "app.backend.main:app",
            "--reload",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ],
        ROOT,
        "[backend]",
    )
    frontend = start_process([npm_command(), "run", "dev"], FRONTEND_DIR, "[frontend]")
    processes = [(backend, "backend"), (frontend, "frontend")]

    for process, label in processes:
        threading.Thread(target=stream_output, args=(process, f"[{label}]"), daemon=True).start()

    try:
        wait_for_url(BACKEND_URL, "Backend")
        wait_for_url(FRONTEND_URL, "Frontend")
        print(f"Backend ready:  {BACKEND_URL}")
        print(f"Frontend ready: {FRONTEND_URL}")
        if args.open:
            webbrowser.open(FRONTEND_URL)

        while not shutdown_requested.is_set():
            for process, label in processes:
                code = process.poll()
                if code is not None:
                    raise RuntimeError(f"{label} exited unexpectedly with code {code}")
            time.sleep(0.5)
        return 0
    finally:
        for process, label in processes:
            stop_process(process, label)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(f"[error] {error}", file=sys.stderr)
        raise SystemExit(1)
