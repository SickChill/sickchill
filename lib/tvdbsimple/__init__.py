# -*- coding: utf-8 -*-

"""
`tvdbsimple` is a wrapper, written in Python, for TheTVDb.com 
API v2.  By calling the functions available in `tvdbsimple` you can simplify 
your code and easily access a vast amount of tv and cast data. To find 
out more about TheTVDb API, check out the [official api page](https://api.thetvdb.com/swagger/)

Features
--------

- Full API implementation. Supports Search, Series, Episode, Updated, User and Languages methods.
- Updated with the latest JSON API. 
- Fully tested with automated tests and travis.ci.
- Supports Python 2.7, 3.3, 3.4, 3.5, 3.6.
- Easy to access data using Python class attributes.
- Easy to experiment with `tvdbsimple` functions inside the Python interpreter.

Installation
------------

`tvdbsimple` is available on the [Python Package Index](https://pypi.python.org/pypi/tvdbsimple).

You can install `tvdbsimple` using one of the following techniques:

- Use pip:  `pip install tvdbsimple`
- Download the .zip or .tar.gz file from PyPI and install it yourself
- Download the [source from Github](http://github.com/phate89/tvdbsimple) and install it yourself

If you install it yourself, also install [requests](http://www.python-requests.org/en/latest).

API Key
-------
You will need an API key to TheTVDb to access the API.  To obtain a key, follow these steps:

1) Register for and verify an [account](http://thetvdb.com/?tab=register).
2) [Log into](http://thetvdb.com/?tab=login) your account.
3) [Go to this page](http://thetvdb.com/?tab=apiregister) and fill your details to generate a new API key.

Examples
--------
All the functions are fully documented here but you can find several use examples in the [examples page](https://github.com/phate89/tvdbsimple/blob/master/EXAMPLES.rst).

License
-------
The module is distributed with a GPLv3 license, see [LICENSE](https://www.gnu.org/licenses/gpl-3.0.en.html) for more details

copyright (c) 2017 by phate89.
"""

__title__ = 'tvdbsimple'
__version__ = '1.0.6'
__author__ = 'phate89'
__copyright__ = 'Copyright © 2017 phate89'
__license__ = 'GPLv3'

from .base import APIKeyError
from .keys import keys
from .search import Search
from .series import Series, Series_Episodes, Series_Images
from .languages import Languages
from .episode import Episode
from .updates import Updates
from .user import User, User_Ratings

KEYS=keys()
"""
Contains `API_KEY` and `API_TOKEN`.

To use the module you have to set at least the `API_KEY` value (THETVDb api key).
You can also provide an `API_TOKEN` if you already have a valid one stored. If the 
valid token doesn't work anymore the module will try to retrieve a new one
using the `API_KEY` variable
"""
