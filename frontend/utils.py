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

def build_blueprint(module_location: Path, module_import: str) -> Blueprint:
    """Generate a blueprint for a frontend module"""

    parent_path = Path(module_location).parent
    module_name = parent_path.name
    module_path = parent_path.resolve()
    frontend_path = module_path.parent.resolve()

    templates_path = module_path.joinpath("templates")
    static_path = frontend_path.joinpath("static", module_name)

    blueprint = Blueprint(module_name, module_import, static_folder=static_path, template_folder=templates_path)
    logger.debug(f"Blueprint name: {blueprint.name}")
    logger.debug(f"Templates path: {blueprint.template_folder}")
    logger.debug(f"Static path: {blueprint.static_folder}")
    logger.debug(f"URL prefix: {blueprint.url_prefix}")

    return blueprint
    return blueprint
