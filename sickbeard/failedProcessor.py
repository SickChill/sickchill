# Author: Tyler Fenby <tylerfenby@gmail.com>
# URL: http://code.google.com/p/sickbeard/
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License

from __future__ import with_statement

import sickbeard
from sickbeard import logger
from sickbeard import exceptions
from sickbeard import show_name_helpers
from sickbeard import helpers
from sickbeard import search_queue
from sickbeard import failed_history
from sickbeard import scene_exceptions

from sickbeard.name_parser.parser import NameParser, InvalidNameException


class FailedProcessor(object):
    """Take appropriate action when a download fails to complete"""

    def __init__(self, dirName, nzbName):
        """
        dirName: Full path to the folder of the failed download
        nzbName: Full name of the nzb file that failed
        """
        self.dir_name = dirName
        self.nzb_name = nzbName

        self._show_obj = None

        self.log = ""

    def __del__(self):
        pass

    def process(self):
        self._log(u"Failed download detected: (" + str(self.nzb_name) + ", " + str(self.dir_name) + ")")

        releaseName = show_name_helpers.determineReleaseName(self.dir_name, self.nzb_name)
        if releaseName is None:
            self._log(u"Warning: unable to find a valid release name.", logger.WARNING)
            raise exceptions.FailedProcessingFailed()


        try:
            parser = NameParser(False, convert=True)
            parsed = parser.parse(releaseName)
        except InvalidNameException:
            self._log(u"Error: release name is invalid: " + releaseName, logger.WARNING)
            raise exceptions.FailedProcessingFailed()

        logger.log(u"name_parser info: ", logger.DEBUG)
        logger.log(u" - " + str(parsed.series_name), logger.DEBUG)
        logger.log(u" - " + str(parsed.season_number), logger.DEBUG)
        logger.log(u" - " + str(parsed.episode_numbers), logger.DEBUG)
        logger.log(u" - " + str(parsed.extra_info), logger.DEBUG)
        logger.log(u" - " + str(parsed.release_group), logger.DEBUG)
        logger.log(u" - " + str(parsed.air_date), logger.DEBUG)
        logger.log(u" - " + str(parsed.sports_event_date), logger.DEBUG)

        if parsed.show is None:
            self._log(
                u"Could not create show object. Either the show hasn't been added to SickRage, or it's still loading (if SB was restarted recently)",
                logger.WARNING)
            raise exceptions.FailedProcessingFailed()

        segment = {parsed.season_number:[]}

        for episode in parsed.episode_numbers:
            epObj = parsed.show.getEpisode(parsed.season_number, episode)
            segment[parsed.season_number].append(epObj)

        cur_failed_queue_item = search_queue.FailedQueueItem(parsed.show, segment)
        sickbeard.searchQueueScheduler.action.add_item(cur_failed_queue_item)

        return True

    def _log(self, message, level=logger.MESSAGE):
        """Log to regular logfile and save for return for PP script log"""
        logger.log(message, level)
        self.log += message + "\n"