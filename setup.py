#!/usr/bin/env python3
import sys
from pathlib import Path

from setuptools import setup

info_dict = {'commands': {}}


with open(Path('requirements.txt').absolute()) as fp:
    info_dict['install_requires'] = [line for line in fp.readlines() if not line.startswith('#') and not line.startswith('git+')]


if 'setup.py' in sys.argv[0]:
    setup(
        packages=['sickchill'],
        install_requires=info_dict['install_requires'],
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
        use_scm_version={
            'write_to': 'sickchill/version.py',
            'write_to_template': '__version__ = "{version}"',
            'tag_regex': r'^(?P<prefix>v)?(?P<version>[^\+]+)(?P<suffix>.*)?$'
        }
    )
