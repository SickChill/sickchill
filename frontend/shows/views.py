from flask import Blueprint, render_template

from sickchill import logger, settings

blueprint = Blueprint("shows", __name__, template_folder="templates", static_folder="static", url_prefix="/shows")

# from sickchill.tv import TVEpisode, TVShow


@blueprint.route("/")
def shows():
    logger.info("Loading shows page")
    logger.debug(f"Shows: {settings.showList}")
    return render_template("shows.html", shows=settings.showList)


@blueprint.route("/show/")
def show():
    logger.info("Loading show details page")
    logger.debug(f"Shows: {settings.showList}")
    return render_template("show.html", show=None)
