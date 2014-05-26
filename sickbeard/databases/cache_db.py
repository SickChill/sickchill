# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from sickbeard import db

# Add new migrations at the bottom of the list; subclass the previous migration.
class InitialSchema(db.SchemaUpgrade):
    def test(self):
        return self.hasTable("lastUpdate")

    def execute(self):

        queries = [
            ("CREATE TABLE lastUpdate (provider TEXT, time NUMERIC);",),
            ("CREATE TABLE lastSearch (provider TEXT, time NUMERIC);",),
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
            "CREATE TABLE scene_exceptions (exception_id INTEGER PRIMARY KEY, indexer_id INTEGER KEY, show_name TEXT)")


class AddSceneNameCache(AddSceneExceptions):
    def test(self):
        return self.hasTable("scene_names")

    def execute(self):
        self.connection.action("CREATE TABLE scene_names (indexer_id INTEGER, name TEXT)")


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
            "CREATE TABLE xem_numbering (indexer TEXT, indexer_id INTEGER, season INTEGER, episode INTEGER, absolute_number INTEGER, scene_season INTEGER, scene_episode INTEGER, scene_absolute_number INTEGER, PRIMARY KEY (indexer_id, scene_season, scene_episode))")

class AddXemRefresh(AddXemNumbering):
    def test(self):
        return self.hasTable("xem_refresh")

    def execute(self):
        self.connection.action(
            "CREATE TABLE xem_refresh (indexer TEXT, indexer_id INTEGER PRIMARY KEY, last_refreshed INTEGER)")

class AddLastSearch(AddXemRefresh):
    def test(self):
        return self.hasTable("lastSearch")

    def execute(self):
        self.connection.action("CREATE TABLE lastSearch (provider TEXT, time NUMERIC)")

class AddAbsoluteNumbering(AddLastSearch):
    def test(self):
        return self.hasColumn("xem_numbering", "absolute_number")

    def execute(self):
        self.addColumn("xem_numbering", "absolute_number", "NUMERIC", "0")
        self.addColumn("xem_numbering", "scene_absolute_number", "NUMERIC", "0")

class AddSceneExceptionsSeasons(AddSceneNameCache):
    def test(self):
        return self.hasColumn("scene_exceptions", "season")

    def execute(self):
        self.addColumn("scene_exceptions", "season", "NUMERIC", -1)