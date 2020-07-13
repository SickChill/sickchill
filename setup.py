# -*- coding: utf-8 -*
"""
Use setup tools to install sickchill
"""
# Stdlib Imports
import gettext
import os
import sys

# Third Party Imports
from setuptools import find_packages, setup

try:
    # Third Party Imports
    from babel.messages import frontend as babel
except ImportError:
    babel = None

ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__)))


info_dict = {'commands': {}}


with open(os.path.join(ROOT, 'requirements.txt'), 'r') as fp:
    info_dict['install_requires'] = [l for l in fp.readlines() if not l.startswith('#')]

with open(os.path.join(ROOT, 'readme.md'), 'r') as fp:
    info_dict['readme'] = fp.read()


if babel:
    info_dict['commands'].update({
        'compile_catalog': babel.compile_catalog,
        'extract_messages': babel.extract_messages,
        'init_catalog': babel.init_catalog,
        'update_catalog': babel.update_catalog
    })

# setup(
#     name="sickchill",
#     version="0.0.1",
#
#     description="Automatic Video Library Manager for TV Shows",
#     long_description=info_dict['readme'],
#
#     url='https://sickchill.github.io',
#     download_url='https://github.com/SickChill/SickChill.git',
#
#     author='miigotu',
#     author_email='miigotu@gmail.com',
#
#     license='GPLv2',
#
#     packages=find_packages(),
#     install_requires=info_dict['install_requires'],
#
#     test_suite="tests",
#     tests_require=[
#         'coveralls',
#         'nose',
#         'rednose',
#         'mock',
#         'vcrpy-unittest',
#         'babel',
#         'flake8-coding',
#         'isort'
#     ],
#     python_requires='>=2.7, <3',
#     classifiers=[
#         'Development Status :: 3 - Alpha',
#         'Intended Audience :: System Administrators',
#         'Operating System :: OS Independent',
#         'Topic :: Multimedia :: Video',
#     ],
#
#     cmdclass=info_dict['commands'],
#
#     # message_extractors={
#     #     'gui': [
#     #         ('**/views/**.mako', 'mako', {'input_encoding': 'utf-8'}),
#     #         ('**/js/*.min.js', 'ignore', None),
#     #         ('**/js/*.js', 'javascript', {'input_encoding': 'utf-8'})
#     #     ],
#     #     'sickchill': [('**.py', 'python', None)],
#     #     'sickbeard': [('**.py', 'python', None)],
#     # },
# )


def setup_lib_path(additional=None):
    lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'lib3'))
    if lib_path not in sys.path:
        sys.path.insert(1, lib_path)
    if additional and additional not in sys.path:
        sys.path.insert(1, additional)


def setup_gettext(language=None):
    languages = [language] if language else None
    gt = gettext.translation('messages', os.path.abspath(os.path.join(os.path.dirname(__file__), 'locale')), languages=languages, codeset='UTF-8')
    gt.install(names=["ngettext"])
