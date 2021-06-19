from sickchill.init_helpers import poetry_install

poetry_install()

from .show.indexers import indexer, ShowIndexer
