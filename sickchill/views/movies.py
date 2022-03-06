import logging

from sickchill import settings
from sickchill.oldbeard import config

from .common import PageTemplate
from .index import WebRoot

logger = logging.getLogger("sickchill.movie")


class MoviesHandler(WebRoot):
    def _genericMessage(self, subject=None, message=None):
        t = PageTemplate(rh=self, filename="genericMessage.mako")
        return t.render(message=message, subject=subject, topmenu="movies", title="")

    def index(self):
        t = PageTemplate(rh=self, filename="movies/index.mako")
        return t.render(title=_("Movies"), header=_("Movie List"), topmenu="movies", movies=settings.movie_list, controller="movies", action="index")

    def search(self):
        query = self.get_body_argument("query", "")
        year = self.get_body_argument("year", "")
        language = self.get_body_argument("language", "")
        adult = config.checkbox_to_value(self.get_body_argument("adult", False))
        search_results = []
        if query:
            search_results = settings.movie_list.search_tmdb(query=query, year=year, language=language, adult=adult)
        t = PageTemplate(rh=self, filename="movies/search.mako")
        return t.render(
            title=_("Movies"),
            header=_("Movie Search"),
            topmenu="movies",
            controller="movies",
            action="search",
            search_results=search_results,
            movies=settings.movie_list,
            query=query,
            year=year,
            language=language,
            adult=adult,
        )

    def add(self):
        movie = None
        imdb_id = self.get_body_argument("imdb", None)
        if imdb_id:
            movie = settings.movie_list.add_from_imdb(imdb_id=imdb_id)
        tmdb_id = self.get_body_argument("tmdb", None)
        if tmdb_id:
            movie = settings.movie_list.add_from_tmdb(tmdb_id=tmdb_id)

        if not movie:
            return self.redirect(self.reverse_url("movies-search", "search"))

        return self.redirect(self.reverse_url("movies-details", "details", movie.slug))

    def remove(self):
        pk = self.path_kwargs.get("pk")
        if pk is not None:
            if not settings.movie_list.query.get(pk):
                return self._genericMessage(_("Error"), _("Movie not found"))

            settings.movie_list.delete(pk)

        t = PageTemplate(rh=self, filename="movies/remove.mako")
        return t.render(title=_("Movies"), header=_("Movie Remove"), topmenu="movies", movies=settings.movie_list, controller="movies", action="remove")

    def details(self):
        movie = settings.movie_list.by_slug(self.path_kwargs.get("slug"))
        if not movie:
            return self._genericMessage(_("Error"), _("Movie not found"))

        t = PageTemplate(rh=self, filename="movies/details.mako")
        return t.render(title=_("Movies"), header=_("Movie Remove"), topmenu="movies", controller="movies", action="details", movie=movie, movie_message=None)
