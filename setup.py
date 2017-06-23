# -*- coding: utf-8 -*
"""
Use setup tools to install sickrage
"""
import os

from babel.messages import frontend as babel
from setuptools import find_packages, setup
from requirements.sort import file_to_dict

ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__)))

with open(os.path.join(ROOT, 'readme.md'), 'r') as r:
    long_description = r.read()


def get_requirements(rel_file_path):
    file_path = os.path.join(ROOT, rel_file_path)
    data = [pkg['install'] for pkg in file_to_dict(file_path) if pkg['active'] and pkg['install']]
    return data


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
