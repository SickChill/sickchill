kodipydent
==========
A complete Python client for the Kodi JSON-RPC API


Why?
----
Because JSON-RPC is one of the trickier communication schemes to write for. And if you want to code for it, then you're probably going to get into bit of a dysfunctional relationship with the documentation. 

What?
-----
A native-Python JSON-RPC client. Loads all the methods from your Kodi instance each time it gets instantiated, so you know you're never behind. And, it puts it in some semblance of a reasonable object structure.

Future updates will bundle a carefully-manicured static hive that will give you a better object structure at the cost of not always being completely up-to-date.

How?
----

.. code:: python

    >>> from kodipydent import Kodi
    >>> my_kodi = Kodi('192.168.1.1')
    >>> movies = my_kodi.VideoLibrary.GetMovies()

Simple as that. beekeeper makes it easy to use and easy to learn; if you don't know the name of the method you want to use, just do this:

.. code:: python

    >>> print(my_kodi)

and you'll get a printout of all the methods available, and all the variables each one takes.

Installation
------------

.. code:: bash

    $ pip install kodipydent

Under the Hood
--------------

kodipydent is driven by beekeeper, the family-friendly, object-oriented Python REST library. With beekeeper, even JSON-RPC clients are relatively simple to write. Don't believe me? Read the code. And you can check out `kodipydent/hive.json` to see what a full hive looks like.

Here's the full signature of the method to create your API:

.. code:: python

    Kodi(hostname[, port=8080, username='kodi', password=None])

"Advanced" Usage
----------------

kodipydent supports Kodi installations that have usernames and passwords set up. If you've created a password for web access, then simply construct your kodipydent instance as follows:

.. code:: python

    Kodi('localhost', username='kodi', password='myawesomepassword')


