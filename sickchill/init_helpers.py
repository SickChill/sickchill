import gettext
import os
import sys
import sysconfig


def setup_useragent():
    from random_user_agent.params import OperatingSystem, SoftwareName
    from random_user_agent.user_agent import UserAgent

    software_names = [SoftwareName.CHROME.value]
    operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]

    return UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)


def setup_lib_path(additional=None):
    lib_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lib3'))
    if lib_path not in sys.path:
        sys.path.insert(1, lib_path)
    if additional and additional not in sys.path:
        sys.path.insert(1, additional)


def sickchill_dir():
    return os.path.abspath(os.path.dirname(__file__))


def locale_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'locale'))


def setup_gettext(language=None):
    languages = [language] if language else None
    if not [key for key in ('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG') if key in os.environ]:
        os.environ['LC_MESSAGES'] = 'en_US.UTF-8'
    gt = gettext.translation('messages', locale_dir(), languages=languages)
    gt.install(names=["ngettext"])


def check_installed():
    for location in sysconfig.get_paths():
        if sickchill_dir().startswith(location):
            return True
    return False
