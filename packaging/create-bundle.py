"""Create a normalized, checksummed platform bundle from release inputs."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import os
import shutil
import tarfile
import tempfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--wheel-dir", type=Path, required=True)
    parser.add_argument("--requirements", type=Path, required=True)
    parser.add_argument("--uninstaller", type=Path, required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    wheels = sorted(args.wheel_dir.glob("*.whl"))
    if len(wheels) != 1:
        parser.error("Expected exactly one Python engine wheel in --wheel-dir.")

    epoch = int(os.environ.get("SOURCE_DATE_EPOCH", "0"))
    with tempfile.TemporaryDirectory(prefix="omnix-bundle-") as temporary:
        bundle = Path(temporary)
        shutil.copy2(args.binary, bundle / "omnix")
        shutil.copy2(wheels[0], bundle / wheels[0].name)
        shutil.copy2(args.requirements, bundle / "requirements.txt")
        shutil.copy2(args.uninstaller, bundle / "uninstall.sh")
        (bundle / "omnix").chmod(0o755)
        (bundle / "uninstall.sh").chmod(0o755)

        checksummed = sorted(path for path in bundle.iterdir() if path.name != "SHA256SUMS")
        (bundle / "SHA256SUMS").write_text(
            "".join(
                f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n"
                for path in checksummed
            )
        )

        args.output.parent.mkdir(parents=True, exist_ok=True)
        with (
            args.output.open("wb") as raw,
            gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=epoch) as compressed,
            tarfile.open(fileobj=compressed, mode="w", format=tarfile.USTAR_FORMAT) as archive,
        ):
            for path in sorted(bundle.iterdir(), key=lambda item: item.name):
                info = archive.gettarinfo(str(path), arcname=path.name)
                info.uid = info.gid = 0
                info.uname = info.gname = ""
                info.mtime = epoch
                info.mode = 0o755 if path.name in {"omnix", "uninstall.sh"} else 0o644
                with path.open("rb") as contents:
                    archive.addfile(info, contents)

    print(f"Created normalized bundle for {args.target}: {args.output}")


if __name__ == "__main__":
    main()
