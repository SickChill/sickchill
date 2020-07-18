from abc import ABCMeta
import configobj

from sickbeard import logger


class ConfigMixin(metaclass=ABCMeta):
    __options: tuple
    __config: configobj.ConfigObj

    def config(self, key: str):
        if not self.options(key):
            raise Exception('Unsupported key attempted to be read for provider: {}, key: {}'.format(self.__name__, key))
        return self.__config.get(key)

    def set_config(self, key: str, value) -> None:
        if not self.options(key):
            logger.debug('Unsupported key attempted to be written for provider: {}, key: {}, value: {}'.format(self.__name__, key, value))
            return
        self.__config[key] = value

    def options(self, option):
        return option in self.__options
