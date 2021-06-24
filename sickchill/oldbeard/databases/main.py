import datetime
import os.path

from sickchill import logger
from sickchill.helper.common import episode_num
from sickchill.oldbeard import common, db, helpers

MIN_DB_VERSION = 44
MAX_DB_VERSION = 44


class MainSanityCheck(db.DBSanityCheck):
    def check(self):
        self.fix_missing_table_indexes()
        self.fix_duplicate_shows()
        self.fix_duplicate_episodes()
        self.fix_orphan_episodes()
        self.fix_unaired_episodes()
        self.fix_episode_statuses()
        self.fix_invalid_airdates()
        self.fix_show_nfo_lang()
        self.convert_archived_to_compound()

    def convert_archived_to_compound(self):
        logger.debug(_("Checking for archived episodes not qualified"))

        sql_results = self.connection.select(
            "SELECT episode_id, showid, status, location, season, episode FROM tv_episodes WHERE status = ?", [common.ARCHIVED]
        )
        if sql_results:
            logger.warning(_("Found {count} shows with bare archived status, attempting automatic conversion...".format(count=len(sql_results))))

        for archivedEp in sql_results:
            fixed_status = common.Quality.compositeStatus(common.ARCHIVED, common.Quality.UNKNOWN)
            existing = archivedEp["location"] and os.path.exists(archivedEp["location"])
            if existing:
                quality = common.Quality.nameQuality(archivedEp["location"])
                fixed_status = common.Quality.compositeStatus(common.ARCHIVED, quality)

            old_status = common.statusStrings[common.ARCHIVED]
            new_status = common.statusStrings[fixed_status]
            archived_episode = archivedEp["showid"]
            ep = episode_num(archivedEp["season"])
            episode_id = archivedEp["episode_id"]
            location = archivedEp["location"] or "unknown location"
            result = ("NOT FOUND", "EXISTS")[bool(existing)]

            logger.info(
                _(
                    "Changing status from {old_status} to {new_status} for {archived_episode}: {ep} at {location} (File {result})".format(
                        old_status=old_status, new_status=new_status, archived_episode=archived_episode, ep=ep, location=location, result=result
                    )
                )
            )

            self.connection.action("UPDATE tv_episodes SET status = ? WHERE episode_id = ?", [fixed_status, episode_id])

    def fix_duplicate_shows(self, column="indexer_id"):

        sql_results = self.connection.select(f"SELECT show_id, {column}, COUNT({column}) as count FROM tv_shows GROUP BY {column} HAVING count > 1")

        for cur_duplicate in sql_results:

            logger.debug(
                _("Duplicate show detected! {column}: {dupe} count: {count}".format(column=column, dupe=cur_duplicate[column], count=cur_duplicate["count"]))
            )

            cur_dupe_results = self.connection.select(
                "SELECT show_id, " + column + " FROM tv_shows WHERE " + column + " = ? LIMIT ?", [cur_duplicate[column], int(cur_duplicate["count"]) - 1]
            )

            for cur_dupe_id in cur_dupe_results:
                logger.info(
                    _(
                        "Deleting duplicate show with {column}: {dupe} showid: {show}".format(
                            column=column, dupe=cur_dupe_id[column], show=cur_dupe_id["show_id"]
                        )
                    )
                )
                self.connection.action("DELETE FROM tv_shows WHERE show_id = ?", [cur_dupe_id["show_id"]])

    def fix_duplicate_episodes(self):

        sql_results = self.connection.select(
            "SELECT showid, season, episode, COUNT(showid) as count FROM tv_episodes GROUP BY showid, season, episode HAVING count > 1"
        )

        for cur_duplicate in sql_results:
            dupe_id = cur_duplicate["showid"]
            dupe_season = cur_duplicate["season"]
            dupe_episode = (cur_duplicate["episode"],)
            dupe_count = cur_duplicate["count"]
            logger.debug(
                _(
                    "Duplicate episode detected! showid: {dupe_id} season: {dupe_season} episode {dupe_episode} count: {dupe_count}".format(
                        dupe_id=dupe_id, dupe_season=dupe_season, dupe_episode=dupe_episode, dupe_count=dupe_count
                    )
                )
            )

            cur_dupe_results = self.connection.select(
                "SELECT episode_id FROM tv_episodes WHERE showid = ? AND season = ? and episode = ? ORDER BY episode_id DESC LIMIT ?",
                [cur_duplicate["showid"], cur_duplicate["season"], cur_duplicate["episode"], int(cur_duplicate["count"]) - 1],
            )

            for cur_dupe_id in cur_dupe_results:
                current_episode_id = cur_dupe_id["episode_id"]
                logger.info(_("Deleting duplicate episode with episode_id: {current_episode_id}".format(current_episode_id=current_episode_id)))
                self.connection.action("DELETE FROM tv_episodes WHERE episode_id = ?", [current_episode_id])

    def fix_orphan_episodes(self):

        sql_results = self.connection.select(
            "SELECT episode_id, showid, tv_shows.indexer_id FROM tv_episodes "
            "LEFT JOIN tv_shows ON tv_episodes.showid=tv_shows.indexer_id WHERE tv_shows.indexer_id is NULL"
        )

        for cur_orphan in sql_results:
            current_episode_id = cur_orphan["episode_id"]
            current_show_id = cur_orphan["showid"]
            logger.debug(
                _(
                    "Orphan episode detected! episode_id: {current_episode_id} showid: {current_show_id}".format(
                        current_episode_id=current_episode_id, current_show_id=current_show_id
                    )
                )
            )
            logger.info(_("Deleting orphan episode with episode_id: {current_episode_id}".format(current_episode_id=current_episode_id)))
            self.connection.action("DELETE FROM tv_episodes WHERE episode_id = ?", [current_episode_id])

    def fix_missing_table_indexes(self):
        if not self.connection.select("PRAGMA index_info('idx_indexer_id')"):
            logger.info(_("Missing idx_indexer_id for TV Shows table detected!, fixing..."))
            self.connection.action("CREATE UNIQUE INDEX idx_indexer_id ON tv_shows(indexer_id);")

        if not self.connection.select("PRAGMA index_info('idx_tv_episodes_showid_airdate')"):
            logger.info(_("Missing idx_tv_episodes_showid_airdate for TV Episodes table detected!, fixing..."))
            self.connection.action("CREATE INDEX idx_tv_episodes_showid_airdate ON tv_episodes(showid, airdate);")

        if not self.connection.select("PRAGMA index_info('idx_showid')"):
            logger.info(_("Missing idx_showid for TV Episodes table detected!, fixing..."))
            self.connection.action("CREATE INDEX idx_showid ON tv_episodes (showid);")

        if not self.connection.select("PRAGMA index_info('idx_status')"):
            logger.info(_("Missing idx_status for TV Episodes table detected!, fixing..."))
            self.connection.action("CREATE INDEX idx_status ON tv_episodes (status, season, episode, airdate)")

        if not self.connection.select("PRAGMA index_info('idx_sta_epi_air')"):
            logger.info(_("Missing idx_sta_epi_air for TV Episodes table detected!, fixing..."))
            self.connection.action("CREATE INDEX idx_sta_epi_air ON tv_episodes (status, episode, airdate)")

        if not self.connection.select("PRAGMA index_info('idx_sta_epi_sta_air')"):
            logger.info(_("Missing idx_sta_epi_sta_air for TV Episodes table detected!, fixing..."))
            self.connection.action("CREATE INDEX idx_sta_epi_sta_air ON tv_episodes (season, episode, status, airdate)")

    def fix_unaired_episodes(self):

        current_date = datetime.date.today()
        sql_results = self.connection.select(
            "SELECT episode_id FROM tv_episodes WHERE (airdate > ? or airdate = 1) AND status in (?,?) AND season > 0",
            [current_date.toordinal(), common.SKIPPED, common.WANTED],
        )

        for cur_unaired in sql_results:
            current_episode_id = cur_unaired["episode_id"]
            logger.info(_("Fixing unaired episode status for episode_id: {current_episode_id}".format(current_episode_id=current_episode_id)))
            self.connection.action("UPDATE tv_episodes SET status = ? WHERE episode_id = ?", [common.UNAIRED, current_episode_id])

    def fix_episode_statuses(self):
        sql_results = self.connection.select("SELECT episode_id, showid FROM tv_episodes WHERE status IS NULL")
        for cur_ep in sql_results:
            current_episode_id = cur_ep["episode_id"]
            current_show_id = cur_ep["showid"]
            logger.debug(
                _(
                    "MALFORMED episode status detected! episode_id: {current_episode_id} showid: {current_show_id}".format(
                        current_episode_id=current_episode_id, current_show_id=current_show_id
                    )
                )
            )
            logger.info(_("Fixing malformed episode status with episode_id: {current_episode_id}".format(current_episode_id=current_episode_id)))
            self.connection.action("UPDATE tv_episodes SET status = ? WHERE episode_id = ?", [common.UNKNOWN, current_episode_id])

    def fix_invalid_airdates(self):

        sql_results = self.connection.select("SELECT episode_id, showid FROM tv_episodes WHERE airdate >= ? OR airdate < 1", [datetime.date.max.toordinal()])

        for bad_airdate in sql_results:
            current_episode_id = bad_airdate["episode_id"]
            current_show_id = bad_airdate["showid"]
            logger.debug(
                _(
                    "Bad episode airdate detected! episode_id: {current_episode_id} showid: {current_show_id}".format(
                        current_episode_id=current_episode_id, current_show_id=current_show_id
                    )
                )
            )
            logger.info(_("Fixing bad episode airdate for episode_id: {current_episode_id}".format(current_episode_id=current_episode_id)))
            self.connection.action("UPDATE tv_episodes SET airdate = '1' WHERE episode_id = ?", [current_episode_id])

    def fix_show_nfo_lang(self):
        self.connection.action("UPDATE tv_shows SET lang = '' WHERE lang = 0 or lang = '0'")


