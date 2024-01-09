import markdown2

from .. import logger
from ..oldbeard import helpers
from .common import PageTemplate
from .home import Home
from .routes import Route


@Route("/changes(/?.*)", name="changelog")
class HomeChangeLog(Home):
    def index(self, *args, **kwargs):
        # noinspection PyBroadException
        try:
            changes = helpers.getURL("https://raw.githubusercontent.com/SickChill/sickchill/master/CHANGES.md", session=helpers.make_session(), returns="text")
        except Exception:
            logger.debug("Could not load changes from repo, giving a link!")
            changes_url = "https://raw.githubusercontent.com/SickChill/sickchill/master/CHANGES.md"
            changes = _("Could not load changes from the repo. [Click here for CHANGES.md]") + f"({changes_url})"

        t = PageTemplate(rh=self, filename="markdown.mako")
        data = markdown2.markdown(changes if changes else _("The was a problem connecting to github, please refresh and try again"), extras=["header-ids"])

        return t.render(title=_("Changelog"), header=_("Changelog"), topmenu="system", data=data, controller="changes", action="index")
