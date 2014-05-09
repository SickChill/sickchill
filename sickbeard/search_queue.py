# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of Sick Beard.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import with_statement

import datetime
import Queue
import time
import traceback

import sickbeard
from sickbeard import db, logger, common, exceptions, helpers
from sickbeard import generic_queue, scheduler
from sickbeard import search, failed_history, history
from sickbeard import ui
from lib.concurrent import futures
from lib.concurrent.futures.thread import ThreadPoolExecutor

BACKLOG_SEARCH = 10
RSS_SEARCH = 20
FAILED_SEARCH = 30
MANUAL_SEARCH = 30
SNATCH = 40

# snatch queues
ManualSnatchQueue = Queue.PriorityQueue()
RSSSnatchQueue = Queue.PriorityQueue()
BacklogSnatchQueue = Queue.PriorityQueue()
FailedSnatchQueue = Queue.PriorityQueue()

SearchItemQueue = Queue.PriorityQueue()


class SnatchQueue(generic_queue.GenericQueue):
    def __init__(self):
        generic_queue.GenericQueue.__init__(self)
        self.queue_name = "SNATCHQUEUE"

    def is_in_queue(self, show, episodes, quality):
        for cur_item in self.queue.queue:
            if cur_item.results.extraInfo[0] == show \
                    and cur_item.results.episodes.sort() == episodes.sort() \
                    and cur_item.results.quality >= quality:
                return True
        return False

    def add_item(self, item):
        # dynamically select our snatch queue
        if item.type == 'RSSSearchQueueItem':
            self.queue = RSSSnatchQueue
        elif item.type == 'ManualSearchQueueItem':
            self.queue = ManualSnatchQueue
        elif item.type == 'BacklogQueueItem':
            self.queue = BacklogSnatchQueue
        elif item.type == 'FailedQueueItem':
            self.queue = FailedSnatchQueue
        else:
            return

        # check if we already have a item ready to snatch with same or better quality score
        if not self.is_in_queue(item.results.extraInfo[0], item.results.episodes, item.results.quality):
            generic_queue.GenericQueue.add_item(self, item)
        else:
            logger.log(
                u"Not adding item [" + item.results.name + "] it's already in the queue with same or higher quality",
                logger.DEBUG)


class SnatchQueueItem(generic_queue.QueueItem):
    def __init__(self, results, queue_item):
        generic_queue.QueueItem.__init__(self, 'Snatch', SNATCH)
        self.priority = generic_queue.QueuePriorities.HIGH
        self.thread_name = 'SNATCH-' + str(results.extraInfo[0].indexerid)
        self.results = results
        self.success = None
        self.queue_item = queue_item
        self.type = queue_item.type

    def execute(self):
        generic_queue.QueueItem.execute(self)

        # just use the first result for now
        logger.log(u"Downloading " + self.results.name + " from " + self.results.provider.name)

        result = search.snatchEpisode(self.results)

        if self.type == "ManualSearchQueueItem":
            providerModule = self.results.provider
            if not result:
                ui.notifications.error(
                    'Error while attempting to snatch ' + self.results.name + ', check your logs')
            elif providerModule == None:
                ui.notifications.error('Provider is configured incorrectly, unable to download')

        self.success = result
        self.queue_item.success = result

        generic_queue.QueueItem.finish(self.queue_item)
        generic_queue.QueueItem.finish(self)

