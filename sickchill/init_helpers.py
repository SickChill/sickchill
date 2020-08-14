import gettext
import os
import platform
import sys
import sysconfig


def setup_useragent():
    from random_user_agent.params import HardwareType, SoftwareEngine, SoftwareName, SoftwareType
    from random_user_agent.user_agent import UserAgent
    software_names = [SoftwareName.CHROME.value]
    software_types = [SoftwareType.WEB_BROWSER.value]
    operating_systems = [sys.platform]
    software_engines = [SoftwareEngine.WEBKIT.value]
    hardware_types = [HardwareType.COMPUTER.value]
    user_agent = UserAgent(operating_systems=operating_systems, software_types=software_types, hardware_types=hardware_types, software_names=software_names, software_engines=software_engines, limit=100)
    user_agents = [x['user_agent'] for x in user_agent.user_agents if platform.machine() in x]
    if user_agents:
        return user_agents[0]


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
