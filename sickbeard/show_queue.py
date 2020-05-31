# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickchill.github.io
#
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, print_function, unicode_literals

# Stdlib Imports
import os
import traceback
from collections import namedtuple

# Third Party Imports
import dateutil
import six
from trakt import TraktAPI

# First Party Imports
import sickbeard
import sickchill
from sickchill.helper.common import sanitize_filename
from sickchill.helper.encoding import ek
from sickchill.helper.exceptions import (CantRefreshShowException, CantRemoveShowException, CantUpdateShowException, EpisodeDeletedException,
                                         MultipleShowObjectsException, ShowDirectoryNotFoundException)
from sickchill.show.Show import Show

# Local Folder Imports
from . import generic_queue, logger, name_cache, notifiers, scene_numbering, ui
from .blackandwhitelist import BlackAndWhiteList
from .common import WANTED
from .helpers import chmodAsParent, makeDir, sortable_name
from .tv import TVShow


class ShowQueue(generic_queue.GenericQueue):
    def __init__(self):
        super(ShowQueue, self).__init__()
        self.queue_name = 'SHOWQUEUE'

    def _is_in_queue(self, show, actions):
        if not show:
            return False

        return show.indexerid in (x.show.indexerid if x.show else 0 for x in self.queue if x.action_id in actions)

    def _is_being_somethinged(self, show, actions):
        return self.currentItem is not None and show == self.currentItem.show and self.currentItem.action_id in actions

    # def is_in_add_queue(self, show):
    #     return self._isInQueue(show, (ShowQueueActions.ADD,))

    def is_in_update_queue(self, show):
        return self._is_in_queue(show, (ShowQueueActions.UPDATE, ShowQueueActions.FORCEUPDATE))

    def is_in_refresh_queue(self, show):
        return self._is_in_queue(show, (ShowQueueActions.REFRESH,))

    def is_in_rename_queue(self, show):
        return self._is_in_queue(show, (ShowQueueActions.RENAME,))

    def is_in_remove_queue(self, show):
        return self._is_in_queue(show, (ShowQueueActions.REMOVE,))

    def is_in_subtitle_queue(self, show):
        return self._is_in_queue(show, (ShowQueueActions.SUBTITLE,))

    def is_being_added(self, show):
        return self._is_being_somethinged(show, (ShowQueueActions.ADD,))

    def is_being_updated(self, show):
        return self._is_being_somethinged(show, (ShowQueueActions.UPDATE, ShowQueueActions.FORCEUPDATE))

    def is_being_refreshed(self, show):
        return self._is_being_somethinged(show, (ShowQueueActions.REFRESH,))

    def is_being_renamed(self, show):
        return self._is_being_somethinged(show, (ShowQueueActions.RENAME,))

    def is_being_removed(self, show):
        return self._is_being_somethinged(show, (ShowQueueActions.REMOVE,))

    def is_being_subtitled(self, show):
        return self._is_being_somethinged(show, (ShowQueueActions.SUBTITLE,))

    @property
    def loading_show_list(self):
        return {x for x in self.queue + [self.currentItem] if x and x.is_loading}

    def update_show(self, show, force=False):

        if self.is_being_added(show):
            raise CantUpdateShowException(
                '{0} is still being added, wait until it is finished before you update.'.format(show.name)
            )

        if self.is_being_updated(show):
            raise CantUpdateShowException(
                '{0} is already being updated by Post-processor or manually started, can\'t update again until it\'s done.'.format(show.name)
            )

        if self.is_in_update_queue(show):
            raise CantUpdateShowException(
                '{0} is in process of being updated by Post-processor or manually started, can\'t update again until it\'s done.'.format(show.name)
            )

        queue_item_obj = QueueItemUpdate(show, force=force)
        self.add_item(queue_item_obj)
        return queue_item_obj

    def refresh_show(self, show, force=False):

        if self.is_being_refreshed(show) and not force:
            raise CantRefreshShowException('This show is already being refreshed, not refreshing again.')

        if self.is_being_updated(show) or self.is_in_update_queue(show):
            logger.log(
                'A refresh was attempted but there is already an update queued or in progress. Updates do a refresh at the end so I\'m skipping this request.',
                logger.DEBUG)
            return

        if show.paused and not force:
            logger.log('Skipping show [{0}] because it is paused.'.format(show.name), logger.DEBUG)
            return

        logger.log('Queueing show refresh for {0}'.format(show.name), logger.DEBUG)

        queue_item_obj = QueueItemRefresh(show, force=force)
        self.add_item(queue_item_obj)
        return queue_item_obj

    # noinspection PyUnusedLocal
    def rename_show_episodes(self, show, force=False):
        queue_item_obj = QueueItemRename(show)
        self.add_item(queue_item_obj)
        return queue_item_obj

    # noinspection PyUnusedLocal
    def download_subtitles(self, show, force=False):
        queue_item_obj = QueueItemSubtitle(show)
        self.add_item(queue_item_obj)
        return queue_item_obj

    # noinspection PyPep8Naming
    def add_show(self, indexer, indexer_id, showDir, default_status=None, quality=None, season_folders=None,
                 lang=None, subtitles=None, subtitles_sr_metadata=None, anime=None, scene=None, paused=None,
                 blacklist=None, whitelist=None, default_status_after=None, root_dir=None):

        if lang is None:
            lang = sickbeard.INDEXER_DEFAULT_LANGUAGE

        if default_status_after is None:
            default_status_after = sickbeard.STATUS_DEFAULT_AFTER

        queue_item_obj = QueueItemAdd(indexer, indexer_id, showDir, default_status, quality, season_folders, lang,
                                      subtitles, subtitles_sr_metadata, anime, scene, paused, blacklist, whitelist,
                                      default_status_after, root_dir)

        self.add_item(queue_item_obj)
        return queue_item_obj

    def remove_show(self, show, full=False):
        if not show:
            raise CantRemoveShowException('Failed removing show: Show does not exist')

        if not hasattr(show, 'indexerid'):
            raise CantRemoveShowException('Failed removing show: Show does not have an indexer id')

        if self._is_in_queue(show, (ShowQueueActions.REMOVE,)):
            raise CantRemoveShowException('{0} is already queued to be removed'.format(show.name))

        # remove other queued actions for this show.
        for item in self.queue:
            if item and item.show and item != self.currentItem and show.indexerid == item.show.indexerid:
                self.queue.remove(item)

        queue_item_obj = QueueItemRemove(show=show, full=full)
        self.add_item(queue_item_obj)
        return queue_item_obj


