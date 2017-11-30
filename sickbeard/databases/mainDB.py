# coding=utf-8

# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickrage.github.io
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
# pylint: disable=line-too-long

from __future__ import print_function, unicode_literals

import datetime
import os.path
import warnings

import six

import sickbeard
from sickbeard import common, db, helpers, logger, subtitles
from sickbeard.name_parser.parser import InvalidNameException, InvalidShowException, NameParser
from sickrage.helper.common import dateTimeFormat, episode_num
from sickrage.helper.encoding import ek

MIN_DB_VERSION = 9  # oldest db version we support migrating from
MAX_DB_VERSION = 44


class MainSanityCheck(db.DBSanityCheck):
    def check(self):
        self.fix_missing_table_indexes()
        self.fix_duplicate_shows()
        self.fix_duplicate_episodes()
        self.fix_orphan_episodes()
        self.fix_unaired_episodes()
        self.fix_tvrage_show_statues()
        self.fix_episode_statuses()
        self.fix_invalid_airdates()
        # self.fix_subtitles_codes()
        self.fix_show_nfo_lang()
        self.convert_tvrage_to_tvdb()
        self.convert_archived_to_compound()

    def convert_archived_to_compound(self):
        logger.log('Checking for archived episodes not qualified', logger.DEBUG)

        query = "SELECT episode_id, showid, status, location, season, episode " + \
                "FROM tv_episodes WHERE status = {0}".format(common.ARCHIVED)

        sql_results = self.connection.select(query)
        if sql_results:
            logger.log("Found {0:d} shows with bare archived status, attempting automatic conversion...".format(len(sql_results)), logger.WARNING)

        for archivedEp in sql_results:
            fixedStatus = common.Quality.compositeStatus(common.ARCHIVED, common.Quality.UNKNOWN)
            existing = archivedEp[b'location'] and ek(os.path.exists, archivedEp[b'location'])
            if existing:
                quality = common.Quality.nameQuality(archivedEp[b'location'])
                fixedStatus = common.Quality.compositeStatus(common.ARCHIVED, quality)

            logger.log('Changing status from {old_status} to {new_status} for {id}: {ep} at {location} (File {result})'.format
                       (old_status=common.statusStrings[common.ARCHIVED], new_status=common.statusStrings[fixedStatus],
                        id=archivedEp[b'showid'], ep=episode_num(archivedEp[b'season'], archivedEp[b'episode']),
                        location=archivedEp[b'location'] if archivedEp[b'location'] else 'unknown location',
                        result=('NOT FOUND', 'EXISTS')[bool(existing)]))

            self.connection.action("UPDATE tv_episodes SET status = {0:d} WHERE episode_id = {1:d}".format(fixedStatus, archivedEp[b'episode_id']))

    def convert_tvrage_to_tvdb(self):
        logger.log("Checking for shows with tvrage id's, since tvrage is gone", logger.DEBUG)
        from sickbeard.indexers.indexer_config import INDEXER_TVRAGE
        from sickbeard.indexers.indexer_config import INDEXER_TVDB

        sql_results = self.connection.select("SELECT indexer_id, show_name, location FROM tv_shows WHERE indexer = {0:d}".format(INDEXER_TVRAGE))

        if sql_results:
            logger.log("Found {0:d} shows with TVRage ID's, attempting automatic conversion...".format(len(sql_results)), logger.WARNING)

        for tvrage_show in sql_results:
            logger.log("Processing {0} at {1}".format(tvrage_show[b'show_name'], tvrage_show[b'location']))
            mapping = self.connection.select("SELECT mindexer_id FROM indexer_mapping WHERE indexer_id={0:d} AND indexer={1:d} AND mindexer={2:d}".format
                                             (tvrage_show[b'indexer_id'], INDEXER_TVRAGE, INDEXER_TVDB))

            if len(mapping) != 1:
                logger.log("Error mapping show from tvrage to tvdb for {0} ({1}), found {2:d} mapping results. Cannot convert automatically!".format
                           (tvrage_show[b'show_name'], tvrage_show[b'location'], len(mapping)), logger.WARNING)

                logger.log("Removing the TVRage show and it's episodes from the DB, use 'addExistingShow'", logger.WARNING)
                self.connection.action("DELETE FROM tv_shows WHERE indexer_id = {0:d} AND indexer = {1:d}".format(tvrage_show[b'indexer_id'], INDEXER_TVRAGE))
                self.connection.action("DELETE FROM tv_episodes WHERE showid = {0:d}".format(tvrage_show[b'indexer_id']))
                continue

            logger.log('Checking if there is already a show with id:%i in the show list')
            duplicate = self.connection.select("SELECT show_name, indexer_id, location FROM tv_shows WHERE indexer_id = {0:d} AND indexer = {1:d}".format(
                mapping[0][b'mindexer_id'], INDEXER_TVDB))
            if duplicate:
                logger.log('Found {0} which has the same id as {1}, cannot convert automatically so I am pausing {2}'.format(
                    duplicate[0][b'show_name'], tvrage_show[b'show_name'], duplicate[0][b'show_name']), logger.WARNING
                )
                self.connection.action("UPDATE tv_shows SET paused=1 WHERE indexer={0:d} AND indexer_id={1:d}".format(
                    INDEXER_TVDB, duplicate[0][b'indexer_id'])
                )

                logger.log("Removing {0} and it's episodes from the DB".format(tvrage_show[b'show_name']), logger.WARNING)
                self.connection.action("DELETE FROM tv_shows WHERE indexer_id = {0:d} AND indexer = {1:d}".format(tvrage_show[b'indexer_id'], INDEXER_TVRAGE))
                self.connection.action("DELETE FROM tv_episodes WHERE showid = {0:d}".format(tvrage_show[b'indexer_id']))
                logger.log('Manually move the season folders from {0} into {1}, and delete {2} before rescanning {3} and unpausing it'.format(
                    tvrage_show[b'location'], duplicate[0][b'location'], tvrage_show[b'location'], duplicate[0][b'show_name']), logger.WARNING
                )
                continue

            logger.log('Mapping {0} to tvdb id {1:d}'.format(tvrage_show[b'show_name'], mapping[0][b'mindexer_id']))

            self.connection.action(
                "UPDATE tv_shows SET indexer={0:d}, indexer_id={1:d} WHERE indexer_id={2:d}".format(
                    INDEXER_TVDB, mapping[0][b'mindexer_id'], tvrage_show[b'indexer_id']
                )
            )

            logger.log('Relinking episodes to show')
            self.connection.action(
                "UPDATE tv_episodes SET indexer={0:d}, showid={1:d}, indexerid=0 WHERE showid={2:d}".format(
                    INDEXER_TVDB, mapping[0][b'mindexer_id'], tvrage_show[b'indexer_id']
                )
            )

            logger.log('Please perform a full update on {0}'.format(tvrage_show[b'show_name']), logger.WARNING)

    def fix_duplicate_shows(self, column=b'indexer_id'):

        sql_results = self.connection.select(
            "SELECT show_id, " + column + ", COUNT(" + column + ") as count FROM tv_shows GROUP BY " + column + " HAVING count > 1")

        for cur_duplicate in sql_results:

            logger.log("Duplicate show detected! " + column + ": " + str(cur_duplicate[column]) + " count: " + str(
                cur_duplicate[b"count"]), logger.DEBUG)

            cur_dupe_results = self.connection.select(
                "SELECT show_id, " + column + " FROM tv_shows WHERE " + column + " = ? LIMIT ?",
                [cur_duplicate[column], int(cur_duplicate[b"count"]) - 1]
            )

            for cur_dupe_id in cur_dupe_results:
                logger.log(
                    "Deleting duplicate show with " + column + ": " + str(cur_dupe_id[column]) + " show_id: " + str(
                        cur_dupe_id[b"show_id"]))
                self.connection.action("DELETE FROM tv_shows WHERE show_id = ?", [cur_dupe_id[b"show_id"]])

    def fix_duplicate_episodes(self):

        sql_results = self.connection.select(
            "SELECT showid, season, episode, COUNT(showid) as count FROM tv_episodes GROUP BY showid, season, episode HAVING count > 1")

        for cur_duplicate in sql_results:

            logger.log("Duplicate episode detected! showid: {dupe_id} season: {dupe_season} episode {dupe_episode} count: {dupe_count}".format
                       (dupe_id=str(cur_duplicate[b"showid"]), dupe_season=str(cur_duplicate[b"season"]), dupe_episode=str(cur_duplicate[b"episode"]),
                        dupe_count=str(cur_duplicate[b"count"])),
                       logger.DEBUG)

            cur_dupe_results = self.connection.select(
                "SELECT episode_id FROM tv_episodes WHERE showid = ? AND season = ? and episode = ? ORDER BY episode_id DESC LIMIT ?",
                [cur_duplicate[b"showid"], cur_duplicate[b"season"], cur_duplicate[b"episode"],
                 int(cur_duplicate[b"count"]) - 1]
            )

            for cur_dupe_id in cur_dupe_results:
                logger.log("Deleting duplicate episode with episode_id: " + str(cur_dupe_id[b"episode_id"]))
                self.connection.action("DELETE FROM tv_episodes WHERE episode_id = ?", [cur_dupe_id[b"episode_id"]])

    def fix_orphan_episodes(self):

        sql_results = self.connection.select(
            "SELECT episode_id, showid, tv_shows.indexer_id FROM tv_episodes LEFT JOIN tv_shows ON tv_episodes.showid=tv_shows.indexer_id WHERE tv_shows.indexer_id is NULL")

        for cur_orphan in sql_results:
            logger.log("Orphan episode detected! episode_id: " + str(cur_orphan[b"episode_id"]) + " showid: " + str(
                cur_orphan[b"showid"]), logger.DEBUG)
            logger.log("Deleting orphan episode with episode_id: " + str(cur_orphan[b"episode_id"]))
            self.connection.action("DELETE FROM tv_episodes WHERE episode_id = ?", [cur_orphan[b"episode_id"]])

    def fix_missing_table_indexes(self):
        if not self.connection.select("PRAGMA index_info('idx_indexer_id')"):
            logger.log("Missing idx_indexer_id for TV Shows table detected!, fixing...")
            self.connection.action("CREATE UNIQUE INDEX idx_indexer_id ON tv_shows(indexer_id);")

        if not self.connection.select("PRAGMA index_info('idx_tv_episodes_showid_airdate')"):
            logger.log("Missing idx_tv_episodes_showid_airdate for TV Episodes table detected!, fixing...")
            self.connection.action("CREATE INDEX idx_tv_episodes_showid_airdate ON tv_episodes(showid, airdate);")

        if not self.connection.select("PRAGMA index_info('idx_showid')"):
            logger.log("Missing idx_showid for TV Episodes table detected!, fixing...")
            self.connection.action("CREATE INDEX idx_showid ON tv_episodes (showid);")

        if not self.connection.select("PRAGMA index_info('idx_status')"):
            logger.log("Missing idx_status for TV Episodes table detected!, fixing...")
            self.connection.action("CREATE INDEX idx_status ON tv_episodes (status, season, episode, airdate)")

        if not self.connection.select("PRAGMA index_info('idx_sta_epi_air')"):
            logger.log("Missing idx_sta_epi_air for TV Episodes table detected!, fixing...")
            self.connection.action("CREATE INDEX idx_sta_epi_air ON tv_episodes (status, episode, airdate)")

        if not self.connection.select("PRAGMA index_info('idx_sta_epi_sta_air')"):
            logger.log("Missing idx_sta_epi_sta_air for TV Episodes table detected!, fixing...")
            self.connection.action("CREATE INDEX idx_sta_epi_sta_air ON tv_episodes (season, episode, status, airdate)")

    def fix_unaired_episodes(self):

        curDate = datetime.date.today()
        
        if curDate.year >= 2017:

            sql_results = self.connection.select(
                "SELECT episode_id FROM tv_episodes WHERE (airdate > ? or airdate = 1) AND status in (?,?) AND season > 0",
                [curDate.toordinal(), common.SKIPPED, common.WANTED])

            for cur_unaired in sql_results:
                logger.log("Fixing unaired episode status for episode_id: {0}".format(cur_unaired[b"episode_id"]))
                self.connection.action("UPDATE tv_episodes SET status = ? WHERE episode_id = ?",
                                       [common.UNAIRED, cur_unaired[b"episode_id"]])

    def fix_tvrage_show_statues(self):
        status_map = {
            'returning series': 'Continuing',
            'canceled/ended': 'Ended',
            'tbd/on the bubble': 'Continuing',
            'in development': 'Continuing',
            'new series': 'Continuing',
            'never aired': 'Ended',
            'final season': 'Continuing',
            'on hiatus': 'Continuing',
            'pilot ordered': 'Continuing',
            'pilot rejected': 'Ended',
            'canceled': 'Ended',
            'ended': 'Ended',
            '': 'Unknown',
        }

        for old_status, new_status in six.iteritems(status_map):
            self.connection.action("UPDATE tv_shows SET status = ? WHERE LOWER(status) = ?", [new_status, old_status])

    def fix_episode_statuses(self):
        sql_results = self.connection.select("SELECT episode_id, showid FROM tv_episodes WHERE status IS NULL")

        for cur_ep in sql_results:
            logger.log("MALFORMED episode status detected! episode_id: " + str(cur_ep[b"episode_id"]) + " showid: " + str(
                cur_ep[b"showid"]), logger.DEBUG)
            logger.log("Fixing malformed episode status with episode_id: " + str(cur_ep[b"episode_id"]))
            self.connection.action("UPDATE tv_episodes SET status = ? WHERE episode_id = ?",
                                   [common.UNKNOWN, cur_ep[b"episode_id"]])

    def fix_invalid_airdates(self):

        sql_results = self.connection.select(
            "SELECT episode_id, showid FROM tv_episodes WHERE airdate >= ? OR airdate < 1",
            [datetime.date.max.toordinal()])

        for bad_airdate in sql_results:
            logger.log("Bad episode airdate detected! episode_id: " + str(bad_airdate[b"episode_id"]) + " showid: " + str(
                bad_airdate[b"showid"]), logger.DEBUG)
            logger.log("Fixing bad episode airdate for episode_id: " + str(bad_airdate[b"episode_id"]))
            self.connection.action("UPDATE tv_episodes SET airdate = '1' WHERE episode_id = ?", [bad_airdate[b"episode_id"]])

    def fix_subtitles_codes(self):

        sql_results = self.connection.select(
            "SELECT subtitles, episode_id FROM tv_episodes WHERE subtitles != '' AND subtitles_lastsearch < ?;",
            [datetime.datetime(2015, 7, 15, 17, 20, 44, 326380).strftime(dateTimeFormat)]
        )

        for sql_result in sql_results:
            langs = []

            logger.log("Checking subtitle codes for episode_id: {0}, codes: {1}".format(sql_result[b'episode_id'], sql_result[b'subtitles']), logger.DEBUG)

            for subcode in sql_result[b'subtitles'].split(','):
                if not len(subcode) == 3 or subcode not in subtitles.subtitle_code_filter():
                    logger.log("Fixing subtitle codes for episode_id: {0}, invalid code: {1}".format(sql_result[b'episode_id'], subcode), logger.DEBUG)
                    continue

                langs.append(subcode)

            self.connection.action("UPDATE tv_episodes SET subtitles = ?, subtitles_lastsearch = ? WHERE episode_id = ?;",
                                   [','.join(langs), datetime.datetime.now().strftime(dateTimeFormat), sql_result[b'episode_id']])

    def fix_show_nfo_lang(self):
        self.connection.action("UPDATE tv_shows SET lang = '' WHERE lang = 0 or lang = '0'")


