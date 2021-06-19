import platform
import re
import subprocess

from sickchill import logger, settings
from sickchill.oldbeard import helpers, notifiers

from .abstract import UpdateManagerBase


class GitUpdateManager(UpdateManagerBase):
    def __init__(self):
        self._git_path = self._find_working_git()

        self.branch = settings.BRANCH = self._find_installed_branch()

        self._check_detached_head()

        self._cur_commit_hash = None
        self._newest_commit_hash = None
        self._num_commits_behind = 0
        self._num_commits_ahead = 0

    def get_current_commit_hash(self):
        return self._cur_commit_hash

    def get_newest_commit_hash(self):
        return self._newest_commit_hash

    def get_current_version(self):
        return self._run_git(self._git_path, "describe --abbrev=0 {0}".format(self._cur_commit_hash))[0]

    def get_newest_version(self):
        if self._newest_commit_hash:
            return self._run_git(self._git_path, "describe --abbrev=0 " + self._newest_commit_hash)[0]
        else:
            return self._run_git(self._git_path, "describe --abbrev=0 " + self._cur_commit_hash)[0]

    def get_num_commits_behind(self):
        return self._num_commits_behind

    def _find_working_git(self):
        test_cmd = "version"

        if settings.GIT_PATH:
            main_git = '"' + settings.GIT_PATH + '"'
        else:
            main_git = "git"

        logger.debug("Checking if we can use git commands: " + main_git + " " + test_cmd)
        stdout_, stderr_, exit_status = self._run_git(main_git, test_cmd)

        if exit_status == 0:
            logger.debug("Using: " + main_git)
            return main_git
        else:
            logger.debug("Not using: " + main_git)

        # trying alternatives

        alternative_git = []

        # osx people who start sc from launchd have a broken path, so try a hail-mary attempt for them
        if platform.system() == "Darwin":
            alternative_git.append("/usr/local/git/bin/git")

        if platform.system() == "Windows":
            if main_git != main_git.lower():
                alternative_git.append(main_git.lower())

        if alternative_git:
            logger.debug("Trying known alternative git locations")

            for cur_git in alternative_git:
                logger.debug("Checking if we can use git commands: " + cur_git + " " + test_cmd)
                stdout_, stderr_, exit_status = self._run_git(cur_git, test_cmd)

                if exit_status == 0:
                    logger.debug("Using: " + cur_git)
                    return cur_git
                else:
                    logger.debug("Not using: " + cur_git)

        # Still haven't found a working git
        helpers.add_site_message(
            _(
                "Unable to find your git executable - Shutdown SickChill and EITHER set git_path in "
                "your config.ini OR delete your .git folder and run from source to enable updates."
            ),
            tag="unable_to_find_git",
        )
        return None

    @staticmethod
    def _run_git(git_path, args, log_errors=False):

        output = err = exit_status = None

        if not git_path:
            logger.warning("No git specified, can't use git commands")
            exit_status = 1
            return output, err, exit_status

        cmd = git_path + " " + args

        try:
            logger.debug("Executing {0} with your shell in {1}".format(cmd, settings.PROG_DIR))
            p = subprocess.Popen(
                cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, universal_newlines=True, cwd=settings.PROG_DIR
            )
            output, err = p.communicate()
            exit_status = p.returncode
            if output:
                output = output.strip()

        except OSError:
            logger.info("Command {} didn't work".format(cmd))
            exit_status = 1

        if exit_status == 0:
            logger.debug("{} : returned successful".format(cmd))

        elif exit_status == 1:
            if "stash" in output:
                logger.warning("Please enable 'git reset' in settings or stash your changes in local files")
            elif log_errors:
                logger.exception("{0} returned : {1}".format(cmd, output))

        elif log_errors:
            if exit_status in (127, 128) or "fatal:" in output:
                logger.warning("{0} returned : ({1}) {2}".format(cmd, exit_status, output or err))
            else:
                logger.exception("{0} returned code {1}, treating as error : {2}".format(cmd, exit_status, output or err))
                exit_status = 1

        return output, err, exit_status

    def _find_installed_version(self):
        """
        Attempts to find the currently installed version of SickChill.

        Uses git show to get commit version.

        Returns: True for success or False for failure
        """

        output, errors_, exit_status = self._run_git(self._git_path, "rev-parse HEAD")

        if exit_status == 0 and output:
            cur_commit_hash = output.strip()
            if not re.match("^[a-z0-9]+$", cur_commit_hash):
                logger.exception("Output doesn't look like a hash, not using it")
                return False
            self._cur_commit_hash = settings.CUR_COMMIT_HASH = cur_commit_hash
            return True
        else:
            return False

    def _find_installed_branch(self):
        branch_info, errors_, exit_status = self._run_git(self._git_path, "symbolic-ref -q HEAD")
        if exit_status == 0 and branch_info:
            branch = branch_info.strip().replace("refs/heads/", "", 1)
            if branch:
                settings.BRANCH = branch
                return branch
        return ""

    def _check_detached_head(self):
        # stdout, stderr_, exit_status = self._run_git(self._git_path, 'branch --show-current')
        # if exit_status == 0 and not stdout:
        if helpers.is_docker() and not self.branch:
            logger.info("We found you in a detached state that prevents updates. Fixing")
            self._run_git(self._git_path, "fetch origin")
            stdout_, stderr_, exit_status = self._run_git(self._git_path, "checkout -f master")
            if exit_status == 0:
                self.branch = settings.BRANCH = "master"

    def _check_github_for_update(self):
        """
        Uses git commands to check if there is a newer version that the provided
        commit hash. If there is a newer version it sets _num_commits_behind.
        """

        self._num_commits_behind = 0
        self._num_commits_ahead = 0

        # update remote origin url
        self._update_remote_origin()

        # get all new info from github
        output, errors_, exit_status = self._run_git(self._git_path, "fetch {0} --prune".format(settings.GIT_REMOTE))
        if exit_status != 0:
            logger.warning("Unable to contact github, can't check for update")
            return

        # Try both formats, but continue on fail because older git versions do not have this option
        output, stderr_, exit_status = self._run_git(self._git_path, "branch --set-upstream-to {0}/{1}".format(settings.GIT_REMOTE, self.branch))
        if exit_status != 0:
            self._run_git(self._git_path, "branch -u {0}/{1}".format(settings.GIT_REMOTE, self.branch))

        # get latest commit_hash from remote
        output, stderr_, exit_status = self._run_git(self._git_path, 'rev-parse --verify --quiet "@{upstream}"')

        if exit_status == 0 and output:
            cur_commit_hash = output.strip()

            if not re.match(r"^[a-z0-9]+$", cur_commit_hash):
                logger.debug("Output doesn't look like a hash, not using it")
                return

            else:
                self._newest_commit_hash = cur_commit_hash
        else:
            logger.debug("git didn't return newest commit hash")
            return

        # get number of commits behind and ahead (option --count not supported git < 1.7.2)
        output, stderr_, exit_status = self._run_git(self._git_path, 'rev-list --left-right "@{upstream}"...HEAD')
        if exit_status == 0 and output:

            try:
                self._num_commits_behind = int(output.count("<"))
                self._num_commits_ahead = int(output.count(">"))

            except Exception:
                logger.debug("git didn't return numbers for behind and ahead, not using it")
                return

        logger.debug(
            "cur_commit = {0}, newest_commit = {1}, num_commits_behind = {2}, num_commits_ahead = {3}".format(
                self._cur_commit_hash, self._newest_commit_hash, self._num_commits_behind, self._num_commits_ahead
            )
        )

    def set_newest_text(self):
        if self._num_commits_ahead:
            newest_tag = "local_branch_ahead"
            newest_text = "Local branch is ahead of {branch}. Automatic update not possible.".format(branch=self.branch)
            logger.warning(newest_text)

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
                'There is a <a href="{url}" onclick="window.open(this.href); return false;">newer version available</a> (you\'re {commits_behind} commit{s} behind) &mdash; <a href="{update_url}">Update Now</a>'.format(
                    commits_behind=commits_behind, update_url=update_url, url=url, s=s
                )
            )
        else:
            return

        helpers.add_site_message(newest_text, tag=newest_tag, level="success")

    def need_update(self):

        if self.branch != self._find_installed_branch():
            logger.debug("Branch checkout: " + self._find_installed_branch() + "->" + self.branch)
            return True

        self._find_installed_version()
        if not self._cur_commit_hash:
            return True
        else:
            import traceback

            try:
                self._check_github_for_update()
            except Exception as e:
                logger.debug(traceback.format_exc())
                logger.warning("Unable to contact github, can't check for update: " + repr(e))
                return False

            if self._num_commits_behind > 0:
                return True

        return False

    def update(self):
        """
        Calls git pull origin <branch> in order to update SickChill. Returns a bool depending
        on the call's success.
        """

        # update remote origin url
        self._update_remote_origin()

        # remove untracked files and performs a hard reset on git branch to avoid update issues
        if settings.GIT_RESET:
            # self._clean() # This is removing user data and backups
            self._reset()

        if self.branch == self._find_installed_branch():
            stdout_, stderr_, exit_status = self._run_git(self._git_path, "pull -f {0} {1}".format(settings.GIT_REMOTE, self.branch))
        else:
            stdout_, stderr_, exit_status = self._run_git(self._git_path, "checkout -f " + self.branch)

        if exit_status == 0:
            self._find_installed_version()

            # Notify update successful
            notifiers.notify_git_update(settings.CUR_COMMIT_HASH or "")
            return True
        else:
            return False

    def _clean(self):
        """
        Calls git clean to remove all untracked files. Returns a bool depending
        on the call's success.
        """
        stdout_, stderr_, exit_status = self._run_git(self._git_path, 'clean -df ""')
        if exit_status == 0:
            return True

    def _reset(self):
        """
        Calls git reset --hard to perform a hard reset. Returns a bool depending
        on the call's success.
        """
        stdout_, stderr_, exit_status = self._run_git(self._git_path, "reset --hard")
        if exit_status == 0:
            return True

    def list_remote_branches(self):
        # update remote origin url
        self._update_remote_origin()
        settings.BRANCH = self._find_installed_branch()

        branches, stderr_, exit_status = self._run_git(self._git_path, "ls-remote --heads {0}".format(settings.GIT_REMOTE))
        if exit_status == 0 and branches:
            if branches:
                return re.findall(r"refs/heads/(.*)", branches)
        return []

    def _update_remote_origin(self):
        if not settings.DEVELOPER:
            self._run_git(self._git_path, "config remote.{0}.url {1}".format(settings.GIT_REMOTE, settings.GIT_REMOTE_URL))
