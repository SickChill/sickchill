import gettext
import os
import subprocess


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
        from importlib.metadata import Distribution, PackageNotFoundError
    except ImportError:
        from importlib_metadata import Distribution, PackageNotFoundError

    try:
        Distribution.from_name("sickchill")
    except PackageNotFoundError:
        return False
    return True


def pip_install(packages):
    if not isinstance(packages, list):
        packages = [packages]

    args = ["pip", "install", "--no-input", "--disable-pip-version-check", "--no-color", "--no-python-version-warning", "-qqU"]
    args.extend(packages)
    try:
        subprocess.check_call(args)
    except subprocess.CalledProcessError:
        try:
            args.append("--user")
            subprocess.check_call(args)
        except subprocess.CalledProcessError:
            return False
    return True


def poetry_install():
    if not check_installed():
        pip_install("poetry")
        requirements = subprocess.getoutput(["poetry export -f requirements.txt --without-hashes"]).splitlines()
        pip_install(requirements)
