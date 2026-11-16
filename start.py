#!/usr/bin/env python3
"""One-command local launcher. Reuses a venv and installs pinned dependencies once."""

import argparse
import hashlib
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent


def load_environment():
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for number, raw in enumerate(env_file.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        key = key.strip()
        if not separator or not key.isidentifier():
            raise ValueError(f".env line {number}: use NAME=value.")
        value = value.strip()
        if len(value) > 1 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


def main():
    if sys.version_info < (3, 12):
        raise RuntimeError(
            "Python 3.12 or newer is required; Python 3.12 is the tested version."
        )
    load_environment()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")))
    parser.add_argument(
        "--use-current-env",
        action="store_true",
        help="Use the current Python environment without installing packages.",
    )
    parser.add_argument("--install-only", action="store_true")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild React with npm ci and npm run build.",
    )
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        raise ValueError("Port must be between 1 and 65535.")
    requirements = ROOT / "backend" / "requirements.txt"
    if args.use_current_env:
        python = Path(sys.executable)
        missing = [
            name
            for name in [
                "uvicorn",
                "fastapi",
                "qiskit",
                "qiskit_aer",
                "qiskit_ibm_runtime",
                "pennylane",
                "numpy",
            ]
            if importlib.util.find_spec(name) is None
        ]
        if missing:
            raise RuntimeError(
                "Missing packages: "
                + ", ".join(missing)
                + ". Run without --use-current-env to install them."
            )
    else:
        env_path = ROOT / ".venv"
        python = env_path / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        if not python.exists():
            print("Creating a dedicated Python environment…", flush=True)
            venv.EnvBuilder(with_pip=True).create(env_path)
        stamp = env_path / ".quantum-requirements"
        digest = hashlib.sha256(requirements.read_bytes()).hexdigest()
        if not stamp.exists() or stamp.read_text() != digest:
            print(
                "Installing pinned quantum packages. The first start may take several minutes…",
                flush=True,
            )
            subprocess.run(
                [str(python), "-m", "pip", "install", "-r", str(requirements)],
                cwd=ROOT,
                check=True,
            )
            stamp.write_text(digest)
    if args.install_only:
        print("Python environment is ready.")
        return 0
    if args.rebuild:
        npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
        if not npm:
            raise RuntimeError(
                "Node.js 22 and npm are required to rebuild the frontend."
            )
        subprocess.run([npm, "ci"], cwd=ROOT, check=True)
        subprocess.run([npm, "run", "build"], cwd=ROOT, check=True)
    if not (ROOT / "dist" / "index.html").is_file():
        raise RuntimeError(
            "Frontend build is missing. Install Node.js 22 and run python start.py --rebuild."
        )
    os.environ.setdefault(
        "DATABASE_PATH", str(ROOT / "data" / "quantum-sandbox.sqlite3")
    )
    os.environ["FRONTEND_DIST"] = str(ROOT / "dist")
    os.environ["PYTHONPATH"] = (
        str(ROOT / "backend") + os.pathsep + os.environ.get("PYTHONPATH", "")
    )
    print(f"Quantum Sandbox → http://{args.host}:{args.port}", flush=True)
    print(
        "Press Ctrl+C to stop. Hardware is disabled unless explicitly configured.",
        flush=True,
    )
    return subprocess.call(
        [
            str(python),
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            args.host,
            "--port",
            str(args.port),
            "--workers",
            "1",
        ],
        cwd=ROOT,
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nQuantum Sandbox stopped.")
        raise SystemExit(0)
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"Cannot start Quantum Sandbox: {exc}", file=sys.stderr)
        raise SystemExit(1)
