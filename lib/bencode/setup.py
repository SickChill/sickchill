from setuptools import setup

setup(
    name = "BitTorrent-bencode",
    version = "5.0.8.1",
    py_modules = ['bencode', 'BTL'],
    # metadata for upload to PyPI
    author = "Bram Cohen",
    author_email = "bugs@bittorrent.com",
    description = "The BitTorrent bencode module as leight-weight, standalone package.",
    license = "BitTorrent Open Source License",
    keywords = "bittorrent bencode bdecode",
    url = "http://bittorrent.com/",
    zip_safe = True,
    test_suite = "test.testbencode",
    long_description = """This package simply re-packages the existing bencoding and bdecoding implemention from the 'official' BitTorrent client as a separate, leight-weight package for re-using them without having the entire BitTorrent software as a dependency.

It currently uses the implementation from BitTorrent Version 5.0.8, the file `bencode.py` is a verbatim, unmodified copy from that distribution.

It also contains some tests and a benchmark.
""",
)