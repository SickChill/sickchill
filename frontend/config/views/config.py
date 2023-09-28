from flask import render_template

from sickchill import logger, settings

from .. import config_blueprint


@config_blueprint.route("/")
def config():
    logger.info("Loading config page")
    return render_template("/config.html")
