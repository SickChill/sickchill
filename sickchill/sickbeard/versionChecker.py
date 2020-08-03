




# Stdlib Imports
import datetime
import glob
import os
import platform
import re
import shutil
import subprocess
import tarfile
import time
import traceback

# First Party Imports
from sickchill import settings

# Local Folder Imports
from . import db, helpers, logger, notifiers, ui


class CheckVersion(object):
    """
    Version check class meant to run as a thread object with the sr scheduler.
    """

    def __init__(self):
        self.updater = None
        self.install_type = None
        self.amActive = False
        if settings.gh:
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
            settings.BRANCH = self.get_branch()

            if self.check_for_new_version(force):
                if settings.AUTO_UPDATE:
                    logger.info("New update found for SickChill, starting auto-updater ...")
                    ui.notifications.message(_('New update found for SickChill, starting auto-updater'))
                    if self.run_backup_if_safe():
                        if settings.versionCheckScheduler.action.update():
                            logger.info("Update was successful!")
                            ui.notifications.message(_('Update was successful'))
                            settings.events.put(settings.events.SystemEvent.RESTART)
                        else:
                            logger.info("Update failed!")
                            ui.notifications.message(_('Update failed!'))

            self.check_for_new_news()

        self.amActive = False

    def run_backup_if_safe(self):
        return self.safe_to_update() is True and self._runbackup() is True

    def _runbackup(self):
        # Do a system backup before update
        logger.info("Config backup in progress...")
        ui.notifications.message(_('Backup'), _('Config backup in progress...'))
        try:
            backupDir = os.path.join(settings.DATA_DIR, 'backup')
            if not os.path.isdir(backupDir):
                os.mkdir(backupDir)

            if self._keeplatestbackup(backupDir) and self._backup(backupDir):
                logger.info("Config backup successful, updating...")
                ui.notifications.message(_('Backup'), _('Config backup successful, updating...'))
                return True
            else:
                logger.exception("Config backup failed, aborting update")
                ui.notifications.message(_('Backup'), _('Config backup failed, aborting update'))
                return False
        except Exception as error:
            logger.exception('Update: Config backup failed. Error: {}'.format(error))
            ui.notifications.message(_('Backup'), _('Config backup failed, aborting update'))
            return False

    @staticmethod
    def _keeplatestbackup(backupDir=None):
        if not backupDir:
            return False

        # noinspection PyUnresolvedReferences
        files = glob.glob(os.path.join(glob.escape(backupDir), '*.zip'))
        if not files:
            return True

        now = time.time()
        newest = files[0], now - os.path.getctime(files[0])
        for f in files[1:]:
            age = now - os.path.getctime(f)
            if age < newest[1]:
                newest = f, age
        files.remove(newest[0])

        for f in files:
            os.remove(f)

        return True

    @staticmethod
    def _backup(backupDir=None):
        if not backupDir:
            return False
        source = [
            os.path.join(settings.DATA_DIR, 'sickbeard.db'),
            settings.CONFIG_FILE,
            os.path.join(settings.DATA_DIR, 'failed.db'),
            os.path.join(settings.DATA_DIR, 'cache.db')
        ]
        target = os.path.join(backupDir, 'sickchill-' + time.strftime('%Y%m%d%H%M%S') + '.zip')

        for (path, dirs, files) in os.walk(settings.CACHE_DIR, topdown=True):
            for dirname in dirs:
                if path == settings.CACHE_DIR and dirname not in ['images']:
                    dirs.remove(dirname)
            for filename in files:
                source.append(os.path.join(path, filename))

        return helpers.backup_config_zip(source, target, settings.DATA_DIR)

    def safe_to_update(self):

        def db_safe(self):
            message = {
                'equal': {
                    'type': logger.DEBUG,
                    'text': "We can proceed with the update. New update has same DB version"
                },
                'upgrade': {
                    'type': logger.WARNING,
                    'text': "We can't proceed with the update. New update has a new DB version. Please manually update"
                },
                'downgrade': {
                    'type': logger.ERROR,
                    'text': "We can't proceed with the update. New update has a old DB version. It's not possible to downgrade"
                },
            }
            try:
                result = self.getDBcompare()
                if result in message:
                    logger.log(message[result]['type'], message[result]['text'])  # unpack the result message into a log entry
                else:
                    logger.warning("We can't proceed with the update. Unable to check remote DB version. Error: {0}".format(result))
                return result in ['equal']  # add future True results to the list
            except Exception as error:
                logger.warning("We can't proceed with the update. Unable to compare DB version. Error: {0}".format(repr(error)))
                return False

        def postprocessor_safe():
            if not settings.autoPostProcessorScheduler.action.amActive:
                logger.debug("We can proceed with the update. Post-Processor is not running")
                return True
            else:
                logger.debug("We can't proceed with the update. Post-Processor is running")
                return False

        def showupdate_safe():
            if not settings.showUpdateScheduler.action.amActive:
                logger.debug("We can proceed with the update. Shows are not being updated")
                return True
            else:
                logger.debug("We can't proceed with the update. Shows are being updated")
                return False

        db_safe = db_safe(self)
        postprocessor_safe = postprocessor_safe()
        showupdate_safe = showupdate_safe()

        if db_safe and postprocessor_safe and showupdate_safe:
            logger.debug("Proceeding with auto update")
            return True
        else:
            logger.debug("Auto update aborted")
            return False

    def getDBcompare(self):
        try:
            self.updater.need_update()
            cur_hash = self.updater.get_newest_commit_hash()
            assert len(cur_hash) == 40, "Commit hash wrong length: {0} hash: {1}".format(len(cur_hash), cur_hash)

            response = None
            check_url = "https://raw.githubusercontent.com/{0}/{1}/{2}/sickbeard/databases/main.py"
            for attempt in (cur_hash, "master"):
                response = helpers.getURL(check_url.format(settings.GIT_ORG, settings.GIT_REPO, attempt), session=self.session, returns='text')
                if response:
                    break

            assert response, "Empty response from {0}".format(check_url)

            match = re.search(r"MAX_DB_VERSION\s=\s(?P<version>\d{2,3})", response)
            branchDestDBversion = int(match.group('version'))
            main_db_con = db.DBConnection()
            branchCurrDBversion = main_db_con.get_db_version()
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
        if settings.BRANCH.startswith('build '):
            install_type = 'win'
        elif os.path.isdir(os.path.join(settings.PROG_DIR, '.git')):
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

        if not self.updater or (not settings.VERSION_NOTIFY and not settings.AUTO_UPDATE and not force):
            logger.info("Version checking is disabled, not checking for the newest version")
            return False

        # checking for updates
        if not settings.AUTO_UPDATE:
            logger.info("Checking for updates using " + self.install_type.upper())

        if not self.updater.need_update():
            if force:
                ui.notifications.message(_('No update needed'))
                logger.info("No update needed")

            # no updates needed
            return False

        # found updates
        self.updater.set_newest_text()
        return True

    def check_for_new_news(self):
        """
        Checks GitHub for the latest news.

        returns: str, a copy of the news

        force: ignored
        """

        # Grab a copy of the news
        logger.debug('check_for_new_news: Checking GitHub for latest news.')
        try:
            news = helpers.getURL(settings.NEWS_URL, session=self.session, returns='text')
        except Exception:
            logger.warning('check_for_new_news: Could not load news from repo.')
            news = ''

        if not news:
            return ''

        try:
            last_read = datetime.datetime.strptime(settings.NEWS_LAST_READ, '%Y-%m-%d')
        except Exception:
            last_read = 0

        settings.NEWS_UNREAD = 0
        gotLatest = False
        for match in re.finditer(r'^####\s*(\d{4}-\d{2}-\d{2})\s*####', news, re.M):
            if not gotLatest:
                gotLatest = True
                settings.NEWS_LATEST = match.group(1)

            try:
                if datetime.datetime.strptime(match.group(1), '%Y-%m-%d') > last_read:
                    settings.NEWS_UNREAD += 1
            except Exception:
                pass

        return news

    def update(self):
        if self.updater:
            # update branch with current config branch value
            self.updater.branch = settings.BRANCH

            # check for updates
            if self.updater.need_update():
                return self.updater.update()

    def list_remote_branches(self):
        if self.updater:
            return self.updater.list_remote_branches()

    def get_branch(self):
        if self.updater:
            return self.updater.branch


