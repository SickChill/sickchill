import sickbeard

from sickbeard import showQueueScheduler
from sickbeard.exceptions import CantRemoveException, MultipleShowObjectsException
from sickbeard.helpers import findCertainShow


class Show:
    def __init__(self):
        pass

    @staticmethod
    def delete(indexer_id, remove_files=False):
        """
        Try to delete a show
        :param indexer_id: The unique id of the show to delete
        :param remove_files: ``True`` to remove the files associated with the show, ``False`` otherwise
        :return: A tuple containing:
         - an error message if the show could not be deleted, ``None`` otherwise
         - the show object that was deleted, if it exists, ``None`` otherwise
        """

        if indexer_id is None:
            return 'Invalid show ID', None

        try:
            show = findCertainShow(sickbeard.showList, int(indexer_id))
        except MultipleShowObjectsException:
            return 'Unable to find the specified show', None

        try:
            showQueueScheduler.action.removeShow(show, bool(remove_files))
        except CantRemoveException:
            return 'Unable to delete show: %s' % show.name, show

        return None, show
