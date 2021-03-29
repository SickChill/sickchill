import os
import threading
import time
import traceback

from sickchill import logger, settings

from . import common, config, generic_queue
from .processTV import log_helper, process_dir

MANUAL_POST_PROCESS = 120
AUTO_POST_PROCESS = 100

# TODO: Add html to the server status page showing processing tasks in the queue
# TODO: Add html to the management section to pause/unpause the processing queue


class PostProcessor(object):
    def __init__(self):
        self.lock = threading.Lock()
        self.amActive = False

    def run(self, force=False):
        """
        Runs the postprocessor

        :param force: Forces postprocessing run
        :return: Returns when done without a return state/code
        """
        self.amActive = True
        settings.postProcessorTaskScheduler.action.add_item(settings.TV_DOWNLOAD_DIR, force=force)
        self.amActive = False

    def __del__(self):
        pass


class ProcessingQueue(generic_queue.GenericQueue):
    """
    Queue to handle multiple post processing tasks
    """

    def __init__(self):
        """

        :rtype: object
        """
        super().__init__()
        self.queue_name = "POSTPROCESSOR"

    def find_in_queue(self, directory, filename, mode):
        """
        Finds any item in the queue with the given directory and mode pair
        :param directory: directory to be processed by the task
        :param filename: filename/nzbname/release_name to be processed by the task
        :param mode: processing type, auto/manual
        :return: instance of PostProcessorTask or None
        """
        for cur_item in self.queue + [self.currentItem]:
            if isinstance(cur_item, PostProcessorTask) and cur_item.matches(directory, filename, mode):
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
        length = {"auto": 0, "manual": 0}
        for cur_item in self.queue + [self.currentItem]:
            if isinstance(cur_item, PostProcessorTask):
                if cur_item.mode == "auto":
                    length["auto"] += 1
                else:
                    length["manual"] += 1
        return length

    def add_item(self, directory, filename=None, method=None, force=False, is_priority=None, delete=None, failed=False, mode="auto", force_next=False):
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
        replacements = dict(mode=mode.title(), info=filename or directory)
        if not directory:
            return log_helper("{mode} post-processing attempted but directory is not set: {info}".format(**replacements), logger.WARNING)

        # if not os.path.isdir(directory):
        #     return log_helper("{mode} post-processing attempted but directory doesn't exist: {info}".format(
        #         **replacements), logger.WARNING)

        if not os.path.isabs(directory):
            return log_helper(
                "{mode} post-processing attempted but directory is relative (and probably not what you really want to process): {info}".format(**replacements),
                logger.WARNING,
            )

        item = self.find_in_queue(directory, filename, mode)

        if not delete:
            delete = (False, (not settings.NO_DELETE, True)[method == "move"])[mode == "auto"]

        if item:
            if self.currentItem == item:
                return log_helper("{info} is already being processed right now, please wait until it completes before trying again".format(**replacements))

            item.set_params(directory, filename, method, force, is_priority, delete, failed, mode)
            message = log_helper("A task for {info} was already in the processing queue, updating the settings for that task".format(**replacements))
            return message + r"<br\><span class='hidden'>Processing succeeded</span>"
        else:
            item = PostProcessorTask(directory, filename, method, force, is_priority, delete, failed, mode)
            if force_next:
                with self.lock:
                    item.run()  # Non threaded, but with queue lock
                    message = item.last_result
                return message
            else:
                super().add_item(item)
                message = log_helper("{mode} post processing task for {info} was added to the queue".format(**replacements))
                return message + r"<br\><span class='hidden'>Processing succeeded</span>"


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
        super().__init__("{mode}".format(mode=mode.title()), (MANUAL_POST_PROCESS, AUTO_POST_PROCESS)[mode == "auto"])

        self.directory = directory
        self.filename = filename
        self.method = method
        self.force = config.checkbox_to_value(force)
        self.is_priority = config.checkbox_to_value(is_priority)
        self.delete = config.checkbox_to_value(delete)
        self.failed = config.checkbox_to_value(failed)
        self.mode = mode

        self.priority = (generic_queue.QueuePriorities.HIGH, generic_queue.QueuePriorities.NORMAL)[mode == "auto"]

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

    @property
    def info(self):
        return self.directory, self.filename, self.mode

    def matches(self, directory, filename, mode):
        return self.info == (directory, filename, mode)

    def run(self):
        """
        Runs the task
        :return: None
        """
        super().run()

        # noinspection PyBroadException
        try:
            logger.info("Beginning {mode} post processing task: {info}".format(mode=self.mode, info=self.filename or self.directory))
            self.last_result = process_dir(
                process_path=self.directory,
                release_name=self.filename,
                process_method=self.method,
                force=self.force,
                is_priority=self.is_priority,
                delete_on=self.delete,
                failed=self.failed,
                mode=self.mode,
            )
            logger.info("{mode} post processing task for {info} completed".format(mode=self.mode.title(), info=self.filename or self.directory))

            # give the CPU a break
            time.sleep(common.cpu_presets[settings.CPU_PRESET])
        except Exception:
            logger.debug(traceback.format_exc())

        super().finish()
        self.finish()
