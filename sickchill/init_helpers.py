import sys
from pathlib import Path


def setup_lib_path(additional=None):
    lib_path = Path('lib3').resolve()
    if lib_path.exists() and str(lib_path) not in sys.path:
        sys.path.insert(1, str(lib_path))
    if additional and additional not in sys.path:
        sys.path.insert(1, additional)


def setup_gettext(language=None):
    import gettext
    languages = [language] if language else None
    gt = gettext.translation('messages', str(Path('locale').resolve()), languages=languages, codeset='UTF-8')
    gt.install(names=["ngettext"])
