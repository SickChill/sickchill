import gettext
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, List, Union

sickchill_module = Path(__file__).parent.resolve()
pyproject_path = sickchill_module.parent / "pyproject.toml"
# locale_dir = sickchill_dir / "locale"


def sickchill_dir():
    return os.path.abspath(os.path.dirname(__file__))


def locale_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "locale"))


def setup_gettext(language: str = None) -> None:
    languages = [language] if language else None
    if not [key for key in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG") if os.environ.get(key)]:
        os.environ["LC_MESSAGES"] = "en_US.UTF-8"
    gt = gettext.translation("messages", locale_dir(), languages=languages, fallback=True)
    gt.install(names=["ngettext"])


def check_installed(name: str = __package__) -> bool:
    try:
        from importlib.metadata import Distribution, PackageNotFoundError  # noqa
    except ImportError:
        try:
            from importlib_metadata import Distribution, PackageNotFoundError  # noqa
        except ImportError:
            requirements = subprocess.getoutput([f"{sys.executable} -m pip freeze"]).splitlines()
            return name in [req.split("==")[0] for req in requirements]

    try:
        Distribution.from_name(name)
    except PackageNotFoundError:
        return False
    return True


def print_result(result: Union[str, List[str]], error: subprocess.CalledProcessError = None, log: Callable[[str], None] = print) -> None:
    if not log:
        return

    if result:
        if isinstance(result, list):
            for line in result:
                log(line)

        log(result)
    if error:
        if error.stdout:
            log(error.stdout)
        if error.stderr:
            log(error.stderr)


def pip_install(packages: Union[List[str], str], log: Callable[[str], None] = print) -> bool:
    if not isinstance(packages, list):
        packages = [packages]

    args = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--no-input",
        "--disable-pip-version-check",
        "--no-python-version-warning",
        "--no-color",
        "--trusted-host=pypi.org",
        "--trusted-host=files.pythonhosted.org",
        "-qqU",
    ]

    args.extend(packages)

    result = ""
    try:
        result = subprocess.check_output(args, text=True)
    except subprocess.CalledProcessError as error:
        print_result(result, error, log)
        try:
            args.append("--user")
            result = subprocess.check_output(args, text=True)
        except subprocess.CalledProcessError as error:
            print_result(result, error, log)
            return False

    print_result(result, log=log)
    return True


def poetry_install() -> None:
    if not check_installed():
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            pip_install(["setuptools", "poetry", "--pre"])
            requirements = subprocess.getoutput(
                [f"cd {pyproject_path.parent} && {sys.executable} -m poetry export -f requirements.txt --without-hashes"]
            ).splitlines()
            if len(requirements) <= 1:
                print_result(requirements)
            else:
                pip_install(requirements)
