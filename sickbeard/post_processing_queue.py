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
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

import os
import time
import traceback

import sickbeard
from sickbeard import common, generic_queue, logger, processTV
from sickrage.helper.encoding import ek

MANUAL_POST_PROCESS = 120
AUTO_POST_PROCESS = 100


class ProcessingQueue(generic_queue.GenericQueue):
    def __init__(self):
        generic_queue.GenericQueue.__init__(self)
        self.queue_name = "POSTPROCESSOR"

    def find_in_queue(self, directory, mode):
        for cur_item in self.queue + [self.currentItem]:
            if isinstance(cur_item, PostProcessorTask) and cur_item.directory == directory and cur_item.mode == mode:
                return cur_item
        return None

    @property
    def is_paused(self):
        return self.min_priority == generic_queue.QueuePriorities.HIGH

    @property
    def pause(self):
        self.min_priority = generic_queue.QueuePriorities.HIGH
        return True

    @property
    def unpause(self):
        self.min_priority = 0
        return True

    def queue_length(self):
        length = {'auto': 0, 'manual': 0}
        for cur_item in self.queue + [self.currentItem]:
            if isinstance(cur_item, PostProcessorTask):
                if cur_item.mode == 'auto':
                    length['auto'] += 1
                else:
                    length['manual'] += 1
        return length

    def add_item(self, directory, filename=None, method=None, force=False, is_priority=None, delete=False, failed=False, mode="auto"):

        replacements = dict(mode=mode.title(), directory=directory)
        if not directory:
            message = u"{mode} post-processing attempted but directory is not set: {directory}".format(**replacements)
            logger.log(message, logger.WARNING)
            return message

        if not ek(os.path.isdir, directory):
            message = u"{mode} post-processing attempted but directory doesn't exist: {directory}".format(**replacements)
            logger.log(message, logger.WARNING)
            return message

        if not ek(os.path.isabs, directory):
            message = u"{mode} post-processing attempted but directory is relative (and probably not what you really want to process): {directory}".format(
                **replacements)
            logger.log(message, logger.WARNING)
            return message

        item = self.find_in_queue(directory, mode)
        if item:
            if self.currentItem == item:
                message = "{directory} is already being processed right now, please wait until it completes before trying again".format(**replacements)
                logger.log(message, logger.INFO)
                return message

            message = "A task for {directory} was already in the processing queue, updating the settings for that task\n<br\><span class='hidden'>Processing succeeded</span>".format(**replacements)
            if item.mode != 'auto':
                logger.log(message.split('\n')[0], logger.DEBUG)

            item.set_params(directory, filename, method, force, is_priority, delete, failed, mode)
            return message
        else:
            message = "{mode} post processing task for {directory} was added to the queue\n<br\><span class='hidden'>Processing succeeded</span>".format(
                **replacements)
            item = PostProcessorTask(directory, filename, method, force, is_priority, delete, failed, mode)
            super(ProcessingQueue, self).add_item(item)
            logger.log(message.split('\n')[0], logger.INFO)
            return message


class PostProcessorTask(generic_queue.QueueItem):
    def __init__(self, directory, filename=None, method=None, force=False, is_priority=None, delete=False, failed=False, mode="auto"):
        self.directory = directory
        self.filename = filename
        self.method = method
        self.force = self.__bool(force)
        self.is_priority = self.__bool(is_priority)
        self.delete = self.__bool(delete)
        self.failed = self.__bool(failed)
        self.mode = mode

        self.priority = (generic_queue.QueuePriorities.HIGH, generic_queue.QueuePriorities.NORMAL)[mode == 'auto']

        self.last_result = None
        generic_queue.QueueItem.__init__(self, u'{mode}'.format(mode=self.mode.title()), (MANUAL_POST_PROCESS, AUTO_POST_PROCESS)[mode == "auto"])

    def set_params(self, directory, filename=None, method=None, force=False, is_priority=None, delete=False, failed=False, mode="auto"):
        self.directory = directory
        self.filename = filename
        self.method = method
        self.force = self.__bool(force)
        self.is_priority = self.__bool(is_priority)
        self.delete = self.__bool(delete)
        self.failed = self.__bool(failed)
        self.mode = mode

    @staticmethod
    def __bool(argument):
        if not isinstance(argument, (str, unicode)):
            _arg = argument
        else:
            _arg = str(argument).strip().lower()

        if _arg in (1, '1', 'on', 'true', True):
            return True
        elif _arg in (0, '0', 'off', 'false', False):
            return False

        return argument

    def run(self):
        super(PostProcessorTask, self).run()

        try:
            logger.log(u"Beginning {mode} post processing task: {directory}".format(mode=self.mode, directory=self.directory))
            self.last_result = processTV.processDir(
                dirName=self.directory,
                nzbName=self.filename,
                process_method=self.method,
                force=self.force,
                is_priority=self.is_priority,
                delete_on=self.delete,
                failed=self.failed, proc_type=self.mode
            )
            logger.log(u"{mode} post processing task for {directory} completed".format(mode=self.mode.title(), directory=self.directory))

            # give the CPU a break
            time.sleep(common.cpu_presets[sickbeard.CPU_PRESET])
        except Exception:
            logger.log(traceback.format_exc(), logger.DEBUG)

        super(PostProcessorTask, self).finish()
        self.finish()
