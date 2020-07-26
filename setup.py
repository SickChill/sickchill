#!/usr/bin/env python3
# -*- coding: utf-8 -*
"""
Use setup tools to install sickchill
"""
# Stdlib Imports
import sys
from pathlib import Path

# Third Party Imports
from setuptools import find_namespace_packages, setup


info_dict = {'commands': {}}


with open(Path('requirements.txt').absolute(), 'r') as fp:
    info_dict['install_requires'] = [line for line in fp.readlines() if not line.startswith('#') and not line.startswith('git+')]


with open(Path('readme.md').absolute(), 'r') as fp:
    long_description = fp.read()


if 'setup.py' in sys.argv[0]:
    setup(
        name="sickchill",
        version="0.0.2",

        description="Automatic Video Library Manager for TV Shows",
        long_description=long_description,
        long_description_content_type='text/markdown',

        url='https://sickchill.github.io',
        download_url='https://github.com/SickChill/SickChill.git',

        author='miigotu',
        author_email='miigotu@gmail.com',

        license='GPLv2',

        packages=find_namespace_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests", "lib3/*"]),
        install_requires=info_dict['install_requires'],

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
        python_requires='>=3.5',
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Intended Audience :: System Administrators',
            'Operating System :: OS Independent',
            'Topic :: Multimedia :: Video',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3 :: Only',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9'
        ],

        cmdclass=info_dict['commands'],

        message_extractors={
            'gui': [
                ('**/views/**.mako', 'mako', {'input_encoding': 'utf-8'}),
                ('**/js/*.min.js', 'ignore', None),
                ('**/js/*.js', 'javascript', {'input_encoding': 'utf-8'})
            ],
            'sickchill': [('**.py', 'python', None)],
            'sickbeard': [('**.py', 'python', None)],
        },
        scripts=['SickChill.py']
    )


