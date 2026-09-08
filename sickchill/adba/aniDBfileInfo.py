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

        return md4_hash(reduce(lambda b, c: b + c, hashes, b"")).hexdigest()


def download_file(url, filename: Path):
    """Download ``url`` to ``filename``.

    Writes via a temp file and only replaces the destination on success, so a
    failed refresh never deletes a previously good cache file.
    """
    tmp_path = filename.with_suffix(filename.suffix + ".tmp")
    try:
        r = requests.get(url, stream=True, verify=False, timeout=120)
        r.raise_for_status()
        with tmp_path.open("wb") as fp:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    fp.write(chunk)
                    fp.flush()
        tmp_path.replace(filename)
    except requests.exceptions.RequestException:
        if tmp_path.is_file():
            tmp_path.unlink()
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
            return None
    else:
        mtime = os.path.getmtime(file_path)
        # Best-effort daily refresh; keep the stale file if the download fails.
        if time.time() > mtime + 24 * 60 * 60:
            get_anime_titles_xml(file_path)

    if not file_path.exists():
        return None
    return read_xml_into_etree(file_path)


def read_tvdb_map_xml(cache_dir: Path):
    file_path = cache_dir / "anime-list.xml"
    if not file_path.is_file():
        if not get_anime_list_xml(file_path):
            return None
    else:
        mtime = os.path.getmtime(file_path)
        # Best-effort daily refresh; keep the stale file if the download fails.
        if time.time() > mtime + 24 * 60 * 60:
            get_anime_list_xml(file_path)

    if not file_path.is_file():
        return None
    return read_xml_into_etree(file_path)


def read_xml_into_etree(file_path):
    return ElementTree.parse(file_path)