class UpdateManager(object):
    @staticmethod
    def get_update_url():
        return settings.WEB_ROOT + "/home/update/?pid=".format(settings.PID)

    @staticmethod
    def remove_pyc(path):
        path_parts = [settings.PROG_DIR, path, '*.pyc']
        for f in glob.iglob(os.path.join(*path_parts)):
            os.remove(f)

        path_parts.insert(-1, '**')
        for f in glob.iglob(os.path.join(*path_parts)):
            os.remove(f)


class GitUpdateManager(UpdateManager):
    def __init__(self):
        self._git_path = self._find_working_git()

        self.branch = settings.BRANCH = self._find_installed_branch()

        self.check_detached_head()

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

    def _find_working_git(self):
        test_cmd = 'version'

        if settings.GIT_PATH:
            main_git = '"' + settings.GIT_PATH + '"'
        else:
            main_git = 'git'

        logger.debug("Checking if we can use git commands: " + main_git + ' ' + test_cmd)
        stdout_, stderr_, exit_status = self._run_git(main_git, test_cmd)

        if exit_status == 0:
            logger.debug("Using: " + main_git)
            return main_git
        else:
            logger.debug("Not using: " + main_git)

        # trying alternatives

        alternative_git = []

        # osx people who start sr from launchd have a broken path, so try a hail-mary attempt for them
        if platform.system() == 'Darwin':
            alternative_git.append('/usr/local/git/bin/git')

        if platform.system() == 'Windows':
            if main_git != main_git.lower():
                alternative_git.append(main_git.lower())

        if alternative_git:
            logger.debug("Trying known alternative git locations")

            for cur_git in alternative_git:
                logger.debug("Checking if we can use git commands: " + cur_git + ' ' + test_cmd)
                stdout_, stderr_, exit_status = self._run_git(cur_git, test_cmd)

                if exit_status == 0:
                    logger.debug("Using: " + cur_git)
                    return cur_git
                else:
                    logger.debug("Not using: " + cur_git)

        # Still haven't found a working git
        helpers.add_site_message(
            _('Unable to find your git executable - Shutdown SickChill and EITHER set git_path in '
              'your config.ini OR delete your .git folder and run from source to enable updates.'),
            tag='unable_to_find_git', level='danger')
        return None

    @staticmethod
    def _run_git(git_path, args, log_errors=False):

        output = err = exit_status = None

        if not git_path:
            logger.warning("No git specified, can't use git commands")
            exit_status = 1
            return output, err, exit_status

        cmd = git_path + ' ' + args

        try:
            logger.debug("Executing {0} with your shell in {1}".format(cmd, settings.PROG_DIR))
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 shell=True, cwd=settings.PROG_DIR)
            output, err = p.communicate()
            exit_status = p.returncode

            if output:
                output = output.decode().strip()

        except OSError:
            logger.info("Command {} didn't work".format(cmd))
            exit_status = 1

        if exit_status == 0:
            logger.debug("{} : returned successful".format(cmd))

        elif exit_status == 1:
            if 'stash' in output:
                logger.warning("Please enable 'git reset' in settings or stash your changes in local files")
            elif log_errors:
                logger.exception("{0} returned : {1}".format(cmd, output))

        elif log_errors:
            if exit_status in (127, 128) or 'fatal:' in output:
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

        output, errors_, exit_status = self._run_git(self._git_path, 'rev-parse HEAD')  # @UnusedVariable

        if exit_status == 0 and output:
            cur_commit_hash = output.strip()
            if not re.match('^[a-z0-9]+$', cur_commit_hash):
                logger.exception("Output doesn't look like a hash, not using it")
                return False
            self._cur_commit_hash = settings.CUR_COMMIT_HASH = cur_commit_hash
            return True
        else:
            return False

    def _find_installed_branch(self):
        branch_info, errors_, exit_status = self._run_git(self._git_path, 'symbolic-ref -q HEAD')  # @UnusedVariable
        if exit_status == 0 and branch_info:
            branch = branch_info.strip().replace('refs/heads/', '', 1)
            if branch:
                settings.BRANCH = branch
                return branch
        return ""

    def check_detached_head(self):
        # stdout, stderr_, exit_status = self._run_git(self._git_path, 'branch --show-current')
        # if exit_status == 0 and not stdout:
        if helpers.is_docker() and not self.branch:
            logger.info('We found you in a detached state that prevents updates. Fixing')
            self._run_git(self._git_path, 'fetch origin')
            stdout_, stderr_, exit_status = self._run_git(self._git_path, 'checkout -f master')
            if exit_status == 0:
                self.branch = settings.BRANCH = 'master'

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
        output, errors_, exit_status = self._run_git(self._git_path, 'fetch {0} --prune'.format(settings.GIT_REMOTE))
        if exit_status != 0:
            logger.warning("Unable to contact github, can't check for update")
            return

        # Try both formats, but continue on fail because older git versions do not have this option
        output, stderr_, exit_status = self._run_git(self._git_path, 'branch --set-upstream-to {0}/{1}'.format(settings.GIT_REMOTE, self.branch), False)
        if exit_status != 0:
            self._run_git(self._git_path, 'branch -u {0}/{1}'.format(settings.GIT_REMOTE, self.branch), False)

        # get latest commit_hash from remote
        output, stderr_, exit_status = self._run_git(self._git_path, 'rev-parse --verify --quiet "@{upstream}"')

        if exit_status == 0 and output:
            cur_commit_hash = output.strip()

            if not re.match('^[a-z0-9]+$', cur_commit_hash):
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

        logger.debug("cur_commit = {0}, newest_commit = {1}, num_commits_behind = {2}, num_commits_ahead = {3}".format
                   (self._cur_commit_hash, self._newest_commit_hash, self._num_commits_behind, self._num_commits_ahead))

    def set_newest_text(self):
        if self._num_commits_ahead:
            newest_tag = 'local_branch_ahead'
            newest_text = 'Local branch is ahead of {branch}. Automatic update not possible.'.format(branch=self.branch)
            logger.warning(newest_text)

        elif self._num_commits_behind > 0:

            base_url = 'https://github.com/' + settings.GIT_ORG + '/' + settings.GIT_REPO
            if self._newest_commit_hash:
                url = base_url + '/compare/' + self._cur_commit_hash + '...' + self._newest_commit_hash
            else:
                url = base_url + '/commits/'

            newest_tag = 'newer_version_available'
            commits_behind = _("(you're {num_commits} commit behind)").format(num_commits=self._num_commits_behind)
            newest_text = _('There is a <a href="{compare_url}" onclick="window.open(this.href); return false;">'
                            'newer version available</a> {commits_behind} &mdash; '
                            '<a href="{update_url}">Update Now</a>').format(
                compare_url=url, commits_behind=commits_behind, update_url=self.get_update_url())

        else:
            return

        helpers.add_site_message(newest_text, tag=newest_tag, level='success')

    def need_update(self):

        if self.branch != self._find_installed_branch():
            logger.debug("Branch checkout: " + self._find_installed_branch() + "->" + self.branch)
            return True

        self._find_installed_version()
        if not self._cur_commit_hash:
            return True
        else:
            try:
                self._check_github_for_update()
            except Exception as e:
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
        self.update_remote_origin()

        # remove untracked files and performs a hard reset on git branch to avoid update issues
        if settings.GIT_RESET:
            # self.clean() # This is removing user data and backups
            self.reset()

        if self.branch == self._find_installed_branch():
            stdout_, stderr_, exit_status = self._run_git(self._git_path, 'pull -f {0} {1}'.format(settings.GIT_REMOTE, self.branch))
        else:
            stdout_, stderr_, exit_status = self._run_git(self._git_path, 'checkout -f ' + self.branch)

        if exit_status == 0:
            self._find_installed_version()
            self.clean_libs()

            # Notify update successful
            notifiers.notify_git_update(settings.CUR_COMMIT_HASH or "")
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

    def clean_libs(self):
        """
        Calls git clean to remove all untracked files in the lib dir before restart. Returns a bool depending
        on the call's success.
        """
        stdout_, stderr_, exit_status = self._run_git(self._git_path, 'clean -df lib')  # @UnusedVariable
        if exit_status == 0:
            return True

        self.remove_pyc('lib')

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
        settings.BRANCH = self._find_installed_branch()

        branches, stderr_, exit_status = self._run_git(self._git_path, 'ls-remote --heads {0}'.format(settings.GIT_REMOTE))  # @UnusedVariable
        if exit_status == 0 and branches:
            if branches:
                return re.findall(r'refs/heads/(.*)', branches)
        return []

    def update_remote_origin(self):
        if not settings.DEVELOPER:
            self._run_git(self._git_path, 'config remote.{0}.url {1}'.format(settings.GIT_REMOTE, settings.GIT_REMOTE_URL))


