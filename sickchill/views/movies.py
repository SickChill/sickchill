from sickchill import logger, settings
from .common import PageTemplate
from .index import WebRoot

class Movies(WebRoot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _genericMessage(self, subject=None, message=None):
        t = PageTemplate(rh=self, filename="genericMessage.mako")
        return t.render(message=message, subject=subject, topmenu="movies", title="")

    def index(self):
        t = PageTemplate(rh=self, filename="movies/index.mako")
        return t.render(title=_("Movies"), header=_("Movie List"), topmenu="movies", movies=settings.movie_list, controller="movies", action="index")

    def search(self):
        t = PageTemplate(rh=self, filename="movies/search.mako")
        return t.render(title=_("Movies"), header=_("Movie Search"), topmenu="movies", movies=settings.movie_list, controller="movies", action="search")

    def add(self):
        t = PageTemplate(rh=self, filename="movies/add.mako")
        return t.render(title=_("Movies"), header=_("Movie Add"), topmenu="movies", movies=settings.movie_list, controller="movies", action="add")

    def remove(self):
        t = PageTemplate(rh=self, filename="movies/remove.mako")
        return t.render(title=_("Movies"), header=_("Movie Remove"), topmenu="movies", movies=settings.movie_list, controller="movies", action="remove")