def backupDatabase(version):
    logger.log("Backing up database before upgrade")
    if not helpers.backupVersionedFile(db.dbFilename(), version):
        logger.log_error_and_exit("Database backup failed, abort upgrading database")
    else:
        logger.log("Proceeding with upgrade")


# ======================
# = Main DB Migrations =
# ======================
# Add new migrations at the bottom of the list; subclass the previous migration.

class InitialSchema(db.SchemaUpgrade):
    def test(self):
        return self.hasTable("db_version")

    def execute(self):
        if not self.hasTable("tv_shows") and not self.hasTable("db_version"):
            queries = [
                "CREATE TABLE db_version(db_version INTEGER);",
                "CREATE TABLE history(action NUMERIC, date NUMERIC, showid NUMERIC, season NUMERIC, episode NUMERIC, quality NUMERIC, resource TEXT, provider TEXT, version NUMERIC DEFAULT -1);",
                "CREATE TABLE imdb_info(indexer_id INTEGER PRIMARY KEY, imdb_id TEXT, title TEXT, year NUMERIC, akas TEXT, runtimes NUMERIC, genres TEXT, countries TEXT, country_codes TEXT, certificates TEXT, rating TEXT, votes INTEGER, last_update NUMERIC);",
                "CREATE TABLE info(last_backlog NUMERIC, last_indexer NUMERIC, last_proper_search NUMERIC);",
                "CREATE TABLE scene_numbering(indexer TEXT, indexer_id INTEGER, season INTEGER, episode INTEGER, scene_season INTEGER, scene_episode INTEGER, absolute_number NUMERIC, scene_absolute_number NUMERIC, PRIMARY KEY(indexer_id, season, episode));",
                "CREATE TABLE tv_shows(show_id INTEGER PRIMARY KEY, indexer_id NUMERIC, indexer NUMERIC, show_name TEXT, location TEXT, network TEXT, genre TEXT, classification TEXT, runtime NUMERIC, quality NUMERIC, airs TEXT, status TEXT, flatten_folders NUMERIC, paused NUMERIC, startyear NUMERIC, air_by_date NUMERIC, lang TEXT, subtitles NUMERIC, notify_list TEXT, imdb_id TEXT, last_update_indexer NUMERIC, dvdorder NUMERIC, archive_firstmatch NUMERIC, rls_require_words TEXT, rls_ignore_words TEXT, sports NUMERIC, anime NUMERIC, scene NUMERIC, default_ep_status NUMERIC DEFAULT -1);",
                "CREATE TABLE tv_episodes(episode_id INTEGER PRIMARY KEY, showid NUMERIC, indexerid NUMERIC, indexer TEXT, name TEXT, season NUMERIC, episode NUMERIC, description TEXT, airdate NUMERIC, hasnfo NUMERIC, hastbn NUMERIC, status NUMERIC, location TEXT, file_size NUMERIC, release_name TEXT, subtitles TEXT, subtitles_searchcount NUMERIC, subtitles_lastsearch TIMESTAMP, is_proper NUMERIC, scene_season NUMERIC, scene_episode NUMERIC, absolute_number NUMERIC, scene_absolute_number NUMERIC, version NUMERIC DEFAULT -1, release_group TEXT);",
                "CREATE TABLE blacklist (show_id INTEGER, range TEXT, keyword TEXT);",
                "CREATE TABLE whitelist (show_id INTEGER, range TEXT, keyword TEXT);",
                "CREATE TABLE xem_refresh (indexer TEXT, indexer_id INTEGER PRIMARY KEY, last_refreshed INTEGER);",
                "CREATE TABLE indexer_mapping (indexer_id INTEGER, indexer NUMERIC, mindexer_id INTEGER, mindexer NUMERIC, PRIMARY KEY (indexer_id, indexer));",
                "CREATE UNIQUE INDEX idx_indexer_id ON tv_shows(indexer_id);",
                "CREATE INDEX idx_showid ON tv_episodes(showid);",
                "CREATE INDEX idx_sta_epi_air ON tv_episodes(status, episode, airdate);",
                "CREATE INDEX idx_sta_epi_sta_air ON tv_episodes(season, episode, status, airdate);",
                "CREATE INDEX idx_status ON tv_episodes(status,season,episode,airdate);",
                "CREATE INDEX idx_tv_episodes_showid_airdate ON tv_episodes(showid, airdate);",
                "INSERT INTO db_version(db_version) VALUES (43);"
            ]
            for query in queries:
                self.connection.action(query)

        else:
            cur_db_version = self.checkDBVersion()

            if cur_db_version < MIN_DB_VERSION:
                logger.log_error_and_exit(
                    "Your database version ({cur_db_version}) is too old to migrate from what this version of SickRage supports ({min_db_version}).\n"
                    "Upgrade using a previous version (tag) build 496 to build 501 of SickRage first or remove database file to begin fresh.".format
                    (cur_db_version=str(cur_db_version), min_db_version=str(MIN_DB_VERSION)))

            if cur_db_version > MAX_DB_VERSION:
                logger.log_error_and_exit(
                    "Your database version ({cur_db_version}) has been incremented past what this version of SickRage supports ({max_db_version}).\n"
                    "If you have used other forks of SickRage, your database may be unusable due to their modifications.".format
                    (cur_db_version=str(cur_db_version), max_db_version=str(MAX_DB_VERSION)))


