#!/usr/bin/env python3
import re
import sys

import toml
from setuptools import setup

with open("pyproject.toml", "r") as f:
    pyproject = toml.loads(f.read())

config = pyproject["tool"]["poetry"]
prod = config["dependencies"]
dev = config["dev-dependencies"]

author = None
author_email = None
def parse_authors():
    global author
    global author_email

    parsed = re.match(r"(?P<name>.*) <(?P<email>.*)>", config["authors"][0])
    author, author_email = parsed.groups()

if "setup.py" in sys.argv[0] or 'poetry' in sys.argv[0]:
    parse_authors()
    setup(
        name=config["name"],
        packages=["sickchill"],
        version=config["version"],
        description=config["description"],
        author=author,
        author_email=author_email,
        license=config["license"],
        url=config["homepage"],
        download_url=config["repository"],
        classifiers=config["classifiers"],
        install_requires=[item + prod[item].replace("^", ">=") if prod[item] != "*" else item for item in prod],
        extras_require={"dev": [item + dev[item].replace("^", ">=") if dev[item] != "*" else item for item in dev]},
        message_extractors={
            "gui": [
                ("**/views/**.mako", "mako", {"input_encoding": "utf-8"}),
                ("**/js/*.min.js", "ignore", None),
                ("**/js/*.js", "javascript", {"input_encoding": "utf-8"})
            ],
            "sickchill": [("**.py", "python", None)],
        },
        include_package_data=True,
    )
