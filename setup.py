# -*- coding: utf-8 -*
"""
Use setup tools to install sickchill
"""
import os

from setuptools import find_packages, setup
from requirements.sort import file_to_dict

try:
    from babel.messages import frontend as babel
except ImportError:
    babel = None

ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__)))

with open(os.path.join(ROOT, 'readme.md'), 'r') as r:
    long_description = r.read()


def get_requirements(rel_file_path):
    file_path = os.path.join(ROOT, rel_file_path)
    data = file_to_dict(file_path)
    if data is False:
        print('get_requirements failed')
        return []
    return [pkg['install'] for pkg in data
            if pkg['active'] and pkg['install']]

requirements = get_requirements('requirements/requirements.txt')
commands = {}
if babel:
    commands.update({
        'compile_catalog': babel.compile_catalog,
        'extract_messages': babel.extract_messages,
        'init_catalog': babel.init_catalog,
        'update_catalog': babel.update_catalog
    })

setup(
    name="sickchill",
    version="0.0.1",

    description="Automatic Video Library Manager for TV Shows",
    long_description=long_description,

    url='https://sickchill.github.io',
    download_url='https://github.com/SickChill/SickChill.git',

    author='miigotu',
    author_email='miigotu@gmail.com',

    license='GPLv2',

    packages=find_packages(),
    # install_requires=requirements,  # Commented-out for now
    install_requires=[
        'pytz',
        'requests',
        'mako',
        'configobj'
    ],

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
    python_requires='>=2.7, <3',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Multimedia :: Video',
    ],

    cmdclass=commands,

    message_extractors={
        'gui': [
            ('**/views/**.mako', 'mako', {'input_encoding': 'utf-8'}),
            ('**/js/*.min.js', 'ignore', None),
            ('**/js/*.js', 'javascript', {'input_encoding': 'utf-8'})
        ],
        'sickchill': [('**.py', 'python', None)],
        'sickbeard': [('**.py', 'python', None)],
    },
)
