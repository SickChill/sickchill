# coding=utf-8
# This file is part of SickRage.
#
# URL: https://sickrage.github.io
# Git: https://github.com/SickRage/SickRage.git
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <https://www.gnu.org/licenses/>.

from __future__ import print_function, unicode_literals

import six

from sickrage.helper.encoding import ss


def ex(e):
    """
    :param e: The exception to convert into a six.text_type string
    :return: A six.text_type string from the exception text if it exists
    """

    message = ''

    if not e or not e.args:
        return message

    for arg in e.args:
        if arg is not None:
            if isinstance(arg, six.string_types):
                fixed_arg = ss(arg)
            else:
                try:
                    fixed_arg = 'error {0}'.format(ss(str(arg)))
                except Exception:
                    fixed_arg = None

            if fixed_arg:
                if not message:
                    message = fixed_arg
                else:
                    try:
                        message = '{0} : {1}'.format(message, fixed_arg)
                    except UnicodeError:
                        message = '{0} : {1}'.format(
                            six.text_type(message, errors='replace'),
                            six.text_type(fixed_arg, errors='replace'))

    return message


class SickRageException(Exception):
    """
    Generic SickRage Exception - should never be thrown, only sub-classed
    """


class AuthException(SickRageException):
    """
    Your authentication information are incorrect
    """


class CantRefreshShowException(SickRageException):
    """
    The show can't be refreshed right now
    """


class CantRemoveShowException(SickRageException):
    """
    The show can't removed right now
    """


class CantUpdateShowException(SickRageException):
    """
    The show can't be updated right now
    """


class EpisodeDeletedException(SickRageException):
    """
    This episode has been deleted
    """


class EpisodeNotFoundException(SickRageException):
    """
    The episode wasn't found on the Indexer
    """


class EpisodePostProcessingFailedException(SickRageException):
    """
    The episode post-processing failed
    """


class FailedPostProcessingFailedException(SickRageException):
    """
    The failed post-processing failed
    """


class MultipleEpisodesInDatabaseException(SickRageException):
    """
    Multiple episodes were found in the database! The database must be fixed first
    """


class MultipleShowsInDatabaseException(SickRageException):
    """
    Multiple shows were found in the database! The database must be fixed first
    """


class MultipleShowObjectsException(SickRageException):
    """
    Multiple objects for the same show were found! Something is very wrong
    """


class NoNFOException(SickRageException):
    """
    No NFO was found
    """


class ShowDirectoryNotFoundException(SickRageException):
    """
    The show directory was not found
    """


class ShowNotFoundException(SickRageException):
    """
    The show wasn't found on the Indexer
    """
