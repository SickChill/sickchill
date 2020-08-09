from packaging import version as packaging_version

from sickchill import settings, version
from sickchill.oldbeard import helpers

from .abstract import UpdateManagerBase


class PipUpdateManager(UpdateManagerBase):
    def __init__(self):
        self._newest_version = ''
        self.session = helpers.make_session()
        self.branch = 'pip'

    def get_current_version(self):
        return packaging_version.parse(version.__version__)

    def get_current_commit_hash(self):
        return self.get_current_version()

    def get_newest_version(self):
        return packaging_version.parse(self.session.get(f'https://pypi.org/pypi/sickchill/json').json()['info']['version'])

    def get_newest_commit_hash(self):
        return self.get_newest_version()

    def get_num_commits_behind(self):
        if not self.need_update():
            return 0

        newest, current = self.get_newest_version(), self.get_current_version()
        return 'Major: {}, Minor: {}, Micro: {}'.format(newest.major - current.major, newest.minor - current.minor, newest.micro - current.micro)

    def list_remote_branches(self):
        return ['pip']

    def set_newest_text(self):
        if self.need_update():
            base_url = 'https://github.com/{}/{}'.format(settings.GIT_ORG, settings.GIT_REPO)
            if self.get_newest_commit_hash():
                url = '{}/compare{}...{}'.format(base_url, self.get_current_commit_hash().base_version, self.get_newest_commit_hash().base_version)
            else:
                url = '{}/commits/'.format(base_url)

            newest_tag = 'newer_version_available'
            newest_text = _('There is a <a href="{compare_url}" onclick="window.open(this.href); return false;">'
                            'newer version available</a> &mdash; <a href="{update_url}">Update Now</a>').format(
                compare_url=url, update_url=self.get_update_url())

        else:
            return

        helpers.add_site_message(newest_text, tag=newest_tag, level='success')

    def need_update(self):
        return self.get_newest_version() > self.get_current_version()

    def update(self):
        pass
