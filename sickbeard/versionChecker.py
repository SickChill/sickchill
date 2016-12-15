# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

import datetime
import os
import platform
import re
import shutil
import stat
import subprocess
import tarfile
import time
import traceback

import sickbeard
from sickbeard import db, helpers, logger, notifiers, ui
from sickrage.helper.encoding import ek
from sickrage.helper.exceptions import ex


class CheckVersion(object):
    """
    Version check class meant to run as a thread object with the sr scheduler.
    """

    def __init__(self):
        self.updater = None
        self.install_type = None
        self.amActive = False
        if sickbeard.gh:
            self.install_type = self.find_install_type()
            if self.install_type == 'git':
                self.updater = GitUpdateManager()
            elif self.install_type == 'source':
                self.updater = SourceUpdateManager()

        self.session = helpers.make_session()

    def run(self, force=False):

        self.amActive = True

        if self.updater:
            # set current branch version
            sickbeard.BRANCH = self.get_branch()

            if self.check_for_new_version(force):
                if sickbeard.AUTO_UPDATE:
                    logger.log(u"New update found for SickRage, starting auto-updater ...")
                    ui.notifications.message(_('New update found for SickRage, starting auto-updater'))
                    if self.run_backup_if_safe():
                        if sickbeard.versionCheckScheduler.action.update():
                            logger.log(u"Update was successful!")
                            ui.notifications.message(_('Update was successful'))
                            sickbeard.events.put(sickbeard.events.SystemEvent.RESTART)
                        else:
                            logger.log(u"Update failed!")
                            ui.notifications.message(_('Update failed!'))

            self.check_for_new_news()

        self.amActive = False

    def run_backup_if_safe(self):
        return self.safe_to_update() is True and self._runbackup() is True

    def _runbackup(self):
        # Do a system backup before update
        logger.log(u"Config backup in progress...")
        ui.notifications.message(_('Backup'), _('Config backup in progress...'))
        try:
            backupDir = ek(os.path.join, sickbeard.DATA_DIR, 'backup')
            if not ek(os.path.isdir, backupDir):
                ek(os.mkdir, backupDir)

            if self._keeplatestbackup(backupDir) and self._backup(backupDir):
                logger.log(u"Config backup successful, updating...")
                ui.notifications.message(_('Backup'), _('Config backup successful, updating...'))
                return True
            else:
                logger.log(u"Config backup failed, aborting update", logger.ERROR)
                ui.notifications.message(_('Backup'), _('Config backup failed, aborting update'))
                return False
        except Exception as e:
            logger.log(u'Update: Config backup failed. Error: {0}'.format(ex(e)), logger.ERROR)
            ui.notifications.message(_('Backup'), _('Config backup failed, aborting update'))
            return False

    @staticmethod
    def _keeplatestbackup(backupDir=None):
        if not backupDir:
            return False

        from sickrage.helper import glob
        files = glob.glob(ek(os.path.join, glob.escape(backupDir), '*.zip'))
        if not files:
            return True

        now = time.time()
        newest = files[0], now - ek(os.path.getctime, files[0])
        for f in files[1:]:
            age = now - ek(os.path.getctime, f)
            if age < newest[1]:
                newest = f, age
        files.remove(newest[0])

        for f in files:
            ek(os.remove, f)

        return True

    @staticmethod
    def _backup(backupDir=None):
        if not backupDir:
            return False
        source = [
            ek(os.path.join, sickbeard.DATA_DIR, 'sickbeard.db'),
            sickbeard.CONFIG_FILE,
            ek(os.path.join, sickbeard.DATA_DIR, 'failed.db'),
            ek(os.path.join, sickbeard.DATA_DIR, 'cache.db')
        ]
        target = ek(os.path.join, backupDir, 'sickrage-' + time.strftime('%Y%m%d%H%M%S') + '.zip')

        for (path, dirs, files) in ek(os.walk, sickbeard.CACHE_DIR, topdown=True):
            for dirname in dirs:
                if path == sickbeard.CACHE_DIR and dirname not in ['images']:
                    dirs.remove(dirname)
            for filename in files:
                source.append(ek(os.path.join, path, filename))

        return helpers.backupConfigZip(source, target, sickbeard.DATA_DIR)

    def safe_to_update(self):

        def db_safe(self):
            message = {
                'equal': {
                    'type': logger.DEBUG,
                    'text': u"We can proceed with the update. New update has same DB version"},
                'upgrade': {
                    'type': logger.WARNING,
                    'text': u"We can't proceed with the update. New update has a new DB version. Please manually update"},
                'downgrade': {
                    'type': logger.ERROR,
                    'text': u"We can't proceed with the update. New update has a old DB version. It's not possible to downgrade"},
            }
            try:
                result = self.getDBcompare()
                if result in message:
                    logger.log(message[result]['text'], message[result]['type'])  # unpack the result message into a log entry
                else:
                    logger.log(u"We can't proceed with the update. Unable to check remote DB version. Error: {0}".format(result), logger.ERROR)
                return result in ['equal']  # add future True results to the list
            except Exception as error:
                logger.log(u"We can't proceed with the update. Unable to compare DB version. Error: {0}".format(repr(error)), logger.ERROR)
                return False

        def postprocessor_safe():
            if not sickbeard.autoPostProcesserScheduler.action.amActive:
                logger.log(u"We can proceed with the update. Post-Processor is not running", logger.DEBUG)
                return True
            else:
                logger.log(u"We can't proceed with the update. Post-Processor is running", logger.DEBUG)
                return False

        def showupdate_safe():
            if not sickbeard.showUpdateScheduler.action.amActive:
                logger.log(u"We can proceed with the update. Shows are not being updated", logger.DEBUG)
                return True
            else:
                logger.log(u"We can't proceed with the update. Shows are being updated", logger.DEBUG)
                return False

        db_safe = db_safe(self)
        postprocessor_safe = postprocessor_safe()
        showupdate_safe = showupdate_safe()

        if db_safe and postprocessor_safe and showupdate_safe:
            logger.log(u"Proceeding with auto update", logger.DEBUG)
            return True
        else:
            logger.log(u"Auto update aborted", logger.DEBUG)
            return False

    def getDBcompare(self):
        try:
            self.updater.need_update()
            cur_hash = str(self.updater.get_newest_commit_hash())
            assert len(cur_hash) == 40, "Commit hash wrong length: {0} hash: {1}".format(len(cur_hash), cur_hash)

            check_url = "http://cdn.rawgit.com/{0}/{1}/{2}/sickbeard/databases/mainDB.py".format(sickbeard.GIT_ORG, sickbeard.GIT_REPO, cur_hash)
            response = helpers.getURL(check_url, session=self.session, returns='text')
            assert response, "Empty response from {0}".format(check_url)

            match = re.search(r"MAX_DB_VERSION\s=\s(?P<version>\d{2,3})", response)
            branchDestDBversion = int(match.group('version'))
            main_db_con = db.DBConnection()
            branchCurrDBversion = main_db_con.checkDBVersion()
            if branchDestDBversion > branchCurrDBversion:
                return 'upgrade'
            elif branchDestDBversion == branchCurrDBversion:
                return 'equal'
            else:
                return 'downgrade'
        except Exception as e:
            return repr(e)

    @staticmethod
    def find_install_type():
        """
        Determines how this copy of sr was installed.

        returns: type of installation. Possible values are:
            'win': any compiled windows build
            'git': running from source using git
            'source': running from source without git
        """

        # check if we're a windows build
        if sickbeard.BRANCH.startswith('build '):
            install_type = 'win'
        elif ek(os.path.isdir, ek(os.path.join, sickbeard.PROG_DIR, u'.git')):
            install_type = 'git'
        else:
            install_type = 'source'

        return install_type

    def check_for_new_version(self, force=False):
        """
        Checks the internet for a newer version.

        returns: bool, True for new version or False for no new version.

        force: if true the VERSION_NOTIFY setting will be ignored and a check will be forced
        """

        if not self.updater or (not sickbeard.VERSION_NOTIFY and not sickbeard.AUTO_UPDATE and not force):
            logger.log(u"Version checking is disabled, not checking for the newest version")
            return False

        # checking for updates
        if not sickbeard.AUTO_UPDATE:
            logger.log(u"Checking for updates using " + self.install_type.upper())

        if not self.updater.need_update():
            sickbeard.NEWEST_VERSION_STRING = None

            if force:
                ui.notifications.message(_('No update needed'))
                logger.log(u"No update needed")

            # no updates needed
            return False

        # found updates
        self.updater.set_newest_text()
        return True

    def check_for_new_news(self):
        """
        Checks GitHub for the latest news.

        returns: unicode, a copy of the news

        force: ignored
        """

        # Grab a copy of the news
        logger.log(u'check_for_new_news: Checking GitHub for latest news.', logger.DEBUG)
        try:
            news = helpers.getURL(sickbeard.NEWS_URL, session=self.session, returns='text')
        except Exception:
            logger.log(u'check_for_new_news: Could not load news from repo.', logger.WARNING)
            news = ''

        if not news:
            return ''

        try:
            last_read = datetime.datetime.strptime(sickbeard.NEWS_LAST_READ, '%Y-%m-%d')
        except Exception:
            last_read = 0

        sickbeard.NEWS_UNREAD = 0
        gotLatest = False
        for match in re.finditer(r'^####\s*(\d{4}-\d{2}-\d{2})\s*####', news, re.M):
            if not gotLatest:
                gotLatest = True
                sickbeard.NEWS_LATEST = match.group(1)

            try:
                if datetime.datetime.strptime(match.group(1), '%Y-%m-%d') > last_read:
                    sickbeard.NEWS_UNREAD += 1
            except Exception:
                pass

        return news

    def update(self):
        if self.updater:
            # update branch with current config branch value
            self.updater.branch = sickbeard.BRANCH

            # check for updates
            if self.updater.need_update():
                return self.updater.update()

    def list_remote_branches(self):
        if self.updater:
            return self.updater.list_remote_branches()

    def get_branch(self):
        if self.updater:
            return self.updater.branch


