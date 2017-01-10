# Copyright 2012 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from . import const
from ._compat import iterkeys, string_types
from .importer import require_version, get_required_version
from .codegen import set_backend
from .foreign import require_foreign
from .util import PyGIDeprecationWarning, PyGIWarning


require_version = require_version
get_required_version = get_required_version
set_backend = set_backend
require_foreign = require_foreign
PyGIDeprecationWarning = PyGIDeprecationWarning
PyGIWarning = PyGIWarning

version_info = const.VERSION
__version__ = ".".join(map(str, version_info))


def check_version(version):
    """Takes a version string or tuple and raises ValueError in case
    the passed version is newer than the current version of pgi.

    Keep in mind that the pgi version is different from the pygobject one.
    """

    if isinstance(version, string_types):
        version = tuple(map(int, version.split(".")))

    if version > version_info:
        str_version = ".".join(map(str, version))
        raise ValueError("pgi version '%s' requested, '%s' available" %
                         (str_version, __version__))


def install_as_gi():
    """Call before the first gi import to redirect gi imports to pgi"""

    import sys

    # check if gi has already been replaces
    if "gi.repository" in const.PREFIX:
        return

    # make sure gi isn't loaded first
    for mod in iterkeys(sys.modules):
        if mod == "gi" or mod.startswith("gi."):
            raise AssertionError("pgi has to be imported before gi")

    # replace and tell the import hook
    import pgi
    import pgi.repository
    sys.modules["gi"] = pgi
    sys.modules["gi.repository"] = pgi.repository
    const.PREFIX.append("gi.repository")
