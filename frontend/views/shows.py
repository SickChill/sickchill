from flask import Blueprint, render_template

from sickchill import logger, settings

# from sickchill.tv import TVEpisode, TVShow

shows_blueprint = Blueprint("shows", __name__)


@shows_blueprint.route("/")
@shows_blueprint.route("/shows")
def index():
    logger.info("Loading shows page")
    logger.debug(f"Shows: {settings.showList}")
    return render_template("shows.html", shows=settings.showList)
