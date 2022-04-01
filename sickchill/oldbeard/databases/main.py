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
            count = len(sql_results)
            logger.warning(_(f"Found {count} shows with bare archived status, attempting automatic conversion..."))

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

            logger.info(_(f"Changing status from {old_status} to {new_status} for {archived_episode}: {ep} at {location} (File {result})"))

            self.connection.action("UPDATE tv_episodes SET status = ? WHERE episode_id = ?", [fixed_status, episode_id])

    def fix_duplicate_shows(self, column="indexer_id"):

        sql_results = self.connection.select(f"SELECT show_id, {column}, COUNT({column}) as count FROM tv_shows GROUP BY {column} HAVING count > 1")

        for cur_duplicate in sql_results:

            logger.debug(_(f"Duplicate show detected! {column}: {cur_duplicate[column]} count: {cur_duplicate['count']}"))

            cur_dupe_results = self.connection.select(
                "SELECT show_id, " + column + " FROM tv_shows WHERE " + column + " = ? LIMIT ?", [cur_duplicate[column], int(cur_duplicate["count"]) - 1]
            )

            for cur_dupe_id in cur_dupe_results:
                logger.info(_(f"Deleting duplicate show with {column}: {cur_dupe_id[column]} showid: {cur_dupe_id['show_id']}"))
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
            logger.debug(_(f"Duplicate episode detected! showid: {dupe_id} season: {dupe_season} episode {dupe_episode} count: {dupe_count}"))

            cur_dupe_results = self.connection.select(
                "SELECT episode_id FROM tv_episodes WHERE showid = ? AND season = ? and episode = ? ORDER BY episode_id DESC LIMIT ?",
                [cur_duplicate["showid"], cur_duplicate["season"], cur_duplicate["episode"], int(cur_duplicate["count"]) - 1],
            )

            for cur_dupe_id in cur_dupe_results:
                current_episode_id = cur_dupe_id["episode_id"]
                logger.info(_(f"Deleting duplicate episode with episode_id: {current_episode_id}"))
                self.connection.action("DELETE FROM tv_episodes WHERE episode_id = ?", [current_episode_id])

    def fix_orphan_episodes(self):

        sql_results = self.connection.select(
            "SELECT episode_id, showid, tv_shows.indexer_id FROM tv_episodes "
            "LEFT JOIN tv_shows ON tv_episodes.showid=tv_shows.indexer_id WHERE tv_shows.indexer_id is NULL"
        )

        for cur_orphan in sql_results:
            current_episode_id = cur_orphan["episode_id"]
            current_show_id = cur_orphan["showid"]
            logger.debug(_(f"Orphan episode detected! episode_id: {current_episode_id} showid: {current_show_id}"))
            logger.info(_(f"Deleting orphan episode with episode_id: {current_episode_id}"))
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
            logger.info(_(f"Fixing unaired episode status for episode_id: {current_episode_id}"))
            self.connection.action("UPDATE tv_episodes SET status = ? WHERE episode_id = ?", [common.UNAIRED, current_episode_id])

    def fix_episode_statuses(self):
        sql_results = self.connection.select("SELECT episode_id, showid FROM tv_episodes WHERE status IS NULL")
        for cur_ep in sql_results:
            current_episode_id = cur_ep["episode_id"]
            current_show_id = cur_ep["showid"]
            logger.debug(_(f"MALFORMED episode status detected! episode_id: {current_episode_id} showid: {current_show_id}"))
            logger.info(_(f"Fixing malformed episode status with episode_id: {current_episode_id}"))
            self.connection.action("UPDATE tv_episodes SET status = ? WHERE episode_id = ?", [common.UNKNOWN, current_episode_id])

    def fix_invalid_airdates(self):

        sql_results = self.connection.select("SELECT episode_id, showid FROM tv_episodes WHERE airdate >= ? OR airdate < 1", [datetime.date.max.toordinal()])

        for bad_airdate in sql_results:
            current_episode_id = bad_airdate["episode_id"]
            current_show_id = bad_airdate["showid"]
            logger.debug(_(f"Bad episode airdate detected! episode_id: {current_episode_id} showid: {current_show_id}"))
            logger.info(_(f"Fixing bad episode airdate for episode_id: {current_episode_id}"))
            self.connection.action("UPDATE tv_episodes SET airdate = '1' WHERE episode_id = ?", [current_episode_id])

    def fix_show_nfo_lang(self):
        self.connection.action("UPDATE tv_shows SET lang = '' WHERE lang = 0 or lang = '0'")


def backup_database(full_path, version):
    logger.info("Backing up database before upgrade")
    if not helpers.backupVersionedFile(full_path, "{0}.{1}".format(*version)):
        logger.log_error_and_exit("Database backup failed, abort upgrading database")
    else:
        logger.info("Proceeding with upgrade")


# ======================
# = Main DB Migrations =
# ======================
# Add new migrations at the bottom of the list; subclass the previous migration.


class InitialSchema(db.SchemaUpgrade):
    def test(self):
        return self.has_table("tv_shows") and self.has_table("db_version")

    def execute(self):
        self.connection.import_ddl()