class SearchQueue(generic_queue.GenericQueue):
    def __init__(self):
        generic_queue.GenericQueue.__init__(self)
        self.queue_name = "SEARCHQUEUE"
        self.queue = SearchItemQueue

    def is_in_queue(self, show, segment):
        for cur_item in self.queue.queue:
            if isinstance(cur_item, BacklogQueueItem) and cur_item.show == show and cur_item.segment == segment:
                return True
        return False

    def is_ep_in_queue(self, ep_obj):
        for cur_item in self.queue.queue:
            if isinstance(cur_item, ManualSearchQueueItem) and cur_item.ep_obj == ep_obj:
                return True
        return False

    def pause_backlog(self):
        self.min_priority = generic_queue.QueuePriorities.HIGH

    def unpause_backlog(self):
        self.min_priority = 0

    def is_backlog_paused(self):
        # backlog priorities are NORMAL, this should be done properly somewhere
        return self.min_priority >= generic_queue.QueuePriorities.NORMAL

    def is_backlog_in_progress(self):
        for cur_item in self.queue.queue + [self.currentItem]:
            if isinstance(cur_item, BacklogQueueItem):
                return True
        return False

    def add_item(self, item):

        if isinstance(item, RSSSearchQueueItem):
            generic_queue.GenericQueue.add_item(self, item)
        elif isinstance(item, BacklogQueueItem) and not self.is_in_queue(item.show, item.segment):
            generic_queue.GenericQueue.add_item(self, item)
        elif isinstance(item, ManualSearchQueueItem) and not self.is_ep_in_queue(item.ep_obj):
            generic_queue.GenericQueue.add_item(self, item)
        elif isinstance(item, FailedQueueItem) and not self.is_in_queue(item.show, item.episodes):
            generic_queue.GenericQueue.add_item(self, item)
        else:
            logger.log(u"Not adding item, it's already in the queue", logger.DEBUG)


class ManualSearchQueueItem(generic_queue.QueueItem):
    def __init__(self, ep_obj):
        generic_queue.QueueItem.__init__(self, 'Manual Search', MANUAL_SEARCH)
        self.priority = generic_queue.QueuePriorities.HIGH
        self.type = self.__class__.__name__
        self.thread_name = 'MANUAL-' + str(ep_obj.show.indexerid)
        self.success = None
        self.show = ep_obj.show
        self.ep_obj = ep_obj

    def execute(self):
        generic_queue.QueueItem.execute(self)

        fs = []
        didSearch = False

        providers = [x for x in sickbeard.providers.sortedProviderList() if x.isActive()]
        try:
            with ThreadPoolExecutor(sickbeard.NUM_OF_THREADS) as executor:
                for provider in providers:
                    didSearch = True
                    logger.log("Beginning manual search for [" + self.ep_obj.prettyName() + "] on " + provider.name)
                    executor.submit(
                        search.searchProviders, self, self.show, self.ep_obj.season, [self.ep_obj], provider, False,
                        True).add_done_callback(snatch_results)
                executor.shutdown(wait=True)
        except Exception, e:
            logger.log(traceback.format_exc(), logger.DEBUG)

        if not didSearch:
            logger.log(
                u"No NZB/Torrent providers found or enabled in your SickRage config. Please check your settings.",
                logger.ERROR)

        if ManualSnatchQueue.empty():
            ui.notifications.message('No downloads were found',
                                     "Couldn't find a download for <i>%s</i>" % self.ep_obj.prettyName())
            logger.log(u"Unable to find a download for " + self.ep_obj.prettyName())
        else:
            # snatch all items in queue
            scheduler.Scheduler(SnatchQueue(), silent=True, runOnce=True, queue=ManualSnatchQueue).thread.start()

        generic_queue.QueueItem.finish(self)

