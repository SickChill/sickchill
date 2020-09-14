# Copyright 2004-2017 Davide Alberani <da@erlug.linux.it>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""
This module provides the exception hierarchy used by the imdb package.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from imdb._logging import imdbpyLogger as logger


class IMDbError(Exception):
    """Base class for every exception raised by the imdb package."""

    def __init__(self, *args, **kwargs):
        """Initialize the exception and pass the message to the log system."""
        # Every raised exception also dispatch a critical log.
        logger.critical(
            '%s exception raised; args: %s; kwds: %s',
            self.__class__.__name__, args, kwargs, exc_info=True
        )
        Exception.__init__(self, *args, **kwargs)


class IMDbDataAccessError(IMDbError):
    """Exception raised when is not possible to access needed data."""
    pass


class IMDbParserError(IMDbError):
    """Exception raised when an error occurred parsing the data."""
    pass
