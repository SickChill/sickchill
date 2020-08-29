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

    def add(self):
        def search_redirect():
            t = PageTemplate(rh=self, filename="movies/search.mako")
            return t.render(title=_("Movies"), header=_("Movie Search"), topmenu="movies", movies=settings.movie_list, controller="movies", action="search")

        if self.request.method == 'GET':
            return search_redirect()

        query = self.get_body_argument('query', None)
        movie = None
        if query:
            if self.get_body_argument('imdb', None):
                movie = settings.movie_list.add_from_imdb(imdbid=query)
            elif self.get_body_argument('tmdb', None):
                movie = settings.movie_list.add_from_tmdb(tmdbid=query)

        if not movie:
            return search_redirect()

        return self.redirect(self.reverse_url('movies-details', movie.slug))

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
