# Author: Nic Wolfe <nic@wolfeden.ca>
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
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import with_statement

import traceback

import sickbeard

from imdb import _exceptions as imdb_exceptions
from sickbeard.common import WANTED
from sickbeard.tv import TVShow
from sickbeard import logger
from sickbeard import notifiers
from sickbeard import ui
from sickbeard import generic_queue
from sickbeard import name_cache
from sickbeard.blackandwhitelist import BlackAndWhiteList
from sickrage.helper.exceptions import CantRefreshShowException, CantRemoveShowException, CantUpdateShowException
from sickrage.helper.exceptions import EpisodeDeletedException, ex, MultipleShowObjectsException
from sickrage.helper.exceptions import ShowDirectoryNotFoundException
from libtrakt import TraktAPI


class ShowQueue(generic_queue.GenericQueue):
    def __init__(self):
        generic_queue.GenericQueue.__init__(self)
        self.queue_name = "SHOWQUEUE"

    def _isInQueue(self, show, actions):
        if not show:
            return False

        return show.indexerid in [x.show.indexerid if x.show else 0 for x in self.queue if x.action_id in actions]

    def _isBeingSomethinged(self, show, actions):
        return self.currentItem != None and show == self.currentItem.show and \
               self.currentItem.action_id in actions

    def isInUpdateQueue(self, show):
        return self._isInQueue(show, (ShowQueueActions.UPDATE, ShowQueueActions.FORCEUPDATE))

    def isInRefreshQueue(self, show):
        return self._isInQueue(show, (ShowQueueActions.REFRESH,))

    def isInRenameQueue(self, show):
        return self._isInQueue(show, (ShowQueueActions.RENAME,))

    def isInSubtitleQueue(self, show):
        return self._isInQueue(show, (ShowQueueActions.SUBTITLE,))

    def isBeingAdded(self, show):
        return self._isBeingSomethinged(show, (ShowQueueActions.ADD,))

    def isBeingUpdated(self, show):
        return self._isBeingSomethinged(show, (ShowQueueActions.UPDATE, ShowQueueActions.FORCEUPDATE))

    def isBeingRefreshed(self, show):
        return self._isBeingSomethinged(show, (ShowQueueActions.REFRESH,))

    def isBeingRenamed(self, show):
        return self._isBeingSomethinged(show, (ShowQueueActions.RENAME,))

    def isBeingSubtitled(self, show):
        return self._isBeingSomethinged(show, (ShowQueueActions.SUBTITLE,))

    def _getLoadingShowList(self):
        return [x for x in self.queue + [self.currentItem] if x != None and x.isLoading]

    loadingShowList = property(_getLoadingShowList)

    def updateShow(self, show, force=False):

        if self.isBeingAdded(show):
            raise CantUpdateShowException(
                str(show.name) + u" is still being added, wait until it is finished before you update.")

        if self.isBeingUpdated(show):
            raise CantUpdateShowException(
                str(show.name) + u" is already being updated by Post-processor or manually started, can't update again until it's done.")

        if self.isInUpdateQueue(show):
            raise CantUpdateShowException(
                str(show.name) + u" is in process of being updated by Post-processor or manually started, can't update again until it's done.")

        if not force:
            queueItemObj = QueueItemUpdate(show)
        else:
            queueItemObj = QueueItemForceUpdate(show)

        self.add_item(queueItemObj)

        return queueItemObj

    def refreshShow(self, show, force=False):

        if self.isBeingRefreshed(show) and not force:
            raise CantRefreshShowException("This show is already being refreshed, not refreshing again.")

        if (self.isBeingUpdated(show) or self.isInUpdateQueue(show)) and not force:
            logger.log(
                u"A refresh was attempted but there is already an update queued or in progress. Since updates do a refresh at the end anyway I'm skipping this request.",
                logger.DEBUG)
            return

        queueItemObj = QueueItemRefresh(show, force=force)

        logger.log(u"Queueing show refresh for " + show.name, logger.DEBUG)

        self.add_item(queueItemObj)

        return queueItemObj

    def renameShowEpisodes(self, show, force=False):

        queueItemObj = QueueItemRename(show)

        self.add_item(queueItemObj)

        return queueItemObj

    def downloadSubtitles(self, show, force=False):

        queueItemObj = QueueItemSubtitle(show)

        self.add_item(queueItemObj)

        return queueItemObj

    def addShow(self, indexer, indexer_id, showDir, default_status=None, quality=None, flatten_folders=None,
                lang=None, subtitles=None, anime=None, scene=None, paused=None, blacklist=None, whitelist=None, default_status_after=None, archive=None):

        if lang is None:
            lang = sickbeard.INDEXER_DEFAULT_LANGUAGE

        queueItemObj = QueueItemAdd(indexer, indexer_id, showDir, default_status, quality, flatten_folders, lang,
                                    subtitles, anime, scene, paused, blacklist, whitelist, default_status_after, archive)

        self.add_item(queueItemObj)

        return queueItemObj

    def removeShow(self, show, full=False):
        if self._isInQueue(show, (ShowQueueActions.REMOVE,)):
            raise CantRemoveShowException("This show is already queued to be removed")

        # remove other queued actions for this show.
        for x in self.queue:
            if show.indexerid == x.show.indexerid and x != self.currentItem:
                self.queue.remove(x)

        queueItemObj = QueueItemRemove(show=show, full=full)
        self.add_item(queueItemObj)

        return queueItemObj

