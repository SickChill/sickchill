import json
import time
import traceback

import requests
from requests.structures import CaseInsensitiveDict

from sickchill import logger, settings

from . import common, generic_queue

DISCORD = 600


class NotificationsQueue(generic_queue.GenericQueue):
    """
    Queue to handle multiple post processing tasks
    """

    def __init__(self):
        """

        :rtype: object
        """
        super().__init__()
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

    def add_item(self, message, notifier="discord", force_next=False):
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
            added = super().add_item(item)
        return added


class DiscordTask(generic_queue.QueueItem):
    """
    Processing task
    """

    def __init__(self, message):
        super().__init__("Discord", DISCORD)

        self.embed = {
            "author": {
                "name": "SickChill",
                # 'url':
                "icon_url": settings.DISCORD_AVATAR_URL,
            },
            "fields": [],
        }

        self.priority = generic_queue.QueuePriorities.LOW
        self.last_result = None

        self.append(message)

    def run(self):
        """
        Runs the task
        :return: None
        """
        super().run()

        # noinspection PyBroadException
        try:
            logger.debug("Task for {} started".format(self.action_id))
            self.last_result = self._send_discord()
            logger.debug("Task for {} completed".format(self.action_id))

            # give the CPU a break
            time.sleep(common.cpu_presets[settings.CPU_PRESET])
        except Exception:
            logger.debug(traceback.format_exc())

        super().finish()
        self.finish()

    def append(self, message):
        self.embed["fields"] += [{"name": "Notification", "value": message}]

    def __len__(self):
        return len(self.embed["fields"])

    def _send_discord(self, webhook: str = None, name: str = None, avatar: str = None, tts=None):
        discord_webhook = webhook or settings.DISCORD_WEBHOOK
        discord_name = name or settings.DISCORD_NAME
        avatar_icon = avatar or settings.DISCORD_AVATAR_URL
        discord_tts = bool(settings.DISCORD_TTS if tts is None else tts)

        logger.info("Sending discord message: " + ", ".join(f["value"] for f in self.embed["fields"]))
        logger.info("Sending discord message to url: " + discord_webhook)

        headers = CaseInsensitiveDict({"Content-Type": "application/json"})
        try:
            r = requests.post(
                discord_webhook, data=json.dumps(dict(embeds=[self.embed], username=discord_name, avatar_url=avatar_icon, tts=discord_tts)), headers=headers
            )
            r.raise_for_status()
        except requests.exceptions.ConnectionError as error:
            logger.info("Could not reach the webhook url")
            return False
        except requests.exceptions.RequestException as error:
            if error.response.status_code != 429 or int(error.response.headers.get("X-RateLimit-Remaining")) != 0:
                raise error

            logger.info("Discord rate limiting, retrying after {} seconds".format(error.response.headers.get("X-RateLimit-Reset-After")))
            time.sleep(int(error.response.headers.get("X-RateLimit-Reset-After")) + 1)
            r = requests.post(
                discord_webhook, data=json.dumps(dict(embeds=[self.embed], username=discord_name, avatar_url=avatar_icon, tts=discord_tts)), headers=headers
            )
            r.raise_for_status()
        except Exception as error:
            logger.exception(f"Error Sending Discord message: {error}")

            return False

        return True
