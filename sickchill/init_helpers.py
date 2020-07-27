# coding=utf-8
# Author: Dustyn Gibson <miigotu@gmail.com>
# URL: https://sickchill.github.io
#
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.
# Stdlib Imports
import gettext
import os
import sys

# Third Party Imports
from random_user_agent.params import OperatingSystem, SoftwareName
from random_user_agent.user_agent import UserAgent

# from pathlib import Path


#
# def setup_lib_path(additional=None):
#     lib_path = Path('lib3').resolve()
#     if lib_path.exists() and str(lib_path) not in sys.path:
#         sys.path.insert(1, str(lib_path))
#     if additional and additional not in sys.path:
#         sys.path.insert(1, additional)
#
#
# def setup_gettext(language=None):
#     languages = [language] if language else None
#     try:
#         assert Path('locale').absolute().exists(), str(Path('../locale').absolute())
#     except AssertionError:
#         print(str(Path('../locale').absolute()))
#         raise
#
#     gt = gettext.translation('messages', str(Path('../locale').absolute()), languages=languages, codeset='UTF-8')
#     gt.install(names=["ngettext"])


def setup_useragent():
    software_names = [SoftwareName.CHROME.value]
    operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]

    return UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)

def setup_lib_path(additional=None):
    lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib3'))
    if lib_path not in sys.path:
        sys.path.insert(1, lib_path)
    if additional and additional not in sys.path:
        sys.path.insert(1, additional)


def setup_gettext(language=None):
    languages = [language] if language else None
    gt = gettext.translation('messages', os.path.abspath(os.path.join(os.path.dirname(__file__), '../locale')), languages=languages, codeset='UTF-8')
    gt.install(names=["ngettext"])
