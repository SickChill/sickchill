# coding=utf-8

# Author: Tyler Fenby <tylerfenby@gmail.com>
# URL: https://sickchill.github.io
#
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from sickbeard import db
from sickbeard.common import Quality


# Add new migrations at the bottom of the list; subclass the previous migration.
class InitialSchema(db.SchemaUpgrade):
    def test(self):
        return self.has_table('db_version')

    def execute(self):
        queries = [
            ('CREATE TABLE failed (release TEXT, size NUMERIC, provider TEXT, hash TEXT, url TEXT, type NUMERIC DEFAULT -1);',),
            ('CREATE TABLE history (date NUMERIC, size NUMERIC, release TEXT, provider TEXT, old_status NUMERIC DEFAULT 0, showid NUMERIC DEFAULT -1, season NUMERIC DEFAULT -1, episode NUMERIC DEFAULT -1, hash TEXT, url TEXT, type NUMERIC DEFAULT -1);',),
            ('CREATE TABLE db_version (db_version INTEGER);',),
            ('INSERT INTO db_version (db_version) VALUES (1);',),
        ]
        for query in queries:
            if len(query) == 1:
                self.connection.action(query[0])
            else:
                self.connection.action(query[0], query[1:])


class AddProvider(InitialSchema):
    def test(self):
        return self.has_column('failed', 'provider')

    def execute(self):
        self.add_column('failed', 'provider', 'TEXT', '')


class AddSize(AddProvider):
    def test(self):
        return self.has_column('failed', 'size')

    def execute(self):
        self.add_column('failed', 'size', 'NUMERIC')


class History(AddSize):
    """Snatch history that can't be modified by the user"""

    def test(self):
        return self.has_table('history')

    def execute(self):
        self.connection.action('CREATE TABLE history (date NUMERIC, ' +
                               'size NUMERIC, release TEXT, provider TEXT);')


class HistoryStatus(History):
    """Store episode status before snatch to revert to if necessary"""

    def test(self):
        return self.has_column('history', 'old_status')

    def execute(self):
        self.add_column('history', 'old_status', 'NUMERIC', Quality.NONE)
        self.add_column('history', 'showid', 'NUMERIC', '-1')
        self.add_column('history', 'season', 'NUMERIC', '-1')
        self.add_column('history', 'episode', 'NUMERIC', '-1')


class BigDBUpdate(HistoryStatus):
    """
    https://github.com/SickChill/SickChill/issues/5167
    """
    def test(self):
        return self.has_column('failed', 'hash')

    def execute(self):
        self.add_column('failed', 'hash', 'TEXT')
        self.add_column('failed', 'url', 'TEXT')
        self.add_column('failed', 'type', 'NUMERIC', '-1')
        self.add_column('history', 'hash', 'TEXT')
        self.add_column('history', 'url', 'TEXT')
        self.add_column('history', 'type', 'NUMERIC', '-1')