class ShowQueueActions:
    REFRESH = 1
    ADD = 2
    UPDATE = 3
    FORCEUPDATE = 4
    RENAME = 5
    SUBTITLE = 6
    REMOVE = 7

    names = {REFRESH: 'Refresh',
             ADD: 'Add',
             UPDATE: 'Update',
             FORCEUPDATE: 'Force Update',
             RENAME: 'Rename',
             SUBTITLE: 'Subtitle',
             REMOVE: 'Remove Show'
    }


class ShowQueueItem(generic_queue.QueueItem):
    """
    Represents an item in the queue waiting to be executed

    Can be either:
    - show being added (may or may not be associated with a show object)
    - show being refreshed
    - show being updated
    - show being force updated
    - show being subtitled
    """

    def __init__(self, action_id, show):
        generic_queue.QueueItem.__init__(self, ShowQueueActions.names[action_id], action_id)
        self.show = show

    def isInQueue(self):
        return self in sickbeard.showQueueScheduler.action.queue + [
            sickbeard.showQueueScheduler.action.currentItem]  #@UndefinedVariable

    def _getName(self):
        return str(self.show.indexerid)

    def _isLoading(self):
        return False

    show_name = property(_getName)

    isLoading = property(_isLoading)


class QueueItemAdd(ShowQueueItem):
    def __init__(self, indexer, indexer_id, showDir, default_status, quality, flatten_folders, lang, subtitles, anime,
                 scene, paused, blacklist, whitelist, default_status_after, archive):

        self.indexer = indexer
        self.indexer_id = indexer_id
        self.showDir = showDir
        self.default_status = default_status
        self.quality = quality
        self.flatten_folders = flatten_folders
        self.lang = lang
        self.subtitles = subtitles
        self.anime = anime
        self.scene = scene
        self.paused = paused
        self.blacklist = blacklist
        self.whitelist = whitelist
        self.default_status_after = default_status_after
        self.archive = archive

        self.show = None

        # this will initialize self.show to None
        ShowQueueItem.__init__(self, ShowQueueActions.ADD, self.show)

        # Process add show in priority
        self.priority = generic_queue.QueuePriorities.HIGH

    def _getName(self):
        """
        Returns the show name if there is a show object created, if not returns
        the dir that the show is being added to.
        """
        if self.show == None:
            return self.showDir
        return self.show.name

    show_name = property(_getName)

    def _isLoading(self):
        """
        Returns True if we've gotten far enough to have a show object, or False
        if we still only know the folder name.
        """
        if self.show == None:
            return True
        return False

    isLoading = property(_isLoading)

    def run(self):

        ShowQueueItem.run(self)

        logger.log(u"Starting to add show " + self.showDir)
        # make sure the Indexer IDs are valid
        try:

            lINDEXER_API_PARMS = sickbeard.indexerApi(self.indexer).api_params.copy()
            if self.lang:
                lINDEXER_API_PARMS['language'] = self.lang

            logger.log(u"" + str(sickbeard.indexerApi(self.indexer).name) + ": " + repr(lINDEXER_API_PARMS))

            t = sickbeard.indexerApi(self.indexer).indexer(**lINDEXER_API_PARMS)
            s = t[self.indexer_id]

            # this usually only happens if they have an NFO in their show dir which gave us a Indexer ID that has no proper english version of the show
            if getattr(s, 'seriesname', None) is None:
                logger.log(u"Show in " + self.showDir + " has no name on " + str(
                    sickbeard.indexerApi(self.indexer).name) + ", probably the wrong language used to search with.",
                           logger.ERROR)
                ui.notifications.error("Unable to add show",
                                       "Show in " + self.showDir + " has no name on " + str(sickbeard.indexerApi(
                                           self.indexer).name) + ", probably the wrong language. Delete .nfo and add manually in the correct language.")
                self._finishEarly()
                return
            # if the show has no episodes/seasons
            if not s:
                logger.log(u"Show " + str(s['seriesname']) + " is on " + str(
                    sickbeard.indexerApi(self.indexer).name) + " but contains no season/episode data.", logger.ERROR)
                ui.notifications.error("Unable to add show",
                                       "Show " + str(s['seriesname']) + " is on " + str(sickbeard.indexerApi(
                                           self.indexer).name) + " but contains no season/episode data.")
                self._finishEarly()
                return
        except Exception, e:
            logger.log(u"Show name with ID %s doesn't exist on %s anymore. If you are using trakt, it will be removed from your TRAKT watchlist. If you are adding manually, try removing the nfo and adding again" %
                (self.indexer_id,sickbeard.indexerApi(self.indexer).name) , logger.ERROR)

            ui.notifications.error("Unable to add show",
                                   "Unable to look up the show in " + self.showDir + " on " + str(sickbeard.indexerApi(
                                       self.indexer).name) + " using ID " + str(
                                       self.indexer_id) + ", not using the NFO. Delete .nfo and try adding manually again.")

            if sickbeard.USE_TRAKT:

                trakt_id = sickbeard.indexerApi(self.indexer).config['trakt_id']
                trakt_api = TraktAPI(sickbeard.SSL_VERIFY, sickbeard.TRAKT_TIMEOUT)

                title = self.showDir.split("/")[-1]
                data = {
                    'shows': [
                        {
                            'title': title,
                            'ids': {}
                        }
                    ]
                }
                if trakt_id == 'tvdb_id':
                    data['shows'][0]['ids']['tvdb'] = self.indexer_id
                else:
                    data['shows'][0]['ids']['tvrage'] = self.indexer_id

                trakt_api.traktRequest("sync/watchlist/remove", data, method='POST')

            self._finishEarly()
            return

        try:
            newShow = TVShow(self.indexer, self.indexer_id, self.lang)
            newShow.loadFromIndexer()

            self.show = newShow

            # set up initial values
            self.show.location = self.showDir
            self.show.subtitles = self.subtitles if self.subtitles != None else sickbeard.SUBTITLES_DEFAULT
            self.show.quality = self.quality if self.quality else sickbeard.QUALITY_DEFAULT
            self.show.flatten_folders = self.flatten_folders if self.flatten_folders != None else sickbeard.FLATTEN_FOLDERS_DEFAULT
            self.show.anime = self.anime if self.anime != None else sickbeard.ANIME_DEFAULT
            self.show.scene = self.scene if self.scene != None else sickbeard.SCENE_DEFAULT
            self.show.archive_firstmatch = self.archive if self.archive != None else sickbeard.ARCHIVE_DEFAULT
            self.show.paused = self.paused if self.paused != None else False

            # set up default new/missing episode status
            logger.log(u"Setting all episodes to the specified default status: " + str(self.show.default_ep_status))
            self.show.default_ep_status = self.default_status

            if self.show.anime:
                self.show.release_groups = BlackAndWhiteList(self.show.indexerid)
                if self.blacklist:
                    self.show.release_groups.set_black_keywords(self.blacklist)
                if self.whitelist:
                    self.show.release_groups.set_white_keywords(self.whitelist)

            # be smartish about this
            #if self.show.genre and "talk show" in self.show.genre.lower():
            #    self.show.air_by_date = 1
            #if self.show.genre and "documentary" in self.show.genre.lower():
            #    self.show.air_by_date = 0
            #if self.show.classification and "sports" in self.show.classification.lower():
            #    self.show.sports = 1

        except sickbeard.indexer_exception, e:
            logger.log(
                u"Unable to add show due to an error with " + sickbeard.indexerApi(self.indexer).name + ": " + ex(e),
                logger.ERROR)
            if self.show:
                ui.notifications.error(
                    "Unable to add " + str(self.show.name) + " due to an error with " + sickbeard.indexerApi(
                        self.indexer).name + "")
            else:
                ui.notifications.error(
                    "Unable to add show due to an error with " + sickbeard.indexerApi(self.indexer).name + "")
            self._finishEarly()
            return

        except MultipleShowObjectsException:
            logger.log(u"The show in " + self.showDir + " is already in your show list, skipping", logger.WARNING)
            ui.notifications.error('Show skipped', "The show in " + self.showDir + " is already in your show list")
            self._finishEarly()
            return

        except Exception, e:
            logger.log(u"Error trying to add show: " + ex(e), logger.ERROR)
            logger.log(traceback.format_exc(), logger.DEBUG)
            self._finishEarly()
            raise

        logger.log(u"Retrieving show info from IMDb", logger.DEBUG)
        try:
            self.show.loadIMDbInfo()
        except imdb_exceptions.IMDbError, e:
            logger.log(u" Something wrong on IMDb api: " + ex(e), logger.WARNING)
        except Exception, e:
            logger.log(u"Error loading IMDb info: " + ex(e), logger.ERROR)

        try:
            self.show.saveToDB()
        except Exception, e:
            logger.log(u"Error saving the show to the database: " + ex(e), logger.ERROR)
            logger.log(traceback.format_exc(), logger.DEBUG)
            self._finishEarly()
            raise

        # add it to the show list
        sickbeard.showList.append(self.show)

        try:
            self.show.loadEpisodesFromIndexer()
        except Exception, e:
            logger.log(
                u"Error with " + sickbeard.indexerApi(self.show.indexer).name + ", not creating episode list: " + ex(e),
                logger.ERROR)
            logger.log(traceback.format_exc(), logger.DEBUG)

        # update internal name cache
        name_cache.buildNameCache()

        try:
            self.show.loadEpisodesFromDir()
        except Exception, e:
            logger.log(u"Error searching dir for episodes: " + ex(e), logger.ERROR)
            logger.log(traceback.format_exc(), logger.DEBUG)

        # if they set default ep status to WANTED then run the backlog to search for episodes
        # FIXME: This needs to be a backlog queue item!!!
        if self.show.default_ep_status == WANTED:
            logger.log(u"Launching backlog for this show since its episodes are WANTED")
            sickbeard.backlogSearchScheduler.action.searchBacklog([self.show])

        self.show.writeMetadata()
        self.show.updateMetadata()
        self.show.populateCache()

        self.show.flushEpisodes()

        if sickbeard.USE_TRAKT:
            # if there are specific episodes that need to be added by trakt
            sickbeard.traktCheckerScheduler.action.manageNewShow(self.show)

            # add show to trakt.tv library
            if sickbeard.TRAKT_SYNC:
                sickbeard.traktCheckerScheduler.action.addShowToTraktLibrary(self.show)

            if sickbeard.TRAKT_SYNC_WATCHLIST:
                logger.log(u"update watchlist")
                notifiers.trakt_notifier.update_watchlist(show_obj=self.show)

        # Load XEM data to DB for show
        sickbeard.scene_numbering.xem_refresh(self.show.indexerid, self.show.indexer, force=True)

        # check if show has XEM mapping so we can determin if searches should go by scene numbering or indexer numbering.
        if not self.scene and sickbeard.scene_numbering.get_xem_numbering_for_show(self.show.indexerid,
                                                                                   self.show.indexer):
            self.show.scene = 1

        # After initial add, set to default_status_after.
        self.show.default_ep_status = self.default_status_after

        self.finish()

    def _finishEarly(self):
        if self.show != None:
            sickbeard.showQueueScheduler.action.removeShow(self.show)

        self.finish()