class SourceUpdateManager(UpdateManager):
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

            newest_tag = 'unknown_current_version'
            newest_text = _('Unknown current version number: '
                            'If you\'ve never used the SickChill upgrade system before then current version is not set. '
                            '&mdash; <a href="{update_url}">Update Now</a>').format(update_url=self.get_update_url())

        elif self._num_commits_behind > 0:
            base_url = 'https://github.com/' + settings.GIT_ORG + '/' + settings.GIT_REPO
            if self._newest_commit_hash:
                url = base_url + '/compare/' + self._cur_commit_hash + '...' + self._newest_commit_hash
            else:
                url = base_url + '/commits/'

            newest_tag = 'newer_version_available'
            commits_behind = _("(you're {num_commits} commit behind)").format(num_commits=self._num_commits_behind)
            newest_text = _('There is a <a href="{compare_url}" onclick="window.open(this.href); return false;">'
                            'newer version available</a> {commits_behind} &mdash; '
                            '<a href="{update_url}">Update Now</a>').format(
                compare_url=url, commits_behind=commits_behind, update_url=self.get_update_url())
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
            sr_update_dir = os.path.join(settings.PROG_DIR, 'sr-update')

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
            logger.info("Moving files from " + content_dir + " to " + settings.PROG_DIR)
            for dirname, stderr_, filenames in os.walk(content_dir):  # @UnusedVariable
                dirname = dirname[len(content_dir) + 1:]
                for curfile in filenames:
                    old_path = os.path.join(content_dir, dirname, curfile)
                    new_path = os.path.join(settings.PROG_DIR, dirname, curfile)

                    if os.path.isfile(new_path):
                        os.remove(new_path)
                    os.renames(old_path, new_path)

            settings.CUR_COMMIT_HASH = self._newest_commit_hash
            settings.CUR_COMMIT_BRANCH = self.branch

        except Exception as error:
            logger.exception("Error while trying to update: {}".format(error))
            logger.debug("Traceback: {}".format(traceback.format_exc()))
            return False

        self.clean_libs()

        # Notify update successful
        notifiers.notify_git_update(settings.CUR_COMMIT_HASH or "")
        return True

    def clean_libs(self):
        lib_path = os.path.join(settings.PROG_DIR, 'lib')

        def removeEmptyFolders(path):
            if not os.path.isdir(path):
                return

            files = os.listdir(path)
            for f in files:
                full_path = os.path.join(path, f)
                if os.path.isdir(full_path):
                    removeEmptyFolders(full_path)

            files = os.listdir(path)
            if len(files) == 0 and path != lib_path:
                os.rmdir(path)

        self.remove_pyc('lib')
        removeEmptyFolders(lib_path)

    @staticmethod
    def list_remote_branches():
        if not settings.gh:
            return []

        repo = settings.gh.get_organization(settings.GIT_ORG).get_repo(settings.GIT_REPO)
        return [x.name for x in repo.get_branches() if x]
