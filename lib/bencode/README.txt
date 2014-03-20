This package simply re-packages the existing bencoding and bdecoding implemention from the 'official' BitTorrent client as a separate, leight-weight package for re-using them without having the entire BitTorrent software as a dependency.

It currently uses the implementation from BitTorrent Version 5.0.8, the file `bencode.py` is a verbatim, unmodified copy from that distribution.

It also contains some tests and a benchmark.

Tom Lazar, tom@tomster.org

HISTORY
=======

5.0.8.1 - 2010-12-19
--------------------

 - re-release containing packaging fixes. should now install on current
   versions of setuptools and distribute (also tested with Python 2.6 now)

5.0.8 - 2007-07-29
------------------

 - original release