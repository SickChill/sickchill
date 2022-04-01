create table blacklist
(
    show_id INTEGER,
    range   TEXT,
    keyword TEXT
);

create table db_version
(
    db_version       INTEGER default 44,
    db_minor_version NUMERIC default 3
);

create table history
(
    action   NUMERIC,
    date     NUMERIC,
    showid   NUMERIC,
    season   NUMERIC,
    episode  NUMERIC,
    quality  NUMERIC,
    resource TEXT,
    provider TEXT,
    version  NUMERIC default -1
);

create table imdb_info
(
    indexer_id    INTEGER
        primary key,
    imdb_id       TEXT,
    title         TEXT,
    year          NUMERIC,
    akas          TEXT,
    runtimes      NUMERIC,
    genres        TEXT,
    countries     TEXT,
    country_codes TEXT,
    certificates  TEXT,
    rating        TEXT,
    votes         INTEGER,
    last_update   NUMERIC
);

create table indexer_mapping
(
    indexer_id  INTEGER,
    indexer     NUMERIC,
    mindexer_id INTEGER,
    mindexer    NUMERIC,
    primary key (indexer_id, indexer)
);

create table info
(
    last_backlog       NUMERIC,
    last_indexer       NUMERIC,
    last_proper_search NUMERIC
);

create table scene_numbering
(
    indexer               TEXT,
    indexer_id            INTEGER,
    season                INTEGER,
    episode               INTEGER,
    scene_season          INTEGER,
    scene_episode         INTEGER,
    absolute_number       NUMERIC,
    scene_absolute_number NUMERIC,
    primary key (indexer_id, season, episode)
);

create table tv_episodes
(
    episode_id            INTEGER
        primary key,
    showid                NUMERIC,
    indexerid             NUMERIC,
    indexer               TEXT,
    name                  TEXT,
    season                NUMERIC,
    episode               NUMERIC,
    description           TEXT,
    airdate               NUMERIC,
    hasnfo                NUMERIC,
    hastbn                NUMERIC,
    status                NUMERIC,
    location              TEXT,
    file_size             NUMERIC,
    release_name          TEXT,
    subtitles             TEXT,
    subtitles_searchcount NUMERIC,
    subtitles_lastsearch  TIMESTAMP,
    is_proper             NUMERIC,
    scene_season          NUMERIC,
    scene_episode         NUMERIC,
    absolute_number       NUMERIC,
    scene_absolute_number NUMERIC,
    version               NUMERIC default -1,
    release_group         TEXT
);

create index idx_showid
    on tv_episodes (showid);

create index idx_sta_epi_air
    on tv_episodes (status, episode, airdate);

create index idx_sta_epi_sta_air
    on tv_episodes (season, episode, status, airdate);

create index idx_status
    on tv_episodes (status, season, episode, airdate);

create index idx_tv_episodes_showid_airdate
    on tv_episodes (showid, airdate);

create table tv_shows
(
    show_id             INTEGER
        primary key,
    indexer_id          NUMERIC,
    indexer             NUMERIC,
    show_name           TEXT,
    location            TEXT,
    network             TEXT,
    genre               TEXT,
    classification      TEXT,
    runtime             NUMERIC,
    quality             NUMERIC,
    airs                TEXT,
    status              TEXT,
    flatten_folders     NUMERIC,
    paused              NUMERIC,
    startyear           NUMERIC,
    air_by_date         NUMERIC,
    lang                TEXT,
    subtitles           NUMERIC,
    notify_list         TEXT,
    imdb_id             TEXT,
    last_update_indexer NUMERIC,
    dvdorder            NUMERIC,
    archive_firstmatch  NUMERIC,
    rls_require_words   TEXT,
    rls_ignore_words    TEXT,
    sports              NUMERIC,
    anime               NUMERIC,
    scene               NUMERIC,
    default_ep_status   NUMERIC default -1,
    sub_use_sr_metadata NUMERIC,
    rls_prefer_words    TEXT,
    custom_name         TEXT
);

create unique index idx_indexer_id
    on tv_shows (indexer_id);

create table whitelist
(
    show_id INTEGER,
    range   TEXT,
    keyword TEXT
);

create table xem_refresh
(
    indexer        TEXT,
    indexer_id     INTEGER
        primary key,
    last_refreshed INTEGER
);