class ShowQueueActions(object):

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
        REFRESH: _('Refresh'),
        ADD: _('Add'),
        UPDATE: _('Update'),
        FORCEUPDATE: _('Force Update'),
        RENAME: _('Rename'),
        SUBTITLE: _('Subtitle'),
        REMOVE: _('Remove Show')
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
        super(ShowQueueItem, self).__init__(ShowQueueActions.names[action_id], action_id)
        self.show = show

    def is_in_queue(self):
        return self in sickbeard.showQueueScheduler.action.queue + [
            sickbeard.showQueueScheduler.action.currentItem]

    @property
    def show_name(self):
        return self.show.name if self.show else 'UNSET'

    @property
    def is_loading(self):
        return False


class QueueItemAdd(ShowQueueItem):
    # noinspection PyPep8Naming
    def __init__(self,
                 indexer, indexer_id, showDir, default_status, quality, season_folders,
                 lang, subtitles, subtitles_sr_metadata, anime, scene, paused, blacklist, whitelist,
                 default_status_after, root_dir):

        super(QueueItemAdd, self).__init__(ShowQueueActions.ADD, None)

        if isinstance(showDir, bytes):
            self.showDir = showDir.decode('utf-8')
        else:
            self.showDir = showDir

        self.indexer = indexer
        self.indexer_id = indexer_id
        self.default_status = default_status
        self.quality = quality
        self.season_folders = season_folders
        self.lang = lang
        self.subtitles = subtitles
        self.subtitles_sr_metadata = subtitles_sr_metadata
        self.anime = anime
        self.scene = scene
        self.paused = paused
        self.blacklist = blacklist
        self.whitelist = whitelist
        self.default_status_after = default_status_after
        self.root_dir = root_dir

        self.show = None

        # Process add show in priority
        self.priority = generic_queue.QueuePriorities.HIGH

    @property
    def show_name(self):
        """
        Returns the show name if there is a show object created, if not returns
        the dir that the show is being added to.
        """
        return self.show.name if self.show else self.showDir.rsplit(os.sep)[-1] if self.showDir else _("Loading")

    @property
    def is_loading(self):
        """
        Returns True if we've gotten far enough to have a show object, or False
        if we still only know the folder name.
        """
        return self.show not in sickbeard.showList or not self.show

    @property
    def info(self):
        info = namedtuple('LoadingShowInfo', 'id name sort_name network network_image_url show_image_url quality')
        if self.show:
            return info(id=self.show.indexerid, name=self.show.name, sort_name=self.show.sort_name, network=self.show.network,
                        network_image_url=self.show.network_image_url, show_image_url=self.show.show_image_url, quality=self.show.quality)
        # noinspection PyUnresolvedReferences
        return info(id=0, name=self.show_name, sort_name=sortable_name(self.show_name), network=_('Loading'),
                    network_image_url='images/network/nonetwork.png', show_image_url=lambda x: 'images/{}.png'.format(('poster', 'banner')['banner' in x]),
                    quality=0)

    def run(self):

        super(QueueItemAdd, self).run()

        if self.showDir:
            try:
                assert isinstance(self.showDir, six.text_type)
            except AssertionError:
                logger.log(traceback.format_exc(), logger.WARNING)
                self._finish_early()
                return

        logger.log(_('Starting to add show {0}').format(_('by ShowDir: {0}').format(self.showDir) if self.showDir else _('by Indexer Id: {0}').format(
            self.indexer_id)))
        # make sure the Indexer IDs are valid
        try:
            s = sickchill.indexer.series_by_id(indexerid=self.indexer_id, indexer=self.indexer, language=self.lang)
            if not s:
                error_string = _('Could not find show with id:{0} on {1}, skipping').format(
                    self.indexer_id, sickchill.indexer.name(self.indexer))

                logger.log(error_string)
                ui.notifications.error(_('Unable to add show'), error_string)

                self._finish_early()
                return

            # Let's try to create the show Dir if it's not provided. This way we force the show dir to build build using the
            # Indexers provided series name
            if self.root_dir and not self.showDir:
                if not s.seriesName:
                    logger.log(_('Unable to get a show {0}, can\'t add the show').format(self.showDir))
                    self._finish_early()
                    return

                show_dir = s.seriesName
                if sickbeard.ADD_SHOWS_WITH_YEAR and s.firstAired:
                    try:
                        year = '({0})'.format(dateutil.parser.parse(s.firstAired).year)
                        if year not in show_dir:
                            show_dir = '{0} {1}'.format(s.seriesName, year)
                    except (TypeError, ValueError):
                        logger.log(_('Could not append the show year folder for the show: {0}').format(show_dir))

                self.showDir = ek(os.path.join, self.root_dir, sanitize_filename(show_dir))

                if sickbeard.ADD_SHOWS_WO_DIR:
                    logger.log(_("Skipping initial creation of {0} due to config.ini setting").format(self.showDir))
                else:
                    dir_exists = makeDir(self.showDir)
                    if not dir_exists:
                        logger.log(_('Unable to create the folder {0}, can\'t add the show').format(self.showDir))
                        self._finish_early()
                        return

                    chmodAsParent(self.showDir)

            # this usually only happens if they have an NFO in their show dir which gave us a Indexer ID that has no proper english version of the show
            if getattr(s, 'seriesName', None) is None:
                # noinspection PyPep8
                error_string = _('Show in {0} has no name on {1}, probably searched with the wrong language. Delete .nfo and add manually in the correct language.').format(
                    self.showDir, sickchill.indexer.name(self.indexer))

                logger.log(error_string, logger.WARNING)
                ui.notifications.error(_('Unable to add show'), error_string)

                self._finish_early()
                return
        except Exception as error:
            error_string = 'Unable to look up the show in {0} on {1} using ID {2}, not using the NFO. Delete .nfo and try adding manually again.'.format(
                self.showDir, sickchill.indexer.name(self.indexer), self.indexer_id)

            logger.log('{0}: {1}'.format(error_string, error), logger.ERROR)
            ui.notifications.error(_('Unable to add show'), error_string)

            if sickbeard.USE_TRAKT:
                trakt_api = TraktAPI(sickbeard.SSL_VERIFY, sickbeard.TRAKT_TIMEOUT)

                title = self.showDir.split('/')[-1]
                data = {
                    'shows': [
                        {
                            'title': title,
                            'ids': {sickchill.indexer.slug(self.indexer): self.indexer_id}
                        }
                    ]
                }
                trakt_api.traktRequest('sync/watchlist/remove', data, method='POST')

            self._finish_early()
            return

        try:
            try:
                newShow = TVShow(self.indexer, self.indexer_id, self.lang)
            except MultipleShowObjectsException as error:
                # If we have the show in our list, but the location is wrong, lets fix it and refresh!
                existing_show = Show.find(sickbeard.showList, self.indexer_id)
                # noinspection PyProtectedMember
                if existing_show and not ek(os.path.isdir, existing_show._location):
                    newShow = existing_show
                else:
                    raise error

            newShow.loadFromIndexer()

            self.show = newShow

            # set up initial values
            self.show.location = self.showDir
            self.show.subtitles = self.subtitles if self.subtitles is not None else sickbeard.SUBTITLES_DEFAULT
            self.show.subtitles_sr_metadata = self.subtitles_sr_metadata
            self.show.quality = self.quality if self.quality else sickbeard.QUALITY_DEFAULT
            self.show.season_folders = self.season_folders if self.season_folders is not None else sickbeard.SEASON_FOLDERS_DEFAULT
            self.show.anime = self.anime if self.anime is not None else sickbeard.ANIME_DEFAULT
            self.show.scene = self.scene if self.scene is not None else sickbeard.SCENE_DEFAULT
            self.show.paused = self.paused if self.paused is not None else False

            # set up default new/missing episode status
            logger.log(_('Setting all episodes to the specified default status: {0}') .format(self.show.default_ep_status))
            self.show.default_ep_status = self.default_status

            if self.show.anime:
                self.show.release_groups = BlackAndWhiteList(self.show.indexerid)
                if self.blacklist:
                    self.show.release_groups.set_black_keywords(self.blacklist)
                if self.whitelist:
                    self.show.release_groups.set_white_keywords(self.whitelist)

            # # be smart-ish about this
            # if self.show.genre and 'talk show' in self.show.genre.lower():
            #     self.show.air_by_date = 1
            # if self.show.genre and 'documentary' in self.show.genre.lower():
            #     self.show.air_by_date = 0
            # if self.show.classification and 'sports' in self.show.classification.lower():
            #     self.show.sports = 1

        except Exception as error:
            error_string = 'Unable to add {0} due to an error with {1}'.format(
                self.show.name if self.show else 'show', sickchill.indexer.name(self.indexer))

            logger.log('{0}: {1}'.format(error_string, error), logger.ERROR)

            logger.log('Error trying to add show: {0}'.format(error), logger.ERROR)
            logger.log(traceback.format_exc(), logger.DEBUG)

            ui.notifications.error(_('Unable to add show'), error_string)

            self._finish_early()
            return

        except MultipleShowObjectsException:
            error_string = _('The show in {0} is already in your show list, skipping').format(self.showDir)
            logger.log(error_string, logger.WARNING)
            ui.notifications.error(_('Show skipped'), error_string)

            self._finish_early()
            return

        self.show.loadIMDbInfo()

        try:
            self.show.saveToDB()
        except Exception as error:
            logger.log('Error saving the show to the database: {0}'.format(error), logger.ERROR)
            logger.log(traceback.format_exc(), logger.DEBUG)
            self._finish_early()
            raise

        # add it to the show list
        if not Show.find(sickbeard.showList, self.indexer_id):
            sickbeard.showList.append(self.show)

        try:
            self.show.loadEpisodesFromIndexer()
        except Exception as error:
            logger.log('Error with {0}, not creating episode list: {1}'.format(self.show.idxr.name, error), logger.ERROR)
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
        scene_numbering.xem_refresh(self.show.indexerid, self.show.indexer, force=True)

        # check if show has XEM mapping so we can determine if searches should go by scene numbering or indexer numbering.
        if not self.scene and scene_numbering.get_xem_numbering_for_show(self.show.indexerid, self.show.indexer):
            self.show.scene = 1

        # After initial add, set to default_status_after.
        self.show.default_ep_status = self.default_status_after

        super(QueueItemAdd, self).finish()
        self.finish()

    def _finish_early(self):
        if self.show is not None:
            sickbeard.showQueueScheduler.action.remove_show(self.show)

        super(QueueItemAdd, self).finish()
        self.finish()


