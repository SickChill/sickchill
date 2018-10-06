# coding=utf-8

# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sick-rage.github.io
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

from sickbeard import db


# Add new migrations at the bottom of the list; subclass the previous migration.
class InitialSchema(db.SchemaUpgrade):
    def test(self):
        return self.has_table("db_version")

    def execute(self):
        queries = [
            ("CREATE TABLE lastUpdate (provider TEXT, time NUMERIC);",),
            ("CREATE TABLE lastSearch (provider TEXT, time NUMERIC);",),
            ("CREATE TABLE scene_exceptions (exception_id INTEGER PRIMARY KEY, indexer_id INTEGER, show_name TEXT, season NUMERIC DEFAULT -1, custom NUMERIC DEFAULT 0);",),
            ("CREATE TABLE scene_names (indexer_id INTEGER, name TEXT);",),
            ("CREATE TABLE network_timezones (network_name TEXT PRIMARY KEY, timezone TEXT);",),
            ("CREATE TABLE scene_exceptions_refresh (list TEXT PRIMARY KEY, last_refreshed INTEGER);",),
            ("CREATE TABLE db_version (db_version INTEGER);",),
            ("INSERT INTO db_version(db_version) VALUES (1);",),
        ]
        for query in queries:
            if len(query) == 1:
                self.connection.action(query[0])
            else:
                self.connection.action(query[0], query[1:])


class AddSceneExceptions(InitialSchema):
    def test(self):
        return self.has_table("scene_exceptions")

    def execute(self):
        self.connection.action(
            "CREATE TABLE scene_exceptions (exception_id INTEGER PRIMARY KEY, indexer_id INTEGER, show_name TEXT);")


class AddSceneNameCache(AddSceneExceptions):
    def test(self):
        return self.has_table("scene_names")

    def execute(self):
        self.connection.action("CREATE TABLE scene_names (indexer_id INTEGER, name TEXT);")


class AddNetworkTimezones(AddSceneNameCache):
    def test(self):
        return self.has_table("network_timezones")

    def execute(self):
        self.connection.action("CREATE TABLE network_timezones (network_name TEXT PRIMARY KEY, timezone TEXT);")


class AddLastSearch(AddNetworkTimezones):
    def test(self):
        return self.has_table("lastSearch")

    def execute(self):
        self.connection.action("CREATE TABLE lastSearch (provider TEXT, time NUMERIC);")


class AddSceneExceptionsSeasons(AddLastSearch):
    def test(self):
        return self.has_column("scene_exceptions", "season")

    def execute(self):
        self.add_column("scene_exceptions", "season", "NUMERIC", -1)


class AddSceneExceptionsCustom(AddSceneExceptionsSeasons):  # pylint:disable=too-many-ancestors
    def test(self):
        return self.has_column("scene_exceptions", "custom")

    def execute(self):
        self.add_column("scene_exceptions", "custom", "NUMERIC", 0)


class AddSceneExceptionsRefresh(AddSceneExceptionsCustom):  # pylint:disable=too-many-ancestors
    def test(self):
        return self.has_table("scene_exceptions_refresh")

    def execute(self):
        self.connection.action(
            "CREATE TABLE scene_exceptions_refresh (list TEXT PRIMARY KEY, last_refreshed INTEGER);")


class ConvertSceneExeptionsToIndexerScheme(AddSceneExceptionsRefresh):  # pylint:disable=too-many-ancestors
    def test(self):
        return self.has_column("scene_exceptions", "indexer_id")

    def execute(self):
        self.connection.action("DROP TABLE IF EXISTS tmp_scene_exceptions;")
        self.connection.action("ALTER TABLE scene_exceptions RENAME TO tmp_scene_exceptions;")
        self.connection.action("CREATE TABLE scene_exceptions (exception_id INTEGER PRIMARY KEY, indexer_id INTEGER, show_name TEXT, season NUMERIC DEFAULT -1, custom NUMERIC DEFAULT 0);")
        self.connection.action("INSERT INTO scene_exceptions SELECT exception_id, tvdb_id as indexer_id, show_name, season, custom FROM tmp_scene_exceptions;")
        self.connection.action("DROP TABLE tmp_scene_exceptions;")


class ConvertSceneNamesToIndexerScheme(AddSceneExceptionsRefresh):  # pylint:disable=too-many-ancestors
    def test(self):
        return self.has_column("scene_names", "indexer_id")

    def execute(self):
        self.connection.action("DROP TABLE IF EXISTS tmp_scene_names;")
        self.connection.action("ALTER TABLE scene_names RENAME TO tmp_scene_names;")
        self.connection.action("CREATE TABLE scene_names (indexer_id INTEGER, name TEXT);")
        self.connection.action("INSERT INTO scene_names SELECT * FROM tmp_scene_names;")
        self.connection.action("DROP TABLE tmp_scene_names;")
