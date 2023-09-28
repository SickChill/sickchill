from flask import render_template

from sickchill import logger, settings

# from sickchill.movies import movie

from .. import movies_blueprint


@movies_blueprint.route("/")
def movies():
    logger.info("Loading movies page")
    movies_blueprint.logger.info("Loaded movies page")

    logger.debug(f"movies: {settings.showList}")
    movies_blueprint.logger.debug(f"movies: {settings.movie_list}")

    return render_template("movies.html", movies=settings.movie_list)
