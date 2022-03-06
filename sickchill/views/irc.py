from .common import PageTemplate
from .home import Home
from .routes import Route


@Route("/IRC(/?.*)", name="irc")
class HomeIRC(Home):
    def index(self):
        t = PageTemplate(rh=self, filename="IRC.mako")
        return t.render(topmenu="system", header=_("IRC"), title=_("IRC"), controller="IRC", action="index")
