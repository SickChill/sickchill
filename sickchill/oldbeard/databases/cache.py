from sickchill.oldbeard import db


# Add new migrations at the bottom of the list; subclass the previous migration.
class InitialSchema(db.SchemaUpgrade):
    def test(self):
        return self.has_table("db_version")

    def execute(self):
        queries = (
            ("CREATE TABLE lastUpdate (provider TEXT, time NUMERIC);",),
            ("CREATE TABLE lastSearch (provider TEXT, time NUMERIC);",),
            (
                "CREATE TABLE scene_exceptions ("
                "exception_id INTEGER PRIMARY KEY, indexer_id INTEGER, show_name TEXT, season NUMERIC DEFAULT -1, custom NUMERIC DEFAULT 0);",
            ),
            ("CREATE TABLE scene_names (indexer_id INTEGER, name TEXT);",),
            ("CREATE TABLE network_timezones (network_name TEXT PRIMARY KEY, timezone TEXT);",),
            ("CREATE TABLE scene_exceptions_refresh (list TEXT PRIMARY KEY, last_refreshed INTEGER);",),
            ("CREATE TABLE db_version (db_version INTEGER);",),
            (
                "CREATE TABLE results (provider TEXT, name TEXT, season NUMERIC, episodes TEXT, indexerid NUMERIC, url TEXT, time NUMERIC, quality TEXT, "
                "release_group TEXT, version NUMERIC, seeders INTEGER DEFAULT 0, leechers INTEGER DEFAULT 0, size INTEGER DEFAULT -1, status INTEGER DEFAULT 0, "
                "failed INTEGER DEFAULT 0, added TEXT DEFAULT CURRENT_TIMESTAMP);",
            ),
            ("INSERT INTO db_version(db_version) VALUES (1);",),
            ("CREATE UNIQUE INDEX IF NOT EXISTS idx_url ON results (url);",),
            ("CREATE INDEX IF NOT EXISTS provider ON results (provider);",),
            ("CREATE INDEX IF NOT EXISTS seeders ON results (seeders);",),
        )
        for query in queries:
            self.connection.action(query[0])


class ResultsTable(InitialSchema):
    def test(self):
        return self.has_table("results")

    def execute(self):
        import sickchill.settings

        self.connection.action(
            "CREATE TABLE results (provider TEXT, name TEXT, season NUMERIC, episodes TEXT, indexerid NUMERIC, url TEXT, time NUMERIC, quality TEXT,"
            "release_group TEXT, version NUMERIC, seeders INTEGER DEFAULT 0, leechers INTEGER DEFAULT 0, size INTEGER DEFAULT -1, status INTEGER DEFAULT 0, "
            "failed INTEGER DEFAULT 0, added TEXT DEFAULT CURRENT_TIMESTAMP);"
        )

        for provider in sickchill.settings.providerList:
            provider_id = provider.get_id()
            if self.has_table(provider_id):
                self.add_column(provider_id, "provider", col_type="TEXT", default=provider_id)
                self.add_column(provider_id, "seeders", col_type="INTEGER")
                self.add_column(provider_id, "leechers", col_type="INTEGER")
                self.add_column(provider_id, "size", col_type="INTEGER")
                self.add_column(provider_id, "status", col_type="INTEGER")
                self.add_column(provider_id, "failed", col_type="INTEGER")
                timestamp = self.connection.select("SELECT CURRENT_TIMESTAMP;")
                self.add_column(provider_id, "added", col_type="TEXT", default=timestamp[0]["CURRENT_TIMESTAMP"])

                # language=TEXT
                self.connection.action(
                    "INSERT INTO results SELECT provider, name , season, episodes, indexerid, url, time, quality,"
                    "release_group, version, seeders, leechers, size, status, failed, added FROM ?",
                    [provider_id],
                )
                self.connection.action("DROP TABLE {}".format(provider_id))
