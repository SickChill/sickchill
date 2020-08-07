"""
This module holds most of the exceptions we use on a day-to-day basis. Woo.
"""

class TooMuchBodyData(Exception):
    """
    The error we raise if the application is trying to send more than
    one request body
    """

    def __init__(self, currentdata, newdata):
        self.currentdata = currentdata
        self.newdata = newdata

    def __str__(self):
        return 'Only one request body can be sent.'

class RequestTimeout(Exception):

    def __init__(self, retry_method):
        self.retry = retry_method

    def __str__(self):
        return "Request timed out"

class MissingHive(Exception):
    """
    The error we raise if we tried to find a hive at a given location
    but that location didn't exist when we looked there.
    """

    def __init__(self, location):
        self.location = location

    def __str__(self):
        return 'Could not open hive at {}'.format(self.location)

class VersionNotInHive(Exception):
    """
    The error we raise if the hive didn't define the location for the
    version argument that we passed to it.
    """

    def __init__(self, version):
        self.version = version

    def __str__(self):
        return 'Could not find location for version {}'.format(self.version)

class CannotHandleVariableTypes(Exception):
    def __init__(self, *types):
        self.types = types

    def __str__(self):
        return 'Cannot handle variable type(s) {}'.format(self.types)

class TraversalError(Exception):
    """
    The error we raise if the given traversal list can't handle the
    object. Contains the original object so that it can be handled
    further.
    """

    def __init__(self, obj, key):
        self.obj = obj
        self.key = key

    def __str__(self):
        return 'Could not traverse object {} with key {}'.format(self.top_level(), repr(self.key))

    def top_level(self):
        """
        Print just the top level of an object, being sure to show where
        it goes deeper
        """
        output = {}
        if isinstance(self.obj, dict):
            for name, item in self.obj.items():
                if isinstance(item, dict):
                    if item:
                        output[name] = StrReprWrapper('{...}')
                    else:
                        output[name] = StrReprWrapper('{}')
                elif isinstance(item, list):
                    if item:
                        output[name] = StrReprWrapper('[...]')
                    else:
                        output[name] = StrReprWrapper('[]')
                else:
                    output[name] = item
            return output
        else:
            return self.obj

class StrReprWrapper(str):
    """
    Subclass of string so that when we print the top level of an object,
    sublists/subdicts can appear without quotes around them.
    """

    def __repr__(self):
        return self

class HiveLoadedOverHTTP(Exception):
    """
    The error we raise if we loaded a hive automatically over HTTP without an
    override argument. It contains the loaded hive so that the developer can
    choose to automatically ignore it and load anyway.
    """

    def __init__(self, url, hive):
        self.url = url
        self.hive = hive

    def __str__(self):
        val = 'Hive was fetched insecurely over HTTP from URL {}'
        val = val.format(self.url)
        return val