class QueueItemRefresh(ShowQueueItem):
    def __init__(self, show=None, force=False):
        super(QueueItemRefresh, self).__init__(ShowQueueActions.REFRESH, show)

        # do refreshes first because they're quick
        self.priority = generic_queue.QueuePriorities.HIGH

        # force refresh certain items
        self.force = force

    def run(self):

        super(QueueItemRefresh, self).run()

        logger.log('Performing refresh on {0}'.format(self.show.name))

        self.show.refreshDir()
        self.show.writeMetadata()
        if self.force:
            self.show.updateMetadata()
        self.show.populateCache()

        # Load XEM data to DB for show
        scene_numbering.xem_refresh(self.show.indexerid, self.show.indexer)

        super(QueueItemRefresh, self).finish()
        self.finish()


class QueueItemRename(ShowQueueItem):
    def __init__(self, show=None):
        super(QueueItemRename, self).__init__(ShowQueueActions.RENAME, show)

    def run(self):

        super(QueueItemRename, self).run()

        logger.log('Performing rename on {0}'.format(self.show.name))

        try:
            self.show.location
        except ShowDirectoryNotFoundException:
            logger.log('Can\'t perform rename on {0} when the show dir is missing.'.format(self.show.name), logger.WARNING)
            super(QueueItemRename, self).finish()
            self.finish()
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

        super(QueueItemRename, self).finish()
        self.finish()


