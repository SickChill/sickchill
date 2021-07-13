from sickchill.init_helpers import maybe_daemonize, poetry_install

maybe_daemonize()
poetry_install()

from .show.indexers import indexer, ShowIndexer
