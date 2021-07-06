import gettext
import os
import subprocess
import sys


def sickchill_dir():
    return os.path.abspath(os.path.dirname(__file__))


def locale_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "locale"))


def setup_gettext(language=None):
    languages = [language] if language else None
    if not [key for key in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG") if os.environ.get(key)]:
        os.environ["LC_MESSAGES"] = "en_US.UTF-8"
    print(locale_dir())
    gt = gettext.translation("messages", locale_dir(), languages=languages, fallback=True)
    gt.install(names=["ngettext"])


def check_installed():
    try:
        from importlib.metadata import Distribution, PackageNotFoundError  # noqa
    except ImportError:
        from importlib_metadata import Distribution, PackageNotFoundError  # noqa

    try:
        Distribution.from_name("sickchill")
    except PackageNotFoundError:
        return False
    return True


def print_result(result: str, error: subprocess.CalledProcessError = None, log=print):
    if not log:
        return

    if result:
        log(result)
    if error:
        if error.stdout:
            log(error.stdout)
        if error.stderr:
            log(error.stderr)


def pip_install(packages, log=print):
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


def poetry_install():
    if not check_installed():
        pip_install(["setuptools", "poetry", "--pre"])
        requirements = subprocess.getoutput(["poetry export -f requirements.txt --without-hashes"]).splitlines()
        pip_install(requirements)
