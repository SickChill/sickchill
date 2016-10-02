# coding=utf-8

# Author: Patrick Begley<forge33@gmail.com>
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

import sickbeard
import lib.requests as requests

from sickbeard import logger, common
from sickrage.helper.exceptions import ex

class Notifier(object):

    SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/'

    def notify_snatch(self, ep_name):
        if sickbeard.SLACK_NOTIFY_SNATCH:
            self._notifySlack(common.notifyStrings[common.NOTIFY_SNATCH] + ': ' + ep_name)

    def notify_download(self, ep_name):
        if sickbeard.SLACK_NOTIFY_DOWNLOAD:
            self._notifySlack(common.notifyStrings[common.NOTIFY_DOWNLOAD] + ': ' + ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if sickbeard.SLACK_NOTIFY_SUBTITLEDOWNLOAD:
            self._notifySlack(common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD] + ' ' + ep_name + ": " + lang)

    def notify_git_update(self, new_version="??"):
        if sickbeard.USE_SLACK:
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            self._notifySlack(title + " - " + update_text + new_version)

    def notify_login(self, ipaddress=""):
        if sickbeard.USE_SLACK:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._notifySlack(title + " - " + update_text.format(ipaddress))

    def test_notify(self):
        return self._notifySlack("This is a test notification from SickRage", force=True)

    def _send_slack(self, message=None):
        slack_webhook = self.SLACK_WEBHOOK_URL + sickbeard.SLACK_WEBHOOK.replace(self.SLACK_WEBHOOK_URL,'')

        logger.log(u"Sending slack message: " + message, logger.INFO)
        logger.log(u"Sending slack message  to url: " + slack_webhook, logger.INFO)

        method = 'POST'
        headers = {"Content-Type": "application/json"}
        postdata = '{"text":"%s"}' % message
        try:
            r = requests.request(method,
                             slack_webhook,
                             data=postdata,
                             headers=headers
                             )
        except Exception as e:
            logger.log(u"Error Sending Slack message: " + ex(e), logger.ERROR)
            return False

        return True

    def _notifySlack(self, message='', force=False):
        if not sickbeard.USE_SLACK and not force:
            return False

        return self._send_slack(message)
