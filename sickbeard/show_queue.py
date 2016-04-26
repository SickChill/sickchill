# coding=utf-8
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import os
import traceback
from imdb import _exceptions as imdb_exceptions
from libtrakt import TraktAPI

import sickbeard
from sickbeard.common import WANTED
from sickbeard.tv import TVShow
from sickbeard import logger, notifiers, ui, generic_queue, name_cache
from sickbeard.helpers import makeDir, chmodAsParent, get_showname_from_indexer
from sickbeard.blackandwhitelist import BlackAndWhiteList

from sickrage.show.Show import Show
from sickrage.helper.encoding import ek
from sickrage.helper.common import sanitize_filename
from sickrage.helper.exceptions import ShowDirectoryNotFoundException
from sickrage.helper.exceptions import EpisodeDeletedException, MultipleShowObjectsException
from sickrage.helper.exceptions import CantRefreshShowException, CantRemoveShowException, CantUpdateShowException


class ShowQueue(generic_queue.GenericQueue):
    def __init__(self):
        generic_queue.GenericQueue.__init__(self)
        self.queue_name = 'SHOWQUEUE'

    def _isInQueue(self, show, actions):
        if not show:
            return False

        return show.indexerid in [x.show.indexerid if x.show else 0 for x in self.queue if x.action_id in actions]

    def _isBeingSomethinged(self, show, actions):
        return self.currentItem is not None and show == self.currentItem.show and self.currentItem.action_id in actions

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
        return [x for x in self.queue + [self.currentItem] if x is not None and x.isLoading]

    loadingShowList = property(_getLoadingShowList)

    def updateShow(self, show, force=False):

        if self.isBeingAdded(show):
            raise CantUpdateShowException(
                '{0} is still being added, wait until it is finished before you update.'.format(show.name)
            )

        if self.isBeingUpdated(show):
            raise CantUpdateShowException(
                '{0} is already being updated by Post-processor or manually started, can\'t update again until it\'s done.'.format(show.name)
            )

        if self.isInUpdateQueue(show):
            raise CantUpdateShowException(
                '{0} is in process of being updated by Post-processor or manually started, can\'t update again until it\'s done.'.format(show.name)
            )

        queueItemObj = QueueItemUpdate(show, force=force)
        self.add_item(queueItemObj)
        return queueItemObj

    def refreshShow(self, show, force=False):

        if self.isBeingRefreshed(show) and not force:
            raise CantRefreshShowException('This show is already being refreshed, not refreshing again.')

        if (self.isBeingUpdated(show) or self.isInUpdateQueue(show)) and not force:
            logger.log(
                'A refresh was attempted but there is already an update queued or in progress. Updates do a refresh at the end so I\'m skipping this request.',
                logger.DEBUG)
            return

        logger.log('Queueing show refresh for {0}'.format(show.name), logger.DEBUG)

        queueItemObj = QueueItemRefresh(show, force=force)
        self.add_item(queueItemObj)
        return queueItemObj

    def renameShowEpisodes(self, show, force=False):
        force_ = force
        queueItemObj = QueueItemRename(show)
        self.add_item(queueItemObj)
        return queueItemObj

    def download_subtitles(self, show, force=False):
        force_ = force
        queueItemObj = QueueItemSubtitle(show)
        self.add_item(queueItemObj)
        return queueItemObj

    def addShow(self,  # pylint: disable=too-many-arguments, too-many-locals
                indexer, indexer_id, showDir, default_status=None, quality=None, flatten_folders=None,
                lang=None, subtitles=None, anime=None, scene=None, paused=None, blacklist=None, whitelist=None,
                default_status_after=None, root_dir=None):

        if lang is None:
            lang = sickbeard.INDEXER_DEFAULT_LANGUAGE

        queueItemObj = QueueItemAdd(indexer, indexer_id, showDir, default_status, quality, flatten_folders, lang,
                                    subtitles, anime, scene, paused, blacklist, whitelist, default_status_after, root_dir)

        self.add_item(queueItemObj)
        return queueItemObj

    def removeShow(self, show, full=False):
        if not show:
            raise CantRemoveShowException('Failed removing show: Show does not exist')

        if not hasattr(show, 'indexerid'):
            raise CantRemoveShowException('Failed removing show: Show does not have an indexer id')

        if self._isInQueue(show, (ShowQueueActions.REMOVE,)):
            raise CantRemoveShowException('{0} is already queued to be removed'.format(show.name))

        # remove other queued actions for this show.
        for item in self.queue:
            if item and item.show and item != self.currentItem and show.indexerid == item.show.indexerid:
                self.queue.remove(item)

        queue_item_obj = QueueItemRemove(show=show, full=full)
        self.add_item(queue_item_obj)
        return queue_item_obj


