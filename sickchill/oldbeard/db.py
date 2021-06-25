import os.path
import re
import sqlite3
import threading
import time
import traceback
import warnings
from sqlite3 import OperationalError
from typing import List

import sickchill.oldbeard.helpers
from sickchill import logger, settings

db_cons = {}
db_locks = {}


def db_full_path(filename="sickchill.db", suffix=None):
    """
    @param filename: The sqlite database filename to use. If not specified,
                     will be made to be sickchill.db
    @param suffix: The suffix to append to the filename. A "." will be added
                   automatically, i.e. suffix="v0" will make filename.db.v0
    @return: the correct location of the database file.
    """
    if suffix:
        filename = "{0}.{1}".format(filename, suffix)
    return os.path.join(settings.DATA_DIR, filename)


class DBConnection(object):
    MAX_ATTEMPTS = 5

    def __init__(self, filename="sickchill.db", suffix=None, row_type=None):

        self.filename = filename
        self.suffix = suffix
        self.row_type = row_type
        self.full_path = db_full_path(self.filename, self.suffix)

        if filename == "sickchill.db" and not os.path.isfile(self.full_path):
            sickbeard_db = db_full_path("sickbeard.db", suffix)
            if os.path.isfile(sickbeard_db):
                os.rename(sickbeard_db, self.full_path)

        try:
            if self.filename not in db_cons or not db_cons[self.filename]:
                db_locks[self.filename] = threading.Lock()

                self.connection = sqlite3.connect(self.full_path, 20, check_same_thread=False)
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
            logger.warning(_("Please check your database owner/permissions: {db_filename}").format(db_filename=self.full_path))
        except Exception as e:
            self._error_log_helper(e, logger.ERROR, locals(), None, "DBConnection.__init__")
            raise

    def _error_log_helper(self, exception, severity, local_variables, attempts, called_method):
        if attempts in (0, self.MAX_ATTEMPTS):  # Only log the first try and the final failure
            prefix = ("Database", "Fatal")[severity == logger.ERROR]
            # noinspection PyUnresolvedReferences
            logger.log(
                severity,
                _("{exception_severity} error executing query with {method} in database {db_location}: ").format(
                    db_location=self.full_path, method=called_method, exception_severity=prefix
                )
                + str(exception),
            )

            # Lets print out all of the arguments so we can debug this better
            logger.info(traceback.format_exc())
            logger.info(_("If this happened in cache.db, you can safely stop SickChill, and delete the cache.db file without losing any data"))
            logger.info(_(f"Here are the arguments that were passed to this function (This is what the developers need to know): {local_variables}"))

    @staticmethod
    def _is_locked_or_denied(exception):
        # noinspection PyUnresolvedReferences
        return (
            _("unable to open database file") in exception.args[0]
            or _("database is locked") in exception.args[0]
            or "unable to open database file" in exception.args[0]
            or "database is locked" in exception.args[0]
        )

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
            print("ERROR GETTING MINOR!")
            return 0

    @property
    def version(self):
        """The database version

        :return: A tuple containing the major and minor versions
        """
        # return tuple(self.select_one("SELECT * FROM db_version"))
        return self.get_db_major_version(), self.get_db_minor_version()

    def mass_action(self, query_list=None, log_transaction=False, fetchall=False):
        # type: (list, bool, bool) -> List[sqlite3.Row]
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
                            logger.log(log_level, _("{filename}: {query}").format(filename=self.filename, query=qu[0]))
                            sql_results.append(self._execute(qu[0], fetchall=fetchall))
                        elif len(qu) > 1:
                            # noinspection PyUnresolvedReferences
                            logger.log(log_level, _("{filename}: {query} with args {args}").format(filename=self.filename, query=qu[0], args=qu[1]))
                            sql_results.append(self._execute(qu[0], qu[1], fetchall=fetchall))
                    self.connection.commit()
                    # noinspection PyUnresolvedReferences
                    logger.log(log_level, _("Transaction with {count:d} of queries executed successfully").format(count=len(query_list)))

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
                    if settings.DBDEBUG:
                        if args is None:
                            logger.log(logger.DB, self.filename + ": " + query)
                        else:
                            logger.log(logger.DB, "{filename}: {query} with args {args}".format(filename=self.filename, query=query, args=args))

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

    def mass_upsert(self, table_name, query_list, log_transaction=False):
        # type: (str, List[tuple, list], bool) -> None
        """
        Execute multiple queries

        :param table_name: name of table to upsert
        :param query_list: list of queries
        :param log_transaction: Boolean to wrap all in one transaction
        :return: None
        """
        log_level = (logger.DB, logger.DEBUG)[log_transaction]
        for values, control in query_list:
            logger.log(log_level, _("{filename}: {query} [{control}]").format(filename=self.filename, query=values, control=control))
            self.upsert(table_name, values, control)

    def upsert(self, table_name, value_dict, key_dict):
        """
        Update values, or if no updates done, insert values
        TODO: Make this return true/false on success/error

        :param table_name: table to update/insert
        :param value_dict: values in table to update/insert
        :param key_dict:  columns in table to update/insert
        """

        changesBefore = self.connection.total_changes

        assert None not in list(key_dict.values()), _("Control dict to upsert cannot have values of None!")
        if key_dict:

            def make_string(my_dict, separator):
                return separator.join(["{} = ?".format(x) for x in my_dict])

            # language=TEXT
            query = "UPDATE [{table}] SET {pairs} WHERE {control}".format(
                table=table_name, pairs=make_string(value_dict, ", "), control=make_string(key_dict, " AND ")
            )

            self.action(query, list(value_dict.values()) + list(key_dict.values()))

        if self.connection.total_changes == changesBefore:
            keys = list(value_dict) + list(key_dict)
            count = len(keys)
            columns = ", ".join(keys)
            replacements = ", ".join(["?"] * count)
            values = list(value_dict.values()) + list(key_dict.values())

            # language=TEXT
            query = "INSERT INTO '{table}' ({columns}) VALUES ({replacements})".format(table=table_name, columns=columns, replacements=replacements)

            self.action(query, values)

    def table_info(self, table_name):
        """
        Return information on a database table

        :param table_name: name of table
        :return: array of name/type info
        """
        return {column["name"]: {"type": column["type"]} for column in self.select("PRAGMA table_info(`{0}`)".format(table_name))}

    @staticmethod
    def _dict_factory(cursor, row):
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    def has_table(self, table_name):
        """
        Check if a table exists in database

        :param table_name: table name to check
        :return: True if table exists, False if it does not
        """
        return len(self.select("SELECT 1 FROM sqlite_master WHERE name = ?;", (table_name,))) > 0

    def has_column(self, table_name, column):
        """
        Check if a table has a column

        :param table_name: Table to check
        :param column: Column to check for
        :return: True if column exists, False if it does not
        """
        return column in self.table_info(table_name)

    def has_index(self, index_name):
        """
        Check if a table has an index

        :param index_name: Index to check
        :return: True if column exists, False if it does not
        """
        return len(self.select('SELECT 1 FROM sqlite_master WHERE type = "index" AND name = ?', [index_name])) > 0

    def add_column(self, table, column, col_type="NUMERIC", default=0):
        """
        Adds a column to a table, default column type is NUMERIC
        TODO: Make this return true/false on success/failure

        :param table: Table to add column too
        :param column: Column name to add
        :param col_type: Column type to add
        :param default: Default value for column
        """

        # language=TEXT
        self.action("ALTER TABLE [{0}] ADD {1} {2}".format(table, column, col_type))
        # language=TEXT
        self.action("UPDATE [{0}] SET {1} = ?".format(table, column), (default,))


