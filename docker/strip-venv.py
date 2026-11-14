"""Remove build-only files from the runtime virtualenv before it is copied."""

from __future__ import annotations

import os
import shutil
import sysconfig
from pathlib import Path


def main() -> None:
    root = Path(sysconfig.get_path("purelib"))
    drop_names = {
        "wheel",
        "setuptools_rust",
        "poetry",
    }
    for path in list(root.iterdir()):
        name = path.name
        pkg = name.split("-", 1)[0]
        if name in drop_names or pkg in drop_names or name == "distutils-precedence.pth":
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)

    for dirpath, _dirnames, _filenames in os.walk(root, topdown=False):
        if os.path.basename(dirpath) in {"__pycache__", "tests", "test", "testing"}:
            shutil.rmtree(dirpath, ignore_errors=True)

    locale_dir = root / "sickchill" / "locale"
    if locale_dir.is_dir():
        for extra in locale_dir.rglob("*"):
            if extra.suffix in {".po", ".pot"}:
                extra.unlink(missing_ok=True)

    venv = Path(os.environ["POETRY_VIRTUALENVS_PATH"])
    for binary in ("wheel", "poetry"):
        for path in venv.joinpath("bin").glob(binary + "*"):
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
