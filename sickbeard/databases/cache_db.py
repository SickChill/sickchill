# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of Sick Beard.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

from sickbeard import db

# Add new migrations at the bottom of the list; subclass the previous migration.
class InitialSchema(db.SchemaUpgrade):
    def test(self):
        return self.hasTable("lastUpdate")

    def execute(self):

        queries = [
            ("CREATE TABLE lastUpdate (provider TEXT, time NUMERIC);",),
            ("CREATE TABLE db_version (db_version INTEGER);",),
            ("INSERT INTO db_version (db_version) VALUES (?)", 1),
        ]
        for query in queries:
            if len(query) == 1:
                self.connection.action(query[0])
            else:
                self.connection.action(query[0], query[1:])


class AddSceneExceptions(InitialSchema):
    def test(self):
        return self.hasTable("scene_exceptions")

    def execute(self):
        self.connection.action(
            "CREATE TABLE scene_exceptions (exception_id INTEGER PRIMARY KEY, tvdb_id INTEGER KEY, show_name TEXT)")


class AddSceneNameCache(AddSceneExceptions):
    def test(self):
        return self.hasTable("scene_names")

    def execute(self):
        self.connection.action("CREATE TABLE scene_names (tvdb_id INTEGER, name TEXT)")


class AddNetworkTimezones(AddSceneNameCache):
    def test(self):
        return self.hasTable("network_timezones")

    def execute(self):
        self.connection.action("CREATE TABLE network_timezones (network_name TEXT PRIMARY KEY, timezone TEXT)")


class AddXemNumbering(AddNetworkTimezones):
    def test(self):
        return self.hasTable("xem_numbering")

    def execute(self):
        self.connection.action(
            "CREATE TABLE xem_numbering (indexer TEXT, indexer_id INTEGER, season INTEGER, episode INTEGER, scene_season INTEGER, scene_episode INTEGER)")
class AddXemRefresh(AddXemNumbering):
    def test(self):
        return self.hasTable("xem_refresh")

    def execute(self):
        self.connection.action(
            "CREATE TABLE xem_refresh (indexer TEXT, indexer_id INTEGER PRIMARY KEY, last_refreshed INTEGER)")

class ConvertSceneExceptionsToIndexerID(AddXemRefresh):
    def test(self):
        return self.hasColumn("scene_exceptions", "indexer_id")

    def execute(self):
        if self.hasTable("tmp_scene_exceptions"):
            self.connection.action("DROP TABLE tmp_scene_exceptions")

        self.connection.action("ALTER TABLE scene_exceptions RENAME TO tmp_scene_exceptions")
        self.connection.action(
            "CREATE TABLE scene_exceptions (exception_id INTEGER PRIMARY KEY, indexer_id INTEGER KEY, show_name TEXT)")
        self.connection.action(
            "INSERT INTO scene_exceptions(exception_id, indexer_id, show_name) SELECT exception_id, tvdb_id, show_name FROM tmp_scene_exceptions")
        self.connection.action("DROP TABLE tmp_scene_exceptions")


class ConvertSceneNamesToIndexerID(ConvertSceneExceptionsToIndexerID):
    def test(self):
        return self.hasColumn("scene_names", "indexer_id")

    def execute(self):
        if self.hasTable("tmp_scene_names"):
            self.connection.action("DROP TABLE tmp_scene_names")

        self.connection.action("ALTER TABLE scene_names RENAME TO tmp_scene_names")
        self.connection.action("CREATE TABLE scene_names (indexer_id INTEGER, name TEXT)")
        self.connection.action("INSERT INTO scene_names(indexer_id, name) SELECT tvdb_id, name FROM tmp_scene_names")
        self.connection.action("DROP TABLE tmp_scene_names")

class ConvertIndexerToInteger(ConvertSceneNamesToIndexerID):
    def execute(self):
        ql = []
        ql.append(["UPDATE xem_numbering SET indexer = ? WHERE LOWER(indexer) = ?", ["1", "tvdb"]])
        ql.append(["UPDATE xem_numbering SET indexer = ? WHERE LOWER(indexer) = ?", ["2", "tvrage"]])
        ql.append(["UPDATE xem_refresh SET indexer = ? WHERE LOWER(indexer) = ?", ["1", "tvdb"]])
        ql.append(["UPDATE xem_refresh SET indexer = ? WHERE LOWER(indexer) = ?", ["2", "tvrage"]])
        self.connection.mass_action(ql)

class RemoveKeysFromXemNumbering(ConvertIndexerToInteger):
    def execute(self):
        self.connection.action("ALTER TABLE xem_numbering DROP UNIQUE (indexer, indexer_id, season, episode)")
        self.connection.action("ALTER TABLE xem_numbering DROP PRIMARY KEY")