class AddSizeAndSceneNameFields(InitialSchema):
    def test(self):
        return self.checkDBVersion() >= 10

    def execute(self):

        backupDatabase(self.checkDBVersion())

        if not self.hasColumn("tv_episodes", "file_size"):
            self.addColumn("tv_episodes", "file_size")

        if not self.hasColumn("tv_episodes", "release_name"):
            self.addColumn("tv_episodes", "release_name", "TEXT", "")

        ep_results = self.connection.select("SELECT episode_id, location, file_size FROM tv_episodes")

        logger.log("Adding file size to all episodes in DB, please be patient")
        for cur_ep in ep_results:
            if not cur_ep[b"location"]:
                continue

            # if there is no size yet then populate it for us
            if (not cur_ep[b"file_size"] or not int(cur_ep[b"file_size"])) and ek(os.path.isfile, cur_ep[b"location"]):
                cur_size = ek(os.path.getsize, cur_ep[b"location"])
                self.connection.action("UPDATE tv_episodes SET file_size = ? WHERE episode_id = ?",
                                       [cur_size, int(cur_ep[b"episode_id"])])

        # check each snatch to see if we can use it to get a release name from
        history_results = self.connection.select("SELECT * FROM history WHERE provider != -1 ORDER BY date ASC")

        logger.log("Adding release name to all episodes still in history")
        for cur_result in history_results:
            # find the associated download, if there isn't one then ignore it
            download_results = self.connection.select(
                "SELECT resource FROM history WHERE provider = -1 AND showid = ? AND season = ? AND episode = ? AND date > ?",
                [cur_result[b"showid"], cur_result[b"season"], cur_result[b"episode"], cur_result[b"date"]])
            if not download_results:
                logger.log(
                    "Found a snatch in the history for " + cur_result[b"resource"] + " but couldn't find the associated download, skipping it",
                    logger.DEBUG
                )
                continue

            nzb_name = cur_result[b"resource"]
            file_name = ek(os.path.basename, download_results[0][b"resource"])

            # take the extension off the filename, it's not needed
            if '.' in file_name:
                file_name = file_name.rpartition('.')[0]

            # find the associated episode on disk
            ep_results = self.connection.select(
                "SELECT episode_id, status FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ? AND location != ''",
                [cur_result[b"showid"], cur_result[b"season"], cur_result[b"episode"]])
            if not ep_results:
                logger.log(
                    "The episode " + nzb_name + " was found in history but doesn't exist on disk anymore, skipping",
                    logger.DEBUG)
                continue

            # get the status/quality of the existing ep and make sure it's what we expect
            ep_status, ep_quality = common.Quality.splitCompositeStatus(int(ep_results[0][b"status"]))
            if ep_status != common.DOWNLOADED:
                continue

            if ep_quality != int(cur_result[b"quality"]):
                continue

            # make sure this is actually a real release name and not a season pack or something
            for cur_name in (nzb_name, file_name):
                logger.log("Checking if " + cur_name + " is actually a good release name", logger.DEBUG)
                try:
                    parse_result = NameParser(False).parse(cur_name)
                except (InvalidNameException, InvalidShowException):
                    continue

                if parse_result.series_name and parse_result.season_number is not None and parse_result.episode_numbers and parse_result.release_group:
                    # if all is well by this point we'll just put the release name into the database
                    self.connection.action("UPDATE tv_episodes SET release_name = ? WHERE episode_id = ?",
                                           [cur_name, ep_results[0][b"episode_id"]])
                    break

        # check each snatch to see if we can use it to get a release name from
        empty_results = self.connection.select("SELECT episode_id, location FROM tv_episodes WHERE release_name = ''")

        logger.log("Adding release name to all episodes with obvious scene filenames")
        for cur_result in empty_results:

            ep_file_name = ek(os.path.basename, cur_result[b"location"])
            ep_file_name = ek(os.path.splitext, ep_file_name)[0]

            # only want to find real scene names here so anything with a space in it is out
            if ' ' in ep_file_name:
                continue

            try:
                parse_result = NameParser(False).parse(ep_file_name)
            except (InvalidNameException, InvalidShowException):
                continue

            if not parse_result.release_group:
                continue

            logger.log(
                "Name " + ep_file_name + " gave release group of " + parse_result.release_group + ", seems valid",
                logger.DEBUG)
            self.connection.action("UPDATE tv_episodes SET release_name = ? WHERE episode_id = ?",
                                   [ep_file_name, cur_result[b"episode_id"]])

        self.incDBVersion()


