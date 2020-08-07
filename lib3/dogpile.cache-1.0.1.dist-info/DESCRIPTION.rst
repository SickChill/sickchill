dogpile
=======

Dogpile consists of two subsystems, one building on top of the other.

``dogpile`` provides the concept of a "dogpile lock", a control structure
which allows a single thread of execution to be selected as the "creator" of
some resource, while allowing other threads of execution to refer to the previous
version of this resource as the creation proceeds; if there is no previous
version, then those threads block until the object is available.

``dogpile.cache`` is a caching API which provides a generic interface to
caching backends of any variety, and additionally provides API hooks which
integrate these cache backends with the locking mechanism of ``dogpile``.

Overall, dogpile.cache is intended as a replacement to the `Beaker
<https://pypi.org/project/Beaker/>`_ caching system, the internals of which are
written by the same author.   All the ideas of Beaker which "work" are re-
implemented in dogpile.cache in a more efficient and succinct manner, and all
the cruft (Beaker's internals were first written in 2005) relegated to the
trash heap.

Documentation
-------------

See dogpile.cache's full documentation at
`dogpile.cache documentation <https://dogpilecache.sqlalchemy.org>`_.  The
sections below provide a brief synopsis of the ``dogpile`` packages.

Features
--------

* A succinct API which encourages up-front configuration of pre-defined
  "regions", each one defining a set of caching characteristics including
  storage backend, configuration options, and default expiration time.
* A standard get/set/delete API as well as a function decorator API is
  provided.
* The mechanics of key generation are fully customizable.   The function
  decorator API features a pluggable "key generator" to customize how
  cache keys are made to correspond to function calls, and an optional
  "key mangler" feature provides for pluggable mangling of keys
  (such as encoding, SHA-1 hashing) as desired for each region.
* The dogpile lock, first developed as the core engine behind the Beaker
  caching system, here vastly simplified, improved, and better tested.
  Some key performance
  issues that were intrinsic to Beaker's architecture, particularly that
  values would frequently be "double-fetched" from the cache, have been fixed.
* Backends implement their own version of a "distributed" lock, where the
  "distribution" matches the backend's storage system.  For example, the
  memcached backends allow all clients to coordinate creation of values
  using memcached itself.   The dbm file backend uses a lockfile
  alongside the dbm file.  New backends, such as a Redis-based backend,
  can provide their own locking mechanism appropriate to the storage
  engine.
* Writing new backends or hacking on the existing backends is intended to be
  routine - all that's needed are basic get/set/delete methods. A distributed
  lock tailored towards the backend is an optional addition, else dogpile uses
  a regular thread mutex. New backends can be registered with dogpile.cache
  directly or made available via setuptools entry points.
* Included backends feature three memcached backends (python-memcached, pylibmc,
  bmemcached), a Redis backend, a backend based on Python's
  anydbm, and a plain dictionary backend.
* Space for third party plugins, including one which provides the
  dogpile.cache engine to Mako templates.


The SQLAlchemy Project
----------------------

Dogpile is part of the `SQLAlchemy Project <https://www.sqlalchemy.org>`_ and
adheres to the same standards and conventions as the core project.

Development / Bug reporting / Pull requests
___________________________________________

Please refer to the
`SQLAlchemy Community Guide <https://www.sqlalchemy.org/develop.html>`_ for
guidelines on coding and participating in this project.

Code of Conduct
_______________

Above all, SQLAlchemy places great emphasis on polite, thoughtful, and
constructive communication between users and developers.
Please see our current Code of Conduct at
`Code of Conduct <https://www.sqlalchemy.org/codeofconduct.html>`_.

License
-------

Dogpile is distributed under the `MIT license
<https://opensource.org/licenses/MIT>`_.


