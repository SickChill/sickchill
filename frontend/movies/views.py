from flask import Blueprint, render_template

from sickchill import logger, settings

# from sickchill.movies import movie

blueprint = Blueprint("movies", __name__, template_folder="templates", static_folder="static", url_prefix="/movies")


@blueprint.route("/")
def movies():
    logger.info("Loading movies page")
    blueprint.logger.info("Loaded movies page")

    logger.debug(f"movies: {settings.showList}")
    blueprint.logger.debug(f"movies: {settings.movie_list}")

    return render_template("movies.html", movies=settings.movie_list)