class RenameSeasonFolders(AddSizeAndSceneNameFields):
    def test(self):
        return self.checkDBVersion() >= 11

    def execute(self):
        backupDatabase(self.checkDBVersion())

        # rename the column
        self.connection.action("DROP TABLE IF EXISTS tmp_tv_shows")
        self.connection.action("ALTER TABLE tv_shows RENAME TO tmp_tv_shows")
        self.connection.action(
            "CREATE TABLE tv_shows (show_id INTEGER PRIMARY KEY, location TEXT, show_name TEXT, tvdb_id NUMERIC, network TEXT, genre TEXT, runtime NUMERIC, quality NUMERIC, airs TEXT, status TEXT, flatten_folders NUMERIC, paused NUMERIC, startyear NUMERIC, tvr_id NUMERIC, tvr_name TEXT, air_by_date NUMERIC, lang TEXT)")
        self.connection.action("INSERT INTO tv_shows SELECT * FROM tmp_tv_shows")

        # flip the values to be opposite of what they were before
        self.connection.action("UPDATE tv_shows SET flatten_folders = 2 WHERE flatten_folders = 1")
        self.connection.action("UPDATE tv_shows SET flatten_folders = 1 WHERE flatten_folders = 0")
        self.connection.action("UPDATE tv_shows SET flatten_folders = 0 WHERE flatten_folders = 2")
        self.connection.action("DROP TABLE tmp_tv_shows")

        self.incDBVersion()


