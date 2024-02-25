from datetime import date
from typing import TYPE_CHECKING, Union

from sickchill import settings
from sickchill.helper.exceptions import CantRefreshShowException, CantRemoveShowException, CantUpdateShowException, MultipleShowObjectsException
from sickchill.oldbeard.common import Quality, SKIPPED, WANTED
from sickchill.oldbeard.db import DBConnection

if TYPE_CHECKING:
    from sickchill.tv import TVShow


class Show(object):
    @staticmethod
    def find(shows: list, indexer_id: Union[int, str]) -> Union["TVShow", None]:
        """
        Find a show by its indexer id in the provided list of shows
        :param shows: The list of shows to search in
        :param indexer_id: The indexer id of the desired show
        :return: The desired show if found, ``None`` if not found
        :throw: ``MultipleShowObjectsException`` if multiple shows match the provided ``indexer_id``
        """
        if not (indexer_id and shows):
            return None

        if isinstance(indexer_id, list):
            if not isinstance(indexer_id[0], (int, str)):
                return None

            indexer_ids = [int(x) for x in indexer_id]
        else:
            if not isinstance(indexer_id, (int, str)):
                return None
            indexer_ids = [int(indexer_id)]

        results = [show for show in shows if show.indexerid in indexer_ids]

        if not results:
            return None

        if len(results) == 1:
            return results[0]

        raise MultipleShowObjectsException()

    @staticmethod
    def find_name(shows: list, name: str) -> Union["TVShow", None]:
        """
        Find a show by its namer in the provided list of shows
        :param shows: The list of shows to search in
        :param name: The known name of the desired show
        :return: The desired show if found, ``None`` if not found
        :throw: ``MultipleShowObjectsException`` if multiple shows match the provided ``indexer_id``
        """
        if not (name and shows):
            return None

        if isinstance(name, list):
            names = name
            for item in names:
                if not isinstance(item, str):
                    return None
        else:
            if not isinstance(name, str):
                return None

            names = [name]

        results = [show for show in shows if show.name in names]

        if not results:
            return None

        if len(results) == 1:
            return results[0]

        raise MultipleShowObjectsException()

    @staticmethod
    def overall_stats() -> dict:
        db = DBConnection()
        shows = settings.show_list
        today = date.today().toordinal()

        downloaded_status = Quality.DOWNLOADED + Quality.ARCHIVED
        snatched_status = Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST
        total_status = [SKIPPED, WANTED]

        results = db.select("SELECT airdate, status FROM tv_episodes WHERE season > 0 AND episode > 0 AND airdate > 1")

        stats = {
            "episodes": {
                "downloaded": 0,
                "snatched": 0,
                "total": 0,
            },
            "shows": {
                "active": len([show for show in shows if show.paused == 0 and show.status == "Continuing"]),
                "total": len(shows),
            },
        }

        for result in results:
            if result["status"] in downloaded_status:
                stats["episodes"]["downloaded"] += 1
                stats["episodes"]["total"] += 1
            elif result["status"] in snatched_status:
                stats["episodes"]["snatched"] += 1
                stats["episodes"]["total"] += 1
            elif result["airdate"] <= today and result["status"] in total_status:
                stats["episodes"]["total"] += 1

        return stats

    @staticmethod
    def validate_indexer_id(show_or_id: Union["TVShow", str, int], show_list: list = None) -> (Union[str, None], Union["TVShow", None]):
        """
        Check that the provided indexer_id is valid and corresponds with a known show
        :param show_or_id: The indexer id or object to check
        :param show_list: The list of shows to check against
        :return: A tuple containing:
         - an error message if the indexer id is not correct, ``None`` otherwise
         - the show object corresponding to ``indexer_id`` if it exists, ``None`` otherwise
        """

        # NOTE: cannot import TVShow here because of circular import, check this way
        if hasattr(show_or_id, "custom_name"):
            return None, show_or_id

        try:
            indexer_id = int(show_or_id)
        except (TypeError, ValueError):
            return _("Invalid show ID") + f" {show_or_id}", None

        if not show_list:
            show_list = settings.show_list

        try:
            show = Show.find(show_list, indexer_id)
        except MultipleShowObjectsException:
            return "Unable to find the specified show", None

        return None, show

    @staticmethod
    def pause(show_or_id: Union[int, str, "TVShow"], pause: Union[bool, None] = None) -> (Union[str, None], Union["TVShow", None]):
        """
        Change the pause state of a show
        :param show_or_id: The unique id or object of the show to update
        :param pause: ``True`` to pause the show, ``False`` to resume the show, ``None`` to toggle the pause state
        :return: A tuple containing:
         - an error message if the pause state could not be changed, ``None`` otherwise
         - the show object that was updated, if it exists, ``None`` otherwise
        """

        error, show = Show.validate_indexer_id(show_or_id)
        if error is not None:
            return error, show

        if pause is None:
            show.paused = not show.paused
        else:
            show.paused = pause

        show.save_to_db()

        return None, show

    @staticmethod
    def refresh(show_or_id: Union[int, str, "TVShow"], force: bool = False) -> (Union[str, None], Union["TVShow", None]):
        """
        Try to refresh a show
        :param force: Force refresh
        :param show_or_id: The unique id or object of the show to refresh
        :return: A tuple containing:
         - an error message if the show could not be refreshed, ``None`` otherwise
         - the show object that was refreshed, if it exists, ``None`` otherwise
        """

        error, show = Show.validate_indexer_id(show_or_id)
        if error is not None:
            return error, show

        try:
            settings.showQueueScheduler.action.refresh_show(show, force)
        except CantRefreshShowException as exception:
            return str(exception), show

        return None, show

    @staticmethod
    def update(show_or_id: Union[int, str, "TVShow"], force: bool = False) -> (Union[str, None], Union["TVShow", None]):
        """
        Try to delete a show
        :param show_or_id: The unique id or object of the show to delete
        :param force: Force update
        :return: A tuple containing:
         - an error message if the show could not be deleted, ``None`` otherwise
         - the show object that was deleted, if it exists, ``None`` otherwise
        """
        error, show = Show.validate_indexer_id(show_or_id)
        if error is not None:
            return error, show

        try:
            settings.showQueueScheduler.action.update_show(show, bool(force))
        except CantUpdateShowException as exception:
            return str(exception), show

        return None, show

    @staticmethod
    def delete(show_or_id: Union[int, str, "TVShow"], remove_files: bool = False) -> (Union[str, None], Union["TVShow", None]):
        """
        Try to delete a show
        :param show_or_id: The unique id or object of the show to delete
        :param remove_files: ``True`` to remove the files associated with the show, ``False`` otherwise
        :return: A tuple containing:
         - an error message if the show could not be deleted, ``None`` otherwise
         - the show object that was deleted, if it exists, ``None`` otherwise
        """
        error, show = Show.validate_indexer_id(show_or_id)
        if error is not None:
            return error, show

        try:
            settings.showQueueScheduler.action.remove_show(show, bool(remove_files))
        except CantRemoveShowException as exception:
            return str(exception), show

        return None, show
