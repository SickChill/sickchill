#!/usr/bin/python
# -- Content-Encoding: UTF-8 --
"""
The history module.

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

# Module version
__version_info__ = (0, 4, 2)
__version__ = ".".join(str(x) for x in __version_info__)

# Documentation strings format
__docformat__ = "restructuredtext en"

# ------------------------------------------------------------------------------


class History(object):
    """
    This holds all the response and request objects for a
    session. A server using this should call "clear" after
    each request cycle in order to keep it from clogging
    memory.
    """

    def __init__(self):
        """
        Sets up members
        """
        self.requests = []
        self.responses = []

    def add_response(self, response_obj):
        """
        Adds a response to the history

        :param response_obj: Response content
        """
        self.responses.append(response_obj)

    def add_request(self, request_obj):
        """
        Adds a request to the history

        :param request_obj: A request object
        """
        self.requests.append(request_obj)

    @property
    def request(self):
        """
        Returns the latest stored request or None
        """
        try:
            return self.requests[-1]
        except IndexError:
            return None

    @property
    def response(self):
        """
        Returns the latest stored response or None
        """
        try:
            return self.responses[-1]
        except IndexError:
            return None

    def clear(self):
        """
        Clears the history lists
        """
        del self.requests[:]
        del self.responses[:]