class Add1080pAndRawHDQualities(RenameSeasonFolders):
    """Add support for 1080p related qualities along with RawHD

    Quick overview of what the upgrade needs to do:

           quality   | old  | new
        --------------------------
        hdwebdl      | 1<<3 | 1<<5
        hdbluray     | 1<<4 | 1<<7
        fullhdbluray | 1<<5 | 1<<8
        --------------------------
        rawhdtv      |      | 1<<3
        fullhdtv     |      | 1<<4
        fullhdwebdl  |      | 1<<6
    """

    def test(self):
        return self.checkDBVersion() >= 12

    def _update_status(self, old_status):
        (status, quality) = common.Quality.splitCompositeStatus(old_status)
        return common.Quality.compositeStatus(status, self._update_quality(quality))

    def _update_quality(self, old_quality):
        """Update bitwise flags to reflect new quality values

        Check flag bits (clear old then set their new locations) starting
        with the highest bits so we dont overwrite data we need later on
        """

        result = old_quality
        # move fullhdbluray from 1<<5 to 1<<8 if set
        if result & (1 << 5):
            result &= ~(1 << 5)
            result |= 1 << 8
        # move hdbluray from 1<<4 to 1<<7 if set
        if result & (1 << 4):
            result &= ~(1 << 4)
            result |= 1 << 7
        # move hdwebdl from 1<<3 to 1<<5 if set
        if result & (1 << 3):
            result &= ~(1 << 3)
            result |= 1 << 5

        return result

    def _update_composite_qualities(self, status):
        """Unpack, Update, Return new quality values

        Unpack the composite archive/initial values.
        Update either qualities if needed.
        Then return the new compsite quality value.
        """

        best = (status & (0xffff << 16)) >> 16
        initial = status & 0xffff

        best = self._update_quality(best)
        initial = self._update_quality(initial)

        result = ((best << 16) | initial)
        return result

    def execute(self):
        backupDatabase(self.checkDBVersion())

        # update the default quality so we dont grab the wrong qualities after migration
        sickbeard.QUALITY_DEFAULT = self._update_composite_qualities(sickbeard.QUALITY_DEFAULT)
        sickbeard.save_config()

        # upgrade previous HD to HD720p -- shift previous qualities to new placevalues
        old_hd = common.Quality.combineQualities(
            [common.Quality.HDTV, common.Quality.HDWEBDL >> 2, common.Quality.HDBLURAY >> 3], [])
        new_hd = common.Quality.combineQualities([common.Quality.HDTV, common.Quality.HDWEBDL, common.Quality.HDBLURAY],
                                                 [])

        # update ANY -- shift existing qualities and add new 1080p qualities, note that rawHD was not added to the ANY template
        old_any = common.Quality.combineQualities(
            [common.Quality.SDTV, common.Quality.SDDVD, common.Quality.HDTV, common.Quality.HDWEBDL >> 2,
             common.Quality.HDBLURAY >> 3, common.Quality.UNKNOWN], [])
        new_any = common.Quality.combineQualities(
            [common.Quality.SDTV, common.Quality.SDDVD, common.Quality.HDTV, common.Quality.FULLHDTV,
             common.Quality.HDWEBDL, common.Quality.FULLHDWEBDL, common.Quality.HDBLURAY, common.Quality.FULLHDBLURAY,
             common.Quality.UNKNOWN], [])

        # update qualities (including templates)
        logger.log("[1/4] Updating pre-defined templates and the quality for each show...", logger.INFO)
        cl = []
        shows = self.connection.select("SELECT * FROM tv_shows")
        for cur_show in shows:
            if cur_show[b"quality"] == old_hd:
                new_quality = new_hd
            elif cur_show[b"quality"] == old_any:
                new_quality = new_any
            else:
                new_quality = self._update_composite_qualities(cur_show[b"quality"])
            cl.append(["UPDATE tv_shows SET quality = ? WHERE show_id = ?", [new_quality, cur_show[b"show_id"]]])
        self.connection.mass_action(cl)

        # update status that are are within the old hdwebdl (1<<3 which is 8) and better -- exclude unknown (1<<15 which is 32768)
        logger.log("[2/4] Updating the status for the episodes within each show...", logger.INFO)
        cl = []
        episodes = self.connection.select("SELECT * FROM tv_episodes WHERE status < 3276800 AND status >= 800")
        for cur_episode in episodes:
            cl.append(["UPDATE tv_episodes SET status = ? WHERE episode_id = ?",
                       [self._update_status(cur_episode[b"status"]), cur_episode[b"episode_id"]]])
        self.connection.mass_action(cl)

        # make two seperate passes through the history since snatched and downloaded (action & quality) may not always coordinate together

        # update previous history so it shows the correct action
        logger.log("[3/4] Updating history to reflect the correct action...", logger.INFO)
        cl = []
        historyAction = self.connection.select("SELECT * FROM history WHERE action < 3276800 AND action >= 800")
        for cur_entry in historyAction:
            cl.append(["UPDATE history SET action = ? WHERE showid = ? AND date = ?",
                       [self._update_status(cur_entry[b"action"]), cur_entry[b"showid"], cur_entry[b"date"]]])
        self.connection.mass_action(cl)

        # update previous history so it shows the correct quality
        logger.log("[4/4] Updating history to reflect the correct quality...", logger.INFO)
        cl = []
        historyQuality = self.connection.select("SELECT * FROM history WHERE quality < 32768 AND quality >= 8")
        for cur_entry in historyQuality:
            cl.append(["UPDATE history SET quality = ? WHERE showid = ? AND date = ?",
                       [self._update_quality(cur_entry[b"quality"]), cur_entry[b"showid"], cur_entry[b"date"]]])
        self.connection.mass_action(cl)

        self.incDBVersion()

        # cleanup and reduce db if any previous data was removed
        logger.log("Performing a vacuum on the database.", logger.DEBUG)
        self.connection.action("VACUUM")


class AddShowidTvdbidIndex(Add1080pAndRawHDQualities):
    """ Adding index on tvdb_id (tv_shows) and showid (tv_episodes) to speed up searches/queries """

    def test(self):
        return self.checkDBVersion() >= 13

    def execute(self):
        backupDatabase(self.checkDBVersion())

        logger.log("Check for duplicate shows before adding unique index.")
        MainSanityCheck(self.connection).fix_duplicate_shows(b'tvdb_id')

        logger.log("Adding index on tvdb_id (tv_shows) and showid (tv_episodes) to speed up searches/queries.")
        if not self.hasTable("idx_showid"):
            self.connection.action("CREATE INDEX idx_showid ON tv_episodes (showid);")
        if not self.hasTable("idx_tvdb_id"):
            self.connection.action("CREATE UNIQUE INDEX idx_tvdb_id ON tv_shows (tvdb_id);")

        self.incDBVersion()


class AddLastUpdateTVDB(AddShowidTvdbidIndex):
    """ Adding column last_update_tvdb to tv_shows for controlling nightly updates """

    def test(self):
        return self.checkDBVersion() >= 14

    def execute(self):
        backupDatabase(self.checkDBVersion())

        logger.log("Adding column last_update_tvdb to tvshows")
        if not self.hasColumn("tv_shows", "last_update_tvdb"):
            self.addColumn("tv_shows", "last_update_tvdb", default=1)

        self.incDBVersion()


class AddDBIncreaseTo15(AddLastUpdateTVDB):
    def test(self):
        return self.checkDBVersion() >= 15

    def execute(self):
        backupDatabase(self.checkDBVersion())
        self.incDBVersion()


