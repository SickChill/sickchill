import importlib
import pkgutil

import sickchill.extensions
from sickchill import logger, settings
from sickchill.oldbeard import config


def iter_namespace(ns_pkg):
    return pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + ".")


def discover():
    global extenstions
    extensions = {}
    for finder, name, ispkg in iter_namespace(sickchill.extensions):
        if name == __name__:
            continue
        try:
            plugin = importlib.import_module(name)
            extensions[name] = plugin
        except Exception as e:
            logger.debug("Error importing extension: {0}".format(name), exc_info=e)

    config.check_section(settings.CFG, "extensions")
    for extension in extensions:
        logger.debug("Loading {extension} from {path}".format(extension=extension, path=extensions[extension].__path__))
        config.check_section(settings.CFG["extensions"], extension.name)

    global clients, providers, metadata, notifiers, indexers, post_processors

    # Clients
    clients = {extension.name: extension for name, extension in extensions.items() if hasattr(extension, "Client")}

    # Providers
    providers = {extension.name: extension for name, extension in extensions.items() if hasattr(extension, "Provider")}

    # Metadata
    metadata = {extension.name: extension for name, extension in extensions.items() if hasattr(extension, "Metadata")}

    # Notifiers
    notifiers = {extension.name: extension for name, extension in extensions.items() if hasattr(extension, "Notifier")}

    # TVDB, TVMAZE, TMDB, etc
    indexers = {extension.name: extension for name, extension in extensions.items() if hasattr(extension, "Indexer")}

    # Post Processors
    post_processors = {extension.name: extension for name, extension in extensions.items() if hasattr(extension, "PostProcessor")}
