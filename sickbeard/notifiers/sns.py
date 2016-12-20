# coding=utf-8

# Author: Benjamin Burkhart <benburkhart1@gmail.com>
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

import sickbeard

from sickbeard import logger, common
from sickrage.helper.exceptions import ex

import json

import boto3 as boto3

class Notifier(object):

    def notify_snatch(self, ep_name):
        if sickbeard.SNS_NOTIFY_ONSNATCH:
            self._notifySNS(
              "SNATCH", 
              episode_name=ep_name,
              prefix=common.notifyStrings[common.NOTIFY_SNATCH]
            )

    def notify_download(self, ep_name):
        if sickbeard.SNS_NOTIFY_ONDOWNLOAD:
            self._notifySNS(
              "DOWNLOAD", 
              episode_name=ep_name, 
              prefix=common.notifyStrings[common.NOTIFY_DOWNLOAD]
            )

    def notify_subtitle_download(self, ep_name, lang):
        if sickbeard.SNS_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notifySNS(
              "SUBTITLE_DOWNLOAD", 
              prefix=common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD], 
              episode_name=ep_name, 
              lang=lang
            )

    def test_notify(self):
        return self._notifySNS(
          "TEST", 
          prefix="Test Completed",
          episode_name="SNS Test",
          force=True
        )

    def _send_sns(self, message=None):

        access_key_id = sickbeard.SNS_ACCESSKEYID
        secret_key = sickbeard.SNS_SECRETKEY
        arn = sickbeard.SNS_ARN

        arn_parsed = arn.split(':')

        if len(arn_parsed) != 6:
          logger.log(u"Error Sending SNS: Invalid ARN", logger.ERROR)
          return False

        region_name = arn_parsed[3]

        logger.log(u"Sending SNS: " + message, logger.DEBUG)

        sns = client = boto3.client(
           'sns',
           aws_access_key_id=access_key_id,
           aws_secret_access_key=secret_key,
           region_name=region_name
        )

        try:
            sns.publish
            client.publish(
                TargetArn=arn,
                Message=message
            )
        except Exception as e:
            logger.log(u"Error Sending SNS: " + ex(e), logger.ERROR)
            return False

        return True

    def _notifySNS(self, msg_type='', force=False, prefix=False, episode_name=False, lang=False):
        if not sickbeard.USE_SNS and not force:
            return False

        if sickbeard.SNS_USEJSONMSG:
          obj = { "msg_type": msg_type } 
          
          if episode_name:
            obj.update({ "episode_name": episode_name})

          if lang:
            obj.update({ "lang": lang })

          if prefix:
            obj.update({ "prefix": prefix })

          return self._send_sns(json.dumps(obj, ensure_ascii=False))

        if prefix:
          message = prefix + " " + episode_name
        else:
          message = episode_name
        
        if lang:
          message += ": " + lang

        return self._send_sns(message)
