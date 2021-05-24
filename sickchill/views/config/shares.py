from tornado.web import addslash

from sickchill import logger, settings
from sickchill.oldbeard import ui
from sickchill.views.common import PageTemplate
from sickchill.views.routes import Route

from . import Config


@Route("/config/shares(/?.*)", name="config:shares")
class ConfigShares(Config):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @addslash
    def index(self):

        t = PageTemplate(rh=self, filename="config_shares.mako")
        return t.render(
            title=_("Config - Shares"),
            header=_("Windows Shares Configuration"),
            topmenu="config",
            submenu=self.ConfigMenu(),
            controller="config",
            action="shares",
        )

    @staticmethod
    def save_shares(shares):
        new_shares = {}
        for index, share in enumerate(shares):
            if share.get("server") and share.get("path") and share.get("name"):
                new_shares[share.get("name")] = {"server": share.get("server"), "path": share.get("path")}
            elif any([share.get("server"), share.get("path"), share.get("name")]):
                info = []
                if not share.get("name"):
                    info.append("name")
                if not share.get("server"):
                    info.append("server")
                if not share.get("path"):
                    info.append("path")

                info = " and ".join(info)
                logger.info(
                    "Cannot save share #{index}. You must enter name, server and path."
                    "{info} {copula} missing, got: [name: {name}, server:{server}, path: {path}]".format(
                        index=index, info=info, copula=("is", "are")["and" in info], name=share.get("name"), server=share.get("server"), path=share.get("path")
                    )
                )

        settings.WINDOWS_SHARES.clear()
        settings.WINDOWS_SHARES.update(new_shares)

        ui.notifications.message(_("Saved Shares"), _("Your Windows share settings have been saved"))
