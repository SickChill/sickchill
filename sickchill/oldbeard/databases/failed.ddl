create table db_version
(
    db_version INTEGER default 0
);

create table failed
(
    "release" TEXT,
    size      NUMERIC,
    provider  TEXT
);

create table history
(
    date       NUMERIC,
    size       NUMERIC,
    "release"  TEXT,
    provider   TEXT,
    old_status NUMERIC default 0,
    showid     NUMERIC default -1,
    season     NUMERIC default -1,
    episode    NUMERIC default -1
);