class AddIMDbInfo(AddDBIncreaseTo15):
    def test(self):
        return self.checkDBVersion() >= 16

    def execute(self):
        backupDatabase(self.checkDBVersion())
        self.connection.action(
            "CREATE TABLE imdb_info (tvdb_id INTEGER PRIMARY KEY, imdb_id TEXT, title TEXT, year NUMERIC, akas TEXT, runtimes NUMERIC, genres TEXT, countries TEXT, country_codes TEXT, certificates TEXT, rating TEXT, votes INTEGER, last_update NUMERIC)")

        if not self.hasColumn("tv_shows", "imdb_id"):
            self.addColumn("tv_shows", "imdb_id")

        self.incDBVersion()


class AddProperNamingSupport(AddIMDbInfo):
    def test(self):
        return self.checkDBVersion() >= 17

    def execute(self):
        backupDatabase(self.checkDBVersion())
        self.addColumn("tv_episodes", "is_proper")
        self.incDBVersion()


class AddEmailSubscriptionTable(AddProperNamingSupport):
    def test(self):
        return self.checkDBVersion() >= 18

    def execute(self):
        backupDatabase(self.checkDBVersion())
        self.addColumn('tv_shows', 'notify_list', 'TEXT', None)
        self.incDBVersion()


class AddProperSearch(AddEmailSubscriptionTable):
    def test(self):
        return self.checkDBVersion() >= 19

    def execute(self):
        backupDatabase(self.checkDBVersion())

        logger.log("Adding column last_proper_search to info")
        if not self.hasColumn("info", "last_proper_search"):
            self.addColumn("info", "last_proper_search", default=1)

        self.incDBVersion()


class AddDvdOrderOption(AddProperSearch):
    def test(self):
        return self.checkDBVersion() >= 20

    def execute(self):
        backupDatabase(self.checkDBVersion())
        logger.log("Adding column dvdorder to tvshows")
        if not self.hasColumn("tv_shows", "dvdorder"):
            self.addColumn("tv_shows", "dvdorder", "NUMERIC", "0")

        self.incDBVersion()


class AddSubtitlesSupport(AddDvdOrderOption):
    def test(self):
        return self.checkDBVersion() >= 21

    def execute(self):
        backupDatabase(self.checkDBVersion())
        if not self.hasColumn("tv_shows", "subtitles"):
            self.addColumn("tv_shows", "subtitles")
            self.addColumn("tv_episodes", "subtitles", "TEXT", "")
            self.addColumn("tv_episodes", "subtitles_searchcount")
            self.addColumn("tv_episodes", "subtitles_lastsearch", "TIMESTAMP", str(datetime.datetime.min))
        self.incDBVersion()


class ConvertTVShowsToIndexerScheme(AddSubtitlesSupport):
    def test(self):
        return self.checkDBVersion() >= 22

    def execute(self):
        backupDatabase(self.checkDBVersion())

        logger.log("Converting TV Shows table to Indexer Scheme...")

        self.connection.action("DROP TABLE IF EXISTS tmp_tv_shows")

        self.connection.action("ALTER TABLE tv_shows RENAME TO tmp_tv_shows")
        self.connection.action("CREATE TABLE tv_shows (show_id INTEGER PRIMARY KEY, indexer_id NUMERIC, indexer NUMERIC, show_name TEXT, location TEXT, network TEXT, genre TEXT, classification TEXT, runtime NUMERIC, quality NUMERIC, airs TEXT, status TEXT, flatten_folders NUMERIC, paused NUMERIC, startyear NUMERIC, air_by_date NUMERIC, lang TEXT, subtitles NUMERIC, notify_list TEXT, imdb_id TEXT, last_update_indexer NUMERIC, dvdorder NUMERIC)")
        self.connection.action(
            "INSERT INTO tv_shows (show_id, indexer_id, show_name, location, network, genre, runtime, quality, airs, status, flatten_folders, paused, startyear, air_by_date, lang, subtitles, dvdorder) " +
            "SELECT show_id, tvdb_id as indexer_id, show_name, location, network, genre, runtime, quality, airs, status, flatten_folders, paused, startyear, air_by_date, lang, subtitles, dvdorder FROM tmp_tv_shows"
        )
        self.connection.action("DROP TABLE tmp_tv_shows")

        self.connection.action("CREATE UNIQUE INDEX idx_indexer_id ON tv_shows (indexer_id);")

        self.connection.action("UPDATE tv_shows SET classification = 'Scripted'")
        self.connection.action("UPDATE tv_shows SET indexer = 1")

        self.incDBVersion()


class ConvertTVEpisodesToIndexerScheme(ConvertTVShowsToIndexerScheme):
    def test(self):
        return self.checkDBVersion() >= 23

    def execute(self):
        backupDatabase(self.checkDBVersion())

        logger.log("Converting TV Episodes table to Indexer Scheme...")

        self.connection.action("DROP TABLE IF EXISTS tmp_tv_episodes")

        self.connection.action("ALTER TABLE tv_episodes RENAME TO tmp_tv_episodes")
        self.connection.action(
            "CREATE TABLE tv_episodes (episode_id INTEGER PRIMARY KEY, showid NUMERIC, indexerid NUMERIC, indexer NUMERIC, name TEXT, season NUMERIC, episode NUMERIC, description TEXT, airdate NUMERIC, hasnfo NUMERIC, hastbn NUMERIC, status NUMERIC, location TEXT, file_size NUMERIC, release_name TEXT, subtitles TEXT, subtitles_searchcount NUMERIC, subtitles_lastsearch TIMESTAMP, is_proper NUMERIC)")

        self.connection.action(
            "INSERT INTO tv_episodes (episode_id, showid, indexerid, name, season, episode, description, airdate, hasnfo, hastbn, status, location, file_size, release_name, subtitles, subtitles_searchcount, subtitles_lastsearch) " +
            "SELECT episode_id, showid, tvdbid as indexerid, name, season, episode, description, airdate, hasnfo, hastbn, status, location, file_size, release_name, subtitles, subtitles_searchcount, subtitles_lastsearch FROM tmp_tv_episodes"
        )

        self.connection.action("DROP TABLE tmp_tv_episodes")

        self.connection.action("CREATE INDEX idx_tv_episodes_showid_airdate ON tv_episodes(showid,airdate);")
        self.connection.action("CREATE INDEX idx_showid ON tv_episodes (showid);")
        self.connection.action("CREATE INDEX idx_status ON tv_episodes (status,season,episode,airdate)")
        self.connection.action("CREATE INDEX idx_sta_epi_air ON tv_episodes (status,episode, airdate)")
        self.connection.action("CREATE INDEX idx_sta_epi_sta_air ON tv_episodes (season,episode, status, airdate)")

        self.connection.action("UPDATE tv_episodes SET indexer = 1, is_proper = 0")

        self.incDBVersion()


