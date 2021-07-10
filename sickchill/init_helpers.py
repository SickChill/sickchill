import gettext
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Union

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
            # Should not get here EVER, but just in case lets just try checking pip freeze instead
            result, output = subprocess.getstatusoutput([f"{sys.executable} -m pip freeze"])
            if result != 0:  # Not Ok
                return False
            return name in [requirement.split("==")[0] for requirement in output.splitlines()]

    try:
        Distribution.from_name(name)
    except PackageNotFoundError:
        return False
    return True


def in_virtualenv():
    base_prefix = getattr(sys, "base_prefix", getattr(sys, "real_prefix", sys.prefix))
    return base_prefix != sys.prefix


def pip_install(packages: Union[List[str], str]) -> bool:
    if not isinstance(packages, list):
        packages = packages.splitlines()

    cmd = [
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

    cmd.extend(packages)

    result, output = subprocess.getstatusoutput(cmd)
    if result != 0:  # Not Ok
        print(output)
        cmd.append("--user")
        result, output = subprocess.getstatusoutput(cmd)
        if result != 0:  # Not Ok
            print(output)
            return False

    print(output)
    return True


def make_virtualenv_and_rerun(location: Path) -> None:
    """
    This is a hail mary, when we cannot install to the already existing virtualenv because
    someone created it as root or another user than the user running this process

    Creates a .venv dir in project root (which is gitignored already)
    if found SC will restart automatically using tthe environment in .venv
    """

    location = location.resolve()
    current_interpreter = Path(sys.executable).resolve()
    current_venv_root = current_interpreter.parent.parent

    result = 0  # Ok

    if str(location) == str(current_venv_root):
        if in_virtualenv():
            print(f"Unable to install to the existing virtual environment located at {current_venv_root}")
            print("Please check the permissions, and that it does not include global site packages")
        result = 126  # Command invoked cannot execute
    else:
        if not location.is_dir():
            print(f"Because of the above errors, we will try creating a new virtualenvironment in {location}")
            if not check_installed("virtualenv"):
                print("virtualenv module not found, cannot create virtualenv")
                result = 126  # Command invoked cannot execute
            else:
                result, output = subprocess.getstatusoutput(f"{sys.executable} -m virtualenv {location}")
                if result != 0:  # Not Ok
                    print(output)
                    print("Due to the above error, we cannot continue! Exiting")
                else:
                    print(f"Created new virtualenvironment in {location}")

            if result == 0:  # Ok
                # append the bin/python.ext to the new venv path
                for part in current_interpreter.parts[-2:]:
                    location = location / part

                # add original arguments to this re-call
                new_argv = [str(location)] + sys.argv
                print(f"Restarting SickChill with {new_argv}")

                subprocess.run(new_argv, cwd=os.getcwd(), universal_newlines=True)

    os._exit(result)


def poetry_install() -> None:
    if not check_installed():
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        pyproject_path = pyproject_path.resolve()

        if pyproject_path.exists():
            pip_install(["setuptools", "poetry", "--pre"])
            if check_installed("poetry"):
                result, output = subprocess.getstatusoutput(
                    f"cd {pyproject_path.parent} && {sys.executable} -m poetry export -f requirements.txt --without-hashes"
                )
                if result != 0:  # Not Ok
                    print(output)
                    make_virtualenv_and_rerun(pyproject_path.with_name(".venv"))
                else:
                    pip_install(output)
            else:
                make_virtualenv_and_rerun(pyproject_path.with_name(".venv"))
