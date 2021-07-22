import hashlib
import os
import time
from functools import reduce
from pathlib import Path
from xml.etree import ElementTree

# http://www.radicand.org/blog/orz/2010/2/21/edonkey2000-hash-in-python/
import requests


def get_file_hash(filePath: Path):
    """Returns the ed2k hash of a given file."""

    md4 = hashlib.new("md4").copy

    def gen(f):
        while True:
            x = f.read(9728000)
            if x:
                yield x
            else:
                return

    def md4_hash(data):
        m = md4()
        m.update(data)
        return m

    with filePath.open("rb") as f:
        a = gen(f)
        hashes = [md4_hash(data).digest() for data in a]
        if len(hashes) == 1:
            return hashes[0].hex()
        else:
            return md4_hash(reduce(lambda b, c: b + c, hashes, b"")).hexdigest()


def download_file(url, filename: Path):
    try:
        r = requests.get(url, stream=True, verify=False)
        r.raise_for_status()
        with filename.open("wb") as fp:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    fp.write(chunk)
                    fp.flush()

    except requests.exceptions.RequestException:
        if filename.is_file():
            filename.unlink()
        return False

    return True


def get_anime_titles_xml(path: Path):
    return download_file("https://raw.githubusercontent.com/ScudLee/anime-lists/master/animetitles.xml", path)


def get_anime_list_xml(path: Path):
    return download_file("https://raw.githubusercontent.com/ScudLee/anime-lists/master/anime-list.xml", path)


def read_anidb_xml(cache_dir: Path):
    file_path = cache_dir / "animetitles.xml"

    if not file_path.exists():
        if not get_anime_titles_xml(file_path):
            return
    else:
        mtime = os.path.getmtime(file_path)
        if time.time() > mtime + 24 * 60 * 60:
            if not get_anime_titles_xml(file_path):
                return

    return read_xml_into_etree(file_path)


def read_tvdb_map_xml(cache_dir: Path):
    file_path = cache_dir / "anime-list.xml"
    if not file_path.is_file():
        if not get_anime_list_xml(file_path):
            return
    else:
        mtime = os.path.getmtime(file_path)
        if time.time() > mtime + 24 * 60 * 60:
            if not get_anime_list_xml(file_path):
                return

    return read_xml_into_etree(file_path)


def read_xml_into_etree(file_path):
    with file_path.open("r") as f:
        return ElementTree.ElementTree(file=f)
