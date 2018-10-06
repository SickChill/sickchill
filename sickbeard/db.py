# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sick-rage.github.io
# Git: https://github.com/Sick-Rage/Sick-Rage.git
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

from __future__ import print_function, unicode_literals

import os.path
import re
import sqlite3
import threading
import time
import warnings
from sqlite3 import OperationalError

import six

import sickbeard
from sickbeard import logger
from sickrage.helper.encoding import ek
from sickrage.helper.exceptions import ex

db_cons = {}
db_locks = {}


def db_full_path(filename="sickbeard.db", suffix=None):
    """
    @param filename: The sqlite database filename to use. If not specified,
                     will be made to be sickbeard.db
    @param suffix: The suffix to append to the filename. A "." will be added
                   automatically, i.e. suffix="v0" will make filename.db.v0
    @return: the correct location of the database file.
    """
    if suffix:
        filename = "{0}.{1}".format(filename, suffix)
    return ek(os.path.join, sickbeard.DATA_DIR, filename)


class DBConnection(object):
    MAX_ATTEMPTS = 5

    def __init__(self, filename="sickbeard.db", suffix=None, row_type=None):

        self.filename = filename
        self.suffix = suffix
        self.row_type = row_type
        self.full_path = db_full_path(self.filename, self.suffix)
        try:
            if self.filename not in db_cons or not db_cons[self.filename]:
                db_locks[self.filename] = threading.Lock()

                self.connection = sqlite3.connect(self.full_path, 20, check_same_thread=False)
                self.connection.text_factory = DBConnection._unicode_text_factory

                db_cons[self.filename] = self.connection
            else:
                self.connection = db_cons[self.filename]

            # start off row factory configured as before out of
            # paranoia but wait to do so until other potential users
            # of the shared connection are done using
            # it... technically not required as row factory is reset
            # in all the public methods after the lock has been
            # acquired
            with db_locks[self.filename]:
                self._set_row_factory()

        except OperationalError:
            # noinspection PyUnresolvedReferences
            logger.log(_("Please check your database owner/permissions: {db_filename}").format(db_filename=self.full_path), logger.WARNING)
        except Exception as e:
            self._error_log_helper(e, logger.ERROR, locals(), None, 'DBConnection.__init__')
            raise

    def _error_log_helper(self, exception, severity, local_variables, attempts, called_method):
        if attempts in (0, self.MAX_ATTEMPTS):  # Only log the first try and the final failure
            prefix = ("Database", "Fatal")[severity == logger.ERROR]
            # noinspection PyUnresolvedReferences
            logger.log(
                _("{exception_severity} error executing query with {method} in database {db_location}: ").format(
                    db_location=self.full_path, method=called_method, exception_severity=prefix
                ) + ex(exception), severity
            )

            # Lets print out all of the arguments so we can debug this better
            # noinspection PyUnresolvedReferences
            logger.log(_("If this happened in cache.db, you can safely stop SickRage, and delete the cache.db file without losing any data"))
            # noinspection PyUnresolvedReferences
            logger.log(
                _("Here is the arguments that were passed to this function (This is what the developers need to know): {local_variables!s}").format(
                    local_variables=local_variables
                )
            )

    @staticmethod
    def _is_locked_or_denied(exception):
        # noinspection PyUnresolvedReferences
        return _("unable to open database file") in exception.args[0] or _("database is locked") in exception.args[0] or \
                "unable to open database file" in exception.args[0] or "database is locked" in exception.args[0]

    def _set_row_factory(self):
        """
        once lock is acquired we can configure the connection for
        this particular instance of DBConnection
        """
        if self.row_type == "dict":
            self.connection.row_factory = DBConnection._dict_factory
        else:
            self.connection.row_factory = sqlite3.Row

    def _execute(self, query, args=None, fetchall=False, fetchone=False):
        """
        Executes DB query

        :param query: Query to execute
        :param args: Arguments in query
        :param fetchall: Boolean to indicate all results must be fetched
        :param fetchone: Boolean to indicate one result must be fetched (to walk results for instance)
        :return: query results
        """
        try:
            if not args:
                sql_results = self.connection.cursor().execute(query)
            else:
                sql_results = self.connection.cursor().execute(query, args)
            if fetchall:
                return sql_results.fetchall()
            elif fetchone:
                return sql_results.fetchone()
            else:
                return sql_results
        except Exception:
            raise

    def get_db_version(self):
        """
        Fetch major database version

        :return: Integer indicating current DB major version
        """
        if self.has_column("db_version", "db_minor_version"):
            warnings.warn("Deprecated: Use the version property", DeprecationWarning)
        return self.get_db_major_version()

    def get_db_major_version(self):
        """
        Fetch database version

        :return: Integer indicating current DB version
        """
        # noinspection PyBroadException
        try:
            result = int(self.select_one("SELECT db_version FROM db_version")[0])
            return result
        except Exception:
            return 0

    def get_db_minor_version(self):
        """
        Fetch database version

        :return: Integer indicating current DB major version
        """
        # noinspection PyBroadException
        try:
            result = int(self.select_one("SELECT db_minor_version FROM db_version")[0])
            return result
        except Exception:
            print('ERROR GETTING MINOR!')
            return 0

    @property
    def version(self):
        """The database version

        :return: A tuple containing the major and minor versions
        """
        # return tuple(self.select_one("SELECT * FROM db_version"))
        return self.get_db_major_version(), self.get_db_minor_version()

    def mass_action(self, query_list=None, log_transaction=False, fetchall=False):
        """
        Execute multiple queries

        :param query_list: list of queries
        :param log_transaction: Boolean to wrap all in one transaction
        :param fetchall: Boolean, when using a select query force returning all results
        :return: list of results
        """

        # noinspection PyUnresolvedReferences
        assert hasattr(query_list, "__iter__"), _("You passed a non-iterable to mass_action: {0!r}").format(query_list)

        # remove None types
        query_list = [i for i in query_list if i]

        sql_results = []
        attempt = 0

        with db_locks[self.filename]:
            self._set_row_factory()
            while attempt <= self.MAX_ATTEMPTS:
                try:
                    log_level = (logger.DB, logger.DEBUG)[log_transaction]
                    for qu in query_list:
                        if len(qu) == 1:
                            # noinspection PyUnresolvedReferences
                            logger.log(_("{filename}: {query}").format(filename=self.filename, query=qu[0]), log_level)
                            sql_results.append(self._execute(qu[0], fetchall=fetchall))
                        elif len(qu) > 1:
                            # noinspection PyUnresolvedReferences
                            logger.log(_("{filename}: {query} with args {args!s}").format(filename=self.filename, query=qu[0], args=qu[1]), log_level)
                            sql_results.append(self._execute(qu[0], qu[1], fetchall=fetchall))
                    self.connection.commit()
                    # noinspection PyUnresolvedReferences
                    logger.log(_("Transaction with {count!s} of queries executed successfully").format(count=len(query_list)), log_level)

                    # finished
                    break
                except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                    sql_results = []  # Reset results because of rollback
                    if self.connection:
                        self.connection.rollback()
                    severity = (logger.ERROR, logger.WARNING)[self._is_locked_or_denied(e) and attempt < self.MAX_ATTEMPTS]
                    self._error_log_helper(e, severity, locals(), attempt, "db.mass_action")
                    if severity == logger.ERROR:
                        raise
                    time.sleep(1)
                except Exception as e:
                    sql_results = []
                    if self.connection:
                        self.connection.rollback()
                    self._error_log_helper(e, logger.ERROR, locals(), attempt, "db.mass_action")
                    raise

                attempt += 1
            return sql_results

    def action(self, query, args=None, fetchall=False, fetchone=False):
        """
        Execute single query

        :param query: Query string
        :param args: Arguments to query string
        :param fetchall: Boolean to indicate all results must be fetched
        :param fetchone: Boolean to indicate one result must be fetched (to walk results for instance)
        :return: query results
        """
        if query is None:
            return

        # noinspection PyUnresolvedReferences
        assert not (fetchall and fetchone), _("Cannot fetch all and only one at the same time!")

        sql_results = []
        attempt = 0

        with db_locks[self.filename]:
            self._set_row_factory()
            while attempt < self.MAX_ATTEMPTS:
                try:
                    if args is None:
                        logger.log(self.filename + ": " + query, logger.DB)
                    else:
                        logger.log("{filename}: {query} with args {args!s}".format(filename=self.filename, query=query, args=args), logger.DB)

                    sql_results = self._execute(query, args, fetchall=fetchall, fetchone=fetchone)
                    self.connection.commit()

                    # get out of the connection attempt loop since we were successful
                    break
                except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                    sql_results = []  # Reset results because of rollback
                    if self.connection:
                        self.connection.rollback()

                    severity = (logger.ERROR, logger.WARNING)[self._is_locked_or_denied(e) and attempt < self.MAX_ATTEMPTS]
                    self._error_log_helper(e, severity, locals(), attempt, "db.action")
                    if severity == logger.ERROR:
                        raise
                    time.sleep(1)
                except Exception as e:
                    sql_results = []
                    if self.connection:
                        self.connection.rollback()
                    self._error_log_helper(e, logger.ERROR, locals(), attempt, "db.action")
                    raise

                attempt += 1

            return sql_results

    def select(self, query, args=None):
        """
        Perform single select query on database

        :param query: query string
        :param args:  arguments to query string
        :return: query results
        """

        sql_results = self.action(query, args, fetchall=True)

        if sql_results is None:
            return []

        return sql_results

    def select_one(self, query, args=None):
        """
        Perform single select query on database, returning one result

        :param query: query string
        :param args: arguments to query string
        :return: query results
        """
        sql_results = self.action(query, args, fetchone=True)

        if sql_results is None:
            return []

        return sql_results

    def upsert(self, table_name, value_dict, key_dict):
        """
        Update values, or if no updates done, insert values
        TODO: Make this return true/false on success/error

        :param table_name: table to update/insert
        :param value_dict: values in table to update/insert
        :param key_dict:  columns in table to update/insert
        """

        changesBefore = self.connection.total_changes

        # noinspection PyUnresolvedReferences
        assert None not in key_dict.values(), _("Control dict to upsert cannot have values of None!")
        if key_dict:
            def make_string(my_dict, separator):
                return separator.join([x + " = ?" for x in my_dict.keys()])

            query = "UPDATE [{table}] SET {pairs} WHERE {control}".format(
                table=table_name, pairs=make_string(value_dict, ", "), control=make_string(key_dict, " AND ")
            )

            self.action(query, value_dict.values() + key_dict.values())

        if self.connection.total_changes == changesBefore:
            keys = value_dict.keys() + key_dict.keys()
            count = len(keys)
            columns = ", ".join(keys)
            replacements = ", ".join(["?"] * count)
            values = value_dict.values() + key_dict.values()

            query = "INSERT INTO '{table}' ({columns}) VALUES ({replacements})".format(table=table_name, columns=columns, replacements=replacements)

            self.action(query, values)

    def table_info(self, table_name):
        """
        Return information on a database table

        :param table_name: name of table
        :return: array of name/type info
        """
        return {column[b"name"]: {"type": column[b"type"]} for column in self.select("PRAGMA table_info(`{0}`)".format(table_name))}

    @staticmethod
    def _unicode_text_factory(x):
        """
        Convert text to six.text_type

        :param x: text to parse
        :return: six.text_type result
        """
        # noinspection PyBroadException
        try:
            # Just revert to the old code for now, until we can fix unicode
            return six.text_type(x, "utf-8")
        except Exception:
            return six.text_type(x, sickbeard.SYS_ENCODING, errors="ignore")

    @staticmethod
    def _dict_factory(cursor, row):
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    def has_table(self, table_name):
        """
        Check if a table exists in database

        :param table_name: table name to check
        :return: True if table exists, False if it does not
        """
        return len(self.select("SELECT 1 FROM sqlite_master WHERE name = ?;", (table_name, ))) > 0

    def has_column(self, table_name, column):
        """
        Check if a table has a column

        :param table_name: Table to check
        :param column: Column to check for
        :return: True if column exists, False if it does not
        """
        return column in self.table_info(table_name)

    def add_column(self, table, column, col_type="NUMERIC", default=0):
        """
        Adds a column to a table, default column type is NUMERIC
        TODO: Make this return true/false on success/failure

        :param table: Table to add column too
        :param column: Column name to add
        :param col_type: Column type to add
        :param default: Default value for column
        """
        self.action("ALTER TABLE [{0}] ADD {1} {2}".format(table, column, col_type))
        self.action("UPDATE [{0}] SET {1} = ?".format(table, column), (default,))


