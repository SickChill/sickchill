from sickchill.oldbeard import db


# Add new migrations at the bottom of the list; subclass the previous migration.
class InitialSchema(db.SchemaUpgrade):
    def test(self):
        return self.has_table("db_version")

    def execute(self):
        queries = (
            ("CREATE TABLE lastUpdate (provider TEXT, time NUMERIC);",),
            ("CREATE TABLE lastSearch (provider TEXT, time NUMERIC);",),
            ("CREATE TABLE scene_exceptions (exception_id INTEGER PRIMARY KEY, indexer_id INTEGER, show_name TEXT, season NUMERIC DEFAULT -1, custom NUMERIC DEFAULT 0);",),
            ("CREATE TABLE scene_names (indexer_id INTEGER, name TEXT);",),
            ("CREATE TABLE network_timezones (network_name TEXT PRIMARY KEY, timezone TEXT);",),
            ("CREATE TABLE scene_exceptions_refresh (list TEXT PRIMARY KEY, last_refreshed INTEGER);",),
            ("CREATE TABLE db_version (db_version INTEGER);",),
            ("CREATE TABLE results (provider TEXT, name TEXT, season NUMERIC, episodes TEXT, indexerid NUMERIC, url TEXT, time NUMERIC, quality TEXT, release_group TEXT, version NUMERIC, seeders INTEGER DEFAULT 0, leechers INTEGER DEFAULT 0, size INTEGER DEFAULT -1, status INTEGER DEFAULT 0, failed INTEGER DEFAULT 0, added TEXT DEFAULT CURRENT_TIMESTAMP);",),
            ("INSERT INTO db_version(db_version) VALUES (1);",),
            ("CREATE UNIQUE INDEX IF NOT EXISTS idx_url ON results (url);",),
            ("CREATE UNIQUE INDEX IF NOT EXISTS provider ON results (provider);",),
            ("CREATE UNIQUE INDEX IF NOT EXISTS seeders ON results (seeders);",)
        )
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
        # language=TEXT
        self.connection.action("INSERT INTO scene_exceptions SELECT exception_id, tvdb_id as indexer_id, show_name, season, custom FROM tmp_scene_exceptions;")
        # language=TEXT
        self.connection.action("DROP TABLE tmp_scene_exceptions;")


class ConvertSceneNamesToIndexerScheme(AddSceneExceptionsRefresh):  # pylint:disable=too-many-ancestors
    def test(self):
        return self.has_column("scene_names", "indexer_id")

    def execute(self):
        self.connection.action("DROP TABLE IF EXISTS tmp_scene_names;")
        self.connection.action("ALTER TABLE scene_names RENAME TO tmp_scene_names;")
        self.connection.action("CREATE TABLE scene_names (indexer_id INTEGER, name TEXT);")
        # language=TEXT
        self.connection.action("INSERT INTO scene_names SELECT * FROM tmp_scene_names;")
        # language=TEXT
        self.connection.action("DROP TABLE tmp_scene_names;")


class ResultsTable(ConvertSceneExeptionsToIndexerScheme):
    def test(self):
        return self.has_table('results')

    def execute(self):
        import sickchill.settings
        assert len(sickchill.settings.providerList) != 0
        self.connection.action(
            "CREATE TABLE results (provider TEXT, name TEXT, season NUMERIC, episodes TEXT, indexerid NUMERIC, url TEXT, time NUMERIC, quality TEXT,"
            "release_group TEXT, version NUMERIC, seeders INTEGER DEFAULT 0, leechers INTEGER DEFAULT 0, size INTEGER DEFAULT -1, status INTEGER DEFAULT 0, failed INTEGER DEFAULT 0, added TEXT DEFAULT CURRENT_TIMESTAMP);")

        for provider in sickchill.settings.providerList:
            provider_id = provider.get_id()
            if self.has_table(provider_id):
                self.add_column(provider_id, 'provider', col_type="TEXT", default=provider_id)
                self.add_column(provider_id, 'seeders', col_type="INTEGER")
                self.add_column(provider_id, 'leechers', col_type="INTEGER")
                self.add_column(provider_id, 'size', col_type="INTEGER")
                self.add_column(provider_id, 'status', col_type="INTEGER")
                self.add_column(provider_id, 'failed', col_type="INTEGER")
                self.add_column(provider_id, 'added', col_type="TEXT", default='CURRENT_TIMESTAMP')

                self.connection.action(
                    "INSERT INTO results SELECT provider, name , season, episodes, indexerid, url, time, quality, release_group, version, seeders, leechers, size, status, failed, added FROM {}".format(provider_id))
                self.connection.action('DROP TABLE {}'.format(provider_id))


class LastUpdate(ResultsTable):
    def test(self):
        return self.has_table('lastUpdate')

    def execute(self):
        self.connection.action("CREATE TABLE lastUpdate (provider TEXT, time NUMERIC)")
