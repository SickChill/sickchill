# This file is part of SickRage.
#
# URL: https://www.sickrage.tv
# Git: https://github.com/SiCKRAGETV/SickRage.git
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from sickrage.helper.encoding import ss


def ex(e):
    """
    :param e: The exception to convert into a unicode string
    :return: A unicode string from the exception text if it exists
    """

    message = u''

    if not e or not e.args:
        return message

    for arg in e.args:
        if arg is not None:
            if isinstance(arg, (str, unicode)):
                fixed_arg = ss(arg)
            else:
                try:
                    fixed_arg = u'error %s' % ss(str(arg))
                except Exception:
                    fixed_arg = None

            if fixed_arg:
                if not message:
                    message = fixed_arg
                else:
                    message = '%s : %s' % (message, fixed_arg)

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
