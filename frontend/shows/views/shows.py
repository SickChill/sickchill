from flask import render_template

from sickchill import logger, settings

# from sickchill.tv import TVEpisode, TVShow

from .. import shows_blueprint


@shows_blueprint.route("/")
def shows():
    logger.info("Loading shows page")
    logger.debug(f"Shows: {settings.showList}")
    return render_template("shows.html", shows=settings.showList)


@shows_blueprint.route("/show/")
def show():
    logger.info("Loading show details page")
    logger.debug(f"Shows: {settings.showList}")
    return render_template("show.html", show=None)
