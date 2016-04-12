# coding=utf-8
# Author: Tyler Fenby <tylerfenby@gmail.com>
# URL: https://sickrage.github.io
# Git: https://github.com/SickRage/SickRage.git
#
# This file is part of SickRage.
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


import sickbeard
from sickbeard import logger
from sickbeard import show_name_helpers
from sickbeard import search_queue
from sickbeard.name_parser.parser import NameParser, InvalidNameException, InvalidShowException
from sickrage.helper.exceptions import FailedPostProcessingFailedException


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
        self._log(u"Failed download detected: (" + str(self.nzb_name) + ", " + str(self.dir_name) + ")")

        releaseName = show_name_helpers.determineReleaseName(self.dir_name, self.nzb_name)
        if not releaseName:
            self._log(u"Warning: unable to find a valid release name.", logger.WARNING)
            raise FailedPostProcessingFailedException()

        try:
            parsed = NameParser(False).parse(releaseName)
        except (InvalidNameException, InvalidShowException) as error:
            self._log(u"{0}".format(error), logger.DEBUG)
            raise FailedPostProcessingFailedException()

        self._log(u"name_parser info: ", logger.DEBUG)
        self._log(u" - " + str(parsed.series_name), logger.DEBUG)
        self._log(u" - " + str(parsed.season_number), logger.DEBUG)
        self._log(u" - " + str(parsed.episode_numbers), logger.DEBUG)
        self._log(u" - " + str(parsed.extra_info), logger.DEBUG)
        self._log(u" - " + str(parsed.release_group), logger.DEBUG)
        self._log(u" - " + str(parsed.air_date), logger.DEBUG)

        for episode in parsed.episode_numbers:
            segment = parsed.show.get_episode(parsed.season_number, episode)

            cur_failed_queue_item = search_queue.FailedQueueItem(parsed.show, [segment])
            sickbeard.search_queue_scheduler.action.add_item(cur_failed_queue_item)

        return True

    def _log(self, message, level=logger.INFO):
        """Log to regular logfile and save for return for PP script log"""
        logger.log(message, level)
        self.log += message + "\n"
