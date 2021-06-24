from sickchill import logger, settings
from sickchill.adba.aniDBerrors import AniDBCommandTimeoutError

from . import db, helpers


class BlackAndWhiteList(object):
    blacklist = []
    whitelist = []

    def __init__(self, show_id):
        if not show_id:
            raise BlackWhitelistNoShowIDException()
        self.show_id = show_id
        self.load()

    def load(self):
        """
        Builds black and whitelist
        """
        logger.debug("Building black and white list for {id}".format(id=self.show_id))
        self.blacklist = self._load_list("blacklist")
        self.whitelist = self._load_list("whitelist")

    def _add_keywords(self, table, values):
        """
        DB: Adds keywords into database for current show

        :param table: SQL table to add keywords to
        :param values: Values to be inserted in table
        """
        main_db_con = db.DBConnection()
        for value in values:
            main_db_con.action("INSERT INTO [" + table + "] (show_id, keyword) VALUES (?,?)", [self.show_id, value])

    def set_black_keywords(self, values):
        """
        Sets blacklist to new value

        :param values: Complete list of keywords to be set as blacklist
        """
        self._del_all_keywords("blacklist")
        self._add_keywords("blacklist", values)
        self.blacklist = values
        logger.debug("Blacklist set to: {blacklist}".format(blacklist=self.blacklist))

    def set_white_keywords(self, values):
        """
        Sets whitelist to new value

        :param values: Complete list of keywords to be set as whitelist
        """
        self._del_all_keywords("whitelist")
        self._add_keywords("whitelist", values)
        self.whitelist = values
        logger.debug("Whitelist set to: {whitelist}".format(whitelist=self.whitelist))

    def _del_all_keywords(self, table):
        """
        DB: Remove all keywords for current show

        :param table: SQL table remove keywords from
        """
        main_db_con = db.DBConnection()
        main_db_con.action("DELETE FROM [" + table + "] WHERE show_id = ?", [self.show_id])

    def _load_list(self, table):
        """
        DB: Fetch keywords for current show

        :param table: Table to fetch list of keywords from

        :return: keywords in list
        """
        main_db_con = db.DBConnection()
        sql_results = main_db_con.select("SELECT keyword FROM [" + table + "] WHERE show_id = ?", [self.show_id])
        if not sql_results or not len(sql_results):
            return []
        groups = []
        for result in sql_results:
            groups.append(result["keyword"])

        logger.debug("BWL: {id} loaded keywords from {table}: {groups}".format(id=self.show_id, table=table, groups=groups))

        return groups

    def is_valid(self, result):
        """
        Check if result is valid according to white/blacklist for current show

        :param result: Result to analyse
        :return: False if result is not allowed in white/blacklist, True if it is
        """

        if self.whitelist or self.blacklist:
            if not result.release_group:
                logger.debug("Failed to detect release group, invalid result")
                return False

            if result.release_group.lower() in [x.lower() for x in self.whitelist]:
                white_result = True
            elif not self.whitelist:
                white_result = True
            else:
                white_result = False

            if result.release_group.lower() in [x.lower() for x in self.blacklist]:
                black_result = False
            else:
                black_result = True

            logger.debug("Whitelist check passed: {white}. Blacklist check passed: {black}".format(white=white_result, black=black_result))

            if white_result and black_result:
                return True
            else:
                return False
        else:
            logger.debug("No Whitelist and Blacklist defined, check passed.")
            return True


class BlackWhitelistNoShowIDException(Exception):
    """No show_id was given"""


def short_group_names(groups):
    """
    Find AniDB short group names for release groups

    :param groups: list of groups to find short group names for
    :return: list of shortened group names
    """
    groups = groups.split(",")
    short_group_list = []
    if helpers.set_up_anidb_connection():
        for groupName in groups:
            try:
                group = settings.ADBA_CONNECTION.group(gname=groupName)
            except AniDBCommandTimeoutError:
                logger.debug("Timeout while loading group from AniDB. Trying next group")
            except Exception:
                logger.debug("Failed while loading group from AniDB. Trying next group")
            else:
                for line in group.datalines:
                    if line["shortname"]:
                        short_group_list.append(line["shortname"])
                    else:
                        if groupName not in short_group_list:
                            short_group_list.append(groupName)
    else:
        short_group_list = groups
    return short_group_list
