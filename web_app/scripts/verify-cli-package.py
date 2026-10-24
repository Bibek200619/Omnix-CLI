"""Verify Python release candidates from tracked source without publishing.

Run with Python >=3.12 and uv installed. Output must be a new directory.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import tomllib


def run(*args: str, cwd: Path, capture: bool = False) -> str:
    result = subprocess.run(
        args,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
    )
    return result.stdout.strip() if capture else ""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ref", default="HEAD", help="Reviewed commit or existing cli-vVERSION tag"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        parser.error("Output directory must not already exist.")
    root = Path(__file__).resolve().parents[2]
    commit = run(
        "git",
        "rev-parse",
        "--verify",
        "--end-of-options",
        f"{args.ref}^{{commit}}",
        cwd=root,
        capture=True,
    )
    archive = subprocess.run(
        ["git", "archive", commit, "ai-cli"],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    with tempfile.TemporaryDirectory(prefix="omnix-release-check-") as temporary:
        workspace = Path(temporary)
        with tarfile.open(fileobj=io.BytesIO(archive)) as files:
            files.extractall(workspace, filter="data")
        source = workspace / "ai-cli"
        package = tomllib.loads((source / "pyproject.toml").read_text())["project"]
        version = package["version"]
        if args.ref.startswith("cli-v") and args.ref != f"cli-v{version}":
            parser.error("Tag must match the Python package version exactly.")
        run("uv", "sync", "--frozen", "--python", "3.12", "--extra", "dev", cwd=source)
        run("uv", "run", "--frozen", "pytest", "-q", cwd=source)
        run("uv", "build", cwd=source)
        artifacts = sorted(
            path
            for path in (source / "dist").iterdir()
            if path.is_file() and path.name != ".gitignore"
        )
        if (
            len(artifacts) != 2
            or not any(p.suffix == ".whl" for p in artifacts)
            or not any(p.name.endswith(".tar.gz") for p in artifacts)
        ):
            raise RuntimeError(
                "Expected exactly one wheel and one source distribution."
            )
        for index, artifact in enumerate(artifacts):
            environment = workspace / f"installed-{index}"
            run("uv", "venv", str(environment), "--python", "3.12", cwd=workspace)
            executable = environment / (
                "Scripts/python.exe" if os.name == "nt" else "bin/python"
            )
            run(
                "uv",
                "pip",
                "install",
                "--python",
                str(executable),
                str(artifact),
                cwd=workspace,
            )
            installed = run(
                str(executable),
                "-c",
                "from importlib.metadata import version; print(version('omnix-cli'))",
                cwd=workspace,
                capture=True,
            )
            if installed != version:
                raise RuntimeError("Installed package version does not match source.")
            cli = environment / (
                "Scripts/omnix.exe" if os.name == "nt" else "bin/omnix"
            )
            run(str(cli), "--help", cwd=workspace)
            project = workspace / f"project-{index}"
            run(
                str(cli),
                "init",
                "--project-name",
                "Release check",
                "--workspace",
                str(project),
                cwd=workspace,
            )
            for name in ("project.memory.json", "project.blueprint.json"):
                json.loads((project / ".project" / name).read_text())
        output.mkdir(parents=True)
        for artifact in artifacts:
            shutil.copy2(artifact, output / artifact.name)
        (output / "SHA256SUMS").write_text(
            "".join(
                f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n"
                for p in artifacts
            )
        )
        (output / "verification.json").write_text(
            json.dumps(
                {
                    "commit": commit,
                    "source_ref": args.ref,
                    "package": package["name"],
                    "version": version,
                    "python": "3.12",
                    "published": False,
                },
                indent=2,
            )
            + "\n"
        )
    print(f"Verified candidates and checksums: {output}")


if __name__ == "__main__":
    main()
