timeago
=======

A very simple python lib, used to format datetime with ``*** time ago``
statement. Javascript version here. `timeago.js`_.

|Build Status| |PyPi Status| |Python Versions|

Such as:

::

   just now
   12 seconds ago
   3 minutes ago
   2 hours ago
   24 days ago
   6 months ago
   2 years ago

   in 12 seconds
   in 3 minutes
   in 2 hours
   in 24 days
   in 6 months
   in 2 years

For other languages see below.

Install
-------

.. code:: sh

   pip install timeago

.. _usage--example:

Usage & Example
---------------

.. code:: py

   # -*- coding: utf-8 -*-
   import timeago, datetime

   now = datetime.datetime.now() + datetime.timedelta(seconds = 60 * 3.4)

   date = datetime.datetime.now()

   # locale
   print (timeago.format(date, now, 'zh_CN')) # will print `3分钟前`

   # input datetime
   print (timeago.format(date, now)) # will print 3 minutes ago

   # input timedelta
   print (timeago.format(datetime.timedelta(seconds = 60 * 3.4))) # will print 3 minutes ago

   # input date, auto add time(0, 0, 0)
   print (timeago.format(datetime.date(2016, 5, 27), now))

   # input datetime formated string
   print (timeago.format('2016-05-27 12:12:03', '2016-05-27 12:12:12')) # will print just now

   # inverse two parameters
   print (timeago.format('2016-05-27 12:12:12', '2016-05-27 12:12:03')) # will print a while

.. _method--parameter:

Method & Parameter
------------------

only one API ``format``.

Three parameters of method ``format``:

-  ``date``: the parameter which will be formated, must be instance
   of ``datetime`` / ``timedelta`` or datetime formated string.
-  ``now``: reference time, must be instance of ``datetime`` or
   datetime formated string.
-  ``locale``: the locale code, default ``en``.

Locale
------

At the time we're speaking, `following locale`_ are available:

-  ``ar``
-  ``bg``
-  ``ca``
-  ``da``
-  ``de``
-  ``el``
-  ``en``
-  ``en_short``
-  ``es``
-  ``eu``
-  ``fa_IR``
-  ``fi``
-  ``fr``
-  ``gl``
-  ``he``
-  ``hu``
-  ``in_BG``
-  ``in_HI``
-  ``in_ID``
-  ``it``
-  ``ja``
-  ``ko``
-  ``lt``
-  ``ml``
-  ``my``
-  ``nb_NO``
-  ``nl``
-  ``nn_NO``
-  ``pl``
-  ``pt_BR``
-  ``ru``
-  ``sv_SE``
-  ``ta``
-  ``th``
-  ``tr``
-  ``uk``
-  ``vi``
-  ``zh_CN``
-  ``zh_TW``

Localization
------------

1. Fork the project
2. Create a locale python script called ``[name_of_your_locale].py``
   following the existing other locales.
3. Add the name of your locale in the Readme to keep it updated
   (**alphabetically**).
4. Add test case following the `english model`_
5. Create the Pull Request.

Notes
~~~~~

For complicated plurals, you can take example on the PL (Polish) locale
`here`_

.. _timeago.js: https://github.com/hustcc/timeago.js
.. _following locale: https://github.com/hustcc/timeago/tree/master/src/timeago/locales
.. _english model: https://github.com/hustcc/timeago/tree/master/test/testcase.py#L50
.. _here: https://github.com/hustcc/timeago/tree/master/src/timeago/locales/pl.py

.. |Build Status| image:: https://travis-ci.org/hustcc/timeago.svg?branch=master
   :target: https://travis-ci.org/hustcc/timeago
.. |PyPi Status| image:: https://img.shields.io/pypi/v/timeago.svg
   :target: https://pypi.python.org/pypi/timeago
.. |Python Versions| image:: https://img.shields.io/pypi/pyversions/timeago.svg
   :target: https://pypi.python.org/pypi/timeago