class RSSSearchQueueItem(generic_queue.QueueItem):
    def __init__(self):
        generic_queue.QueueItem.__init__(self, 'RSS Search', RSS_SEARCH)
        self.thread_name = 'RSSFEED'
        self.type = self.__class__.__name__

    def execute(self):
        generic_queue.QueueItem.execute(self)

        results = False
        didSearch = False

        self._changeMissingEpisodes()

        providers = [x for x in sickbeard.providers.sortedProviderList() if x.isActive()]

        try:
            with ThreadPoolExecutor(sickbeard.NUM_OF_THREADS) as executor:
                for provider in providers:
                    didSearch = True
                    logger.log("Beginning RSS Feed search on " + provider.name)
                    executor.submit(search.searchForNeededEpisodes, provider).add_done_callback(snatch_results)
            executor.shutdown(wait=True)
        except:
            logger.log(traceback.format_exc(), logger.DEBUG)

        if not didSearch:
            logger.log(
                u"No NZB/Torrent providers found or enabled in your SickRage config. Please check your settings.",
                logger.ERROR)

        if RSSSnatchQueue.empty():
            logger.log(u"No needed episodes found on the RSS feeds")
        else:
            # snatch all items in queue
            scheduler.Scheduler(SnatchQueue(), silent=True, runOnce=True, queue=RSSSnatchQueue).thread.start()

        generic_queue.QueueItem.finish(self)

    def _changeMissingEpisodes(self):

        logger.log(u"Changing all old missing episodes to status WANTED")

        curDate = datetime.date.today().toordinal()

        myDB = db.DBConnection()
        sqlResults = myDB.select("SELECT * FROM tv_episodes WHERE status = ? AND airdate < ?",
                                 [common.UNAIRED, curDate])

        for sqlEp in sqlResults:

            try:
                show = helpers.findCertainShow(sickbeard.showList, int(sqlEp["showid"]))
            except exceptions.MultipleShowObjectsException:
                logger.log(u"ERROR: expected to find a single show matching " + str(sqlEp["showid"]))
                return None

            if show == None:
                logger.log(u"Unable to find the show with ID " + str(
                    sqlEp["showid"]) + " in your show list! DB value was " + str(sqlEp), logger.ERROR)
                return None

            ep = show.getEpisode(sqlEp["season"], sqlEp["episode"])
            with ep.lock:
                if ep.show.paused:
                    ep.status = common.SKIPPED
                else:
                    ep.status = common.WANTED
                ep.saveToDB()


class BacklogQueueItem(generic_queue.QueueItem):
    def __init__(self, show, segment):
        generic_queue.QueueItem.__init__(self, 'Backlog', BACKLOG_SEARCH)
        self.priority = generic_queue.QueuePriorities.LOW
        self.type = self.__class__.__name__
        self.thread_name = 'BACKLOG-' + str(show.indexerid)

        self.show = show
        self.segment = segment
        self.wantedEpisodes = []

        logger.log(u"Seeing if we need any episodes from " + self.show.name + " season " + str(self.segment))

        myDB = db.DBConnection()

        # see if there is anything in this season worth searching for
        if not self.show.air_by_date:
            statusResults = myDB.select("SELECT status, episode FROM tv_episodes WHERE showid = ? AND season = ?",
                                        [self.show.indexerid, self.segment])
        else:
            season_year, season_month = map(int, self.segment.split('-'))
            min_date = datetime.date(season_year, season_month, 1)

            # it's easier to just hard code this than to worry about rolling the year over or making a month length map
            if season_month == 12:
                max_date = datetime.date(season_year, 12, 31)
            else:
                max_date = datetime.date(season_year, season_month + 1, 1) - datetime.timedelta(days=1)

            statusResults = myDB.select(
                "SELECT status, episode FROM tv_episodes WHERE showid = ? AND airdate >= ? AND airdate <= ?",
                [self.show.indexerid, min_date.toordinal(), max_date.toordinal()])

        anyQualities, bestQualities = common.Quality.splitQuality(self.show.quality)  #@UnusedVariable
        self.wantedEpisodes = self._need_any_episodes(statusResults, bestQualities)

    def execute(self):
        generic_queue.QueueItem.execute(self)

        results = False
        didSearch = False

        # check if we want to search for season packs instead of just season/episode
        seasonSearch = False
        seasonEps = self.show.getAllEpisodes(self.segment)
        if len(seasonEps) == len(self.wantedEpisodes):
            seasonSearch = True

        providers = [x for x in sickbeard.providers.sortedProviderList() if x.isActive()]

        try:
            with ThreadPoolExecutor(sickbeard.NUM_OF_THREADS) as executor:
                for provider in providers:
                    didSearch = True
                    logger.log("Beginning backlog search for [" + str(self.segment) + "] on " + provider.name)
                    executor.submit(
                        search.searchProviders, self, self.show, self.segment, self.wantedEpisodes, provider,
                        seasonSearch, False).add_done_callback(snatch_results)
            executor.shutdown(wait=True)
        except Exception, e:
            logger.log(traceback.format_exc(), logger.DEBUG)

        if not didSearch:
            logger.log(
                u"No NZB/Torrent providers found or enabled in your SickRage config. Please check your settings.",
                logger.ERROR)

        if BacklogSnatchQueue.empty():
            logger.log(u"No needed episodes found during backlog search")
        else:
            # snatch all items in queue
            scheduler.Scheduler(SnatchQueue(), silent=True, runOnce=True, queue=BacklogSnatchQueue).thread.start()

        self.finish()

    def _need_any_episodes(self, statusResults, bestQualities):
        wantedEpisodes = []

        # check through the list of statuses to see if we want any
        for curStatusResult in statusResults:
            time.sleep(1)

            curCompositeStatus = int(curStatusResult["status"])
            curStatus, curQuality = common.Quality.splitCompositeStatus(curCompositeStatus)
            episode = int(curStatusResult["episode"])

            if bestQualities:
                highestBestQuality = max(bestQualities)
            else:
                highestBestQuality = 0

            # if we need a better one then say yes
            if (curStatus in (common.DOWNLOADED, common.SNATCHED, common.SNATCHED_PROPER,
                              common.SNATCHED_BEST) and curQuality < highestBestQuality) or curStatus == common.WANTED:
                epObj = self.show.getEpisode(self.segment, episode)
                wantedEpisodes.append(epObj)

        return wantedEpisodes


