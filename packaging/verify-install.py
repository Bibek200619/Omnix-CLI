"""Exercise install, PATH discovery, upgrade and removal from a local release bundle."""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path


def run(*args: str, env: dict[str, str], capture: bool = False) -> str:
    result = subprocess.run(
        args,
        check=True,
        env=env,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
    )
    return result.stdout.strip() if capture else ""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--requirements", type=Path, required=True)
    parser.add_argument("--target", required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    version = tomllib.loads((root / "ai-cli/pyproject.toml").read_text())["project"]["version"]
    with tempfile.TemporaryDirectory(prefix="omnix-install-check-") as temporary:
        temp = Path(temporary)
        release = temp / "release"
        release.mkdir()
        archive = release / f"omnix-{args.target}.tar.gz"
        subprocess.run(
            [
                sys.executable,
                str(root / "packaging/create-bundle.py"),
                "--binary",
                str(args.binary.resolve()),
                "--wheel-dir",
                str(args.wheel.parent.resolve()),
                "--requirements",
                str(args.requirements.resolve()),
                "--uninstaller",
                str(root / "packaging/uninstall.sh"),
                "--target",
                args.target,
                "--output",
                str(archive),
            ],
            check=True,
            env={**os.environ, "SOURCE_DATE_EPOCH": "0"},
        )
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        (release / "SHA256SUMS").write_text(f"{digest}  {archive.name}\n")

        data_home = temp / "data"
        bin_dir = temp / "bin"
        env = os.environ.copy()
        env.update(
            {
                "OMNIX_INSTALL_PYTHON": sys.executable,
                "OMNIX_DATA_HOME": str(data_home),
                "OMNIX_BIN_DIR": str(bin_dir),
                "OMNIX_RELEASE_BASE_URL": release.as_uri(),
                "PATH": f"{bin_dir}{os.pathsep}{env.get('PATH', '')}",
            }
        )
        installer = root / "packaging/install.sh"
        run("sh", str(installer), env=env)
        installed = bin_dir / "omnix"
        if run("sh", "-c", "command -v omnix", env=env, capture=True) != str(installed):
            raise RuntimeError("The installed omnix command is not discoverable through PATH.")
        if run(str(installed), "--version", env=env, capture=True) != version:
            raise RuntimeError("The installed command does not report the package version.")

        project = temp / "project"
        run(
            str(installed),
            "init",
            "--project-name",
            "Installer check",
            "--workspace",
            str(project),
            env=env,
        )
        memory = project / ".project/project.memory.json"
        if not memory.is_file():
            raise RuntimeError("The installed engine did not initialize project state.")

        startup = subprocess.run(
            [str(installed)],
            input="",
            env={**env, "TERM": "dumb"},
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=True,
        ).stdout
        if "Omnix CLI" not in startup:
            raise RuntimeError("The installed TUI could not start the Python bridge.")

        run("sh", str(installer), env=env)
        run("sh", str(data_home / "omnix/uninstall.sh"), env=env)
        if installed.exists() or (data_home / "omnix").exists():
            raise RuntimeError("Uninstall did not remove the launcher and runtime.")
        if not memory.is_file():
            raise RuntimeError("Uninstall removed project state outside the install directory.")

    print(f"Install, PATH, engine, upgrade and uninstall checks passed for {args.target}.")


if __name__ == "__main__":
    main()
