"""Presentation context for Add Shows discovery list empty/error states."""


def build_list_status(code, settings_url: str = "") -> dict:
    """
    Return a thin status dict for trendingShows.mako.

    code: None | "ok" | "empty" | "fetch_failed" | "missing_key"
    """
    if code == "missing_key":
        return {
            "code": "missing_key",
            "title": _("TMDB API key missing."),
            "message": _("Configure a TMDB API key to load TMDB discovery lists. TVMaze Upcoming Premieres do not require a key."),
            "settings_url": settings_url,
            "settings_label": _("Open General settings"),
        }
    if code == "fetch_failed":
        return {
            "code": "fetch_failed",
            "title": _("Could not load discovery list."),
            "message": _("Check your network connection and try again."),
            "settings_url": settings_url,
            "settings_label": _("Open General settings") if settings_url else "",
        }
    if code == "empty":
        return {
            "code": "empty",
            "title": _("No shows returned for this list."),
            "message": _("Try another list, or refresh later."),
            "settings_url": "",
            "settings_label": "",
        }
    return {
        "code": code or "ok",
        "title": "",
        "message": "",
        "settings_url": "",
        "settings_label": "",
    }
