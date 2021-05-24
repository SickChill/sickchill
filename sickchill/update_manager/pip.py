from packaging import version as packaging_version

from sickchill import settings, version
from sickchill.oldbeard import helpers

from .abstract import UpdateManagerBase


class PipUpdateManager(UpdateManagerBase):
    def __init__(self):
        self._newest_version = ""
        self.session = helpers.make_session()
        self.branch = "pip"

    def get_current_version(self):
        return packaging_version.parse(version.__version__)

    def get_clean_version(self, use_version: packaging_version.Version = None):
        _version = use_version or self.get_current_version()
        result = f"v{_version.major:04d}.{_version.minor:02d}.{_version.micro:02}"
        if _version.is_postrelease:
            result += f"-{_version.post}"

        return result

    def get_current_commit_hash(self):
        return self.get_current_version()

    def get_newest_version(self):
        return packaging_version.parse(self.session.get("https://pypi.org/pypi/sickchill/json").json()["info"]["version"])

    def get_newest_commit_hash(self):
        return self.get_newest_version()

    def get_num_commits_behind(self):
        if not self.need_update():
            return 0

        newest, current = self.get_newest_version(), self.get_current_version()
        return f"Major: {newest.major - current.major}, Minor: {newest.minor - current.minor}, Micro: {newest.micro - current.micro}"

    def list_remote_branches(self):
        return ["pip"]

    def set_newest_text(self):
        if self.need_update():
            if self.get_newest_commit_hash():
                current = self.get_clean_version()
                newest = self.get_clean_version(self.get_newest_commit_hash())
                url = f"https://github.com/{settings.GIT_ORG}/{settings.GIT_REPO}/compare/{current}...{newest}"
            else:
                url = f"https://github.com/{settings.GIT_ORG}/{settings.GIT_REPO}/commits/"

            newest_tag = "newer_version_available"
            update_url = self.get_update_url()
            newest_text = _(
                'There is a <a href="{url}" onclick="window.open(this.href); return false;">newer version available</a> &mdash; <a href="{update_url}">Update Now</a>'.format(
                    url=url, update_url=update_url
                )
            )

        else:
            return

        helpers.add_site_message(newest_text, tag=newest_tag, level="success")

    def need_update(self):
        return self.get_newest_version() > self.get_current_version()

    def get_update_url(self):
        return self.session.get("https://pypi.org/pypi/sickchill/json").json()["info"]["release_url"]

    def update(self):
        pass
