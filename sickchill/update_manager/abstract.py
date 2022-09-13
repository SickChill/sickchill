from abc import ABC

from sickchill import settings


class UpdateManagerBase(ABC):
    @staticmethod
    def get_update_url():
        return f"{settings.WEB_ROOT}/home/update/?pid={settings.PID}"

    def get_current_version(self):
        raise NotImplementedError

    def get_newest_version(self):
        raise NotImplementedError

    def get_version_delta(self):
        raise NotImplementedError

    def set_newest_text(self):
        raise NotImplementedError

    def need_update(self):
        raise NotImplementedError

    def update(self):
        raise NotImplementedError
