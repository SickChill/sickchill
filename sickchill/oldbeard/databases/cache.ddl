CREATE TABLE lastUpdate (
    provider TEXT,
    time NUMERIC
);

CREATE TABLE lastSearch (
    provider TEXT,
    time NUMERIC
);

CREATE TABLE scene_exceptions (
    exception_id INTEGER PRIMARY KEY,
    indexer_id INTEGER,
    show_name TEXT,
    season NUMERIC DEFAULT -1,
    custom NUMERIC DEFAULT 0
);

CREATE TABLE scene_names (
    indexer_id INTEGER,
    name TEXT
);

CREATE TABLE network_timezones (
    network_name TEXT PRIMARY KEY,
    timezone TEXT
);

CREATE TABLE scene_exceptions_refresh (
    list TEXT PRIMARY KEY,
    last_refreshed INTEGER
);

CREATE TABLE results (provider TEXT,
    name TEXT,
    season NUMERIC,
    episodes TEXT,
    indexerid NUMERIC,
    url TEXT,
    time NUMERIC,
    quality TEXT,
    release_group TEXT,
    version NUMERIC,
    seeders INTEGER DEFAULT 0,
    leechers INTEGER DEFAULT 0,
    size INTEGER DEFAULT -1,
    status INTEGER DEFAULT 0,
    failed INTEGER DEFAULT 0,
    added TEXT DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE db_version (db_version INTEGER DEFAULT 1);
CREATE UNIQUE INDEX IF NOT EXISTS idx_url ON results (url);
CREATE INDEX IF NOT EXISTS provider ON results (provider);
CREATE INDEX IF NOT EXISTS seeders ON results (seeders);