class ShowQueueActions(object):  # pylint: disable=too-few-public-methods

    def __init__(self):
        pass

    REFRESH = 1
    ADD = 2
    UPDATE = 3
    FORCEUPDATE = 4
    RENAME = 5
    SUBTITLE = 6
    REMOVE = 7

    names = {
        REFRESH: 'Refresh',
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
            sickbeard.showQueueScheduler.action.currentItem]  # @UndefinedVariable

    def _getName(self):
        return str(self.show.indexerid)

    def _isLoading(self):  # pylint: disable=no-self-use
        return False

    show_name = property(_getName)

    isLoading = property(_isLoading)


class QueueItemAdd(ShowQueueItem):  # pylint: disable=too-many-instance-attributes
    def __init__(self,  # pylint: disable=too-many-arguments, too-many-locals
                 indexer, indexer_id, showDir, default_status, quality, flatten_folders,
                 lang, subtitles, anime, scene, paused, blacklist, whitelist, default_status_after, root_dir):

        if isinstance(showDir, str):
            self.showDir = showDir.decode('utf-8')
        else:
            self.showDir = showDir

        self.indexer = indexer
        self.indexer_id = indexer_id
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
        self.root_dir = root_dir

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
        return self.show.name if self.show else self.showDir

    show_name = property(_getName)

    def _isLoading(self):
        """
        Returns True if we've gotten far enough to have a show object, or False
        if we still only know the folder name.
        """
        return not self.show

    isLoading = property(_isLoading)

    def run(self):  # pylint: disable=too-many-branches, too-many-statements, too-many-return-statements

        ShowQueueItem.run(self)

        if self.showDir:
            assert isinstance(self.showDir, unicode)

        logger.log('Starting to add show {0}'.format('by ShowDir: {0}'.format(self.showDir) if self.showDir else 'by Indexer Id: {0}'.format(self.indexer_id)))
        # make sure the Indexer IDs are valid
        try:

            lINDEXER_API_PARMS = sickbeard.indexerApi(self.indexer).api_params.copy()
            lINDEXER_API_PARMS['language'] = self.lang or sickbeard.INDEXER_DEFAULT_LANGUAGE

            logger.log('{0}: {1!r}'.format(sickbeard.indexerApi(self.indexer).name, lINDEXER_API_PARMS))

            t = sickbeard.indexerApi(self.indexer).indexer(**lINDEXER_API_PARMS)
            s = t[self.indexer_id]

            # Let's try to create the show Dir if it's not provided. This way we force the show dir to build build using the
            # Indexers provided series name
            if self.root_dir and not self.showDir:
                show_name = get_showname_from_indexer(self.indexer, self.indexer_id, self.lang)
                if not show_name:
                    logger.log('Unable to get a show {0}, can\'t add the show'.format(self.showDir))
                    return

                self.showDir = ek(os.path.join, self.root_dir, sanitize_filename(show_name))

                dir_exists = makeDir(self.showDir)
                if not dir_exists:
                    logger.log('Unable to create the folder {0}, can\'t add the show'.format(self.showDir))
                    return

                chmodAsParent(self.showDir)

            # this usually only happens if they have an NFO in their show dir which gave us a Indexer ID that has no proper english version of the show
            if getattr(s, 'seriesname', None) is None:
                error_string = 'Show in {0} has no name on {1}, probably searched with the wrong language. Delete .nfo and add manually in the correct language.'.format(
                    self.showDir, sickbeard.indexerApi(self.indexer).name)

                logger.log(error_string, logger.WARNING)
                ui.notifications.error('Unable to add show', error_string)

                self._finishEarly()
                return

            # if the show has no episodes/seasons
            if not s:
                error_string = 'Show {0} is on {1} but contains no season/episode data.'.format(
                    s[b'seriesname'], sickbeard.indexerApi(self.indexer).name)

                logger.log(error_string)
                ui.notifications.error('Unable to add show', error_string)

                self._finishEarly()
                return
        except Exception as error:
            error_string = 'Unable to look up the show in {0} on {1} using ID {2}, not using the NFO. Delete .nfo and try adding manually again.'.format(
                self.showDir, sickbeard.indexerApi(self.indexer).name, self.indexer_id)

            logger.log('{0}: {1}'.format(error_string, error), logger.ERROR)
            ui.notifications.error(
                'Unable to add show', error_string)

            if sickbeard.USE_TRAKT:
                trakt_id = sickbeard.indexerApi(self.indexer).config[b'trakt_id']
                trakt_api = TraktAPI(sickbeard.SSL_VERIFY, sickbeard.TRAKT_TIMEOUT)

                title = self.showDir.split('/')[-1]
                data = {
                    'shows': [
                        {
                            'title': title,
                            'ids': {}
                        }
                    ]
                }
                if trakt_id == 'tvdb_id':
                    data[b'shows'][0][b'ids'][b'tvdb'] = self.indexer_id
                else:
                    data[b'shows'][0][b'ids'][b'tvrage'] = self.indexer_id

                trakt_api.traktRequest('sync/watchlist/remove', data, method='POST')

            self._finishEarly()
            return

        try:
            try:
                newShow = TVShow(self.indexer, self.indexer_id, self.lang)
            except MultipleShowObjectsException as error:
                # If we have the show in our list, but the location is wrong, lets fix it and refresh!
                existing_show = Show.find(sickbeard.showList, self.indexer_id)
                if existing_show and not ek(os.path.isdir, existing_show._location):  # pylint: disable=protected-access
                    newShow = existing_show
                else:
                    raise error

            newShow.loadFromIndexer()

            self.show = newShow

            # set up initial values
            self.show.location = self.showDir
            self.show.subtitles = self.subtitles if self.subtitles is not None else sickbeard.SUBTITLES_DEFAULT
            self.show.quality = self.quality if self.quality else sickbeard.QUALITY_DEFAULT
            self.show.flatten_folders = self.flatten_folders if self.flatten_folders is not None else sickbeard.FLATTEN_FOLDERS_DEFAULT
            self.show.anime = self.anime if self.anime is not None else sickbeard.ANIME_DEFAULT
            self.show.scene = self.scene if self.scene is not None else sickbeard.SCENE_DEFAULT
            self.show.paused = self.paused if self.paused is not None else False

            # set up default new/missing episode status
            logger.log('Setting all episodes to the specified default status: {0}' .format(self.show.default_ep_status))
            self.show.default_ep_status = self.default_status

            if self.show.anime:
                self.show.release_groups = BlackAndWhiteList(self.show.indexerid)
                if self.blacklist:
                    self.show.release_groups.set_black_keywords(self.blacklist)
                if self.whitelist:
                    self.show.release_groups.set_white_keywords(self.whitelist)

            # # be smartish about this
            # if self.show.genre and 'talk show' in self.show.genre.lower():
            #     self.show.air_by_date = 1
            # if self.show.genre and 'documentary' in self.show.genre.lower():
            #     self.show.air_by_date = 0
            # if self.show.classification and 'sports' in self.show.classification.lower():
            #     self.show.sports = 1

        except sickbeard.indexer_exception as error:
            error_string = 'Unable to add {0} due to an error with {1}'.format(
                self.show.name if self.show else 'show', sickbeard.indexerApi(self.indexer).name)

            logger.log('{0}: {1}'.format(error_string, error), logger.ERROR)
            ui.notifications.error('Unable to add show', error_string)

            self._finishEarly()
            return

        except MultipleShowObjectsException:
            error_string = 'The show in {0} is already in your show list, skipping'.format(self.showDir)
            logger.log(error_string, logger.WARNING)
            ui.notifications.error('Show skipped', error_string)

            self._finishEarly()
            return

        except Exception as error:
            logger.log('Error trying to add show: {0}'.format(error), logger.ERROR)
            logger.log(traceback.format_exc(), logger.DEBUG)
            self._finishEarly()
            raise

        logger.log('Retrieving show info from IMDb', logger.DEBUG)
        try:
            self.show.loadIMDbInfo()
        except imdb_exceptions.IMDbError as error:
            logger.log(' Something wrong on IMDb api: {0}'.format(error), logger.WARNING)
        except Exception as error:
            logger.log('Error loading IMDb info: {0}'.format(error), logger.ERROR)

        try:
            self.show.saveToDB()
        except Exception as error:
            logger.log('Error saving the show to the database: {0}'.format(error), logger.ERROR)
            logger.log(traceback.format_exc(), logger.DEBUG)
            self._finishEarly()
            raise

        # add it to the show list
        if not Show.find(sickbeard.showList, self.indexer_id):
            sickbeard.showList.append(self.show)

        try:
            self.show.loadEpisodesFromIndexer()
        except Exception as error:
            logger.log(
                'Error with {0}, not creating episode list: {1}'.format
                (sickbeard.indexerApi(self.show.indexer).name, error), logger.ERROR)
            logger.log(traceback.format_exc(), logger.DEBUG)

        # update internal name cache
        name_cache.buildNameCache(self.show)

        try:
            self.show.loadEpisodesFromDir()
        except Exception as error:
            logger.log('Error searching dir for episodes: {0}'.format(error), logger.ERROR)
            logger.log(traceback.format_exc(), logger.DEBUG)

        # if they set default ep status to WANTED then run the backlog to search for episodes
        # FIXME: This needs to be a backlog queue item!!!
        if self.show.default_ep_status == WANTED:
            logger.log('Launching backlog for this show since its episodes are WANTED')
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
                logger.log('update watchlist')
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
        if self.show is not None:
            sickbeard.showQueueScheduler.action.removeShow(self.show)

        self.finish()


