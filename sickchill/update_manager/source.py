import os
import shutil
import tarfile
import traceback

from sickchill import logger, settings
from sickchill.oldbeard import helpers, notifiers

from .abstract import UpdateManagerBase


class SourceUpdateManager(UpdateManagerBase):
    def __init__(self):

        self.branch = settings.BRANCH
        if settings.BRANCH == '':
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
        except Exception as e:
            logger.warning("Unable to contact github, can't check for update: " + repr(e))
            return False

        if self.branch != self._find_installed_branch():
            logger.debug("Branch checkout: " + self._find_installed_branch() + "->" + self.branch)
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

        logger.debug("cur_commit = {0}, newest_commit = {1}, num_commits_behind = {2}".format
                     (self._cur_commit_hash, self._newest_commit_hash, self._num_commits_behind))

    def set_newest_text(self):
        if not self._cur_commit_hash:
            logger.debug("Unknown current version number, don't know if we should update or not")

            update_url = self.get_update_url()
            newest_tag = 'unknown_current_version'
            newest_text = _('Unknown current version number: If you\'ve never used the SickChill upgrade system before then current version is not set. '
                            f'&mdash; <a href="{update_url}">Update Now</a>')

        elif self._num_commits_behind > 0:
            if self._newest_commit_hash:
                current = self._cur_commit_hash
                newest = self._newest_commit_hash
                url = f'https://github.com/{settings.GIT_ORG}/{settings.GIT_REPO}/compare{current}...{newest}'
            else:
                url = f'https://github.com/{settings.GIT_ORG}/{settings.GIT_REPO}/commits/'

            newest_tag = 'newer_version_available'
            commits_behind = self._num_commits_behind
            s = ('', 's')[commits_behind != 1]
            update_url = self.get_update_url()
            newest_text = _(f'There is a <a href="{url}" onclick="window.open(this.href); return false;">'
                            f'newer version available</a> (you\'re {commits_behind} commit{s} behind) &mdash; <a href="{update_url}">Update Now</a>')
        else:
            return

        helpers.add_site_message(newest_text, tag=newest_tag, level='success')

    def update(self):
        """
        Downloads the latest source tarball from github and installs it over the existing version.
        """

        tar_download_url = 'https://github.com/' + settings.GIT_ORG + '/' + settings.GIT_REPO + '/tarball/' + self.branch

        try:
            # prepare the update dir
            sr_update_dir = os.path.join(settings.DATA_DIR, 'sr-update')

            if os.path.isdir(sr_update_dir):
                logger.info("Clearing out update folder " + sr_update_dir + " before extracting")
                shutil.rmtree(sr_update_dir)

            logger.info("Creating update folder " + sr_update_dir + " before extracting")
            os.makedirs(sr_update_dir)

            # retrieve file
            logger.info("Downloading update from {url}".format(url=tar_download_url))
            tar_download_path = os.path.join(sr_update_dir, 'sr-update.tar')
            helpers.download_file(tar_download_url, tar_download_path, session=self.session)

            if not os.path.isfile(tar_download_path):
                logger.warning("Unable to retrieve new version from " + tar_download_url + ", can't update")
                return False

            if not tarfile.is_tarfile(tar_download_path):
                logger.exception("Retrieved version from " + tar_download_url + " is corrupt, can't update")
                return False

            # extract to sr-update dir
            logger.info("Extracting file " + tar_download_path)
            tar = tarfile.open(tar_download_path)
            tar.extractall(sr_update_dir)
            tar.close()

            # delete .tar.gz
            logger.info("Deleting file " + tar_download_path)
            os.remove(tar_download_path)

            # find update dir name
            update_dir_contents = [x for x in os.listdir(sr_update_dir) if
                                   os.path.isdir(os.path.join(sr_update_dir, x))]

            if len(update_dir_contents) != 1:
                logger.exception("Invalid update data, update failed: " + str(update_dir_contents))
                return False

            # walk temp folder and move files to main folder
            content_dir = os.path.join(sr_update_dir, update_dir_contents[0])
            logger.info("Moving files from " + content_dir + " to " + os.path.dirname(settings.PROG_DIR))
            for dirname, stderr_, filenames in os.walk(content_dir):
                dirname = dirname[len(content_dir) + 1:]
                for curfile in filenames:
                    old_path = os.path.join(content_dir, dirname, curfile)
                    new_path = os.path.join(os.path.dirname(settings.PROG_DIR), dirname, curfile)

                    if os.path.isfile(new_path):
                        os.remove(new_path)
                    os.renames(old_path, new_path)

            settings.CUR_COMMIT_HASH = self._newest_commit_hash
            settings.CUR_COMMIT_BRANCH = self.branch

        except Exception as error:
            logger.exception("Error while trying to update: {}".format(error))
            logger.debug("Traceback: {}".format(traceback.format_exc()))
            return False

        self._clean_libs()

        # Notify update successful
        notifiers.notify_git_update(settings.CUR_COMMIT_HASH or "")
        return True

    def _clean_libs(self):
        lib_path = os.path.join(os.path.dirname(settings.PROG_DIR), 'lib3')

        def remove_empty_folders(path):
            if not os.path.isdir(path):
                return

            files = os.listdir(path)
            for f in files:
                full_path = os.path.join(path, f)
                if os.path.isdir(full_path):
                    remove_empty_folders(full_path)

            files = os.listdir(path)
            if len(files) == 0 and path != lib_path:
                os.rmdir(path)

        self._clean_pyc('lib3')
        remove_empty_folders(lib_path)

    def list_remote_branches(self):
        if not settings.gh:
            return []

        repo = settings.gh.get_organization(settings.GIT_ORG).get_repo(settings.GIT_REPO)
        return [x.name for x in repo.get_branches() if x]