class QueueItemSubtitle(ShowQueueItem):
    def __init__(self, show=None):
        super(QueueItemSubtitle, self).__init__(ShowQueueActions.SUBTITLE, show)

    def run(self):
        super(QueueItemSubtitle, self).run()

        logger.log('Downloading subtitles for {0} '.format(self.show.name))

        self.show.download_subtitles()

        super(QueueItemSubtitle, self).finish()
        self.finish()


class QueueItemUpdate(ShowQueueItem):
    def __init__(self, show=None, force=False):
        action = ShowQueueActions.FORCEUPDATE if force else ShowQueueActions.UPDATE
        super(QueueItemUpdate, self).__init__(action, show)
        self.force = force
        self.priority = generic_queue.QueuePriorities.HIGH

    def run(self):

        super(QueueItemUpdate, self).run()

        logger.log('Beginning update of {0}'.format(self.show.name), logger.DEBUG)

        logger.log('Retrieving show info from {0}'.format(self.show.idxr.name), logger.DEBUG)
        try:
            self.show.loadFromIndexer()
        except Exception as error:
            logger.log('Unable to contact {0}, aborting: {1}'.format(self.show.idxr.name, error), logger.WARNING)
            super(QueueItemUpdate, self).finish()
            self.finish()
            return

        self.show.loadIMDbInfo()

        # have to save show before reading episodes from db
        try:
            self.show.saveToDB()
        except Exception as error:
            logger.log('Error saving show info to the database: {0}'.format(error), logger.ERROR)
            logger.log(traceback.format_exc(), logger.DEBUG)

        # get episode list from DB
        DBEpList = self.show.loadEpisodesFromDB()

        # get episode list from TVDB
        logger.log('Loading all episodes from {0}'.format(self.show.idxr.name), logger.DEBUG)
        try:
            IndexerEpList = self.show.loadEpisodesFromIndexer()
        except Exception as error:
            logger.log('Unable to get info from {0}, the show info will not be refreshed: {1}'.format
                       (self.show.idxr.name, error), logger.ERROR)
            IndexerEpList = None

        if IndexerEpList:
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

        # sickbeard.showQueueScheduler.action.refresh_show(self.show, self.force)
        QueueItemRefresh(self.show, self.force).run()
        super(QueueItemUpdate, self).finish()
        self.finish()


