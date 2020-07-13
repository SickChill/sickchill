"""
Provides the Hive class to work with JSON hive files, both remotely
retrieved and opened from a local file
"""
from __future__ import absolute_import, division
from __future__ import unicode_literals, print_function

try:
    from urllib2 import URLError
except ImportError:
    from urllib.error import URLError

import json
import os

from beekeeper.comms import download_as_json, ResponseException
from beekeeper.exceptions import MissingHive, VersionNotInHive
from beekeeper.exceptions import HiveLoadedOverHTTP

class Hive(dict):

    """
    The Hive class is invisible to the developer; it wraps the parsed JSON and
    provides methods for working with the information in it. Right now, most
    methods have to do with getting the JSON and parsing version information.
    """

    def __init__(self, **kwargs):
        dict.__init__(self, **kwargs)

    @classmethod
    def from_file(cls, fname, version=None, require_https=True):
        """
        Create a Hive object based on JSON located in a local file.
        """
        if os.path.exists(fname):
            with open(fname) as hive_file:
                return cls(**json.load(hive_file)).from_version(version, require_https=require_https)
        else:
            raise MissingHive(fname)

    @classmethod
    def from_url(cls, url, version=None, require_https=False):
        """
        Create a Hive object based on JSON located at a remote URL.
        """
        if "https://" in url:
            require_https = True
        if "http://" in url and require_https:
            try:
                hive = cls.from_url(url, version=version, require_https=False)
            except HiveLoadedOverHTTP as err:
                hive = err.hive
            raise HiveLoadedOverHTTP(url, hive)
        else:
            try:
                return cls(**download_as_json(url)).from_version(version, require_https)
            except (ResponseException, URLError):
                raise MissingHive(url)

    @classmethod
    def from_domain(cls, domain, version=None, require_https=True):
        """
        Try to find a hive for the given domain; raise an error if we have to
        failover to HTTP and haven't explicitly suppressed it in the call.
        """
        url = 'https://' + domain + '/api/hive.json'
        try:
            return cls.from_url(url, version=version, require_https=require_https)
        except MissingHive:
            url = 'http://' + domain + '/api/hive.json'
            return cls.from_url(url, version=version, require_https=require_https)

    def from_version(self, version, require_https=False):
        """
        Create a Hive object based on the information in the object
        and the version passed into the method.
        """
        if version is None or self.version() == version:
            return self
        else:
            return Hive.from_url(self.get_version_url(version), require_https=require_https)

    def get_version_url(self, version):
        """
        Retrieve the URL for the designated version of the hive.
        """
        for each_version in self.other_versions():
            if version == each_version['version'] and 'location' in each_version:
                return each_version.get('location')
        raise VersionNotInHive(version)

    def version(self):
        """
        Retrieve the current hive's version, if present.
        """
        return self.get('versioning', {}).get('version', None)

    def other_versions(self):
        """
        Generate a list of other versions in the hive.
        """
        return self.get('versioning', {}).get('other_versions', [])
