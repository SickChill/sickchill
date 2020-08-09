import logging

from sickchill import logger, settings
from sickchill.helper.exceptions import FailedPostProcessingFailedException
from sickchill.oldbeard import search_queue, show_name_helpers
from sickchill.oldbeard.name_parser.parser import InvalidNameException, InvalidShowException, NameParser


class FailedProcessor(object):
    """Take appropriate action when a download fails to complete"""

    def __init__(self, dirName, nzbName):
        """
        :param dirName: Full path to the folder of the failed download
        :param nzbName: Full name of the nzb file that failed
        """
        self.dir_name = dirName
        self.nzb_name = nzbName

        self.log = ""

    def process(self):
        """
        Do the actual work

        :return: True
        """
        self._log("Failed download detected: (" + str(self.nzb_name) + ", " + str(self.dir_name) + ")")

        releaseName = show_name_helpers.determineReleaseName(self.dir_name, self.nzb_name)
        if not releaseName:
            self._log("Warning: unable to find a valid release name.", logger.WARNING)
            raise FailedPostProcessingFailedException()

        try:
            parsed = NameParser(False).parse(releaseName)
        except (InvalidNameException, InvalidShowException) as error:
            self._log("{0}".format(error), logger.DEBUG)
            raise FailedPostProcessingFailedException()

        self._log("name_parser info: ", logger.DEBUG)
        self._log(" - " + str(parsed.series_name), logger.DEBUG)
        self._log(" - " + str(parsed.season_number), logger.DEBUG)
        self._log(" - " + str(parsed.episode_numbers), logger.DEBUG)
        self._log(" - " + str(parsed.extra_info), logger.DEBUG)
        self._log(" - " + str(parsed.release_group), logger.DEBUG)
        self._log(" - " + str(parsed.air_date), logger.DEBUG)

        for episode in parsed.episode_numbers:
            segment = parsed.show.getEpisode(parsed.season_number, episode)

            cur_failed_queue_item = search_queue.FailedQueueItem(parsed.show, [segment])
            settings.searchQueueScheduler.action.add_item(cur_failed_queue_item)

        return True

    def _log(self, message, level=logging.INFO):
        """Log to regular logfile and save for return for PP script log"""
        logger.log(level, message)
        self.log += message + "\n"
