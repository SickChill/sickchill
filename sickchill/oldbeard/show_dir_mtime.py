"""Cache helpers for ShowUpdater disk-refresh gating (folder mtime + last refresh)."""

from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING, Optional

from sickchill import logger
from sickchill.oldbeard import db

if TYPE_CHECKING:
    from sickchill.tv import TVShow


def newest_dir_mtime(location: str) -> Optional[float]:
    """
    Return the newest directory mtime under ``location`` (inclusive).

    Walks descendant directories so season/episode folder changes are detected even
    when the show root mtime is unchanged. File-only in-place overwrites may not
    bump any directory mtime — the calendar safety net covers that case.
    """
    if not location or not os.path.isdir(location):
        return None

    try:
        newest = os.path.getmtime(location)
    except OSError as error:
        logger.debug(f"Could not read mtime for {location}: {error}")
        return None

    try:
        for root, _dirs, _files in os.walk(location):
            try:
                newest = max(newest, os.path.getmtime(root))
            except OSError:
                continue
    except OSError as error:
        logger.debug(f"Could not walk show folder {location}: {error}")

    return newest


def get_show_dir_mtime(show: "TVShow") -> Optional[float]:
    """Return newest directory mtime under the show location, or None if unavailable."""
    location = getattr(show, "_location", None) or getattr(show, "location", None)
    try:
        if location:
            return newest_dir_mtime(location)
    except OSError as error:
        logger.debug(f"Could not read mtime for {location}: {error}")
    return None


def get_cached_row(indexer_id: int) -> Optional[dict]:
    cache_db_con = db.DBConnection("cache.db")
    try:
        rows = cache_db_con.select("SELECT indexer_id, location, mtime, last_disk_refresh FROM show_dir_mtime WHERE indexer_id = ?", [indexer_id])
    except Exception as error:
        # Table may not exist yet on a race before migration; treat as no cache
        logger.debug(f"show_dir_mtime select failed for {indexer_id}: {error}")
        return None
    return rows[0] if rows else None


def needs_disk_refresh(show: "TVShow", interval_days: int) -> tuple[bool, str]:
    """
    Decide whether ShowUpdater should queue a disk refresh for a show not in the TVDB feed.

    :param interval_days:
        -1 = never auto disk-refresh when not in feed
         0 = mtime-only (no calendar safety net)
         N = refresh if mtime changed OR last disk refresh was >= N days ago
    :return: (needs_refresh, reason) reason is for DEBUG logging
    """
    if interval_days == -1:
        return False, "auto disk refresh disabled (show_disk_refresh_days=-1)"

    location = ""
    try:
        location = show._location or ""
    except Exception:
        location = ""

    if not location or not os.path.isdir(location):
        return False, "show folder missing"

    current_mtime = get_show_dir_mtime(show)
    if current_mtime is None:
        return False, "could not read show folder mtime"

    row = get_cached_row(show.indexerid)
    if not row:
        return True, "no cached folder mtime (seed)"

    stored_location = row["location"] or ""
    if stored_location != location:
        return True, "show folder location changed"

    stored_mtime = row["mtime"]
    if stored_mtime is None or float(stored_mtime) != float(current_mtime):
        return True, "show folder mtime changed"

    if interval_days == 0:
        return False, "mtime unchanged (mtime-only mode)"

    last_refresh = int(row["last_disk_refresh"] or 0)
    if not last_refresh:
        return True, "no last_disk_refresh timestamp (seed)"

    age_days = (time.time() - last_refresh) / 86400.0
    if age_days >= interval_days:
        return True, f"last disk refresh {age_days:.1f} days ago (>= {interval_days})"

    return False, f"mtime unchanged, last refresh {age_days:.1f} days ago"


def stamp_show_dir_mtime(show: "TVShow") -> None:
    """Upsert folder mtime and last_disk_refresh after a successful QueueItemRefresh."""
    location = ""
    try:
        location = show._location or ""
    except Exception:
        location = ""

    mtime = get_show_dir_mtime(show)
    now = int(time.time())
    cache_db_con = db.DBConnection("cache.db")
    try:
        cache_db_con.action(
            "INSERT OR REPLACE INTO show_dir_mtime (indexer_id, location, mtime, last_disk_refresh) VALUES (?, ?, ?, ?)",
            [show.indexerid, location, mtime if mtime is not None else None, now],
        )
    except Exception as error:
        logger.debug(f"Failed to stamp show_dir_mtime for {show.indexerid}: {error}")