class ConvertIMDBInfoToIndexerScheme(ConvertTVEpisodesToIndexerScheme):
    def test(self):
        return self.checkDBVersion() >= 24

    def execute(self):
        backupDatabase(self.checkDBVersion())

        logger.log("Converting IMDB Info table to Indexer Scheme...")

        self.connection.action("DROP TABLE IF EXISTS tmp_imdb_info")

        if self.hasTable("imdb_info"):
            self.connection.action("ALTER TABLE imdb_info RENAME TO tmp_imdb_info")

        self.connection.action(
            "CREATE TABLE imdb_info (indexer_id INTEGER PRIMARY KEY, imdb_id TEXT, title TEXT, year NUMERIC, akas TEXT, runtimes NUMERIC, genres TEXT, countries TEXT, country_codes TEXT, certificates TEXT, rating TEXT, votes INTEGER, last_update NUMERIC)")

        if self.hasTable("tmp_imdb_info"):
            self.connection.action("INSERT INTO imdb_info SELECT * FROM tmp_imdb_info")

        self.connection.action("DROP TABLE IF EXISTS tmp_imdb_info")

        self.incDBVersion()


class ConvertInfoToIndexerScheme(ConvertIMDBInfoToIndexerScheme):
    def test(self):
        return self.checkDBVersion() >= 25

    def execute(self):
        backupDatabase(self.checkDBVersion())

        logger.log("Converting Info table to Indexer Scheme...")

        self.connection.action("DROP TABLE IF EXISTS tmp_info")

        self.connection.action("ALTER TABLE info RENAME TO tmp_info")
        self.connection.action(
            "CREATE TABLE info (last_backlog NUMERIC, last_indexer NUMERIC, last_proper_search NUMERIC)")
        self.connection.action(
            "INSERT INTO info SELECT * FROM tmp_info")
        self.connection.action("DROP TABLE tmp_info")

        self.incDBVersion()


class AddArchiveFirstMatchOption(ConvertInfoToIndexerScheme):
    def test(self):
        return self.checkDBVersion() >= 26

    def execute(self):
        backupDatabase(self.checkDBVersion())

        logger.log("Adding column archive_firstmatch to tvshows")
        if not self.hasColumn("tv_shows", "archive_firstmatch"):
            self.addColumn("tv_shows", "archive_firstmatch", "NUMERIC", "0")

        self.incDBVersion()


class AddSceneNumbering(AddArchiveFirstMatchOption):
    def test(self):
        return self.checkDBVersion() >= 27

    def execute(self):
        backupDatabase(self.checkDBVersion())

        if self.hasTable("scene_numbering"):
            self.connection.action("DROP TABLE scene_numbering")

        self.connection.action(
            "CREATE TABLE scene_numbering (indexer TEXT, indexer_id INTEGER, season INTEGER, episode INTEGER, scene_season INTEGER, scene_episode INTEGER, PRIMARY KEY (indexer_id, season, episode, scene_season, scene_episode))")

        self.incDBVersion()


class ConvertIndexerToInteger(AddSceneNumbering):
    def test(self):
        return self.checkDBVersion() >= 28

    def execute(self):
        backupDatabase(self.checkDBVersion())

        cl = []
        logger.log("Converting Indexer to Integer ...", logger.INFO)
        cl.append(["UPDATE tv_shows SET indexer = ? WHERE LOWER(indexer) = ?", ["1", "tvdb"]])
        cl.append(["UPDATE tv_shows SET indexer = ? WHERE LOWER(indexer) = ?", ["2", "tvrage"]])
        cl.append(["UPDATE tv_episodes SET indexer = ? WHERE LOWER(indexer) = ?", ["1", "tvdb"]])
        cl.append(["UPDATE tv_episodes SET indexer = ? WHERE LOWER(indexer) = ?", ["2", "tvrage"]])
        cl.append(["UPDATE scene_numbering SET indexer = ? WHERE LOWER(indexer) = ?", ["1", "tvdb"]])
        cl.append(["UPDATE scene_numbering SET indexer = ? WHERE LOWER(indexer) = ?", ["2", "tvrage"]])

        self.connection.mass_action(cl)

        self.incDBVersion()


class AddRequireAndIgnoreWords(ConvertIndexerToInteger):
    """ Adding column rls_require_words and rls_ignore_words to tv_shows """

    def test(self):
        return self.checkDBVersion() >= 29

    def execute(self):
        backupDatabase(self.checkDBVersion())

        logger.log("Adding column rls_require_words to tvshows")
        if not self.hasColumn("tv_shows", "rls_require_words"):
            self.addColumn("tv_shows", "rls_require_words", "TEXT", "")

        logger.log("Adding column rls_ignore_words to tvshows")
        if not self.hasColumn("tv_shows", "rls_ignore_words"):
            self.addColumn("tv_shows", "rls_ignore_words", "TEXT", "")

        self.incDBVersion()


class AddSportsOption(AddRequireAndIgnoreWords):
    def test(self):
        return self.checkDBVersion() >= 30

    def execute(self):
        backupDatabase(self.checkDBVersion())

        logger.log("Adding column sports to tvshows")
        if not self.hasColumn("tv_shows", "sports"):
            self.addColumn("tv_shows", "sports", "NUMERIC", "0")

        if self.hasColumn("tv_shows", "air_by_date") and self.hasColumn("tv_shows", "sports"):
            # update sports column
            logger.log("[4/4] Updating tv_shows to reflect the correct sports value...", logger.INFO)
            cl = []
            historyQuality = self.connection.select(
                "SELECT * FROM tv_shows WHERE LOWER(classification) = 'sports' AND air_by_date = 1 AND sports = 0")
            for cur_entry in historyQuality:
                cl.append(["UPDATE tv_shows SET sports = ? WHERE show_id = ?",
                           [cur_entry[b"air_by_date"], cur_entry[b"show_id"]]])
                cl.append(["UPDATE tv_shows SET air_by_date = 0 WHERE show_id = ?", [cur_entry[b"show_id"]]])
            self.connection.mass_action(cl)

        self.incDBVersion()


class AddSceneNumberingToTvEpisodes(AddSportsOption):
    def test(self):
        return self.checkDBVersion() >= 31

    def execute(self):
        backupDatabase(self.checkDBVersion())

        logger.log("Adding column scene_season and scene_episode to tvepisodes")
        self.addColumn("tv_episodes", "scene_season", "NUMERIC", "NULL")
        self.addColumn("tv_episodes", "scene_episode", "NUMERIC", "NULL")

        self.incDBVersion()


class AddAnimeTVShow(AddSceneNumberingToTvEpisodes):
    def test(self):
        return self.checkDBVersion() >= 32

    def execute(self):
        backupDatabase(self.checkDBVersion())

        logger.log("Adding column anime to tv_episodes")
        self.addColumn("tv_shows", "anime", "NUMERIC", "0")

        self.incDBVersion()


class AddAbsoluteNumbering(AddAnimeTVShow):
    def test(self):
        return self.checkDBVersion() >= 33

    def execute(self):
        backupDatabase(self.checkDBVersion())

        logger.log("Adding column absolute_number to tv_episodes")
        self.addColumn("tv_episodes", "absolute_number", "NUMERIC", "0")

        self.incDBVersion()


