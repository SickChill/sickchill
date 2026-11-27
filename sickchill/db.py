import os.path
import re
import sqlite3
import threading
import time
import traceback
import warnings
from sqlite3 import OperationalError

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

                self.connection = sqlite3.connect(self.full_path, timeout=20, check_same_thread=False)
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
        except Exception as error:
            self._error_log_helper(error, logger.ERROR, locals(), None, "DBConnection.__init__")
            raise

    def _error_log_helper(self, exception, severity, local_variables, attempts, called_method):
        if attempts in (0, self.MAX_ATTEMPTS):  # Only log the first try and the final failure
            prefix = ("Database", "Fatal")[severity == logger.ERROR]
            # noinspection PyUnresolvedReferences
            logger.log(
                severity,
                _("{exception_severity} error executing query with {method} in database {db_location}: {exception}").format(
                    db_location=self.full_path, method=called_method, exception_severity=prefix, exception=exception
                ),
            )

            # Let's print out all the arguments, so we can debug this better
            logger.info(traceback.format_exc())
            logger.info(_("If this happened in cache.db, you can safely stop SickChill, and delete the cache.db file without losing any data"))
            logger.info(
                _("Here are the arguments that were passed to this function (This is what the developers need to know): {local_variables}").format(
                    local_variables=local_variables
                )
            )

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

    @staticmethod
    def _write_succeeded(result) -> bool:
        """True when a write executed.

        action() returns a cursor after a committed write. An empty list means
        the retry loop gave up, which is not a successful write. Selects are
        not checked here: an empty list is a real result for them.
        """
        return result is not None and not isinstance(result, list)

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
                except (sqlite3.OperationalError, sqlite3.DatabaseError) as error:
                    sql_results = []  # Reset results because of rollback
                    if self.connection:
                        self.connection.rollback()
                    severity = (logger.ERROR, logger.WARNING)[self._is_locked_or_denied(error) and attempt < self.MAX_ATTEMPTS]
                    self._error_log_helper(error, severity, locals(), attempt, "db.mass_action")
                    if severity == logger.ERROR:
                        raise
                    time.sleep(1)
                except Exception as error:
                    sql_results = []
                    if self.connection:
                        self.connection.rollback()
                    self._error_log_helper(error, logger.ERROR, locals(), attempt, "db.mass_action")
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
                except (sqlite3.OperationalError, sqlite3.DatabaseError) as error:
                    sql_results = []  # Reset results because of rollback
                    if self.connection:
                        self.connection.rollback()

                    severity = (logger.ERROR, logger.WARNING)[self._is_locked_or_denied(error) and attempt < self.MAX_ATTEMPTS]
                    self._error_log_helper(error, severity, locals(), attempt, "db.action")
                    if severity == logger.ERROR:
                        raise
                    time.sleep(1)
                except Exception as error:
                    sql_results = []
                    if self.connection:
                        self.connection.rollback()
                    self._error_log_helper(error, logger.ERROR, locals(), attempt, "db.action")
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

    @staticmethod
    def _assignment_clause(my_dict, separator):
        return separator.join(["{} = ?".format(x) for x in my_dict])

    def _upsert_statements(self, table_name, value_dict, key_dict):
        assert None not in list(key_dict.values()), _("Control dict to upsert cannot have values of None!")

        update = None
        if key_dict:
            # language=TEXT
            query = "UPDATE [{table}] SET {pairs} WHERE {control}".format(
                table=table_name,
                pairs=self._assignment_clause(value_dict, ", "),
                control=self._assignment_clause(key_dict, " AND "),
            )
            update = (query, list(value_dict.values()) + list(key_dict.values()))

        keys = list(value_dict) + list(key_dict)
        # language=TEXT
        insert_query = "INSERT INTO '{table}' ({columns}) VALUES ({replacements})".format(
            table=table_name,
            columns=", ".join(keys),
            replacements=", ".join(["?"] * len(keys)),
        )
        insert = (insert_query, list(value_dict.values()) + list(key_dict.values()))
        return update, insert

    @staticmethod
    def _cache_value(row, field):
        try:
            return row[field]
        except (KeyError, IndexError, TypeError):
            return None

    @classmethod
    def _release_rank(cls, row):
        """Timestamp of a cached release. An equal timestamp is still a later write."""

        def as_int(value):
            try:
                return int(value)
            except (TypeError, ValueError):
                return 0

        return as_int(cls._cache_value(row, "time"))

    @classmethod
    def _incoming_release_wins(cls, value_dict, execute):
        """True when this row should be written.

        A new download URL replaces stored copies when its timestamp is at least as new.
        An equal timestamp is a later write of that instant, so it wins even with fewer
        seeders. An older timestamp leaves the stored release alone. Rows without a
        release identity fall through to a normal upsert.
        """
        fields = ("provider", "name", "indexerid", "season", "episodes")
        if any(value_dict.get(field) is None for field in fields) or value_dict.get("url") is None:
            return True

        stored = execute(
            "SELECT time FROM results WHERE provider = ? AND name = ? AND indexerid = ? AND season = ? AND episodes = ?",
            [value_dict[field] for field in fields],
            fetchall=True,
        )
        incoming = cls._release_rank(value_dict)
        return all(incoming >= cls._release_rank(row) for row in stored or [])

    @staticmethod
    def _stale_release_delete(value_dict):
        """Drop older copies of one cached release so a new download URL replaces them.

        The results table is unique on url. A provider that rotates that URL, such as
        Jackett's encrypted ``path`` token, would otherwise insert another row.
        """
        fields = ("provider", "name", "indexerid", "season", "episodes", "url")
        if any(value_dict.get(field) is None for field in fields):
            return None
        return (
            "DELETE FROM results WHERE provider = ? AND name = ? AND indexerid = ? AND season = ? AND episodes = ? AND url != ?",
            [value_dict[field] for field in fields],
        )

    def _apply_upsert(self, table_name, value_dict, key_dict, execute):
        """Run UPDATE then INSERT. ``execute`` must not commit; the caller owns the transaction."""
        update, insert = self._upsert_statements(table_name, value_dict, key_dict)
        if update:
            updated = execute(update[0], update[1])
            if not self._write_succeeded(updated):
                logger.warning(_("Upsert failed for {table}").format(table=table_name))
                return False
            # rowcount is this statement only. total_changes includes every write on the shared connection.
            if updated.rowcount:
                return True

        inserted = execute(insert[0], insert[1])
        if not self._write_succeeded(inserted):
            logger.warning(_("Upsert failed for {table}").format(table=table_name))
            return False
        return True

    def mass_upsert(self, table_name, query_list, log_transaction=False, replace_same_release=False):
        # type: (str, List[tuple, list], bool, bool) -> bool
        """
        Update or insert every row in one transaction.

        :param table_name: name of table to upsert
        :param query_list: list of (value_dict, key_dict) pairs
        :param log_transaction: Boolean to log each statement at debug
        :param replace_same_release: For the results cache, delete other URLs of the same release first
        :return: True when every upsert wrote a row
        """
        if not query_list:
            return True

        log_level = (logger.DB, logger.DEBUG)[log_transaction]
        succeeded = True
        attempt = 0

        with db_locks[self.filename]:
            self._set_row_factory()
            while attempt <= self.MAX_ATTEMPTS:
                succeeded = True
                try:
                    for values, control in query_list:
                        logger.log(log_level, _("{filename}: {query} [{control}]").format(filename=self.filename, query=values, control=control))
                        if replace_same_release and not self._incoming_release_wins(values, self._execute):
                            continue
                        if replace_same_release:
                            stale = self._stale_release_delete(values)
                            if stale:
                                self._execute(stale[0], stale[1])
                        if not self._apply_upsert(table_name, values, control, self._execute):
                            succeeded = False
                    self.connection.commit()
                    logger.log(log_level, _("Transaction with {count:d} upserts executed successfully").format(count=len(query_list)))
                    break
                except (sqlite3.OperationalError, sqlite3.DatabaseError) as error:
                    succeeded = False
                    if self.connection:
                        self.connection.rollback()
                    severity = (logger.ERROR, logger.WARNING)[self._is_locked_or_denied(error) and attempt < self.MAX_ATTEMPTS]
                    self._error_log_helper(error, severity, locals(), attempt, "db.mass_upsert")
                    if severity == logger.ERROR:
                        raise
                    time.sleep(1)
                except Exception as error:
                    if self.connection:
                        self.connection.rollback()
                    self._error_log_helper(error, logger.ERROR, locals(), attempt, "db.mass_upsert")
                    raise

                attempt += 1

        return succeeded

    def upsert(self, table_name, value_dict, key_dict):
        """
        Update values, or if no updates done, insert values

        :param table_name: table to update/insert
        :param value_dict: values in table to update/insert
        :param key_dict:  columns in table to update/insert
        :return: True when this call's update changed a row or its insert executed.
            False when that write did not run. Fatal database errors still raise.
        """
        return self._apply_upsert(table_name, value_dict, key_dict, lambda query, args: self.action(query, args))

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

        :param table: Table to add column too
        :param column: Column name to add
        :param col_type: Column type to add
        :param default: Default value for column
        :return: True when the column was added and its default was written.
            False when either write did not run. Fatal database errors still raise.
        """

        # language=TEXT
        altered = self.action("ALTER TABLE [{0}] ADD {1} {2}".format(table, column, col_type))
        if not self._write_succeeded(altered):
            logger.warning(_("Failed to add column {column} to {table}").format(column=column, table=table))
            return False
        # language=TEXT
        updated = self.action("UPDATE [{0}] SET {1} = ?".format(table, column), (default,))
        if not self._write_succeeded(updated):
            logger.warning(_("Failed to set the default for {column} on {table}").format(column=column, table=table))
            return False
        return True


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


def _process_upgrade(connection, upgrade_class):
    instance = upgrade_class(connection)
    # logger.debug("Checking " + pretty_name(upgrade_class.__name__) + " database upgrade")
    if not instance.test():
        logger.debug("Database upgrade required: " + pretty_name(upgrade_class.__name__))
        try:
            instance.execute()
        except Exception as error:
            logger.exception(f"Error in {upgrade_class.__name__}: {error}")
            raise

        logger.debug(f"{upgrade_class.__name__} upgrade completed")
    # else:
    #     logger.debug(f"{upgrade_class.__name__} upgrade not required")

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
        return self.connection.add_column(table=table, column=column, col_type=col_type, default=default)

    def get_db_version(self):
        return self.connection.get_db_version()

    def _require_version_write(self, result, statement):
        if not self.connection._write_succeeded(result):
            raise sqlite3.OperationalError(f"Failed to update db_version: {statement}")

    def increment_db_version(self):
        new_version = self.get_db_version() + 1
        statement = "UPDATE db_version SET db_version = ?"
        self._require_version_write(self.connection.action(statement, [new_version]), statement)
        return new_version

    def inc_major_version(self):
        major_version, minor_version = self.connection.version
        major_version += 1
        minor_version = 0
        statement = "UPDATE db_version SET db_version = ?, db_minor_version = ?"
        self._require_version_write(self.connection.action(statement, [major_version, minor_version]), statement)
        return self.connection.version

    def inc_minor_version(self):
        major_version, minor_version = self.connection.version
        minor_version += 1
        statement = "UPDATE db_version SET db_version = ?, db_minor_version = ?"
        self._require_version_write(self.connection.action(statement, [major_version, minor_version]), statement)
        return self.connection.version
