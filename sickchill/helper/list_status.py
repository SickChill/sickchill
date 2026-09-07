"""Presentation context for Add Shows discovery list empty/error states."""


def build_list_status(code, settings_url: str = "", source: str = "tmdb") -> dict:
    """
    Return a thin status dict for trendingShows.mako.

    code: None | "ok" | "empty" | "fetch_failed" | "missing_key"
    source: "tmdb" | "trakt"
    """
    if code == "missing_key":
        if source == "trakt":
            return {
                "code": "missing_key",
                "title": _("Trakt VIP credentials required."),
                "message": _(
                    "Trakt lists need a VIP API app Client ID and Secret. Create an app at trakt.tv/oauth/applications (VIP), paste the credentials under Config → General → Indexer / Data, then authorize."
                ),
                "settings_url": settings_url,
                "settings_label": _("Open General settings"),
            }
        return {
            "code": "missing_key",
            "title": _("TMDB API key missing."),
            "message": _("Configure a TMDB API key to load TMDB discovery lists. TVMaze Upcoming Premieres do not require a key."),
            "settings_url": settings_url,
            "settings_label": _("Open General settings"),
        }
    if code == "fetch_failed":
        if source == "trakt":
            return {
                "code": "fetch_failed",
                "title": _("Could not load Trakt list."),
                "message": _("Check your Trakt authorization under Config → General → Indexer / Data, then try again."),
                "settings_url": settings_url,
                "settings_label": _("Open General settings") if settings_url else "",
            }
        return {
            "code": "fetch_failed",
            "title": _("Could not load discovery list."),
            "message": _("Check your network connection and try again."),
            "settings_url": settings_url,
            "settings_label": _("Open General settings") if settings_url else "",
        }
    if code == "empty":
        if source == "trakt":
            return {
                "code": "empty",
                "title": _("Trakt API did not return any results."),
                "message": _("Please check your Trakt config, or try another list."),
                "settings_url": settings_url,
                "settings_label": _("Open General settings") if settings_url else "",
            }
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