def backup_database(version):
    logger.info("Backing up database before upgrade")
    if not helpers.backupVersionedFile(db.db_full_path(), "{0}.{1}".format(*version)):
        logger.log_error_and_exit("Database backup failed, abort upgrading database")
    else:
        logger.info("Proceeding with upgrade")


# ======================
# = Main DB Migrations =
# ======================
# Add new migrations at the bottom of the list; subclass the previous migration.


class InitialSchema(db.SchemaUpgrade):
    def test(self):
        return self.has_table("db_version")

    def execute(self):
        if not self.has_table("tv_shows") and not self.has_table("db_version"):
            queries = [
                "CREATE TABLE db_version(db_version INTEGER, db_minor_version INTEGER);",
                "CREATE TABLE history(action NUMERIC, date NUMERIC, showid NUMERIC, season NUMERIC, episode NUMERIC, quality NUMERIC, resource TEXT, provider TEXT, version NUMERIC DEFAULT -1);",
                "CREATE TABLE imdb_info(indexer_id INTEGER PRIMARY KEY, imdb_id TEXT, title TEXT, year NUMERIC, akas TEXT, runtimes NUMERIC, genres TEXT, countries TEXT, country_codes TEXT, certificates TEXT, rating TEXT, votes INTEGER, last_update NUMERIC);",
                "CREATE TABLE info(last_backlog NUMERIC, last_indexer NUMERIC, last_proper_search NUMERIC);",
                "CREATE TABLE scene_numbering(indexer TEXT, indexer_id INTEGER, season INTEGER, episode INTEGER, scene_season INTEGER, scene_episode INTEGER, absolute_number NUMERIC, scene_absolute_number NUMERIC, PRIMARY KEY(indexer_id, season, episode));",
                "CREATE TABLE tv_shows(show_id INTEGER PRIMARY KEY, indexer_id NUMERIC, indexer NUMERIC, show_name TEXT, location TEXT, network TEXT, genre TEXT, classification TEXT, runtime NUMERIC, quality NUMERIC, airs TEXT, status TEXT, flatten_folders NUMERIC, paused NUMERIC, startyear NUMERIC, air_by_date NUMERIC, lang TEXT, subtitles NUMERIC, notify_list TEXT, imdb_id TEXT, last_update_indexer NUMERIC, dvdorder NUMERIC, archive_firstmatch NUMERIC, rls_require_words TEXT, rls_ignore_words TEXT, sports NUMERIC, anime NUMERIC, scene NUMERIC, default_ep_status NUMERIC DEFAULT -1, sub_use_sr_metadata NUMERIC DEFAULT 0);",
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
                "INSERT INTO db_version(db_version, db_minor_version) VALUES (44, 3);",
            ]
            for query in queries:
                self.connection.action(query)

        else:
            cur_db_version = self.get_db_version()

            if cur_db_version < MIN_DB_VERSION:
                logger.log_error_and_exit(
                    _(
                        "Your database version ({cur_db_version}) is too old to migrate from what this version of SickChill supports ({MIN_DB_VERSION}).\nUpgrade using a previous version (tag) build 496 to build 501 of SickChill first or remove database file to begin fresh.".format(
                            cur_db_version=cur_db_version, MIN_DB_VERSION=MIN_DB_VERSION
                        )
                    )
                )

            if cur_db_version > MAX_DB_VERSION:
                logger.log_error_and_exit(
                    _(
                        "Your database version ({cur_db_version}) has been incremented past what this version of SickChill supports ({MAX_DB_VERSION}).\nIf you have used other forks of SickChill, your database may be unusable due to their modifications.".format(
                            cur_db_version=cur_db_version, MAX_DB_VERSION=MAX_DB_VERSION
                        )
                    )
                )


class AddPreferWords(InitialSchema):
    """ Adding column rls_prefer_words to tv_shows """

    def test(self):
        return self.has_column("tv_shows", "rls_prefer_words")

    def execute(self):
        backup_database(self.connection.version)

        logger.info("Adding column rls_prefer_words to tvshows")
        self.add_column("tv_shows", "rls_prefer_words", "TEXT", "")
        self.inc_minor_version()
        logger.info("Updated to: {0:d}.{1:d}".format(*self.connection.version))


class AddCustomNameToShow(AddPreferWords):
    """ Adding column rls_prefer_words to tv_shows """

    def test(self):
        return self.has_column("tv_shows", "custom_name")

    def execute(self):
        backup_database(self.connection.version)

        logger.info("Adding column custom_name to tvshows")
        self.add_column("tv_shows", "custom_name", "TEXT", "")
        self.inc_minor_version()
        logger.info("Updated to: {0:d}.{1:d}".format(*self.connection.version))
