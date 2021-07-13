import os
import shutil
import tarfile
import traceback
from pathlib import Path

from sickchill import logger, settings
from sickchill.oldbeard import helpers, notifiers

from .abstract import UpdateManagerBase


class SourceUpdateManager(UpdateManagerBase):
    def __init__(self):

        self.branch = settings.BRANCH
        if settings.BRANCH == "":
            self.branch = self._find_installed_branch()

        self._cur_commit_hash = settings.CUR_COMMIT_HASH
        self._newest_commit_hash = None
        self._num_commits_behind = 0

        self.session = helpers.make_session()

    @staticmethod
    def _find_installed_branch():
        return settings.CUR_COMMIT_BRANCH if settings.CUR_COMMIT_BRANCH else "master"

    def get_current_commit_hash(self):
        return self._cur_commit_hash

    def get_newest_commit_hash(self):
        return self._newest_commit_hash

    def get_current_version(self):
        return ""

    def get_newest_version(self):
        return ""

    def get_num_commits_behind(self):
        return self._num_commits_behind

    def need_update(self):
        # need this to run first to set self._newest_commit_hash
        try:
            self._check_github_for_update()
        except Exception as error:
            logger.warning(f"Unable to contact github, can't check for update: {error}")
            return False

        if self.branch != self._find_installed_branch():
            logger.debug(f"Branch checkout: {self._find_installed_branch()}->{self.branch}")
            return True

        if not self._cur_commit_hash or self._num_commits_behind > 0:
            return True

        return False

    def _check_github_for_update(self):
        """
        Uses pygithub to ask github if there is a newer version that the provided
        commit hash. If there is a newer version it sets SickChill's version text.

        commit_hash: hash that we're checking against
        """

        self._num_commits_behind = 0
        self._newest_commit_hash = None

        repo = settings.gh.get_organization(settings.GIT_ORG).get_repo(settings.GIT_REPO)
        # try to get newest commit hash and commits behind directly by comparing branch and current commit
        if self._cur_commit_hash:
            try:
                branch_compared = repo.compare(base=self.branch, head=self._cur_commit_hash)
                self._newest_commit_hash = branch_compared.base_commit.sha
                self._num_commits_behind = branch_compared.behind_by
            except Exception:  # UnknownObjectException
                self._newest_commit_hash = ""
                self._num_commits_behind = 0
                self._cur_commit_hash = ""

        # fall back and iterate over last 100 (items per page in gh_api) commits
        if not self._newest_commit_hash:

            for curCommit in repo.get_commits():
                if not self._newest_commit_hash:
                    self._newest_commit_hash = curCommit.sha
                    if not self._cur_commit_hash:
                        break

                if curCommit.sha == self._cur_commit_hash:
                    break

                # when _cur_commit_hash doesn't match anything _num_commits_behind == 100
                self._num_commits_behind += 1

        logger.debug(f"cur_commit = {self._cur_commit_hash}, newest_commit = {self._newest_commit_hash}, num_commits_behind = {self._num_commits_behind}")

    def set_newest_text(self):
        if not self._cur_commit_hash:
            logger.debug("Unknown current version number, don't know if we should update or not")

            update_url = self.get_update_url()
            newest_tag = "unknown_current_version"
            newest_text = _(
                f'Unknown current version number: If you\'ve never used the SickChill upgrade system before then current version is not set. &mdash; <a href="{update_url}">Update Now</a>'
            )

        elif self._num_commits_behind > 0:
            if self._newest_commit_hash:
                current = self._cur_commit_hash
                newest = self._newest_commit_hash
                url = f"https://github.com/{settings.GIT_ORG}/{settings.GIT_REPO}/compare/{current}...{newest}"
            else:
                url = f"https://github.com/{settings.GIT_ORG}/{settings.GIT_REPO}/commits/"

            newest_tag = "newer_version_available"
            commits_behind = self._num_commits_behind
            s = ("", "s")[commits_behind != 1]
            update_url = self.get_update_url()
            newest_text = _(
                f'There is a <a href="{url}" onclick="window.open(this.href); return false;">newer version available</a> (you\'re {commits_behind} commit{s} behind) &mdash; <a href="{update_url}">Update Now</a>'
            )
        else:
            return

        helpers.add_site_message(newest_text, tag=newest_tag, level="success")

    def update(self):
        """
        Downloads the latest source tarball from github and installs it over the existing version.
        """

        tar_download_url = f"https://github.com/{settings.GIT_ORG}/{settings.GIT_REPO}/tarball/{self.branch}"

        try:
            # prepare the update dir
            sc_update_dir = Path(settings.DATA_DIR) / "sc-update"

            if sc_update_dir.is_dir():
                logger.info(f"Clearing out update folder {sc_update_dir} before extracting")
                shutil.rmtree(sc_update_dir)

            logger.info(f"Creating update folder {sc_update_dir} before extracting")
            sc_update_dir.mkdir()

            # retrieve file
            logger.info(f"Downloading update from {tar_download_url}")
            tar_download_path = sc_update_dir / "sc-update.tar"
            helpers.download_file(tar_download_url, tar_download_path, session=self.session)

            if not tar_download_path.is_file():
                logger.warning(f"Unable to retrieve new version from {tar_download_url}, can't update")
                return False

            if not tarfile.is_tarfile(tar_download_path):
                logger.exception(f"Retrieved version from {tar_download_url} is corrupt, can't update")
                return False

            # extract to sc-update dir
            logger.info(f"Extracting file {tar_download_path}")
            tar = tarfile.open(tar_download_path)
            tar.extractall(sc_update_dir)
            tar.close()

            # delete .tar.gz
            logger.info(f"Deleting file {tar_download_path}")
            tar_download_path.unlink(True)

            # find update dir name
            update_dir_contents = [x for x in sc_update_dir.iterdir() if x.is_dir()]

            if len(update_dir_contents) != 1:
                logger.exception(f"Invalid update data, update failed: {str(update_dir_contents)}")
                return False

            # walk temp folder and move files to main folder
            content_dir = sc_update_dir / update_dir_contents[0]
            logger.info(f"Moving files from {content_dir} to {os.path.dirname(settings.PROG_DIR)}")

            for dirname, stderr_, filenames in os.walk(content_dir):
                dirname = dirname[len(content_dir) + 1 :]
                for curfile in filenames:
                    old_path = content_dir / dirname / curfile
                    new_path = os.path.join(os.path.dirname(settings.PROG_DIR), dirname, curfile)

                    if os.path.isfile(new_path):
                        os.remove(new_path)
                    os.renames(old_path, new_path)

            settings.CUR_COMMIT_HASH = self._newest_commit_hash
            settings.CUR_COMMIT_BRANCH = self.branch

        except Exception as error:
            logger.exception(f"Error while trying to update: {error}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return False

        # Notify update successful
        notifiers.notify_git_update(settings.CUR_COMMIT_HASH or "")
        return True

    def list_remote_branches(self):
        if not settings.gh:
            return []

        repo = settings.gh.get_organization(settings.GIT_ORG).get_repo(settings.GIT_REPO)
        return [x.name for x in repo.get_branches() if x]
