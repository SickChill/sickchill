import os
import subprocess
import sys
from pathlib import Path
from typing import List, Union

from packaging import version as packaging_version

from sickchill import logger, settings
from sickchill.init_helpers import get_current_version, sickchill_dir
from sickchill.oldbeard import helpers, notifiers

from .abstract import UpdateManagerBase


class PipUpdateManager(UpdateManagerBase):
    def __init__(self):
        self.version_text = get_current_version()
        self.newest_version_text = get_current_version()

        self._newest_version: Union[packaging_version.LegacyVersion, packaging_version.Version] = None
        self.session = helpers.make_session()

    def get_current_version(self) -> str:
        return packaging_version.parse(self.version_text)

    def get_clean_version(self, use_version: packaging_version.Version = None):
        return str(use_version or self.get_current_version())

    def get_newest_version(self) -> Union[packaging_version.LegacyVersion, packaging_version.Version]:
        self._newest_version = packaging_version.parse(self.session.get("https://pypi.org/pypi/sickchill/json").json()["info"]["version"])
        return self._newest_version

    def get_version_delta(self):
        if not self.need_update():
            return 0

        newest, current = self._newest_version, self.get_current_version()
        return f"Major: {newest.major - current.major}, Minor: {newest.minor - current.minor}, Micro: {newest.micro - current.micro}"

    def set_newest_text(self):
        if self.need_update():
            if self.get_newest_version():
                current = self.get_clean_version()
                newest = self.get_clean_version(self.get_newest_version())
                url = f"https://github.com/{settings.GIT_ORG}/{settings.GIT_REPO}/compare/{current}...{newest}"
            else:
                url = f"https://github.com/{settings.GIT_ORG}/{settings.GIT_REPO}/commits/"

            newest_tag = "newer_version_available"
            update_url = self.get_update_url()
            newest_text = _(
                'There is a <a href="{url}" onclick="window.open(this.href); return false;">newer version available</a> &mdash; <a href="{update_url}">Update Now</a>'
            ).format(url=url, update_url=update_url)

        else:
            return

        helpers.add_site_message(newest_text, tag=newest_tag, level="success")

    def need_update(self):
        return self.get_newest_version() > self.get_current_version()

    def update(self):
        logger.info("Updating using pip in your current environment")
        if not self.pip_install("sickchill"):
            return False

        notifiers.notify_update(f"{self._newest_version}")
        return True

    def pip_install(self, packages: Union[List[str], str]) -> bool:
        def subprocess_call(cmd_list):
            try:
                process = subprocess.Popen(
                    cmd_list, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, cwd=os.getcwd()
                )
                stdout, stderr = process.communicate()
                process.wait()
                if stdout or stderr:
                    for line in (stdout or stderr).splitlines():
                        logger.info(line)
            except Exception as error:
                logger.info(f"Unable to run command: {error}")
                return 126
            return process.returncode

        def get_os_id():
            os_release = Path("/etc/os-release").resolve()
            if os_release.is_file():
                from configparser import ConfigParser

                parser = ConfigParser()
                parser.read_string("[DEFAULT]\n" + os_release.read_text())
                try:
                    return parser["DEFAULT"]["ID"]
                except (KeyError, IndexError):
                    pass

        cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-input",
            "--disable-pip-version-check",
            "--no-python-version-warning",
            "--no-color",
            # "--trusted-host=pypi.org",
            # "--trusted-host=files.pythonhosted.org",
            "-U",
        ]

        os_id = get_os_id()
        if os_id in ("alpine", "ubuntu"):
            cmd.append(f"--find-links=https://wheel-index.linuxserver.io/{os_id}/")

        if os_id == "alpine":
            cmd.append(f"--extra-index-url=https://alpine-wheels.github.io/index")

        elif os_id in ("raspbian", "osmc"):
            cmd.append(f"--extra-index-url=https://www.piwheels.org/simple")

        syno_wheelhouse = sickchill_dir.with_name("wheelhouse")
        if syno_wheelhouse.is_dir():
            logger.debug(f"Found wheelhouse dir at {syno_wheelhouse}")
            cmd.append(f"-f{syno_wheelhouse}")

        if isinstance(packages, list):
            cmd += packages
        elif isinstance(packages, str):
            cmd.append(packages)

        logger.debug(f"pip args: {' '.join(cmd)}")

        result = subprocess_call(cmd)
        if result != 0:  # Not Ok
            logger.info("Trying user site-packages")
            result = subprocess_call(cmd + ["--user"])
            if result != 0:  # Not Ok
                return False
        return True