class UpdateManager(object):  # pylint: disable=too-few-public-methods
    @staticmethod
    def get_update_url():
        return sickbeard.WEB_ROOT + "/home/update/?pid=" + str(sickbeard.PID)


class GitUpdateManager(UpdateManager):
    def __init__(self):
        self._git_path = self._find_working_git()

        self.branch = sickbeard.BRANCH = self._find_installed_branch()

        self._cur_commit_hash = None
        self._newest_commit_hash = None
        self._num_commits_behind = 0
        self._num_commits_ahead = 0

    def get_cur_commit_hash(self):
        return self._cur_commit_hash

    def get_newest_commit_hash(self):
        return self._newest_commit_hash

    def get_cur_version(self):
        return self._run_git(self._git_path, 'describe --abbrev=0 {0}'.format(self._cur_commit_hash))[0]

    def get_newest_version(self):
        if self._newest_commit_hash:
            return self._run_git(self._git_path, "describe --abbrev=0 " + self._newest_commit_hash)[0]
        else:
            return self._run_git(self._git_path, "describe --abbrev=0 " + self._cur_commit_hash)[0]

    def get_num_commits_behind(self):
        return self._num_commits_behind

    @staticmethod
    def _git_error():
        error_message = 'Unable to find your git executable - Shutdown SickRage and EITHER set git_path in your config.ini OR delete your .git folder and run from source to enable updates.'
        sickbeard.NEWEST_VERSION_STRING = error_message

    def _find_working_git(self):
        test_cmd = 'version'

        if sickbeard.GIT_PATH:
            main_git = '"' + sickbeard.GIT_PATH + '"'
        else:
            main_git = 'git'

        logger.log(u"Checking if we can use git commands: " + main_git + ' ' + test_cmd, logger.DEBUG)
        stdout_, stderr_, exit_status = self._run_git(main_git, test_cmd)

        if exit_status == 0:
            logger.log(u"Using: " + main_git, logger.DEBUG)
            return main_git
        else:
            logger.log(u"Not using: " + main_git, logger.DEBUG)

        # trying alternatives

        alternative_git = []

        # osx people who start sr from launchd have a broken path, so try a hail-mary attempt for them
        if platform.system().lower() == 'darwin':
            alternative_git.append('/usr/local/git/bin/git')

        if platform.system().lower() == 'windows':
            if main_git != main_git.lower():
                alternative_git.append(main_git.lower())

        if alternative_git:
            logger.log(u"Trying known alternative git locations", logger.DEBUG)

            for cur_git in alternative_git:
                logger.log(u"Checking if we can use git commands: " + cur_git + ' ' + test_cmd, logger.DEBUG)
                stdout_, stderr_, exit_status = self._run_git(cur_git, test_cmd)

                if exit_status == 0:
                    logger.log(u"Using: " + cur_git, logger.DEBUG)
                    return cur_git
                else:
                    logger.log(u"Not using: " + cur_git, logger.DEBUG)

        # Still haven't found a working git
        error_message = 'Unable to find your git executable - Shutdown SickRage and EITHER set git_path in your config.ini OR delete your .git folder and run from source to enable updates.'
        sickbeard.NEWEST_VERSION_STRING = error_message

        return None

    @staticmethod
    def _run_git(git_path, args, log_errors=True):

        output = err = exit_status = None

        if not git_path:
            logger.log(u"No git specified, can't use git commands", logger.WARNING)
            exit_status = 1
            return output, err, exit_status

        cmd = git_path + ' ' + args

        try:
            logger.log(u"Executing " + cmd + " with your shell in " + sickbeard.PROG_DIR, logger.DEBUG)
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 shell=True, cwd=sickbeard.PROG_DIR)
            output, err = p.communicate()
            exit_status = p.returncode

            if output:
                output = output.strip()

        except OSError:
            logger.log(u"Command " + cmd + " didn't work")
            exit_status = 1

        if exit_status == 0:
            logger.log(cmd + u" : returned successful", logger.DEBUG)
            exit_status = 0

        elif exit_status == 1:
            if 'stash' in output:
                logger.log(u"Please enable 'git reset' in settings or stash your changes in local files", logger.WARNING)
            elif log_errors:
                logger.log(cmd + u" returned : " + str(output), logger.ERROR)
            exit_status = 1

        elif log_errors and exit_status == 128 or 'fatal:' in output or err:
            logger.log(cmd + u" returned : " + str(output), logger.WARNING)
            exit_status = 128

        elif log_errors:
            logger.log(cmd + u" returned : " + str(output) + u", treat as error for now", logger.ERROR)
            exit_status = 1

        return output, err, exit_status

    def _find_installed_version(self):
        """
        Attempts to find the currently installed version of SickRage.

        Uses git show to get commit version.

        Returns: True for success or False for failure
        """

        output, errors_, exit_status = self._run_git(self._git_path, 'rev-parse HEAD')  # @UnusedVariable

        if exit_status == 0 and output:
            cur_commit_hash = output.strip()
            if not re.match('^[a-z0-9]+$', cur_commit_hash):
                logger.log(u"Output doesn't look like a hash, not using it", logger.ERROR)
                return False
            self._cur_commit_hash = cur_commit_hash
            sickbeard.CUR_COMMIT_HASH = str(cur_commit_hash)
            return True
        else:
            return False

    def _find_installed_branch(self):
        branch_info, errors_, exit_status = self._run_git(self._git_path, 'symbolic-ref -q HEAD')  # @UnusedVariable
        if exit_status == 0 and branch_info:
            branch = branch_info.strip().replace('refs/heads/', '', 1)
            if branch:
                sickbeard.BRANCH = branch
                return branch
        return ""

    def _check_github_for_update(self):
        """
        Uses git commands to check if there is a newer version that the provided
        commit hash. If there is a newer version it sets _num_commits_behind.
        """

        self._num_commits_behind = 0
        self._num_commits_ahead = 0

        # update remote origin url
        self.update_remote_origin()

        # get all new info from github
        output, errors_, exit_status = self._run_git(self._git_path, 'fetch {0}'.format(sickbeard.GIT_REMOTE))
        if exit_status != 0:
            logger.log(u"Unable to contact github, can't check for update", logger.WARNING)
            return

        # Try both formats, but continue on fail because older git versions do not have this option
        output, stderr_, exit_status = self._run_git(self._git_path, 'branch --set-upstream-to {0}/{1}'.format(sickbeard.GIT_REMOTE, self.branch), False)
        if exit_status != 0:
            self._run_git(self._git_path, 'branch -u {0}/{1}'.format(sickbeard.GIT_REMOTE, self.branch), False)

        # get latest commit_hash from remote
        output, stderr_, exit_status = self._run_git(self._git_path, 'rev-parse --verify --quiet "@{upstream}"')

        if exit_status == 0 and output:
            cur_commit_hash = output.strip()

            if not re.match('^[a-z0-9]+$', cur_commit_hash):
                logger.log(u"Output doesn't look like a hash, not using it", logger.DEBUG)
                return

            else:
                self._newest_commit_hash = cur_commit_hash
        else:
            logger.log(u"git didn't return newest commit hash", logger.DEBUG)
            return

        # get number of commits behind and ahead (option --count not supported git < 1.7.2)
        output, stderr_, exit_status = self._run_git(self._git_path, 'rev-list --left-right "@{upstream}"...HEAD')
        if exit_status == 0 and output:

            try:
                self._num_commits_behind = int(output.count("<"))
                self._num_commits_ahead = int(output.count(">"))

            except Exception:
                logger.log(u"git didn't return numbers for behind and ahead, not using it", logger.DEBUG)
                return

        logger.log(u"cur_commit = {0}, newest_commit = {1}, num_commits_behind = {2}, num_commits_ahead = {3}".format
                   (self._cur_commit_hash, self._newest_commit_hash, self._num_commits_behind, self._num_commits_ahead), logger.DEBUG)

    def set_newest_text(self):

        # if we're up to date then don't set this
        sickbeard.NEWEST_VERSION_STRING = None

        if self._num_commits_ahead:
            logger.log(u"Local branch is ahead of " + self.branch + ". Automatic update not possible.", logger.WARNING)
            newest_text = "Local branch is ahead of " + self.branch + ". Automatic update not possible."

        elif self._num_commits_behind > 0:

            base_url = 'http://github.com/' + sickbeard.GIT_ORG + '/' + sickbeard.GIT_REPO
            if self._newest_commit_hash:
                url = base_url + '/compare/' + self._cur_commit_hash + '...' + self._newest_commit_hash
            else:
                url = base_url + '/commits/'

            newest_text = 'There is a <a href="' + url + '" onclick="window.open(this.href); return false;">newer version available</a> '
            newest_text += " (you're " + str(self._num_commits_behind) + " commit"
            if self._num_commits_behind > 1:
                newest_text += 's'
            newest_text += ' behind)' + "&mdash; <a href=\"" + self.get_update_url() + "\">Update Now</a>"

        else:
            return

        sickbeard.NEWEST_VERSION_STRING = newest_text

    def need_update(self):

        if self.branch != self._find_installed_branch():
            logger.log(u"Branch checkout: " + self._find_installed_branch() + "->" + self.branch, logger.DEBUG)
            return True

        self._find_installed_version()
        if not self._cur_commit_hash:
            return True
        else:
            try:
                self._check_github_for_update()
            except Exception as e:
                logger.log(u"Unable to contact github, can't check for update: " + repr(e), logger.WARNING)
                return False

            if self._num_commits_behind > 0:
                return True

        return False

    def update(self):
        """
        Calls git pull origin <branch> in order to update SickRage. Returns a bool depending
        on the call's success.
        """

        # update remote origin url
        self.update_remote_origin()

        # remove untracked files and performs a hard reset on git branch to avoid update issues
        if sickbeard.GIT_RESET:
            # self.clean() # This is removing user data and backups
            self.reset()

        if self.branch == self._find_installed_branch():
            stdout_, stderr_, exit_status = self._run_git(self._git_path, 'pull -f {0} {1}'.format(sickbeard.GIT_REMOTE, self.branch))
        else:
            stdout_, stderr_, exit_status = self._run_git(self._git_path, 'checkout -f ' + self.branch)

        if exit_status == 0:
            self._find_installed_version()

            # Notify update successful
            if sickbeard.NOTIFY_ON_UPDATE:
                try:
                    notifiers.notify_git_update(sickbeard.CUR_COMMIT_HASH or "")
                except Exception:
                    logger.log(u"Unable to send update notification. Continuing the update process", logger.DEBUG)
            return True

        else:
            return False

    def clean(self):
        """
        Calls git clean to remove all untracked files. Returns a bool depending
        on the call's success.
        """
        stdout_, stderr_, exit_status = self._run_git(self._git_path, 'clean -df ""')  # @UnusedVariable
        if exit_status == 0:
            return True

    def reset(self):
        """
        Calls git reset --hard to perform a hard reset. Returns a bool depending
        on the call's success.
        """
        stdout_, stderr_, exit_status = self._run_git(self._git_path, 'reset --hard')  # @UnusedVariable
        if exit_status == 0:
            return True

    def list_remote_branches(self):
        # update remote origin url
        self.update_remote_origin()
        sickbeard.BRANCH = self._find_installed_branch()

        branches, stderr_, exit_status = self._run_git(self._git_path, 'ls-remote --heads {0}'.format(sickbeard.GIT_REMOTE))  # @UnusedVariable
        if exit_status == 0 and branches:
            if branches:
                return re.findall(r'refs/heads/(.*)', branches)
        return []

    def update_remote_origin(self):
        self._run_git(self._git_path, 'config remote.{0}.url {1}'.format(sickbeard.GIT_REMOTE, sickbeard.GIT_REMOTE_URL))
        if sickbeard.GIT_USERNAME:
            self._run_git(self._git_path, 'config remote.{0}.pushurl {1}'.format(sickbeard.GIT_REMOTE, sickbeard.GIT_REMOTE_URL.replace(sickbeard.GIT_ORG, sickbeard.GIT_USERNAME, 1)))


