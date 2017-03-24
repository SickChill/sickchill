"""
Use setup tools to install sickrage
"""
import os

from babel.messages import frontend as babel
from setuptools import find_packages, setup

ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__)))

with open(os.path.join(ROOT, 'readme.md'), 'r') as r:
    long_description = r.read()

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
    install_requires=[
        'pytz',
        'requests',
        'mako',
        'configobj',
        'putio.py'
    ],

    test_suite="tests",
    tests_require=[
        'coveralls',
        'nose',
        'rednose',
        'mock',
        'vcrpy-unittest',
        'babel'
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