def sanity_check_database(connection, sanity_check):
    sanity_check(connection).check()


class DBSanityCheck(object):
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
    logger.debug("Checking database structure..." + connection.filename)
    _process_upgrade(connection, schema)


def pretty_name(class_name):
    return " ".join([x.group() for x in re.finditer("([A-Z])([a-z0-9]+)", class_name)])


def restore_database(version):
    """
    Restores a database to a previous version (backup file of version must still exist)

    :param version: Version to restore to
    :return: True if restore succeeds, False if it fails
    """
    logger.info("Restoring database before trying upgrade again")
    if not sickchill.oldbeard.helpers.restoreVersionedFile(db_full_path(suffix="v" + str(version)), version):
        logger.log_error_and_exit("Database restore failed, abort upgrading database")
        return False
    else:
        return True


def _process_upgrade(connection, upgrade_class):
    instance = upgrade_class(connection)
    # logger.debug("Checking " + pretty_name(upgrade_class.__name__) + " database upgrade")
    if not instance.test():
        logger.debug("Database upgrade required: " + pretty_name(upgrade_class.__name__))
        try:
            instance.execute()
        except Exception as e:
            logger.exception("Error in " + str(upgrade_class.__name__) + ": " + str(e))
            raise

        logger.debug(upgrade_class.__name__ + " upgrade completed")
    # else:
    #     logger.debug(upgrade_class.__name__ + " upgrade not required")

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

    def has_index(self, index_name):
        return self.connection.has_index(index_name=index_name)

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
