from pathlib import Path
from flask import Blueprint
import logging

logging.basicConfig(format="{asctime} {levelname} :: {threadName} :: {message}", style="{")
logger = logging.getLogger(__package__)
logger.setLevel(logging.DEBUG)


def build_blueprint(module_location: Path, module_import: str) -> Blueprint:
    """Generate a blueprint for a frontend module"""

    module_name = Path(module_location).parent.name
    module_path = Path(module_location).parent.resolve()
    frontend_path = module_path.parent.resolve()

    templates_path = module_path.joinpath("templates")
    static_path = frontend_path.joinpath("static").joinpath(module_name)

    blueprint = Blueprint(module_name, module_import, static_folder=static_path, template_folder=templates_path)
    logger.debug(
        f"Paths for {blueprint.name}\n\ttemplates: {blueprint.template_folder}\n\tstatic: {blueprint.static_folder}\n\turl_prefix: {blueprint.url_prefix}"
    )
    return blueprint
