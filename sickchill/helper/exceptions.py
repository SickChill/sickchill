# coding=utf-8
# This file is part of SickChill.
#
# URL: https://sickchill.github.io
# Git: https://github.com/SickChill/SickChill.git
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.


class SickChillException(Exception):
    """
    Generic SickChill Exception - should never be thrown, only sub-classed
    """


class AuthException(SickChillException):
    """
    Your authentication information are incorrect
    """


class CantRefreshShowException(SickChillException):
    """
    The show can't be refreshed right now
    """


class CantRemoveShowException(SickChillException):
    """
    The show can't removed right now
    """


class CantUpdateShowException(SickChillException):
    """
    The show can't be updated right now
    """


class EpisodeDeletedException(SickChillException):
    """
    This episode has been deleted
    """


class EpisodeNotFoundException(SickChillException):
    """
    The episode wasn't found on the Indexer
    """


class EpisodePostProcessingFailedException(SickChillException):
    """
    The episode post-processing failed
    """


class FailedPostProcessingFailedException(SickChillException):
    """
    The failed post-processing failed
    """


class MultipleEpisodesInDatabaseException(SickChillException):
    """
    Multiple episodes were found in the database! The database must be fixed first
    """


class MultipleShowsInDatabaseException(SickChillException):
    """
    Multiple shows were found in the database! The database must be fixed first
    """


class MultipleShowObjectsException(SickChillException):
    """
    Multiple objects for the same show were found! Something is very wrong
    """


class NoNFOException(SickChillException):
    """
    No NFO was found
    """


class ShowDirectoryNotFoundException(SickChillException):
    """
    The show directory was not found
    """


class ShowNotFoundException(SickChillException):
    """
    The show wasn't found on the Indexer
    """