class SourceUpdateManager(UpdateManager):
    def __init__(self):

        self.branch = sickbeard.BRANCH
        if sickbeard.BRANCH == '':
            self.branch = self._find_installed_branch()

        self._cur_commit_hash = sickbeard.CUR_COMMIT_HASH
        self._newest_commit_hash = None
        self._num_commits_behind = 0

        self.session = helpers.make_session()

    @staticmethod
    def _find_installed_branch():
        return sickbeard.CUR_COMMIT_BRANCH if sickbeard.CUR_COMMIT_BRANCH else "master"

    def get_cur_commit_hash(self):
        return self._cur_commit_hash

    def get_newest_commit_hash(self):
        return self._newest_commit_hash

    @staticmethod
    def get_cur_version():
        return ""

    @staticmethod
    def get_newest_version():
        return ""

    def get_num_commits_behind(self):
        return self._num_commits_behind

    def need_update(self):
        # need this to run first to set self._newest_commit_hash
        try:
            self._check_github_for_update()
        except Exception as e:
            logger.log(u"Unable to contact github, can't check for update: " + repr(e), logger.WARNING)
            return False

        if self.branch != self._find_installed_branch():
            logger.log(u"Branch checkout: " + self._find_installed_branch() + "->" + self.branch, logger.DEBUG)
            return True

        if not self._cur_commit_hash or self._num_commits_behind > 0:
            return True

        return False

    def _check_github_for_update(self):
        """
        Uses pygithub to ask github if there is a newer version that the provided
        commit hash. If there is a newer version it sets SickRage's version text.

        commit_hash: hash that we're checking against
        """

        self._num_commits_behind = 0
        self._newest_commit_hash = None

        repo = sickbeard.gh.get_organization(sickbeard.GIT_ORG).get_repo(sickbeard.GIT_REPO)
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

        logger.log(u"cur_commit = " + str(self._cur_commit_hash) + u", newest_commit = " + str(self._newest_commit_hash) +
                   u", num_commits_behind = " + str(self._num_commits_behind), logger.DEBUG)

    def set_newest_text(self):

        # if we're up to date then don't set this
        sickbeard.NEWEST_VERSION_STRING = None

        if not self._cur_commit_hash:
            logger.log(u"Unknown current version number, don't know if we should update or not", logger.DEBUG)

            newest_text = "Unknown current version number: If you've never used the SickRage upgrade system before then current version is not set."
            newest_text += "&mdash; <a href=\"" + self.get_update_url() + "\">Update Now</a>"

        elif self._num_commits_behind > 0:
            base_url = 'http://github.com/' + sickbeard.GIT_ORG + '/' + sickbeard.GIT_REPO
            if self._newest_commit_hash:
                url = base_url + '/compare/' + self._cur_commit_hash + '...' + self._newest_commit_hash
            else:
                url = base_url + '/commits/'

            newest_text = 'There is a <a href="' + url + '" onclick="window.open(this.href); return false;">newer version available</a>'
            newest_text += " (you're " + str(self._num_commits_behind) + " commit"
            if self._num_commits_behind > 1:
                newest_text += "s"
            newest_text += " behind)" + "&mdash; <a href=\"" + self.get_update_url() + "\">Update Now</a>"
        else:
            return

        sickbeard.NEWEST_VERSION_STRING = newest_text

    def update(self):  # pylint: disable=too-many-statements
        """
        Downloads the latest source tarball from github and installs it over the existing version.
        """

        tar_download_url = 'http://github.com/' + sickbeard.GIT_ORG + '/' + sickbeard.GIT_REPO + '/tarball/' + self.branch

        try:
            # prepare the update dir
            sr_update_dir = ek(os.path.join, sickbeard.PROG_DIR, u'sr-update')

            if ek(os.path.isdir, sr_update_dir):
                logger.log(u"Clearing out update folder " + sr_update_dir + " before extracting")
                shutil.rmtree(sr_update_dir)

            logger.log(u"Creating update folder " + sr_update_dir + " before extracting")
            ek(os.makedirs, sr_update_dir)

            # retrieve file
            logger.log(u"Downloading update from {url}".format(url=tar_download_url))
            tar_download_path = ek(os.path.join, sr_update_dir, u'sr-update.tar')
            helpers.download_file(tar_download_url, tar_download_path, session=self.session)

            if not ek(os.path.isfile, tar_download_path):
                logger.log(u"Unable to retrieve new version from " + tar_download_url + ", can't update", logger.WARNING)
                return False

            if not ek(tarfile.is_tarfile, tar_download_path):
                logger.log(u"Retrieved version from " + tar_download_url + " is corrupt, can't update", logger.ERROR)
                return False

            # extract to sr-update dir
            logger.log(u"Extracting file " + tar_download_path)
            tar = tarfile.open(tar_download_path)
            tar.extractall(sr_update_dir)
            tar.close()

            # delete .tar.gz
            logger.log(u"Deleting file " + tar_download_path)
            ek(os.remove, tar_download_path)

            # find update dir name
            update_dir_contents = [x for x in ek(os.listdir, sr_update_dir) if
                                   ek(os.path.isdir, ek(os.path.join, sr_update_dir, x))]

            if len(update_dir_contents) != 1:
                logger.log(u"Invalid update data, update failed: " + str(update_dir_contents), logger.ERROR)
                return False

            # walk temp folder and move files to main folder
            content_dir = ek(os.path.join, sr_update_dir, update_dir_contents[0])
            logger.log(u"Moving files from " + content_dir + " to " + sickbeard.PROG_DIR)
            for dirname, stderr_, filenames in ek(os.walk, content_dir):  # @UnusedVariable
                dirname = dirname[len(content_dir) + 1:]
                for curfile in filenames:
                    old_path = ek(os.path.join, content_dir, dirname, curfile)
                    new_path = ek(os.path.join, sickbeard.PROG_DIR, dirname, curfile)

                    # Avoid DLL access problem on WIN32/64
                    # These files needing to be updated manually
                    # or find a way to kill the access from memory
                    if curfile in ('unrar.dll', 'unrar64.dll'):
                        try:
                            ek(os.chmod, new_path, stat.S_IWRITE)
                            ek(os.remove, new_path)
                            ek(os.renames, old_path, new_path)
                        except Exception as e:
                            logger.log(u"Unable to update " + new_path + ': ' + ex(e), logger.DEBUG)
                            ek(os.remove, old_path)  # Trash the updated file without moving in new path
                        continue

                    if ek(os.path.isfile, new_path):
                        ek(os.remove, new_path)
                    ek(os.renames, old_path, new_path)

            sickbeard.CUR_COMMIT_HASH = self._newest_commit_hash
            sickbeard.CUR_COMMIT_BRANCH = self.branch

        except Exception as e:
            logger.log(u"Error while trying to update: " + ex(e), logger.ERROR)
            logger.log(u"Traceback: " + traceback.format_exc(), logger.DEBUG)
            return False

        # Notify update successful
        try:
            notifiers.notify_git_update(sickbeard.CUR_COMMIT_HASH or "")
        except Exception:
            logger.log(u"Unable to send update notification. Continuing the update process", logger.DEBUG)
        return True

    @staticmethod
    def list_remote_branches():
        if not sickbeard.gh:
            return []

        repo = sickbeard.gh.get_organization(sickbeard.GIT_ORG).get_repo(sickbeard.GIT_REPO)
        return [x.name for x in repo.get_branches() if x]
