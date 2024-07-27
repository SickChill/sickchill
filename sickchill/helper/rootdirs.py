from pathlib import Path
from typing import Union

from sickchill import logger, settings


class RootDirectories:
    def __init__(self, root_directories_string: str = "", root_directories_list: Union[list, None] = None) -> None:
        self.default_root_index: Union[int, None] = None
        self.root_directories: list = []

        self.parse(root_directories_string or settings.ROOT_DIRS, root_directories_list)
        logger.debug(f"parsed roots: {[str(directory) for directory in self]} from {settings.ROOT_DIRS}")
        if self.default:
            logger.debug(f"default root directory: {self[self.default]}")
        else:
            logger.debug("no default root directory set")

    def parse(self, root_directories_string: str = "", root_directories_list: Union[list, None] = None) -> None:
        split_setting = root_directories_list or root_directories_string.split("|")

        if len(split_setting) < 2:
            return

        self.default_root_index = int(split_setting[0])
        for root_directory in split_setting[1:]:
            self.add(root_directory)

    def add(self, root_directory: Union[str, Path]) -> bool:
        root_directory = Path(root_directory).resolve()
        if not root_directory.is_dir():
            logger.debug(f"tried to add a non-existent root directory: {root_directory}")
            return False

        if root_directory in self.root_directories:
            logger.debug(f"tried to add a root directory that is already added: {root_directory}")
            return False

        logger.debug(f"adding root directory {root_directory}")
        self.root_directories.append(root_directory)

        self.__check_default_index()

        return True

    def delete(self, root_directory: Union[str, Path]) -> bool:
        root_directory = Path(root_directory)
        if root_directory in self.root_directories:
            self.root_directories.remove(root_directory)
            self.__check_default_index()
            return True
        return False

    @property
    def default(self) -> int:
        return self.default_root_index

    @default.setter
    def default(self, value: Union[int, str]) -> None:
        value = int(value)
        self.default_root_index = value
        self.__check_default_index()

    def info(self) -> list:
        output = []
        for root_dir in self:
            output.append({"valid": root_dir.is_dir(), "location": str(root_dir), "default": int(root_dir is self[self.default])})

        return output or {}

    def __check_default_index(self):
        if not self.root_directories:
            self.default_root_index = None
            return

        if not self.default_root_index or self.default_root_index > len(self.root_directories):
            self.default_root_index = 1

    def __str__(self) -> str:
        return "|".join(f"{item}" for item in [self.default_root_index] + self.root_directories)

    def __getitem__(self, item: int) -> Path:
        return self.root_directories[item - 1]

    def __setitem__(self, index: int, value: Path):
        self.root_directories[index - 1] = value
        self.__check_default_index()

    def __delitem__(self, key):
        self.root_directories.pop(key - 1)
        self.__check_default_index()

    def __contains__(self, item):
        return item in self.root_directories

    def __iter__(self):
        for item in self.root_directories:
            yield item

    def __len__(self):
        return len(self.root_directories)