def sanity_check_database(connection, sanity_check):
    sanity_check(connection).check()


class DBSanityCheck(object):  # pylint: disable=too-few-public-methods
    def __init__(self, connection):
        self.connection = connection

    def check(self):
        pass


# ===============
# = Upgrade API =
# ===============

def upgrade_database(connection, schema):
    """
    Perform database upgrade and provide logging

    :param connection: Existing DB Connection to use
    :param schema: New schema to upgrade to
    """
    logger.log("Checking database structure..." + connection.filename, logger.DEBUG)
    _process_upgrade(connection, schema)


def pretty_name(class_name):
    return " ".join([x.group() for x in re.finditer("([A-Z])([a-z0-9]+)", class_name)])


def restore_database(version):
    """
    Restores a database to a previous version (backup file of version must still exist)

    :param version: Version to restore to
    :return: True if restore succeeds, False if it fails
    """
    logger.log("Restoring database before trying upgrade again")
    if not sickbeard.helpers.restoreVersionedFile(db_full_path(suffix="v" + str(version)), version):
        logger.log_error_and_exit("Database restore failed, abort upgrading database")
        return False
    else:
        return True


def _process_upgrade(connection, upgrade_class):
    instance = upgrade_class(connection)
    # logger.log("Checking " + pretty_name(upgrade_class.__name__) + " database upgrade", logger.DEBUG)
    if not instance.test():
        logger.log("Database upgrade required: " + pretty_name(upgrade_class.__name__), logger.DEBUG)
        try:
            instance.execute()
        except Exception as e:
            logger.log("Error in " + str(upgrade_class.__name__) + ": " + ex(e), logger.ERROR)
            raise

        logger.log(upgrade_class.__name__ + " upgrade completed", logger.DEBUG)
    # else:
    #     logger.log(upgrade_class.__name__ + " upgrade not required", logger.DEBUG)

    for upgradeSubClass in upgrade_class.__subclasses__():
        _process_upgrade(connection, upgradeSubClass)


# Base migration class. All future DB changes should be subclassed from this class
class SchemaUpgrade(object):
    def __init__(self, connection):
        self.connection = connection

    def has_table(self, table_name):
        return self.connection.has_table(table_name=table_name)

    def has_column(self, table_name, column):
        return self.connection.has_column(table_name=table_name, column=column)

    def add_column(self, table, column, col_type="NUMERIC", default=0):
        self.connection.add_column(table=table, column=column, col_type=col_type, default=default)

    def get_db_version(self):
        return self.connection.get_db_version()

    def increment_db_version(self):
        new_version = self.get_db_version() + 1
        self.connection.action("UPDATE db_version SET db_version = ?", [new_version])
        return new_version

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
