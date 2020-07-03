# coding=utf-8
# Author: miigotu
# URL: https://sickchill.github.io
#
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, print_function, unicode_literals

# Stdlib Imports
import json
import time
import traceback

# Third Party Imports
import requests
import six
from requests.exceptions import HTTPError

# First Party Imports
import sickbeard
from sickbeard.logger import ex

# Local Folder Imports
from . import common, generic_queue, logger

DISCORD = 600


class NotificationsQueue(generic_queue.GenericQueue):
    """
    Queue to handle multiple post processing tasks
    """
    def __init__(self):
        """

        :rtype: object
        """
        generic_queue.GenericQueue.__init__(self)
        self.queue_name = "NOTIFICATIONS"

    @property
    def is_paused(self):
        """
        Shows if the post processing queue is paused
        :return: bool
        """
        return self.min_priority == generic_queue.QueuePriorities.HIGH

    @property
    def pause(self):
        """
        Pause the post processing queue
        """
        self.min_priority = generic_queue.QueuePriorities.HIGH
        return True

    @property
    def unpause(self):
        """
        Unpause the processing queue
        """
        self.min_priority = 0
        return True

    def __len__(self):
        size = len(self.queue)
        if self.currentItem:
            size += 1
        return size

    def add_item(self, message, notifier='discord', force_next=False):
        added = False
        item = None
        with self.lock:
            if self.queue and not force_next:
                for index in range(0, len(self.queue)):
                    if isinstance(self.queue[index], DiscordTask):
                        if len(self.queue[index]) < 24:
                            self.queue[index].append(message)
                            added = True
                            break
            if not added:
                item = DiscordTask(message)
                if force_next:
                    item.run()
                    return item.last_result
        if not added:
            added = super(NotificationsQueue, self).add_item(item)
        return added


class DiscordTask(generic_queue.QueueItem):
    """
    Processing task
    """
    def __init__(self, message):
        super(DiscordTask, self).__init__('Discord', DISCORD)

        self.embed = {
            'author': {
                'name': 'SickChill',
                # 'url':
                'icon_url': sickbeard.DISCORD_AVATAR_URL
            },
            'fields': []
        }

        self.priority = generic_queue.QueuePriorities.LOW
        self.last_result = None

        self.append(message)

    def run(self):
        """
        Runs the task
        :return: None
        """
        super(DiscordTask, self).run()

        # noinspection PyBroadException
        try:
            logger.log("Task for {} started".format(self.action_id), logger.DEBUG)
            self.last_result = self._send_discord()
            logger.log("Task for {} completed".format(self.action_id), logger.DEBUG)

            # give the CPU a break
            time.sleep(common.cpu_presets[sickbeard.CPU_PRESET])
        except Exception:
            logger.log(traceback.format_exc(), logger.DEBUG)

        super(DiscordTask, self).finish()
        self.finish()

    def append(self, message):
        if isinstance(message, six.text_type):
            message = message.encode('utf-8')

        self.embed['fields'] += [
                {'name': 'Notification', 'value': message}
            ]

    def __len__(self):
        return len(self.embed['fields'])

    def _send_discord(self):
        discord_webhook = sickbeard.DISCORD_WEBHOOK
        discord_name = sickbeard.DISCORD_NAME
        avatar_icon = sickbeard.DISCORD_AVATAR_URL
        discord_tts = bool(sickbeard.DISCORD_TTS)

        logger.log("Sending discord message: " + ', '.join(f['value'] for f in self.embed['fields']), logger.INFO)
        logger.log("Sending discord message to url: " + discord_webhook, logger.INFO)

        headers = {b"Content-Type": b"application/json"}
        try:
            r = requests.post(discord_webhook,
                              data=json.dumps(dict(embeds=[self.embed], username=discord_name, avatar_url=avatar_icon, tts=discord_tts)),
                              headers=headers)
            r.raise_for_status()
        except HTTPError as error:
            if error.response.status_code != 429 or int(error.response.headers.get('X-RateLimit-Remaining')) != 0:
                raise error

            logger.log('Discord rate limiting, retrying after {} seconds'.format(error.response.headers.get('X-RateLimit-Reset-After')))
            time.sleep(int(error.response.headers.get('X-RateLimit-Reset-After')) + 1)
            r = requests.post(discord_webhook,
                              data=json.dumps(dict(embeds=[self.embed], username=discord_name, avatar_url=avatar_icon, tts=discord_tts)),
                              headers=headers)
            r.raise_for_status()
        except Exception as error:
            logger.log("Error Sending Discord message: " + ex(error), logger.ERROR)

            return False

        return True
