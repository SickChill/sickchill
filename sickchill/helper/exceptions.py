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


class UpdaterException(SickChillException):
    """
    The updater encountered an error
    """
