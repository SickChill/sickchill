"""
Use setup tools to install sickrage
"""
import os
from setuptools import find_packages, setup

ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__)))

with open(os.path.join(ROOT, 'readme.md'), 'r') as r:
    long_description = r.read()

setup(
    name="sickrage",
    version="0.0.1",
    description="Automatic Video Library Manager for TV Shows",
    long_description=long_description,
    packages=find_packages(),
    install_requires=[],
    test_suite="tests",
    tests_require=[
        'coveralls',
        'nose',
        'rednose',
        'mock',
    ],
    classifiers=[
        'Development Status :: ???',
        'Intended Audience :: Developers',
        'Operating System :: POSIC :: LINUX',
        'Topic :: ???',
    ],
)