class QueueItemRefresh(ShowQueueItem):
    def __init__(self, show=None, force=False):
        ShowQueueItem.__init__(self, ShowQueueActions.REFRESH, show)

        # do refreshes first because they're quick
        self.priority = generic_queue.QueuePriorities.NORMAL

        # force refresh certain items
        self.force = force

    def run(self):
        ShowQueueItem.run(self)

        logger.log(u"Performing refresh on " + self.show.name)

        self.show.refreshDir()
        self.show.writeMetadata()
        if self.force:
            self.show.updateMetadata()
        self.show.populateCache()

        # Load XEM data to DB for show
        sickbeard.scene_numbering.xem_refresh(self.show.indexerid, self.show.indexer)

        self.finish()

class QueueItemRename(ShowQueueItem):
    def __init__(self, show=None):
        ShowQueueItem.__init__(self, ShowQueueActions.RENAME, show)

    def run(self):

        ShowQueueItem.run(self)

        logger.log(u"Performing rename on " + self.show.name)

        try:
            show_loc = self.show.location
        except ShowDirectoryNotFoundException:
            logger.log(u"Can't perform rename on " + self.show.name + " when the show dir is missing.", logger.WARNING)
            return

        ep_obj_rename_list = []

        ep_obj_list = self.show.getAllEpisodes(has_location=True)
        for cur_ep_obj in ep_obj_list:
            # Only want to rename if we have a location
            if cur_ep_obj.location:
                if cur_ep_obj.relatedEps:
                    # do we have one of multi-episodes in the rename list already
                    have_already = False
                    for cur_related_ep in cur_ep_obj.relatedEps + [cur_ep_obj]:
                        if cur_related_ep in ep_obj_rename_list:
                            have_already = True
                            break
                    if not have_already:
                        ep_obj_rename_list.append(cur_ep_obj)

                else:
                    ep_obj_rename_list.append(cur_ep_obj)

        for cur_ep_obj in ep_obj_rename_list:
            cur_ep_obj.rename()

        self.finish()

