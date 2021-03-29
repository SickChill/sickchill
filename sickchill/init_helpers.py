import gettext
import os
import sys


def setup_lib_path(additional=None):
    lib_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "lib3"))
    if lib_path not in sys.path:
        sys.path.insert(1, lib_path)
    if additional and additional not in sys.path:
        sys.path.insert(1, additional)


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
