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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import sickbeard

from datetime import date
from sickbeard.common import Quality, SKIPPED, WANTED
from sickbeard.db import DBConnection
from sickbeard.helpers import findCertainShow
from sickrage.helper.exceptions import CantRefreshShowException, CantRemoveShowException, ex
from sickrage.helper.exceptions import MultipleShowObjectsException


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

        error, show = Show._validate_indexer_id(indexer_id)

        if error is not None:
            return error, show

        try:
            sickbeard.showQueueScheduler.action.removeShow(show, bool(remove_files))
        except CantRemoveShowException as exception:
            return ex(exception), show

        return None, show

    @staticmethod
    def overall_stats():
        db = DBConnection()
        shows = sickbeard.showList
        today = str(date.today().toordinal())

        downloaded_status = Quality.DOWNLOADED + Quality.ARCHIVED
        snatched_status = Quality.SNATCHED + Quality.SNATCHED_PROPER
        total_status = [SKIPPED, WANTED]

        results = db.select(
            'SELECT airdate, status '
            'FROM tv_episodes '
            'WHERE season > 0 '
            'AND episode > 0 '
            'AND airdate > 1'
        )

        stats = {
            'episodes': {
                'downloaded': 0,
                'snatched': 0,
                'total': 0,
            },
            'shows': {
                'active': len([show for show in shows if show.paused == 0 and show.status == 'Continuing']),
                'total': len(shows),
            },
        }

        for result in results:
            if result['status'] in downloaded_status:
                stats['episodes']['downloaded'] += 1
                stats['episodes']['total'] += 1
            elif result['status'] in snatched_status:
                stats['episodes']['snatched'] += 1
                stats['episodes']['total'] += 1
            elif result['airdate'] <= today and result['status'] in total_status:
                stats['episodes']['total'] += 1

        return stats

    @staticmethod
    def pause(indexer_id, pause=None):
        """
        Change the pause state of a show
        :param indexer_id: The unique id of the show to update
        :param pause: ``True`` to pause the show, ``False`` to resume the show, ``None`` to toggle the pause state
        :return: A tuple containing:
         - an error message if the pause state could not be changed, ``None`` otherwise
         - the show object that was updated, if it exists, ``None`` otherwise
        """

        error, show = Show._validate_indexer_id(indexer_id)

        if error is not None:
            return error, show

        if pause is None:
            show.paused = not show.paused
        else:
            show.paused = pause

        show.saveToDB()

        return None, show

    @staticmethod
    def refresh(indexer_id):
        """
        Try to refresh a show
        :param indexer_id: The unique id of the show to refresh
        :return: A tuple containing:
         - an error message if the show could not be refreshed, ``None`` otherwise
         - the show object that was refreshed, if it exists, ``None`` otherwise
        """

        error, show = Show._validate_indexer_id(indexer_id)

        if error is not None:
            return error, show

        try:
            sickbeard.showQueueScheduler.action.refreshShow(show)
        except CantRefreshShowException as exception:
            return ex(exception), show

        return None, show

    @staticmethod
    def _validate_indexer_id(indexer_id):
        """
        Check that the provided indexer_id is valid and corresponds with a known show
        :param indexer_id: The indexer id to check
        :return: A tuple containing:
         - an error message if the indexer id is not correct, ``None`` otherwise
         - the show object corresponding to ``indexer_id`` if it exists, ``None`` otherwise
        """

        try:
            indexer_id = int(indexer_id)
        except (TypeError, ValueError):
            return 'Invalid show ID', None

        try:
            show = findCertainShow(sickbeard.showList, int(indexer_id))
        except MultipleShowObjectsException:
            return 'Unable to find the specified show', None

        return None, show
