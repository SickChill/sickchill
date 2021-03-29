#!/usr/bin/env python3
import sys

import toml
from setuptools import setup

with open("pyproject.toml", "r") as f:
    requirements = toml.loads(f.read())

prod = requirements["tool"]["poetry"]["dependencies"]
dev = requirements["tool"]["poetry"]["dev-dependencies"]

if 'setup.py' in sys.argv[0]:
    setup(
        packages=['sickchill'],
        install_requires=[item + prod[item].replace('^', '>=') if prod[item] != '*' else item for item in prod],
        extras_require={'dev': [item + dev[item].replace('^', '>=') if dev[item] != '*' else item for item in dev]},
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
