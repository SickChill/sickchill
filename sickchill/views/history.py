import sickchill.start
from sickchill import settings
from sickchill.helper import try_int
from sickchill.show.History import History as HistoryTool

from ..oldbeard import ui
from .common import PageTemplate
from .index import WebRoot
from .routes import Route


@Route("/history(/?.*)", name="history")
class History(WebRoot):
    def initialize(self):
        super().initialize()
        self.history = HistoryTool()

    def index(self):
        settings.HISTORY_LIMIT = try_int(self.get_query_argument("limit", default=100), 100)
        sickchill.start.save_config()

        compact = []
        data = self.history.get(settings.HISTORY_LIMIT)

        for row in data:
            action = {"action": row["action"], "provider": row["provider"], "resource": row["resource"], "time": row["date"]}

            if not any(
                (
                    history["show_id"] == row["show_id"]
                    and history["season"] == row["season"]
                    and history["episode"] == row["episode"]
                    and history["quality"] == row["quality"]
                )
                for history in compact
            ):
                history = {
                    "actions": [action],
                    "episode": row["episode"],
                    "quality": row["quality"],
                    "resource": row["resource"],
                    "season": row["season"],
                    "show_id": row["show_id"],
                    "show_name": row["show_name"],
                    "provider": row["provider"],
                }

                compact.append(history)
            else:
                index = [
                    i
                    for i, item in enumerate(compact)
                    if item["show_id"] == row["show_id"]
                    and item["season"] == row["season"]
                    and item["episode"] == row["episode"]
                    and item["quality"] == row["quality"]
                ][0]
                history = compact[index]
                history["actions"].append(action)
                history["actions"].sort(key=lambda x: x["time"], reverse=True)

        t = PageTemplate(rh=self, filename="history.mako")
        submenu = [
            {"title": _("Remove Selected"), "path": "history/removeHistory", "icon": "fa fa-eraser", "class": "removehistory", "confirm": False},
            {"title": _("Clear History"), "path": "history/clearHistory", "icon": "fa fa-trash", "class": "clearhistory", "confirm": True},
            {"title": _("Trim History"), "path": "history/trimHistory", "icon": "fa fa-scissors", "class": "trimhistory", "confirm": True},
        ]

        return t.render(
            historyResults=data,
            compactResults=compact,
            limit=settings.HISTORY_LIMIT,
            submenu=submenu,
            title=_("History"),
            header=_("History"),
            topmenu="history",
            controller="history",
            action="index",
        )

    def removeHistory(self):
        log_items = []
        for item in self.get_body_arguments("items"):
            info = item.split(",")
            log_items.append({"dates": info[0].split("$"), "show_id": info[1], "season": info[2], "episode": info[3]})

        self.history.remove(log_items)

        ui.notifications.message(_("Selected history entries removed"))

        return self.redirect("/history/")

    def clearHistory(self):
        self.history.clear()

        ui.notifications.message(_("History cleared"))

        return self.redirect("/history/")

    def trimHistory(self):
        self.history.trim()

        ui.notifications.message(_("Removed history entries older than 30 days"))

        return self.redirect("/history/")
