from ._fixtures import _GenericBackendTest


class MemoryBackendTest(_GenericBackendTest):
    backend = "dogpile.cache.memory"


class MemoryPickleBackendTest(_GenericBackendTest):
    backend = "dogpile.cache.memory_pickle"