class QueueItemSubtitle(ShowQueueItem):
    def __init__(self, show=None):
        ShowQueueItem.__init__(self, ShowQueueActions.SUBTITLE, show)

    def run(self):
        ShowQueueItem.run(self)

        logger.log(u"Downloading subtitles for " + self.show.name)

        self.show.downloadSubtitles()
        self.finish()

class QueueItemUpdate(ShowQueueItem):
    def __init__(self, show=None):
        ShowQueueItem.__init__(self, ShowQueueActions.UPDATE, show)
        self.force = False

    def run(self):

        ShowQueueItem.run(self)

        logger.log(u"Beginning update of " + self.show.name, logger.DEBUG)

        logger.log(u"Retrieving show info from " + sickbeard.indexerApi(self.show.indexer).name + "", logger.DEBUG)
        try:
            self.show.loadFromIndexer(cache=not self.force)
        except sickbeard.indexer_error, e:
            logger.log(u"Unable to contact " + sickbeard.indexerApi(self.show.indexer).name + ", aborting: " + ex(e),
                       logger.WARNING)
            return
        except sickbeard.indexer_attributenotfound, e:
            logger.log(u"Data retrieved from " + sickbeard.indexerApi(
                self.show.indexer).name + " was incomplete, aborting: " + ex(e), logger.ERROR)
            return

        logger.log(u"Retrieving show info from IMDb", logger.DEBUG)
        try:
            self.show.loadIMDbInfo()
        except imdb_exceptions.IMDbError, e:
            logger.log(u" Something wrong on IMDb api: " + ex(e), logger.WARNING)
        except Exception, e:
            logger.log(u"Error loading IMDb info: " + ex(e), logger.ERROR)
            logger.log(traceback.format_exc(), logger.DEBUG)

        # have to save show before reading episodes from db
        try:
            self.show.saveToDB()
        except Exception, e:
            logger.log(u"Error saving show info to the database: " + ex(e), logger.ERROR)
            logger.log(traceback.format_exc(), logger.DEBUG)

        # get episode list from DB
        logger.log(u"Loading all episodes from the database", logger.DEBUG)
        DBEpList = self.show.loadEpisodesFromDB()

        # get episode list from TVDB
        logger.log(u"Loading all episodes from " + sickbeard.indexerApi(self.show.indexer).name + "", logger.DEBUG)
        try:
            IndexerEpList = self.show.loadEpisodesFromIndexer(cache=not self.force)
        except sickbeard.indexer_exception, e:
            logger.log(u"Unable to get info from " + sickbeard.indexerApi(
                self.show.indexer).name + ", the show info will not be refreshed: " + ex(e), logger.ERROR)
            IndexerEpList = None

        if IndexerEpList is None:
            logger.log(u"No data returned from " + sickbeard.indexerApi(
                self.show.indexer).name + ", unable to update this show", logger.ERROR)
        else:
            # for each ep we found on the Indexer delete it from the DB list
            for curSeason in IndexerEpList:
                for curEpisode in IndexerEpList[curSeason]:
                    curEp = self.show.getEpisode(curSeason, curEpisode)
                    curEp.saveToDB()

                    if curSeason in DBEpList and curEpisode in DBEpList[curSeason]:
                        del DBEpList[curSeason][curEpisode]

            # remaining episodes in the DB list are not on the indexer, just delete them from the DB
            for curSeason in DBEpList:
                for curEpisode in DBEpList[curSeason]:
                    logger.log(u"Permanently deleting episode " + str(curSeason) + "x" + str(
                        curEpisode) + " from the database", logger.INFO)
                    curEp = self.show.getEpisode(curSeason, curEpisode)
                    try:
                        curEp.deleteEpisode()
                    except EpisodeDeletedException:
                        pass

        # save show again, in case episodes have changed
        try:
            self.show.saveToDB()
        except Exception, e:
            logger.log(u"Error saving show info to the database: " + ex(e), logger.ERROR)
            logger.log(traceback.format_exc(), logger.DEBUG)

        logger.log(u"Finished update of " + self.show.name, logger.DEBUG)

        sickbeard.showQueueScheduler.action.refreshShow(self.show, self.force)
        self.finish()


class QueueItemForceUpdate(QueueItemUpdate):
    def __init__(self, show=None):
        ShowQueueItem.__init__(self, ShowQueueActions.FORCEUPDATE, show)
        self.force = True


class QueueItemRemove(ShowQueueItem):
    def __init__(self, show=None, full=False):
        ShowQueueItem.__init__(self, ShowQueueActions.REMOVE, show)

        # lets make sure this happens before any other high priority actions
        self.priority = generic_queue.QueuePriorities.HIGH + generic_queue.QueuePriorities.HIGH
        self.full = full

    def run(self):
        ShowQueueItem.run(self)
        logger.log(u"Removing %s" % self.show.name)
        self.show.deleteShow(full=self.full)

        if sickbeard.USE_TRAKT:
            try:
                sickbeard.traktCheckerScheduler.action.removeShowFromTraktLibrary(self.show)
            except Exception as e:
                logger.log(u"Unable to delete show from Trakt: %s. Error: %s" % (self.show.name, ex(e)),logger.WARNING)

        self.finish()
