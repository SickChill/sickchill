import logging

import validators

from sickchill import logger, settings
from sickchill.helper.exceptions import FailedPostProcessingFailedException
from sickchill.oldbeard import search_queue, show_name_helpers
from sickchill.oldbeard.db import DBConnection
from sickchill.oldbeard.name_parser.parser import InvalidNameException, InvalidShowException, NameParser


class FailedProcessor(object):
    """Take appropriate action when a download fails to complete"""

    def __init__(self, directory, release_name):
        """
        :param directory: Full path to the folder of the failed download
        :param release_name: Full name of the release file that failed
        """
        self.directory = directory
        self.release_name = release_name

        self.log = ""

    def process(self):
        """
        Do the actual work

        :return: True
        """
        self._log(_("Failed download detected: ({release_name}, {directory})").format(release_name=self.release_name, directory=self.directory))

        if self.release_name and validators.url(self.release_name) == True:
            cache_db_con = DBConnection("cache.db")
            cache_result = cache_db_con.select_one("SELECT name FROM results WHERE url = ?", [self.release_name])
            if cache_result:
                self.release_name = cache_result["name"]

        release_name = show_name_helpers.determine_release_name(self.directory, self.release_name)
        if not release_name:
            self._log(_("Warning: unable to find a valid release name."), logger.WARNING)
            raise FailedPostProcessingFailedException()

        try:
            parsed = NameParser(False).parse(release_name)
        except (InvalidNameException, InvalidShowException) as error:
            self._log(f"{error}", logger.DEBUG)
            raise FailedPostProcessingFailedException()

        self._log("name_parser info: ", logger.DEBUG)
        self._log(f"{parsed.series_name}", logger.DEBUG)
        self._log(f"{parsed.season_number}", logger.DEBUG)
        self._log(f"{parsed.episode_numbers}", logger.DEBUG)
        self._log(f"{parsed.extra_info}", logger.DEBUG)
        self._log(f"{parsed.release_group}", logger.DEBUG)
        self._log(f"{parsed.air_date}", logger.DEBUG)

        for episode in parsed.episode_numbers:
            segment = parsed.show.getEpisode(parsed.season_number, episode)

            cur_failed_queue_item = search_queue.FailedQueueItem(parsed.show, [segment])
            settings.searchQueueScheduler.action.add_item(cur_failed_queue_item)

        return True

    def _log(self, message, level=logging.INFO):
        """Log to regular logfile and save for return for PP script log"""
        logger.log(level, message)
        self.log += message + "\n"