class AddSceneAbsoluteNumbering(AddAbsoluteNumbering):
    def test(self):
        return self.checkDBVersion() >= 34

    def execute(self):
        backupDatabase(self.checkDBVersion())

        logger.log("Adding column absolute_number and scene_absolute_number to scene_numbering")
        self.addColumn("scene_numbering", "absolute_number", "NUMERIC", "0")
        self.addColumn("scene_numbering", "scene_absolute_number", "NUMERIC", "0")

        self.incDBVersion()


class AddAnimeBlacklistWhitelist(AddSceneAbsoluteNumbering):

    def test(self):
        return self.checkDBVersion() >= 35

    def execute(self):
        backupDatabase(self.checkDBVersion())

        cl = [
            ["CREATE TABLE blacklist (show_id INTEGER, range TEXT, keyword TEXT)"],
            ["CREATE TABLE whitelist (show_id INTEGER, range TEXT, keyword TEXT)"]
        ]

        self.connection.mass_action(cl)

        self.incDBVersion()


class AddSceneAbsoluteNumbering2(AddAnimeBlacklistWhitelist):
    def test(self):
        return self.checkDBVersion() >= 36

    def execute(self):
        backupDatabase(self.checkDBVersion())

        logger.log("Adding column scene_absolute_number to tv_episodes")
        self.addColumn("tv_episodes", "scene_absolute_number", "NUMERIC", "0")

        self.incDBVersion()


class AddXemRefresh(AddSceneAbsoluteNumbering2):
    def test(self):
        return self.checkDBVersion() >= 37

    def execute(self):
        backupDatabase(self.checkDBVersion())

        logger.log("Creating table xem_refresh")
        self.connection.action(
            "CREATE TABLE xem_refresh (indexer TEXT, indexer_id INTEGER PRIMARY KEY, last_refreshed INTEGER)")

        self.incDBVersion()


class AddSceneToTvShows(AddXemRefresh):
    def test(self):
        return self.checkDBVersion() >= 38

    def execute(self):
        backupDatabase(self.checkDBVersion())

        logger.log("Adding column scene to tv_shows")
        self.addColumn("tv_shows", "scene", "NUMERIC", "0")

        self.incDBVersion()


class AddIndexerMapping(AddSceneToTvShows):
    def test(self):
        return self.checkDBVersion() >= 39

    def execute(self):
        backupDatabase(self.checkDBVersion())

        if self.hasTable("indexer_mapping"):
            self.connection.action("DROP TABLE indexer_mapping")

        logger.log("Adding table indexer_mapping")
        self.connection.action(
            "CREATE TABLE indexer_mapping (indexer_id INTEGER, indexer NUMERIC, mindexer_id INTEGER, mindexer NUMERIC, PRIMARY KEY (indexer_id, indexer))")

        self.incDBVersion()


class AddVersionToTvEpisodes(AddIndexerMapping):
    def test(self):
        return self.checkDBVersion() >= 40

    def execute(self):
        backupDatabase(self.checkDBVersion())

        logger.log("Adding column version to tv_episodes and history")
        self.addColumn("tv_episodes", "version", "NUMERIC", "-1")
        self.addColumn("tv_episodes", "release_group", "TEXT", "")
        self.addColumn("history", "version", "NUMERIC", "-1")

        self.incDBVersion()


class AddDefaultEpStatusToTvShows(AddVersionToTvEpisodes):
    def test(self):
        return self.checkDBVersion() >= 41

    def execute(self):
        backupDatabase(self.checkDBVersion())

        logger.log("Adding column default_ep_status to tv_shows")
        self.addColumn("tv_shows", "default_ep_status", "NUMERIC", "-1")

        self.incDBVersion()


class AlterTVShowsFieldTypes(AddDefaultEpStatusToTvShows):
    def test(self):
        return self.checkDBVersion() >= 42

    def execute(self):
        backupDatabase(self.checkDBVersion())

        logger.log("Converting column indexer and default_ep_status field types to numeric")
        self.connection.action("DROP TABLE IF EXISTS tmp_tv_shows")
        self.connection.action("ALTER TABLE tv_shows RENAME TO tmp_tv_shows")
        self.connection.action("CREATE TABLE tv_shows (show_id INTEGER PRIMARY KEY, indexer_id NUMERIC, indexer NUMERIC, show_name TEXT, location TEXT, network TEXT, genre TEXT, classification TEXT, runtime NUMERIC, quality NUMERIC, airs TEXT, status TEXT, flatten_folders NUMERIC, paused NUMERIC, startyear NUMERIC, air_by_date NUMERIC, lang TEXT, subtitles NUMERIC, notify_list TEXT, imdb_id TEXT, last_update_indexer NUMERIC, dvdorder NUMERIC, archive_firstmatch NUMERIC, rls_require_words TEXT, rls_ignore_words TEXT, sports NUMERIC, anime NUMERIC, scene NUMERIC, default_ep_status NUMERIC)")
        self.connection.action("INSERT INTO tv_shows SELECT * FROM tmp_tv_shows")
        self.connection.action("DROP TABLE tmp_tv_shows")

        self.incDBVersion()


class AddMinorVersion(AlterTVShowsFieldTypes):
    def test(self):
        return self.checkDBVersion() >= 42 and self.hasColumn(b'db_version', b'db_minor_version')

    def incDBVersion(self):
        warnings.warn("Deprecated: Use inc_major_version or inc_minor_version instead", DeprecationWarning)

    def inc_major_version(self):
        major_version, minor_version = self.connection.version
        major_version += 1
        minor_version = 0
        self.connection.action("UPDATE db_version SET db_version = ?, db_minor_version = ?", [major_version, minor_version])
        return self.connection.version

    def inc_minor_version(self):
        major_version, minor_version = self.connection.version
        minor_version += 1
        self.connection.action("UPDATE db_version SET db_version = ?, db_minor_version = ?", [major_version, minor_version])
        return self.connection.version

    def execute(self):
        backupDatabase(self.checkDBVersion())

        logger.log("Add minor version numbers to database")
        self.addColumn(b'db_version', b'db_minor_version')

        self.inc_minor_version()

        logger.log('Updated to: {0:d}.{1:d}'.format(*self.connection.version))


class UseSickRageMetadataForSubtitle(AlterTVShowsFieldTypes):
    """
    Add a minor version for adding a show setting to use SR metadata for subtitles
    """
    def test(self):
        return self.hasColumn('tv_shows', 'sub_use_sr_metadata')

    def execute(self):
        backupDatabase(self.checkDBVersion())
        self.addColumn('tv_shows', 'sub_use_sr_metadata', "NUMERIC", "0")


class ResetDBVersion(UseSickRageMetadataForSubtitle):
    def test(self):
        return False

    def execute(self):
        self.connection.action("UPDATE db_version SET db_version = ?, db_minor_version = ?", [MAX_DB_VERSION, 0])
