#!/usr/bin/env python3
# Stdlib Imports
import sys
from pathlib import Path

# Third Party Imports
from setuptools import find_namespace_packages, setup

info_dict = {'commands': {}}


with open(Path('requirements.txt').absolute(), 'r') as fp:
    info_dict['install_requires'] = [line for line in fp.readlines() if not line.startswith('#') and not line.startswith('git+')]


if 'setup.py' in sys.argv[0]:
    setup(
        packages=find_namespace_packages(
            exclude=[
                "*.tests", "*.tests.*", "tests.*", "tests",
                "lib3.*", "lib3",
                "build", "build.*",
                "dist", "dist.*",
                "cache", "cache.*",
                "Logs", "Logs.*"
            ]
        ),
        install_requires=info_dict['install_requires'],
        test_suite="tests",
        cmdclass=info_dict['commands'],

        message_extractors={
            'gui': [
                ('**/views/**.mako', 'mako', {'input_encoding': 'utf-8'}),
                ('**/js/*.min.js', 'ignore', None),
                ('**/js/*.js', 'javascript', {'input_encoding': 'utf-8'})
            ],
            'sickchill': [('**.py', 'python', None)],
        },
        include_package_data=True,
    )
