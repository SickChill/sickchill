#!/usr/bin/python
# -- Content-Encoding: UTF-8 --
"""
Aliases to ease access to jsonrpclib classes

:authors: Josh Marshall, Thomas Calmant
:copyright: Copyright 2020, Thomas Calmant
:license: Apache License 2.0
:version: 0.4.2

..

    Copyright 2020 Thomas Calmant

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

# Easy access to utility methods and classes
from jsonrpclib.jsonrpc import Server, ServerProxy  # noqa: F401
from jsonrpclib.jsonrpc import (  # noqa: F401
    MultiCall,
    Fault,
    ProtocolError,
    AppError,
    TransportError,
)
from jsonrpclib.jsonrpc import loads, dumps, load, dump  # noqa: F401
from jsonrpclib.jsonrpc import jloads, jdumps  # noqa: F401
import jsonrpclib.history as history  # noqa: F401
import jsonrpclib.utils as utils  # noqa: F401

# ------------------------------------------------------------------------------


# Module version
__version_info__ = (0, 4, 2)
__version__ = ".".join(str(x) for x in __version_info__)

# Documentation strings format
__docformat__ = "restructuredtext en"
