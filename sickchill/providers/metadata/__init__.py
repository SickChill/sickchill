import sys

from . import generic, helpers, kodi, mede8er, mediabrowser, ps3, tivo, wdtv

__all__ = ["generic", "helpers", "kodi", "mede8er", "mediabrowser", "ps3", "tivo", "wdtv"]


def available_generators():
    return [x for x in __all__ if x not in ["generic", "helpers"]]


def _getMetadataModule(name):
    name = name.lower()
    prefix = "sickchill.providers.metadata."
    if name in available_generators() and prefix + name in sys.modules:
        return sys.modules[prefix + name]
    else:
        return None


def _getMetadataClass(name):
    module = _getMetadataModule(name)
    if not module:
        return None

    # noinspection PyUnresolvedReferences
    return module.metadata_class()


def get_metadata_generator_dict():
    result = {}
    for cur_generator_id in available_generators():
        cur_generator = _getMetadataClass(cur_generator_id)
        if not cur_generator:
            continue
        result[cur_generator.name] = cur_generator

    return result