class QueueItemRemove(ShowQueueItem):
    def __init__(self, show=None, full=False):
        super(QueueItemRemove, self).__init__(ShowQueueActions.REMOVE, show)

        # lets make sure this happens before any other high priority actions
        self.priority = generic_queue.QueuePriorities.HIGH ** 2
        self.full = full

    def run(self):
        super(QueueItemRemove, self).run()
        logger.log('Removing {0}'.format(self.show.name))
        self.show.deleteShow(full=self.full)

        if sickbeard.USE_TRAKT:
            try:
                sickbeard.traktCheckerScheduler.action.removeShowFromTraktLibrary(self.show)
            except Exception as error:
                logger.log(_('Unable to delete show from Trakt: {0}. Error: {1}').format(self.show.name, error), logger.WARNING)

        # If any notification fails, don't stop removal
        try:
            # TODO: ep_obj is undefined here, so all of these will fail.
            # send notifications
            # notifiers.notify_download(ep_obj._format_pattern('%SN - %Sx%0E - %EN - %QN'))

            # do the library update for KODI
            notifiers.kodi_notifier.update_library(self.show.name)

            # do the library update for Plex
            notifiers.plex_notifier.update_library(self.show)

            # do the library update for EMBY
            notifiers.emby_notifier.update_library(self.show)

            # do the library update for NMJ
            # nmj_notifier kicks off its library update when the notify_download is issued (inside notifiers)

            # do the library update for Synology Indexer
            notifiers.synoindex_notifier.addFolder(self.show._location)

            # do the library update for pyTivo
            notifiers.pytivo_notifier.update_library(self.show)
        except Exception:
            logger.log(_("Some notifications could not be sent. Continuing removal of {}...").format(self.show.name))

        super(QueueItemRemove, self).finish()
        self.finish()