class FailedQueueItem(generic_queue.QueueItem):
    def __init__(self, show, episodes):
        generic_queue.QueueItem.__init__(self, 'Retry', FAILED_SEARCH)
        self.priority = generic_queue.QueuePriorities.HIGH
        self.type = self.__class__.__name__
        self.thread_name = 'RETRY-' + str(show.indexerid)
        self.show = show
        self.episodes = episodes
        self.success = None

    def execute(self):
        generic_queue.QueueItem.execute(self)

        results = False
        didSearch = False

        episodes = []

        for i, epObj in enumerate(episodes):
            time.sleep(1)
            logger.log(
                "Beginning failed download search for " + epObj.prettyName())

            (release, provider) = failed_history.findRelease(self.show, epObj.season, epObj.episode)
            if release:
                logger.log(u"Marking release as bad: " + release)
                failed_history.markFailed(self.show, epObj.season, epObj.episode)
                failed_history.logFailed(release)
                history.logFailed(self.show.indexerid, epObj.season, epObj.episode, epObj.status, release, provider)

                failed_history.revertEpisode(self.show, epObj.season, epObj.episode)
                episodes.append(epObj)

        providers = [x for x in sickbeard.providers.sortedProviderList() if x.isActive()]

        try:
            with ThreadPoolExecutor(sickbeard.NUM_OF_THREADS) as executor:
                for provider in providers:
                    didSearch = True
                    executor.submit(
                        search.searchProviders, self, self.show, self.episodes[0].season, self.episodes, provider,
                        False,
                        True).add_done_callback(snatch_results)
            executor.shutdown(wait=True)
        except Exception, e:
            logger.log(traceback.format_exc(), logger.DEBUG)

        if not didSearch:
            logger.log(
                u"No NZB/Torrent providers found or enabled in your SickRage config. Please check your settings.",
                logger.ERROR)

        if FailedSnatchQueue.empty():
            logger.log(u"No needed episodes found on the RSS feeds")
        else:
            # snatch all items in queue
            scheduler.Scheduler(SnatchQueue(), silent=True, runOnce=True, queue=FailedSnatchQueue).thread.start()

        self.finish()


# send to snatch queue
def snatch_results(f):
    for result in f.result():
        snatch_queue_item = SnatchQueueItem(result, result.queue_item)
        SnatchQueue().add_item(snatch_queue_item)