class QueueItemRefresh(ShowQueueItem):
    def __init__(self, show=None, force=False):
        ShowQueueItem.__init__(self, ShowQueueActions.REFRESH, show)

        # do refreshes first because they're quick
        self.priority = generic_queue.QueuePriorities.HIGH

        # force refresh certain items
        self.force = force

    def run(self):
        ShowQueueItem.run(self)

        logger.log('Performing refresh on {0}'.format(self.show.name))

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

        logger.log('Performing rename on {0}'.format(self.show.name))

        try:
            self.show.location
        except ShowDirectoryNotFoundException:
            logger.log('Can\'t perform rename on {0} when the show dir is missing.'.format(self.show.name), logger.WARNING)
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

        logger.log('Downloading subtitles for {0} '.format(self.show.name))

        self.show.download_subtitles()
        self.finish()


class QueueItemUpdate(ShowQueueItem):
    def __init__(self, show=None, force=False):
        action = ShowQueueActions.FORCEUPDATE if force else ShowQueueActions.UPDATE
        ShowQueueItem.__init__(self, action, show)
        self.force = force
        self.priority = generic_queue.QueuePriorities.HIGH

    def run(self):  # pylint: disable=too-many-branches, too-many-statements

        ShowQueueItem.run(self)

        logger.log('Beginning update of {0}'.format(self.show.name), logger.DEBUG)

        logger.log('Retrieving show info from {0}'.format(sickbeard.indexerApi(self.show.indexer).name), logger.DEBUG)
        try:
            self.show.loadFromIndexer(cache=not self.force)
        except sickbeard.indexer_error as error:
            logger.log('Unable to contact {0}, aborting: {1}'.format
                       (sickbeard.indexerApi(self.show.indexer).name, error), logger.WARNING)
            return
        except sickbeard.indexer_attributenotfound as error:
            logger.log('Data retrieved from {0} was incomplete, aborting: {1}'.format
                       (sickbeard.indexerApi(self.show.indexer).name, error), logger.ERROR)
            return

        logger.log('Retrieving show info from IMDb', logger.DEBUG)
        try:
            self.show.loadIMDbInfo()
        except imdb_exceptions.IMDbError as error:
            logger.log('Something wrong on IMDb api: {0}'.format(error), logger.WARNING)
        except Exception as error:
            logger.log('Error loading IMDb info: {0}'.format(error), logger.ERROR)
            logger.log(traceback.format_exc(), logger.DEBUG)

        # have to save show before reading episodes from db
        try:
            self.show.saveToDB()
        except Exception as error:
            logger.log('Error saving show info to the database: {0}'.format(error), logger.ERROR)
            logger.log(traceback.format_exc(), logger.DEBUG)

        # get episode list from DB
        logger.log('Loading all episodes from the database', logger.DEBUG)
        DBEpList = self.show.loadEpisodesFromDB()

        # get episode list from TVDB
        logger.log('Loading all episodes from {0}'.format(sickbeard.indexerApi(self.show.indexer).name), logger.DEBUG)
        try:
            IndexerEpList = self.show.loadEpisodesFromIndexer(cache=not self.force)
        except sickbeard.indexer_exception as error:
            logger.log('Unable to get info from {0}, the show info will not be refreshed: {1}'.format
                       (sickbeard.indexerApi(self.show.indexer).name, error), logger.ERROR)
            IndexerEpList = None

        if not IndexerEpList:
            logger.log('No data returned from {0}, unable to update this show.'.format
                       (sickbeard.indexerApi(self.show.indexer).name), logger.ERROR)
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
                    logger.log('Permanently deleting episode {0:02d}E{1:02d} from the database'.format
                               (curSeason, curEpisode), logger.INFO)
                    curEp = self.show.getEpisode(curSeason, curEpisode)
                    try:
                        curEp.deleteEpisode()
                    except EpisodeDeletedException:
                        pass

        #  save show again, in case episodes have changed
        try:
            self.show.saveToDB()
        except Exception as error:
            logger.log('Error saving show info to the database: {0}'.format(error), logger.ERROR)
            logger.log(traceback.format_exc(), logger.DEBUG)

        logger.log('Finished update of {0}'.format(self.show.name), logger.DEBUG)

        sickbeard.showQueueScheduler.action.refreshShow(self.show, self.force)
        self.finish()


class QueueItemRemove(ShowQueueItem):
    def __init__(self, show=None, full=False):
        ShowQueueItem.__init__(self, ShowQueueActions.REMOVE, show)

        # lets make sure this happens before any other high priority actions
        self.priority = generic_queue.QueuePriorities.HIGH ** 2
        self.full = full

    def run(self):
        ShowQueueItem.run(self)
        logger.log('Removing {0}'.format(self.show.name))
        self.show.deleteShow(full=self.full)

        if sickbeard.USE_TRAKT:
            try:
                sickbeard.traktCheckerScheduler.action.removeShowFromTraktLibrary(self.show)
            except Exception as error:
                logger.log('Unable to delete show from Trakt: {0}. Error: {1}'.format(self.show.name, error), logger.WARNING)

        self.finish()
