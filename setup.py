# -*- coding: utf-8 -*
"""
Use setup tools to install sickrage
"""
import os
import re

from babel.messages import frontend as babel
from setuptools import find_packages, setup

ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__)))

with open(os.path.join(ROOT, 'readme.md'), 'r') as r:
    long_description = r.read()

def get_requirements(rel_file_path):
    unique_reqs = set()
    with open(os.path.join(ROOT, rel_file_path), 'r') as reqs_f:
        for pkg in reqs_f.readlines():
            pkg = pkg.strip()
            # Discard all commented-out packages, notes and empty lines
            if not pkg or pkg.startswith('#'):
                continue
            pkg_match = re.match(r'^(?P<pkg>[\w\-.]+[=]{2}[\d.]+)(\s*#+\s*(?P<note>.*))*?$', pkg)
            if pkg_match:
                unique_reqs.add(pkg_match.group(1))
            else:
                print('Unable to read package line: {}'.format(pkg))
                return None
    return sorted(unique_reqs, key=str.lower)

requirements = get_requirements('requirements/requirements.txt')
if not requirements:
    raise AssertionError('get_requirements failed')

setup(
    name="sickrage",
    version="0.0.1",

    description="Automatic Video Library Manager for TV Shows",
    long_description=long_description,

    url='https://sickrage.github.io',
    download_url='https://github.com/SickRage/SickRage.git',

    author='miigotu',
    author_email='miigotu@gmail.com',

    license='GPLv2',

    packages=find_packages(),
    install_requires=requirements,

    test_suite="tests",
    tests_require=[
        'coveralls',
        'nose',
        'rednose',
        'mock',
        'vcrpy-unittest',
        'babel',
        'flake8-coding',
        'isort'
    ],

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Multimedia :: Video',
    ],

    cmdclass={
        'compile_catalog': babel.compile_catalog,
        'extract_messages': babel.extract_messages,
        'init_catalog': babel.init_catalog,
        'update_catalog': babel.update_catalog
    },

    message_extractors={
        'gui': [
            ('**/views/**.mako', 'mako', {'input_encoding': 'utf-8'}),
            ('**/js/*.min.js', 'ignore', None),
            ('**/js/*.js', 'javascript', {'input_encoding': 'utf-8'})
        ],
        'sickrage': [('**.py', 'python', None)],
        'sickbeard': [('**.py', 'python', None)],
    },
)
