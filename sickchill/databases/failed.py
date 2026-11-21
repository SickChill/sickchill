from sickchill import db


# Add new migrations at the bottom of the list; subclass the previous migration.
class InitialSchema(db.SchemaUpgrade):
    def test(self):
        return self.has_table("db_version")

    def execute(self):
        # ruff: disable [ISC004]
        queries = [
            ('CREATE TABLE failed ("release" TEXT, size NUMERIC, provider TEXT);',),
            (
                'CREATE TABLE history (date NUMERIC, size NUMERIC, "release" TEXT, provider TEXT, old_status NUMERIC DEFAULT 0, '
                "showid NUMERIC DEFAULT -1, season NUMERIC DEFAULT -1, episode NUMERIC DEFAULT -1);",
            ),
            ("CREATE TABLE db_version (db_version INTEGER);",),
            ("INSERT INTO db_version (db_version) VALUES (1);",),
        ]
        # ruff: enable [ISC004]
        for query in queries:
            if len(query) == 1:
                self.connection.action(query[0])
            else:
                self.connection.action(query[0], query[1:])


class AddDeadUrls(InitialSchema):
    """One row per download URL that did not return a file.

    The ``failed`` table is keyed by release name. Two indexer rows can share that name
    and differ only by URL, so a dead link is stored here instead.
    """

    def test(self):
        return self.has_table("dead_urls")

    def execute(self):
        self.connection.action("CREATE TABLE IF NOT EXISTS dead_urls (url TEXT PRIMARY KEY, name TEXT, provider TEXT, date NUMERIC)")
