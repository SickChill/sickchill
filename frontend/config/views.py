from flask import Blueprint, render_template

from sickchill import logger, settings

blueprint = Blueprint("config", __name__, template_folder="templates", static_folder="static", url_prefix="/config")


@blueprint.route("/")
def config():
    logger.info("Loading config page")
    return render_template("config.html")
