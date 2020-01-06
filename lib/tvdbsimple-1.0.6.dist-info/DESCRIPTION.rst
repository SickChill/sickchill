TheTVDb wrapper module
======================

.. image:: https://travis-ci.org/phate89/tvdbsimple.svg?branch=master
   :target: https://travis-ci.org/phate89/tvdbsimple


*tvdbsimple* is a wrapper, written in Python, for TheTVDB API v2.  By calling the functions available in *tvdbsimple* you can simplify your code and easily access a vast amount of tv series data.  To learn more about TheTVDb API, check out the `website api page`_.

.. _website api page: https://api.thetvdb.com/swagger/.

Features
--------

- Full API implementation. Supports Search, Series, Episode, Updated, User and Languages methods.
- Updated with the latest JSON API. 
- Fully tested with automated tests and travis.ci.
- Supports Python 2.7, 3.3, 3.4, 3.5, 3.6.
- Easy to access data using Python class attributes.
- Easy to experiment with *tvdbsimple* functions inside the Python interpreter.

Installation
------------

*tvdbsimple* is available on the `Python Package Index`_ (PyPI).

.. _Python Package Index: https://pypi.python.org/pypi/tvdbsimple

You can install *tvdbsimple* using one of the following techniques:

- Use pip:  :code:`pip install tvdbsimple`
- Download the .zip or .tar.gz file from PyPI and install it yourself
- Download the `source from Github`_ and install it yourself

If you install it yourself, also install requests_.

.. _source from Github: http://github.com/phate89/tvdbsimple
.. _requests: http://www.python-requests.org/en/latest

API Key
-------
You will need an API key to TheTVDb to access the API.  To obtain a key, follow these steps:

1) Register for and verify an account_.
2) `Log into`_ your account.
3) `Go to this page`_ and fill your details to generate a new API key.

.. _account: http://thetvdb.com/?tab=register
.. _Log into: http://thetvdb.com/?tab=login
.. _Go to this page: http://thetvdb.com/?tab=apiregister

Documentation
-------------
All the functions are fully documented in the docs folder and in the `github wiki page`_ but you can find several use examples in the `examples page`_.

.. _github wiki page: https://github.com/phate89/tvdbsimple/wiki
.. _examples page: https://github.com/phate89/tvdbsimple/blob/master/EXAMPLES.rst

Issues
------
If you find any issue please post `in the github issue page`_ with all the information possible to reproduce the issue

.. _in the github issue page: https://github.com/phate89/tvdbsimple/issues

Support
-------

- If you would like contribute to the projects, feel free to do: fork, pull-request, issues, etc... They're higly welcome
- Instead if you would like offer me a coffee or beer: `Donate with PayPal`_

.. _Donate with PayPal: https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=JD4LD62T6EJRS&lc=GB&item_name=phate89%20Kodi%20Addons&currency_code=USD&bn=PP%2dDonationsBF%3abtn_donate_LG%2egif%3aNonHosted

Thanks
------

- To celiao_, her tmdbsimple_ module inspired my work here
- To BurntSushi_, his pdoc_ module helped me documenting the module
- To TheTVDb website for providing the content and the api

.. _celiao: https://github.com/celiao
.. _tmdbsimple: https://github.com/celiao/tmdbsimple
.. _BurntSushi: https://github.com/BurntSushi
.. _pdoc: https://github.com/BurntSushi/pdoc


