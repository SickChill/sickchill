import logging

from sickchill import settings

from .common import PageTemplate
from .index import WebRoot

logger = logging.getLogger('sickchill.movie')


class MoviesHandler(WebRoot):
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
        if self.request.method == 'GET':
            return self.redirect(self.reverse_url('movies-search'))

        t = PageTemplate(rh=self, filename="movies/add.mako")
        return t.render(title=_("Movies"), header=_("Movie Add"), topmenu="movies", movies=settings.movie_list, controller="movies", action="add")

    def remove(self):
        pk = self.path_kwargs.get('pk')
        if pk is not None:
            if not settings.movie_list.query.get(pk):
                return self._genericMessage(_('Error'), _('Movie not found'))

            settings.movie_list.delete(pk)

        t = PageTemplate(rh=self, filename="movies/remove.mako")
        return t.render(title=_("Movies"), header=_("Movie Remove"), topmenu="movies", movies=settings.movie_list, controller="movies", action="remove")

    def details(self):
        movie = settings.movie_list.by_slug(self.path_kwargs.get('slug'))
        if not movie:
            return self._genericMessage(_('Error'), _('Movie not found'))

        t = PageTemplate(rh=self, filename="movies/details.mako")
        return t.render(title=_("Movies"), header=_("Movie Remove"), topmenu="movies", movie=movie, controller="movies", action="remove")
