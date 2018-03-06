# coding=utf-8
# Author: miigotu
# URL: https://sickrage.github.io
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
# along with SickRage. If not, see <https://www.gnu.org/licenses/>.

from __future__ import print_function, unicode_literals

import os
import time
import traceback

import sickbeard
from sickbeard import common, config, generic_queue, logger, processTV
from sickbeard.processTV import log_helper, process_dir
from sickrage.helper.encoding import ek

MANUAL_POST_PROCESS = 120
AUTO_POST_PROCESS = 100

# TODO: Add html to the server status page showing processing tasks in the queue
# TODO: Add html to the management section to pause/unpause the processing queue


class ProcessingQueue(generic_queue.GenericQueue):
    """
    Queue to handle multiple post processing tasks
    """
    def __init__(self):
        """

        :rtype: object
        """
        generic_queue.GenericQueue.__init__(self)
        self.queue_name = "POSTPROCESSOR"

    def find_in_queue(self, directory, mode):
        """
        Finds any item in the queue with the given directory and mode pair
        :param directory: directory to be processed by the task
        :param mode: processing type, auto/manual
        :return: instance of PostProcessorTask or None
        """
        for cur_item in self.queue + [self.currentItem]:
            if isinstance(cur_item, PostProcessorTask) and cur_item.directory == directory and cur_item.mode == mode:
                return cur_item
        return None

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

    def queue_length(self):
        """
        Returns a dict showing how many auto and manual tasks are in the queue
        :return: dict
        """
        length = {'auto': 0, 'manual': 0}
        for cur_item in self.queue + [self.currentItem]:
            if isinstance(cur_item, PostProcessorTask):
                if cur_item.mode == 'auto':
                    length['auto'] += 1
                else:
                    length['manual'] += 1
        return length

    def add_item(self, directory, filename=None, method=None, force=False, is_priority=None,
                 delete=None, failed=False, mode="auto", force_next=False):
        """
        Adds a processing task to the queue
        :param directory: directory to process
        :param filename: release/nzb name if available
        :param method: processing method, copy/move/symlink/link
        :param force: force overwriting of existing files regardless of quality
        :param is_priority: whether to replace the file even if it exists at higher quality
        :param delete: delete files and folders after they are processed (always happens with move and auto combination)
        :param failed: mark downloads as failed if they fail to process
        :param mode: processing type: auto/manual
        :param force_next: wait until the current item in the queue is finished, acquire the lock and process this task now, so we can return the result
        :return: string indicating success or failure
        """
        replacements = dict(mode=mode.title(), directory=directory)
        if not directory:
            return log_helper("{mode} post-processing attempted but directory is not set: {directory}".format(
                **replacements), logger.WARNING)

        # if not ek(os.path.isdir, directory):
        #     return log_helper(u"{mode} post-processing attempted but directory doesn't exist: {directory}".format(
        #         **replacements), logger.WARNING)

        if not ek(os.path.isabs, directory):
            return log_helper(
                "{mode} post-processing attempted but directory is relative (and probably not what you really want to process): {directory}".format(
                    **replacements), logger.WARNING)

        item = self.find_in_queue(directory, mode)

        if not delete:
            delete = (False, (not sickbeard.NO_DELETE, True)[method == u"move"])[mode == u"auto"]

        if item:
            if self.currentItem == item:
                return log_helper(
                    "{directory} is already being processed right now, please wait until it completes before trying again".format(**replacements))

            item.set_params(directory, filename, method, force, is_priority, delete, failed, mode)
            message = log_helper("A task for {directory} was already in the processing queue, updating the settings for that task".format(**replacements))
            return message + "<br\><span class='hidden'>Processing succeeded</span>"
        else:
            item = PostProcessorTask(directory, filename, method, force, is_priority, delete, failed, mode)
            if force_next:
                with self.lock:
                    item.run()  # Non threaded, but with queue lock
                    message = item.last_result
                return message
            else:
                super(ProcessingQueue, self).add_item(item)
                message = log_helper("{mode} post processing task for {directory} was added to the queue".format(**replacements))
                return message + "<br\><span class='hidden'>Processing succeeded</span>"


class PostProcessorTask(generic_queue.QueueItem):
    """
    Processing task
    """
    def __init__(self, directory, filename=None, method=None, force=False, is_priority=None, delete=False, failed=False, mode="auto"):
        """
        :param directory: directory to process
        :param filename: release/nzb name if available
        :param method: processing method, copy/move/symlink/link
        :param force: force overwriting of existing files regardless of quality
        :param is_priority: whether to replace the file even if it exists at higher quality
        :param delete: delete files and folders after they are processed (always happens with move and auto combination)
        :param failed: mark downloads as failed if they fail to process
        :param mode: processing type: auto/manual
        :return: None
        """
        super(PostProcessorTask, self).__init__('{mode}'.format(mode=mode.title()), (MANUAL_POST_PROCESS, AUTO_POST_PROCESS)[mode == "auto"])

        self.directory = directory
        self.filename = filename
        self.method = method
        self.force = config.checkbox_to_value(force)
        self.is_priority = config.checkbox_to_value(is_priority)
        self.delete = config.checkbox_to_value(delete)
        self.failed = config.checkbox_to_value(failed)
        self.mode = mode

        self.priority = (generic_queue.QueuePriorities.HIGH, generic_queue.QueuePriorities.NORMAL)[mode == 'auto']

        self.last_result = None

    def set_params(self, directory, filename=None, method=None, force=False, is_priority=None, delete=False, failed=False, mode="auto"):
        """
        Adjust settings for a task that is already in the queue
        :param directory: directory to process
        :param filename: release/nzb name if available
        :param method: processing method, copy/move/symlink/link
        :param force: force overwriting of existing files regardless of quality
        :param is_priority: whether to replace the file even if it exists at higher quality
        :param delete: delete files and folders after they are processed (always happens with move and auto combination)
        :param failed: mark downloads as failed if they fail to process
        :param mode: processing type: auto/manual
        :return: None
        """
        self.directory = directory
        self.filename = filename
        self.method = method
        self.force = config.checkbox_to_value(force)
        self.is_priority = config.checkbox_to_value(is_priority)
        self.delete = config.checkbox_to_value(delete)
        self.failed = config.checkbox_to_value(failed)
        self.mode = mode

    def run(self):
        """
        Runs the task
        :return: None
        """
        super(PostProcessorTask, self).run()

        # noinspection PyBroadException
        try:
            logger.log("Beginning {mode} post processing task: {directory}".format(mode=self.mode, directory=self.directory))
            self.last_result = process_dir(
                process_path=self.directory,
                release_name=self.filename,
                process_method=self.method,
                force=self.force,
                is_priority=self.is_priority,
                delete_on=self.delete,
                failed=self.failed,
                mode=self.mode
            )
            logger.log("{mode} post processing task for {directory} completed".format(mode=self.mode.title(), directory=self.directory))

            # give the CPU a break
            time.sleep(common.cpu_presets[sickbeard.CPU_PRESET])
        except Exception:
            logger.log(traceback.format_exc(), logger.DEBUG)

        super(PostProcessorTask, self).finish()
        self.finish()
