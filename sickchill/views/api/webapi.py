# Author: Dennis Lutter <lad1337@gmail.com>
import abc
import datetime
import json
import os
import re
import time
import traceback
import urllib.parse
from pathlib import Path

from tornado.web import RequestHandler

import sickchill
from sickchill import logger, settings
from sickchill.helper.common import dateFormat, dateTimeFormat, pretty_file_size, sanitize_filename, timeFormat, try_int
from sickchill.helper.exceptions import CantUpdateShowException, ShowDirectoryNotFoundException
from sickchill.helper.quality import get_quality_string
from sickchill.init_helpers import get_current_version
from sickchill.oldbeard import classes, db, helpers, network_timezones, sbdatetime, search_queue, ui
from sickchill.oldbeard.common import (
    ARCHIVED,
    DOWNLOADED,
    FAILED,
    IGNORED,
    Overview,
    Quality,
    SKIPPED,
    SNATCHED,
    SNATCHED_PROPER,
    statusStrings_bare,
    UNAIRED,
    UNKNOWN,
    WANTED,
)
from sickchill.oldbeard.postProcessor import PROCESS_METHODS
from sickchill.show.ComingEpisodes import ComingEpisodes
from sickchill.show.History import History
from sickchill.show.Show import Show
from sickchill.system.Restart import Restart
from sickchill.system.Shutdown import Shutdown
from sickchill.update_manager import UpdateManager

indexer_ids = ["indexerid", "tvdbid"]

RESULT_SUCCESS = 10  # only use inside the run methods
RESULT_FAILURE = 20  # only use inside the run methods
RESULT_TIMEOUT = 30  # not used yet :(
RESULT_ERROR = 40  # only use outside of the run methods !
RESULT_FATAL = 50  # only use in Api.default() ! this is the "we encountered an internal error" error
RESULT_DENIED = 60  # only use in Api.default() ! this is the access denied error
result_type_map = {
    RESULT_SUCCESS: "success",
    RESULT_FAILURE: "failure",
    RESULT_TIMEOUT: "timeout",
    RESULT_ERROR: "error",
    RESULT_FATAL: "fatal",
    RESULT_DENIED: "denied",
}


# basically everything except RESULT_SUCCESS / success is bad

# noinspection PyAbstractClass
class ApiHandler(RequestHandler):
    """api class that returns json results"""

    version = 5  # use an int since float-point is unpredictable

    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "content-type")
        self.set_header("Access-Control-Allow-Methods", "GET")
        # self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')

    def get(self, *args, **kwargs):
        # kwargs = self.request.arguments
        kwargs = urllib.parse.parse_qs(self.request.query)
        for arg, value in kwargs.items():
            if len(value) == 1:
                kwargs[arg] = value[0]

        args = args[1:]

        # set the output callback
        # default json
        output_callback_dict = {
            "default": self._out_as_json,
            "image": self._out_as_image,
        }

        access_msg = "API :: " + self.request.remote_ip + " - gave correct API KEY. ACCESS GRANTED"
        logger.debug(access_msg)

        # set the original call_dispatcher as the local _call_dispatcher
        _call_dispatcher = self.call_dispatcher
        # if profile was set wrap "_call_dispatcher" in the profile function
        if "profile" in kwargs:
            from profilehooks import profile

            _call_dispatcher = profile(_call_dispatcher, immediate=True)
            del kwargs["profile"]

        try:
            out_dict = _call_dispatcher(args, kwargs)
        except Exception as error:  # real internal error oohhh nooo :(
            logger.info(traceback.format_exc())
            logger.exception(f"API :: {error}")
            error_data = {"error_msg": f"{error}", "args": args, "kwargs": kwargs}
            out_dict = _responds(RESULT_FATAL, error_data, "SickChill encountered an internal error! Please report to the Devs")

        if "outputType" in out_dict:
            output_callback = output_callback_dict[out_dict["outputType"]]
        else:
            output_callback = output_callback_dict["default"]

        # noinspection PyBroadException
        try:
            self.finish(output_callback(out_dict))
        except Exception:
            pass

    def _out_as_image(self, _dict):
        self.set_header("Content-Type", settings.IMAGE_CACHE.content_type(_dict["image"]))
        return settings.IMAGE_CACHE.image_data(_dict["image"])

    def _out_as_json(self, _dict):
        self.set_header("Content-Type", "application/json;charset=UTF-8")
        try:
            out = json.dumps(_dict, ensure_ascii=False, sort_keys=True)
            callback = self.get_query_argument("callback", None) or self.get_query_argument("jsonp", None)
            if callback:
                out = callback + "(" + out + ");"  # wrap with JSONP call if requested
        except Exception as error:  # if we fail to generate the output fake an error
            logger.debug(f"API :: {traceback.format_exc()}")
            out = f'{{"result": "{result_type_map[RESULT_ERROR]}", "message": "error while composing output: {error}"}}'
        return out

    def call_dispatcher(self, args, kwargs):  # pylint:disable=too-many-branches
        """calls the appropriate CMD class
        looks for a cmd in args and kwargs
        or calls the TVDBShorthandWrapper when the first args element is a number
        or returns an error that there is no such cmd
        """
        logger.debug(f"API :: all args: '{args}'")
        logger.debug(f"API :: all kwargs: '{kwargs}'")

        commands = None
        if args:
            commands, args = args[0], args[1:]
        commands = kwargs.pop("cmd", commands)

        out_dict = {}
        if commands:
            commands = commands.split("|")
            multi_commands = len(commands) > 1
            for cmd in commands:
                cur_args, cur_kwargs = self.filter_params(cmd, args, kwargs)

                if len(cmd.split("_")) > 1:
                    cmd, cmd_index = cmd.split("_")
                else:
                    cmd_index = None

                logger.debug(f"API :: {cmd}: cur_kwargs {cur_kwargs}")
                if not (
                    cmd in ("show.getbanner", "show.getfanart", "show.getnetworklogo", "show.getposter") and multi_commands
                ):  # skip these cmd while chaining
                    try:
                        if cmd in function_mapper:
                            func = function_mapper.get(cmd)  # map function
                            to_call = func(cur_args, cur_kwargs)
                            to_call.rh = self
                            cur_out_dict = to_call.run()  # call function and get response
                        elif _is_int(cmd):
                            to_call = TVDBShorthandWrapper(cur_args, cur_kwargs, cmd)
                            to_call.rh = self
                            cur_out_dict = to_call.run()
                        else:
                            cur_out_dict = _responds(RESULT_ERROR, f"No such cmd: '{cmd}'")
                    except ApiError as error:  # Api errors that we raised, they are harmless
                        logger.info(traceback.format_exc())
                        cur_out_dict = _responds(RESULT_ERROR, msg=f"{error}")
                else:  # if someone chained one of the forbidden commands they will get an error for this one cmd
                    cur_out_dict = _responds(RESULT_ERROR, msg=f"The cmd '{cmd}' is not supported while chaining")

                if multi_commands:
                    # note: if duplicate commands are issued and one has an index defined it will override
                    # all others or the other way around, depending on the command order
                    # THIS IS NOT A BUG!
                    if cmd_index:  # do we need an index dict for this cmd ?
                        if cmd not in out_dict:
                            out_dict[cmd] = {}
                        out_dict[cmd][cmd_index] = cur_out_dict
                    else:
                        out_dict[cmd] = cur_out_dict
                else:
                    out_dict = cur_out_dict

            if multi_commands:  # if we had multiple commands we have to wrap it in a response dict
                out_dict = _responds(RESULT_SUCCESS, out_dict)
        else:  # index / no cmd given
            out_dict = CMDSickChill(args, kwargs).run()

        return out_dict

    @staticmethod
    def filter_params(cmd, args, kwargs):
        """return only params kwargs that are for cmd
        and rename them to a clean version (remove "<cmd>_")
        args are shared across all commands

        all args and kwargs are lowered

        cmd are separated by "|" e.g. &cmd=shows|future
        kwargs are name-spaced with "." e.g. show.indexerid=101501
        if a kwarg has no namespace asking it anyways (global)

        full e.g.
        /api?apikey=1234&cmd=show.seasonlist_asd|show.seasonlist_2&show.seasonlist_asd.indexerid=101501&show.seasonlist_2.indexerid=79488&sort=asc

        two calls of show.seasonlist
        one has the index "asd" the other one "2"
        the "indexerid" kwargs / params have the indexed cmd as a namespace
        and the kwarg / param "sort" is a used as a global
        """
        cur_args = []
        for arg in args:
            cur_args.append(arg.lower())
        cur_args = tuple(cur_args)

        cur_kwargs = {}
        for kwarg in kwargs:
            if kwarg.find(cmd + ".") == 0:
                clean_key = kwarg.rpartition(".")[2]
                cur_kwargs[clean_key] = kwargs[kwarg].lower()
            elif "." not in kwarg:  # the kwarg was not name-spaced therefore a "global"
                cur_kwargs[kwarg] = kwargs[kwarg]
        return cur_args, cur_kwargs


# noinspection PyAbstractClass
class ApiCall(ApiHandler):
    _help = {"desc": "This command is not documented. Please report this to the developers."}

    # noinspection PyMissingConstructor
    def __init__(self, args, kwargs):
        # TODO: Find out why this buggers up RequestHandler init if called
        # super().__init__(args, kwargs)
        self.rh = None
        self.indexer = 1
        self._missing = []
        self._requiredParams = {}
        self._optionalParams = {}
        self.check_params(args, kwargs)

    def run(self):
        raise NotImplementedError()

    def return_help(self):
        for paramDict, paramType in [(self._requiredParams, "requiredParameters"), (self._optionalParams, "optionalParameters")]:

            if paramType in self._help:
                for paramName in paramDict:
                    if paramName not in self._help[paramType]:
                        # noinspection PyUnresolvedReferences
                        self._help[paramType][paramName] = {}
                    if paramDict[paramName]["allowedValues"]:
                        # noinspection PyUnresolvedReferences
                        self._help[paramType][paramName]["allowedValues"] = paramDict[paramName]["allowedValues"]
                    else:
                        # noinspection PyUnresolvedReferences
                        self._help[paramType][paramName]["allowedValues"] = "see desc"
                    # noinspection PyUnresolvedReferences
                    self._help[paramType][paramName]["defaultValue"] = paramDict[paramName]["defaultValue"]
                    # noinspection PyUnresolvedReferences
                    self._help[paramType][paramName]["type"] = paramDict[paramName]["type"]

            elif paramDict:
                for paramName in paramDict:
                    self._help[paramType] = {}
                    # noinspection PyUnresolvedReferences
                    self._help[paramType][paramName] = paramDict[paramName]
            else:
                self._help[paramType] = {}

        msg = "No description available"
        if "desc" in self._help:
            msg = self._help["desc"]

        return _responds(RESULT_SUCCESS, self._help, msg)

    def return_missing(self):
        if len(self._missing) == 1:
            msg = "The required parameter: '" + self._missing[0] + "' was not set"
        else:
            msg = "The required parameters: '" + "','".join(self._missing) + "' where not set"
        return _responds(RESULT_ERROR, msg=msg)

    def check_params(self, args, kwargs, key=None, default=None, required=None, arg_type=None, allowed_values=None):
        """function to check passed params for the shorthand wrapper
        and to detect missing/required params
        """

        # auto-select indexer
        if key in indexer_ids:
            if "tvdbid" in kwargs:
                key = "tvdbid"

            self.indexer = indexer_ids.index(key)

        if key:
            missing = True
            org_default = default

            if arg_type == "bool":
                allowed_values = [0, 1]

            if args:
                default = args[0]
                missing = False
                args = args[1:]
            if kwargs.get(key):
                default = kwargs.get(key)
                missing = False

            key_value = {"allowedValues": allowed_values, "defaultValue": org_default, "type": arg_type}

            if required:
                self._requiredParams[key] = key_value
                if missing and key not in self._missing:
                    self._missing.append(key)
            else:
                self._optionalParams[key] = key_value

            if default:
                default = self._check_param_type(default, key, arg_type)
                self._check_param_value(default, key, allowed_values)

        if self._missing:
            setattr(self, "run", self.return_missing)

        if "help" in kwargs:
            setattr(self, "run", self.return_help)

        return default, args

    @staticmethod
    def _check_param_type(value, name, arg_type):
        """checks if value can be converted / parsed to arg_type
        will raise an error on failure
        or will convert it to arg_type and return new converted value
        can check for:
        - int: will be converted into int
        - bool: will be converted to False / True
        - list: will always return a list
        - string: will do nothing for now
        - ignore: will ignore it, just like "string"
        """
        error = False
        if arg_type == "int":
            if _is_int(value):
                value = int(value)
            else:
                error = True
        elif arg_type == "bool":
            if value in ("0", "1"):
                value = bool(int(value))
            elif value in ("true", "True", "TRUE"):
                value = True
            elif value in ("false", "False", "FALSE"):
                value = False
            elif value not in (True, False):
                error = True
        elif arg_type == "list":
            value = value.split("|")
        elif arg_type == "string":
            pass
        elif arg_type == "ignore":
            pass
        else:
            logger.exception('API :: Invalid param type: "{0}" can not be checked. Ignoring it.'.format(str(arg_type)))

        if error:
            # this is a real ApiError !!
            raise ApiError('param "{0}" with given value "{1}" could not be parsed into "{2}"'.format(str(name), str(value), str(arg_type)))

        return value

    @staticmethod
    def _check_param_value(value, name, allowed_values):
        """will check if value (or all values in it ) are in allowed values
        will raise an exception if value is "out of range"
        if bool(allowed_value) is False a check is not performed and all values are excepted
        """
        if allowed_values:
            error = False
            if isinstance(value, list):
                for item in value:
                    if item not in allowed_values:
                        error = True
            else:
                if value not in allowed_values:
                    error = True

            if error:
                # this is kinda a ApiError but raising an error is the only way of quitting here
                raise ApiError(f"param: '{name}' with given value: '{value}' is out of allowed range '{allowed_values}'")


# noinspection PyAbstractClass
class TVDBShorthandWrapper(ApiCall):
    _help = {"desc": "This is an internal function wrapper. Call the help command directly for more information."}

    def __init__(self, args, kwargs, sid):
        super().__init__(args, kwargs)

        self.origArgs = args
        self.kwargs = kwargs
        self.sid = sid

        self.s, args = self.check_params(args, kwargs, "s", None, False, "ignore", [])
        self.e, args = self.check_params(args, kwargs, "e", None, False, "ignore", [])
        self.args = args

    def run(self):
        """internal function wrapper"""
        args = (self.sid,) + self.origArgs
        if self.e:
            return CMDEpisode(args, self.kwargs).run()
        elif self.s:
            return CMDShowSeasons(args, self.kwargs).run()
        else:
            return CMDShow(args, self.kwargs).run()


# ###############################
#       helper functions        #
# ###############################


def _is_int(data):
    try:
        int(data)
    except (TypeError, ValueError, OverflowError):
        return False
    else:
        return True


def _rename_element(dict_obj, old_key, new_key):
    try:
        dict_obj[new_key] = dict_obj[old_key]
        del dict_obj[old_key]
    except (ValueError, TypeError, NameError):
        pass
    return dict_obj


def _responds(result_type, data=None, msg=""):
    """
    result is a string of given "type" (success/failure/timeout/error)
    message is a human readable string, can be empty
    data is either a dict or a array, can be a empty dict or empty array
    """
    return {"result": result_type_map[result_type], "message": msg, "data": {} if not data else data}


def status_to_code(status_string) -> int:
    # convert the string status to a int
    if isinstance(status_string, int):
        return status_string

    for status in statusStrings_bare:
        if statusStrings_bare[status].lower() == str(status_string).lower():
            return status

    logger.debug(traceback.format_exc())
    raise ApiError("The status string could not be matched to a status. Report to Devs!")


def _ordinal_to_datetime_form(ordinal):
    # workaround for episodes with no air date
    if int(ordinal) != 1:
        date = datetime.date.fromordinal(ordinal)
    else:
        return ""
    return date.strftime(dateTimeFormat)


def _ordinal_to_date_form(ordinal):
    if int(ordinal) != 1:
        date = datetime.date.fromordinal(ordinal)
    else:
        return ""
    return date.strftime(dateFormat)


def _history_date_to_datetime_form(time_string):
    date = datetime.datetime.strptime(time_string, History.date_format)
    return date.strftime(dateTimeFormat)


QUALITY_MAP = {
    Quality.SDTV: "sdtv",
    "sdtv": Quality.SDTV,
    Quality.SDDVD: "sddvd",
    "sddvd": Quality.SDDVD,
    Quality.HDTV: "hdtv",
    "hdtv": Quality.HDTV,
    Quality.RAWHDTV: "rawhdtv",
    "rawhdtv": Quality.RAWHDTV,
    Quality.FULLHDTV: "fullhdtv",
    "fullhdtv": Quality.FULLHDTV,
    Quality.HDWEBDL: "hdwebdl",
    "hdwebdl": Quality.HDWEBDL,
    Quality.FULLHDWEBDL: "fullhdwebdl",
    "fullhdwebdl": Quality.FULLHDWEBDL,
    Quality.HDBLURAY: "hdbluray",
    "hdbluray": Quality.HDBLURAY,
    Quality.FULLHDBLURAY: "fullhdbluray",
    "fullhdbluray": Quality.FULLHDBLURAY,
    Quality.UHD_4K_TV: "uhd4ktv",
    "udh4ktv": Quality.UHD_4K_TV,
    Quality.UHD_4K_BLURAY: "4kbluray",
    "uhd4kbluray": Quality.UHD_4K_BLURAY,
    Quality.UHD_4K_WEBDL: "4kwebdl",
    "udh4kwebdl": Quality.UHD_4K_WEBDL,
    Quality.UHD_8K_TV: "uhd8ktv",
    "udh8ktv": Quality.UHD_8K_TV,
    Quality.UHD_8K_BLURAY: "uhd8kbluray",
    "uhd8kbluray": Quality.UHD_8K_BLURAY,
    Quality.UHD_8K_WEBDL: "udh8kwebdl",
    "udh8kwebdl": Quality.UHD_8K_WEBDL,
    Quality.UNKNOWN: "unknown",
    "unknown": Quality.UNKNOWN,
}

ALLOWED_QUALITY_LIST = [
    "sdtv",
    "sddvd",
    "hdtv",
    "rawhdtv",
    "fullhdtv",
    "hdwebdl",
    "fullhdwebdl",
    "hdbluray",
    "fullhdbluray",
    "udh4ktv",
    "uhd4kbluray",
    "udh4kwebdl",
    "udh8ktv",
    "uhd8kbluray",
    "udh8kwebdl",
    "unknown",
]

PREFERRED_QUALITY_LIST = [
    "sdtv",
    "sddvd",
    "hdtv",
    "rawhdtv",
    "fullhdtv",
    "hdwebdl",
    "fullhdwebdl",
    "hdbluray",
    "fullhdbluray",
    "udh4ktv",
    "uhd4kbluray",
    "udh4kwebdl",
    "udh8ktv",
    "uhd8kbluray",
    "udh8kwebdl",
]


def _map_quality(show_quality):
    any_qualities = []
    best_qualities = []

    i_quality_id, a_quality_id = Quality.splitQuality(int(show_quality))
    for quality in i_quality_id:
        any_qualities.append((QUALITY_MAP[quality], "N/A")[quality is None])
    for quality in a_quality_id:
        best_qualities.append((QUALITY_MAP[quality], "N/A")[quality is None])
    return any_qualities, best_qualities


def _get_root_dirs():
    if settings.ROOT_DIRS == "":
        return {}

    root_dir = {}
    root_dirs = settings.ROOT_DIRS.split("|")
    default_index = int(settings.ROOT_DIRS.split("|")[0])

    root_dir["default_index"] = int(settings.ROOT_DIRS.split("|")[0])
    # remove default_index value from list (this fixes the offset)
    root_dirs.pop(0)

    if len(root_dirs) < default_index:
        return {}

    # clean up the list - replace %xx escapes by their single-character equivalent
    root_dirs = [urllib.parse.unquote_plus(x) for x in root_dirs]

    default_dir = root_dirs[default_index]

    dir_list = []
    for root_dir in root_dirs:
        valid = 1
        # noinspection PyBroadException
        try:
            os.listdir(root_dir)
        except Exception:
            valid = 0
        default = 0
        if root_dir is default_dir:
            default = 1

        cur_dir = {"valid": valid, "location": root_dir, "default": default}
        dir_list.append(cur_dir)

    return dir_list


class ApiError(Exception):
    """
    Generic API error
    """


# -------------------------------------------------------------------------------------#


# noinspection PyAbstractClass
class CMDHelp(ApiCall):
    _help = {
        "desc": "Get help about a given command",
        "optionalParameters": {
            "subject": {"desc": "The name of the command to get the help of"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.subject, args = self.check_params(args, kwargs, "subject", "help", False, "string", list(function_mapper))

    def run(self):
        """Get help about a given command"""
        if self.subject in function_mapper:
            out = _responds(RESULT_SUCCESS, function_mapper.get(self.subject)((), {"help": 1}).run())
        else:
            out = _responds(RESULT_FAILURE, msg="No such cmd")
        return out


# noinspection PyAbstractClass
class CMDComingEpisodes(ApiCall):
    _help = {
        "desc": "Get the coming episodes",
        "optionalParameters": {
            "sort": {"desc": "Change the sort order"},
            "type": {"desc": "One or more categories of coming episodes, separated by |"},
            "paused": {"desc": "0 to exclude paused shows, 1 to include them, or omitted to use SickChill default value"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.sort, args = self.check_params(args, kwargs, "sort", "date", False, "string", list(ComingEpisodes.sorts))
        self.type, args = self.check_params(args, kwargs, "type", "|".join(ComingEpisodes.categories), False, "list", ComingEpisodes.categories)
        self.paused, args = self.check_params(args, kwargs, "paused", bool(settings.COMING_EPS_DISPLAY_PAUSED), False, "bool", [])

    def run(self):
        """Get the coming episodes"""
        grouped_coming_episodes = ComingEpisodes.get_coming_episodes(self.type, self.sort, True, self.paused)
        data = {section: [] for section in grouped_coming_episodes.keys()}

        # noinspection PyCompatibility
        for section, coming_episodes in grouped_coming_episodes.items():
            for coming_episode in coming_episodes:
                data[section].append(
                    {
                        "airdate": coming_episode["airdate"],
                        "airs": coming_episode["airs"],
                        "ep_name": coming_episode["name"],
                        "ep_plot": coming_episode["description"],
                        "episode": coming_episode["episode"],
                        "indexerid": coming_episode["indexer_id"],
                        "network": coming_episode["network"],
                        "paused": coming_episode["paused"],
                        "quality": coming_episode["quality"],
                        "season": coming_episode["season"],
                        "show_name": coming_episode["show_name"],
                        "show_status": coming_episode["status"],
                        "tvdbid": coming_episode["tvdbid"],
                        "weekday": coming_episode["weekday"],
                    }
                )

        return _responds(RESULT_SUCCESS, data)


# noinspection PyAbstractClass
class CMDEpisode(ApiCall):
    _help = {
        "desc": "Get detailed information about an episode",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
            "season": {"desc": "The season number"},
            "episode": {"desc": "The episode number"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "full_path": {"desc": "Return the full absolute show location (if valid, and True), or the relative show location"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        self.s, args = self.check_params(args, kwargs, "season", None, True, "int", [])
        self.e, args = self.check_params(args, kwargs, "episode", None, True, "int", [])
        self.fullPath, args = self.check_params(args, kwargs, "full_path", False, False, "bool", [])

    def run(self):
        """Get detailed information about an episode"""
        show_obj = Show.find(settings.showList, int(self.indexerid))
        if not show_obj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        main_db_con = db.DBConnection(row_type="dict")
        # noinspection PyPep8
        sql_results = main_db_con.select(
            "SELECT name, description, airdate, status, location, file_size, release_name, subtitles FROM tv_episodes WHERE showid = ? AND episode = ? AND season = ?",
            [self.indexerid, self.e, self.s],
        )
        if not len(sql_results) == 1:
            raise ApiError("Episode not found")
        episode = sql_results[0]
        # handle path options
        # absolute vs relative vs broken
        show_path = None
        try:
            show_path = show_obj.location
        except ShowDirectoryNotFoundException:
            pass

        if not show_path:  # show dir is broken ... episode path will be empty
            episode["location"] = ""
        elif not self.fullPath:
            # using the length because lstrip() removes to much
            show_path_length = len(show_path) + 1  # the / or \ yeah not that nice i know
            episode["location"] = episode["location"][show_path_length:]

        # convert stuff to human form
        if try_int(episode["airdate"], 1) > 693595:  # 1900
            episode["airdate"] = sbdatetime.sbdatetime.sbfdate(
                sbdatetime.sbdatetime.convert_to_setting(network_timezones.parse_date_time(int(episode["airdate"]), show_obj.airs, show_obj.network)),
                d_preset=dateFormat,
            )
        else:
            episode["airdate"] = "Never"

        status, quality = Quality.splitCompositeStatus(int(episode["status"]))
        episode["status"] = statusStrings_bare[status]
        episode["quality"] = get_quality_string(quality)
        episode["file_size_human"] = pretty_file_size(episode["file_size"])

        return _responds(RESULT_SUCCESS, episode)


# noinspection PyAbstractClass
class CMDEpisodeSearch(ApiCall):
    _help = {
        "desc": "Search for an episode. The response might take some time.",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
            "season": {"desc": "The season number"},
            "episode": {"desc": "The episode number"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        self.s, args = self.check_params(args, kwargs, "season", None, True, "int", [])
        self.e, args = self.check_params(args, kwargs, "episode", None, True, "int", [])

    def run(self):
        """Search for an episode"""
        show_obj = Show.find(settings.showList, int(self.indexerid))
        if not show_obj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        # retrieve the episode object and fail if we can't get one
        ep_obj = show_obj.getEpisode(self.s, self.e)
        if isinstance(ep_obj, str):
            return _responds(RESULT_FAILURE, msg="Episode not found")

        # make a queue item for it and put it on the queue
        ep_queue_item = search_queue.ManualSearchQueueItem(show_obj, ep_obj)
        settings.searchQueueScheduler.action.add_item(ep_queue_item)  # @UndefinedVariable

        # wait until the queue item tells us whether it worked or not
        while ep_queue_item.success is None:  # @UndefinedVariable
            time.sleep(1)

        # return the correct json value
        if ep_queue_item.success:
            status, quality = Quality.splitCompositeStatus(ep_obj.status)
            # TODO: split quality and status?
            return _responds(RESULT_SUCCESS, {"quality": get_quality_string(quality)}, "Snatched (" + get_quality_string(quality) + ")")

        return _responds(RESULT_FAILURE, msg="Unable to find episode")


class AbstractStartScheduler(ApiCall):
    @property
    @abc.abstractmethod
    def scheduler(self):
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def scheduler_class_str(self):
        raise NotImplementedError

    def run(self):
        error_str = "Start scheduler failed"
        if not isinstance(self.scheduler, sickchill.oldbeard.scheduler.Scheduler):
            error_str = "{0}: {1} is not initialized as a static variable".format(error_str, self.scheduler_class_str)
            return _responds(RESULT_FAILURE, msg=error_str)

        if not self.scheduler.enable:
            error_str = "{0}: {1} is not enabled".format(error_str, self.scheduler_class_str)
            return _responds(RESULT_FAILURE, msg=error_str)

        if not hasattr(self.scheduler.action, "amActive"):
            error_str = "{0}: {1} is not a valid action".format(error_str, self.scheduler.action)
            return _responds(RESULT_FAILURE, msg=error_str)

        time_remain = self.scheduler.timeLeft()
        # Force the search to start in order to skip the search interval check
        if self.scheduler.forceRun():
            cycle_time = self.scheduler.cycleTime
            next_run = datetime.datetime.now() + cycle_time
            result_str = "Force run successful: {0} search underway. Time Remaining: {1}. " "Next Run: {2}".format(
                self.scheduler_class_str, time_remain, next_run
            )
            return _responds(RESULT_SUCCESS, msg=result_str)
        else:
            # Scheduler is currently active
            error_str = "{}: {} search underway. Time remaining: {}.".format(error_str, self.scheduler_class_str, time_remain)
            return _responds(RESULT_FAILURE, msg=error_str)


class CMDFullSubtitleSearch(AbstractStartScheduler):
    def data_received(self, chunk):
        pass

    _help = {"desc": "Force a subtitle search for all shows."}

    @property
    def scheduler(self):
        return settings.subtitlesFinderScheduler

    @property
    def scheduler_class_str(self):
        return "oldbeard.subtitlesFinderScheduler"


class CMDProperSearch(AbstractStartScheduler):
    def data_received(self, chunk):
        pass

    _help = {"desc": "Force a proper search for all shows."}

    @property
    def scheduler(self):
        return settings.properFinderScheduler

    @property
    def scheduler_class_str(self):
        return "oldbeard.properFinderScheduler"


class CMDDailySearch(AbstractStartScheduler):
    def data_received(self, chunk):
        pass

    _help = {"desc": "Force a daily search for all shows."}

    @property
    def scheduler(self):
        return settings.dailySearchScheduler

    @property
    def scheduler_class_str(self):
        return "oldbeard.dailySearchScheduler"


# noinspection PyAbstractClass
class CMDEpisodeSetStatus(ApiCall):
    _help = {
        "desc": "Set the status of an episode or a season (when no episode is provided)",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
            "season": {"desc": "The season number"},
            "status": {"desc": "The status of the episode or season"},
        },
        "optionalParameters": {
            "episode": {"desc": "The episode number"},
            "force": {"desc": "True to replace existing downloaded episode or season, False otherwise"},
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        self.s, args = self.check_params(args, kwargs, "season", None, True, "int", [])
        self.status, args = self.check_params(args, kwargs, "status", None, True, "string", ["wanted", "skipped", "ignored", "failed"])
        self.e, args = self.check_params(args, kwargs, "episode", None, False, "int", [])
        self.force, args = self.check_params(args, kwargs, "force", False, False, "bool", [])

    def run(self):
        """Set the status of an episode or a season (when no episode is provided)"""
        show_obj = Show.find(settings.showList, int(self.indexerid))
        if not show_obj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        self.status = status_to_code(self.status)

        if self.e:
            ep_obj = show_obj.getEpisode(self.s, self.e)
            if not ep_obj:
                return _responds(RESULT_FAILURE, msg="Episode not found")
            ep_list = [ep_obj]
        else:
            # get all episode numbers from self, season
            ep_list = show_obj.getAllEpisodes(season=self.s)

        def _ep_result(result_code, ep, msg=""):
            return {"season": ep.season, "episode": ep.episode, "status": statusStrings_bare[ep.status], "result": result_type_map[result_code], "message": msg}

        ep_results = []
        failure = False
        start_backlog = False
        segments = {}

        sql_l = []
        for ep_obj in ep_list:
            with ep_obj.lock:
                if self.status == WANTED:
                    # figure out what episodes are wanted so we can backlog them
                    if ep_obj.season in segments:
                        segments[ep_obj.season].append(ep_obj)
                    else:
                        segments[ep_obj.season] = [ep_obj]

                # don't let them mess up UN-AIRED episodes
                if ep_obj.status == UNAIRED:
                    # noinspection PyPep8
                    if (
                        self.e is not None
                    ):  # setting the status of an un-aired is only considered a failure if we directly wanted this episode, but is ignored on a season request
                        ep_results.append(_ep_result(RESULT_FAILURE, ep_obj, "Refusing to change status because it is UN-AIRED"))
                        failure = True
                    continue

                if self.status == FAILED and not settings.USE_FAILED_DOWNLOADS:
                    ep_results.append(_ep_result(RESULT_FAILURE, ep_obj, "Refusing to change status to FAILED because failed download handling is disabled"))
                    failure = True
                    continue

                # allow the user to force setting the status for an already downloaded episode
                if ep_obj.status in Quality.DOWNLOADED + Quality.ARCHIVED and not self.force:
                    ep_results.append(_ep_result(RESULT_FAILURE, ep_obj, "Refusing to change status because it is already marked as DOWNLOADED"))
                    failure = True
                    continue

                ep_obj.status = self.status
                sql_l.append(ep_obj.get_sql())

                if self.status == WANTED:
                    start_backlog = True
                ep_results.append(_ep_result(RESULT_SUCCESS, ep_obj))

        if sql_l:
            main_db_con = db.DBConnection()
            main_db_con.mass_action(sql_l)

        extra_msg = ""
        if start_backlog:
            # noinspection PyCompatibility
            for season, segment in segments.items():
                cur_backlog_queue_item = search_queue.BacklogQueueItem(show_obj, segment)
                settings.searchQueueScheduler.action.add_item(cur_backlog_queue_item)  # @UndefinedVariable

                logger.info(f"API :: Starting backlog for {show_obj.name} season {season} because some episodes were set to WANTED")

            extra_msg = " Backlog started"

        if failure:
            return _responds(RESULT_FAILURE, ep_results, "Failed to set all or some status. Check data." + extra_msg)
        else:
            return _responds(RESULT_SUCCESS, msg="All status set successfully." + extra_msg)


# noinspection PyAbstractClass
class CMDSubtitleSearch(ApiCall):
    _help = {
        "desc": "Search for an episode subtitles. The response might take some time.",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
            "season": {"desc": "The season number"},
            "episode": {"desc": "The episode number"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        self.s, args = self.check_params(args, kwargs, "season", None, True, "int", [])
        self.e, args = self.check_params(args, kwargs, "episode", None, True, "int", [])

    def run(self):
        """Search for an episode subtitles"""
        show_obj = Show.find(settings.showList, int(self.indexerid))
        if not show_obj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        # retrieve the episode object and fail if we can't get one
        ep_obj = show_obj.getEpisode(self.s, self.e)
        if isinstance(ep_obj, str):
            return _responds(RESULT_FAILURE, msg="Episode not found")

        # noinspection PyBroadException
        try:
            new_subtitles = ep_obj.download_subtitles()
        except Exception:
            return _responds(RESULT_FAILURE, msg="Unable to find subtitles")

        if new_subtitles:
            new_languages = [sickchill.oldbeard.subtitles.name_from_code(code) for code in new_subtitles]
            status = "New subtitles downloaded: {0}".format(", ".join(new_languages))
            response = _responds(RESULT_SUCCESS, msg="New subtitles found")
        else:
            status = "No subtitles downloaded"
            response = _responds(RESULT_FAILURE, msg="Unable to find subtitles")

        ui.notifications.message("Subtitles Search", status)

        return response


# noinspection PyAbstractClass
class CMDExceptions(ApiCall):
    _help = {
        "desc": "Get the scene exceptions for all or a given show",
        "optionalParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, False, "int", [])
        self.tvdbid, args = self.check_params(args, kwargs, "tvdbid", None, False, "int", [])

    def run(self):
        """Get the scene exceptions for all or a given show"""
        cache_db_con = db.DBConnection("cache.db", row_type="dict")

        if self.indexerid is None:
            sql_results = cache_db_con.select("SELECT show_name, indexer_id AS 'indexerid' FROM scene_exceptions")
            scene_exceptions = {}
            for row in sql_results:
                indexerid = row["indexerid"]
                if indexerid not in scene_exceptions:
                    scene_exceptions[indexerid] = []
                scene_exceptions[indexerid].append(row["show_name"])

        else:
            show_obj = Show.find(settings.showList, int(self.indexerid))
            if not show_obj:
                return _responds(RESULT_FAILURE, msg="Show not found")

            sql_results = cache_db_con.select("SELECT show_name, indexer_id AS 'indexerid' FROM scene_exceptions WHERE indexer_id = ?", [self.indexerid])
            scene_exceptions = []
            for row in sql_results:
                scene_exceptions.append(row["show_name"])

        return _responds(RESULT_SUCCESS, scene_exceptions)


class HistoryApiCall(ApiCall):
    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.history = History()


# noinspection PyAbstractClass
class CMDHistory(HistoryApiCall):
    _help = {
        "desc": "Get the downloaded and/or snatched history",
        "optionalParameters": {
            "limit": {"desc": "The maximum number of results to return"},
            "type": {"desc": "Only get some entries. No value will returns every type"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.limit, args = self.check_params(args, kwargs, "limit", 100, False, "int", [])
        self.type, args = self.check_params(args, kwargs, "type", None, False, "string", ["downloaded", "snatched"])
        self.type = self.type.lower() if isinstance(self.type, str) else ""

    def run(self):
        """Get the downloaded and/or snatched history"""
        data = self.history.get(self.limit, self.type)
        results = []

        for row in data:
            status, quality = Quality.splitCompositeStatus(int(row["action"]))
            status = statusStrings_bare[status]

            if self.type and not status.lower() == self.type:
                continue

            row["status"] = status
            row["quality"] = get_quality_string(quality)
            row["date"] = _history_date_to_datetime_form(str(row["date"]))

            del row["action"]

            _rename_element(row, "show_id", "indexerid")
            row["resource_path"] = os.path.dirname(row["resource"])
            row["resource"] = os.path.basename(row["resource"])

            # Add tvdbid for backward compatibility
            row["tvdbid"] = row["indexerid"]
            results.append(row)

        return _responds(RESULT_SUCCESS, results)


# noinspection PyAbstractClass
class CMDHistoryClear(HistoryApiCall):
    _help = {"desc": "Clear the entire history"}

    def run(self):
        """Clear the entire history"""
        self.history.clear()

        return _responds(RESULT_SUCCESS, msg="History cleared")


# noinspection PyAbstractClass
class CMDHistoryTrim(HistoryApiCall):
    _help = {"desc": "Trim history entries older than 30 days"}

    def run(self):
        """Trim history entries older than 30 days"""
        self.history.trim()

        return _responds(RESULT_SUCCESS, msg="Removed history entries older than 30 days")


# noinspection PyAbstractClass
class CMDFailed(ApiCall):
    _help = {
        "desc": "Get the failed downloads",
        "optionalParameters": {
            "limit": {"desc": "The maximum number of results to return"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.limit, args = self.check_params(args, kwargs, "limit", 100, False, "int", [])

    def run(self):
        """Get the failed downloads"""

        failed_db_con = db.DBConnection("failed.db", row_type="dict")

        u_limit = min(int(self.limit), 100)
        if u_limit == 0:
            sql_results = failed_db_con.select("SELECT * FROM failed")
        else:
            sql_results = failed_db_con.select("SELECT * FROM failed LIMIT ?", [u_limit])

        return _responds(RESULT_SUCCESS, sql_results)


# noinspection PyAbstractClass
class CMDBacklog(ApiCall):
    _help = {"desc": "Get the backlogged episodes"}

    def run(self):
        """Get the backlogged episodes"""

        shows = []

        main_db_con = db.DBConnection(row_type="dict")
        for curShow in settings.showList:

            show_eps = []

            # noinspection PyPep8
            sql_results = main_db_con.select(
                "SELECT tv_episodes.*, tv_shows.paused FROM tv_episodes INNER JOIN tv_shows ON tv_episodes.showid = tv_shows.indexer_id WHERE showid = ? AND paused = 0 ORDER BY season DESC, episode DESC",
                [curShow.indexerid],
            )

            for curResult in sql_results:

                cur_ep_cat = curShow.getOverview(curResult["status"])
                if cur_ep_cat and cur_ep_cat in (Overview.WANTED, Overview.QUAL):
                    show_eps.append(curResult)

            if show_eps:
                shows.append({"indexerid": curShow.indexerid, "show_name": curShow.name, "status": curShow.status, "episodes": show_eps})

        return _responds(RESULT_SUCCESS, shows)


# noinspection PyAbstractClass
class CMDLogs(ApiCall):
    _help = {
        "desc": "Get the logs",
        "optionalParameters": {
            "min_level": {
                "desc": "The minimum level classification of log entries to return. " "Each level inherits its above levels: debug < info < warning < error"
            },
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.min_level, args = self.check_params(args, kwargs, "min_level", "error", False, "string", ["error", "warning", "info", "debug"])

    def run(self):
        """Get the logs"""
        # 10 = Debug / 20 = Info / 30 = Warning / 40 = Error
        min_level = logger.LOGGING_LEVELS[str(self.min_level).upper()]

        data = []
        if os.path.isfile(logger.log_file):
            with open(logger.log_file, "r") as f:
                data = f.readlines()

        regex = r"^(\d\d\d\d)\-(\d\d)\-(\d\d)\s*(\d\d)\:(\d\d):(\d\d)\s*([A-Z]+)\s*(.+?)\s*\:\:\s*(.*)$"

        final_data = []

        num_lines = 0
        last_line = False
        num_to_show = min(50, len(data))

        for x in reversed(data):

            match = re.match(regex, x)

            if match:
                level = match.group(7)
                if level not in logger.LOGGING_LEVELS:
                    last_line = False
                    continue

                if logger.LOGGING_LEVELS[level] >= min_level:
                    last_line = True
                    final_data.append(x.rstrip("\n"))
                else:
                    last_line = False
                    continue

            elif last_line:
                final_data.append("AA" + x)

            num_lines += 1

            if num_lines >= num_to_show:
                break

        return _responds(RESULT_SUCCESS, final_data)


# noinspection PyAbstractClass
class CMDLogsClear(ApiCall):
    _help = {
        "desc": "Clear the logs",
        "optionalParameters": {
            "level": {"desc": "The level of logs to clear"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.level, args = self.check_params(args, kwargs, "level", "warning", False, "string", ["warning", "error"])

    def run(self):
        """Clear the logs"""
        if self.level == "error":
            msg = "Error logs cleared"

            classes.ErrorViewer.clear()
        elif self.level == "warning":
            msg = "Warning logs cleared"

            classes.WarningViewer.clear()
        else:
            return _responds(RESULT_FAILURE, msg="Unknown log level: {0}".format(self.level))

        return _responds(RESULT_SUCCESS, msg=msg)


# noinspection PyAbstractClass
class CMDPostProcess(ApiCall):
    _help = {
        "desc": "Manually post-process the files in the download folder",
        "optionalParameters": {
            "path": {"desc": "The path to the folder to post-process"},
            "proc_dir": {"desc": "The path to the folder to post-process (deprecated, use path param instead)"},
            "release_name": {"desc": "The name of the release to process"},
            "nzbName": {"desc": "The name of the release to process (deprecated, use release_name param instead)"},
            "force_replace": {"desc": "Force already post-processed files to be post-processed again"},
            "force": {"desc": "Force already post-processed files to be post-processed again (deprecated, use force_replace param instead)"},
            "force_next": {"desc": "Waits for the current processing queue item to finish and returns result of this request"},
            "return_data": {"desc": "Returns the result of the post-process"},
            "quiet": {"desc": "Returns the result of the post-process (deprecated, use return_data param instead)"},
            "process_method": {"desc": "How should valid post-processed files be handled"},
            "is_priority": {"desc": "Replace the file even if it exists in a higher quality"},
            "failed": {"desc": "Mark download as failed"},
            "delete": {"desc": "Delete processed files and folders"},
            "type": {"desc": "The type of post-process being requested"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.proc_dir, args = self.check_params(args, kwargs, "proc_dir", None, False, "string", [])
        self.path, args = self.check_params(args, kwargs, "path", None, False, "string", []) or self.proc_dir

        self.nzbName, args = self.check_params(args, kwargs, "nzbName", None, False, "string", [])
        self.release_name, args = self.check_params(args, kwargs, "release_name", None, False, "string", []) or self.nzbName

        self.force, args = self.check_params(args, kwargs, "force", False, False, "bool", [])
        self.force_replace, args = self.check_params(args, kwargs, "force_replace", False, False, "bool", []) or self.force

        self.force_next, args = self.check_params(args, kwargs, "force_next", False, False, "bool", [])

        self.quiet, args = self.check_params(args, kwargs, "quiet", False, False, "bool", [])
        self.return_data, args = self.check_params(args, kwargs, "return_data", False, False, "bool", []) or self.quiet

        self.process_method, args = self.check_params(args, kwargs, "process_method", False, False, "string", PROCESS_METHODS)
        self.is_priority, args = self.check_params(args, kwargs, "is_priority", False, False, "bool", [])
        self.failed, args = self.check_params(args, kwargs, "failed", False, False, "bool", [])
        self.delete, args = self.check_params(args, kwargs, "delete", False, False, "bool", [])
        self.type, args = self.check_params(args, kwargs, "type", "auto", None, "string", ["auto", "manual"])

    def run(self):
        """Manually post-process the files in the download folder"""
        if not self.path and not settings.TV_DOWNLOAD_DIR:
            return _responds(RESULT_FAILURE, msg="You need to provide a path or set TV Download Dir")

        if not self.path:
            self.path = settings.TV_DOWNLOAD_DIR

        if not self.type:
            self.type = "manual"

        data = settings.postProcessorTaskScheduler.action.add_item(
            self.path,
            self.release_name,
            method=self.process_method,
            force=self.force_replace,
            is_priority=self.is_priority,
            failed=self.failed,
            delete=self.delete,
            mode=self.type,
            force_next=self.force_next,
        )

        if not self.return_data:
            data = ""

        return _responds(RESULT_SUCCESS, data=data, msg="Started post-process for {0}".format(self.release_name or self.path))


# noinspection PyAbstractClass
class CMDSickChill(ApiCall):
    _help = {"desc": "Get miscellaneous information about SickChill"}

    def run(self):
        """dGet miscellaneous information about SickChill"""
        data = {"sc_version": get_current_version(), "api_version": self.version, "api_commands": sorted(function_mapper)}
        return _responds(RESULT_SUCCESS, data)


# noinspection PyAbstractClass
class CMDSickChillAddRootDir(ApiCall):
    _help = {
        "desc": "Add a new root (parent) directory to SickChill",
        "requiredParameters": {
            "location": {"desc": "The full path to the new root (parent) directory"},
        },
        "optionalParameters": {
            "default": {"desc": "Make this new location the default root (parent) directory"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.location, args = self.check_params(args, kwargs, "location", None, True, "string", [])
        self.default, args = self.check_params(args, kwargs, "default", False, False, "bool", [])

    def run(self):
        """Add a new root (parent) directory to SickChill"""

        self.location = urllib.parse.unquote_plus(self.location)
        location_matched = 0
        index = 0

        # disallow adding/setting an invalid dir
        if not os.path.isdir(self.location):
            return _responds(RESULT_FAILURE, msg="Location is invalid")

        root_dirs = []

        if settings.ROOT_DIRS == "":
            self.default = 1
        else:
            root_dirs = settings.ROOT_DIRS.split("|")
            index = int(settings.ROOT_DIRS.split("|")[0])
            root_dirs.pop(0)
            # clean up the list - replace %xx escapes by their single-character equivalent
            root_dirs = [urllib.parse.unquote_plus(x) for x in root_dirs]
            for x in root_dirs:
                if x == self.location:
                    location_matched = 1
                    if self.default == 1:
                        index = root_dirs.index(self.location)
                    break

        if location_matched == 0:
            if self.default == 1:
                root_dirs.insert(0, self.location)
            else:
                root_dirs.append(self.location)

        root_dirs_new = [urllib.parse.unquote_plus(x) for x in root_dirs]
        root_dirs_new.insert(0, index)
        # noinspection PyCompatibility
        root_dirs_new = "|".join(str(x) for x in root_dirs_new)

        settings.ROOT_DIRS = root_dirs_new
        return _responds(RESULT_SUCCESS, _get_root_dirs(), msg="Root directories updated")


# noinspection PyAbstractClass
class CMDSickChillCheckVersion(ApiCall):
    _help = {"desc": "Check if a new version of SickChill is available"}

    def run(self):
        update_manager = UpdateManager()
        needs_update = update_manager.check_for_new_version()

        data = {
            "current_version": {
                "version": update_manager.get_current_version(),
            },
            "latest_version": {
                "version": update_manager.get_newest_version(),
            },
            "version_delta": update_manager.get_version_delta(),
            "needs_update": needs_update,
        }

        return _responds(RESULT_SUCCESS, data)


# noinspection PyAbstractClass
class CMDSickChillBackup(ApiCall):
    _help = {
        "desc": "Make a backup of settings, databases, and cached images",
        "optionalParameters": {"location": {"desc": "The full path to the folder where you want to save the backup (must exist)"}},
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.location, args = self.check_params(args, kwargs, "location", None, False, "string", [])

    def run(self):
        update_manager = UpdateManager()
        if self.location:
            if not os.path.isdir(self.location):
                return _responds(RESULT_FAILURE, msg="Not a valid location")
        else:
            self.location = os.path.join(settings.DATA_DIR, "backup")
            if not os.path.isdir(self.location):
                os.mkdir(self.location)

        logger.info(_("API: sc.backup backing up to {location}").format(location=self.location))
        result = update_manager._backup(self.location)
        if result:
            logger.info(_("API: sc.backup successful!"))
            return _responds(RESULT_SUCCESS, msg="Backup successful")
        else:
            logger.warning(_("API: sc.backup failed!"))
            return _responds(RESULT_FAILURE, msg="Backup failed")


# noinspection PyAbstractClass
class CMDSickChillCheckScheduler(ApiCall):
    _help = {"desc": "Get information about the scheduler"}

    def run(self):
        """Get information about the scheduler"""
        main_db_con = db.DBConnection(row_type="dict")
        sql_results = main_db_con.select("SELECT last_backlog FROM info")

        backlog_paused = settings.searchQueueScheduler.action.is_backlog_paused()  # @UndefinedVariable
        backlog_running = settings.searchQueueScheduler.action.is_backlog_in_progress()  # @UndefinedVariable
        next_backlog = settings.backlogSearchScheduler.nextRun().strftime(dateFormat)

        data = {
            "backlog_is_paused": int(backlog_paused),
            "backlog_is_running": int(backlog_running),
            "last_backlog": _ordinal_to_date_form(sql_results[0]["last_backlog"]),
            "next_backlog": next_backlog,
        }
        return _responds(RESULT_SUCCESS, data)


# noinspection PyAbstractClass
class CMDSickChillDeleteRootDir(ApiCall):
    _help = {
        "desc": "Delete a root (parent) directory from SickChill",
        "requiredParameters": {
            "location": {"desc": "The full path to the root (parent) directory to remove"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.location, args = self.check_params(args, kwargs, "location", None, True, "string", [])

    def run(self):
        """Delete a root (parent) directory from SickChill"""
        if settings.ROOT_DIRS == "":
            return _responds(RESULT_FAILURE, _get_root_dirs(), msg="No root directories detected")

        new_index = 0
        root_dirs_new = []
        root_dirs = settings.ROOT_DIRS.split("|")
        index = int(root_dirs[0])
        root_dirs.pop(0)
        # clean up the list - replace %xx escapes by their single-character equivalent
        root_dirs = [urllib.parse.unquote_plus(x) for x in root_dirs]
        old_root_dir = root_dirs[index]
        for curRootDir in root_dirs:
            if not curRootDir == self.location:
                root_dirs_new.append(curRootDir)
            else:
                new_index = 0

        for curIndex, curNewRootDir in enumerate(root_dirs_new):
            if curNewRootDir is old_root_dir:
                new_index = curIndex
                break

        root_dirs_new = [urllib.parse.unquote_plus(x) for x in root_dirs_new]
        if root_dirs_new:
            root_dirs_new.insert(0, new_index)
        # noinspection PyCompatibility
        root_dirs_new = "|".join(str(x) for x in root_dirs_new)

        settings.ROOT_DIRS = root_dirs_new
        # what if the root dir was not found?
        return _responds(RESULT_SUCCESS, _get_root_dirs(), msg="Root directory deleted")


# noinspection PyAbstractClass
class CMDSickChillGetDefaults(ApiCall):
    _help = {"desc": "Get SickChill's user default configuration value"}

    def run(self):
        """Get SickChill's user default configuration value"""

        any_qualities, best_qualities = _map_quality(settings.QUALITY_DEFAULT)

        data = {
            "status": statusStrings_bare[settings.STATUS_DEFAULT].lower(),
            "flatten_folders": int(not settings.SEASON_FOLDERS_DEFAULT),
            "season_folders": int(settings.SEASON_FOLDERS_DEFAULT),
            "initial": any_qualities,
            "archive": best_qualities,
            "future_show_paused": int(settings.COMING_EPS_DISPLAY_PAUSED),
        }
        return _responds(RESULT_SUCCESS, data)


# noinspection PyAbstractClass
class CMDSickChillGetMessages(ApiCall):
    _help = {"desc": "Get all messages"}

    def run(self):
        messages = []
        for cur_notification in ui.notifications.get_notifications(self.rh.request.remote_ip):
            messages.append({"title": cur_notification.title, "message": cur_notification.message, "type": cur_notification.type})
        return _responds(RESULT_SUCCESS, messages)


# noinspection PyAbstractClass
class CMDSickChillGetRootDirs(ApiCall):
    _help = {"desc": "Get all root (parent) directories"}

    def run(self):
        """Get all root (parent) directories"""

        return _responds(RESULT_SUCCESS, _get_root_dirs())


# noinspection PyAbstractClass
class CMDSickChillPauseBacklog(ApiCall):
    _help = {
        "desc": "Pause or un-pause the backlog search",
        "optionalParameters": {"pause": {"desc": "True to pause the backlog search, False to un-pause it"}},
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.pause, args = self.check_params(args, kwargs, "pause", False, False, "bool", [])

    def run(self):
        """Pause or un-pause the backlog search"""
        if self.pause:
            settings.searchQueueScheduler.action.pause_backlog()  # @UndefinedVariable
            return _responds(RESULT_SUCCESS, msg="Backlog paused")
        else:
            settings.searchQueueScheduler.action.unpause_backlog()  # @UndefinedVariable
            return _responds(RESULT_SUCCESS, msg="Backlog un-paused")


# noinspection PyAbstractClass
class CMDSickChillPing(ApiCall):
    _help = {"desc": "Ping SickChill to check if it is running"}

    def run(self):
        """Ping SickChill to check if it is running"""
        if settings.started:
            return _responds(RESULT_SUCCESS, {"pid": settings.PID}, "Pong")
        else:
            return _responds(RESULT_SUCCESS, msg="Pong")


# noinspection PyAbstractClass
class CMDSickChillRestart(ApiCall):
    _help = {"desc": "Restart SickChill"}

    def run(self):
        """Restart SickChill"""
        if not Restart.restart(settings.PID):
            return _responds(RESULT_FAILURE, msg="SickChill can not be restarted")

        return _responds(RESULT_SUCCESS, msg="SickChill is restarting...")


# noinspection PyAbstractClass
class CMDSickChillSearchIndexers(ApiCall):
    _help = {
        "desc": "Search for a show with a given name on all the indexers, in a specific language",
        "optionalParameters": {
            "name": {"desc": "The name of the show you want to search for"},
            "indexerid": {"desc": "Unique ID of a show"},
            "lang": {"desc": "The 2-letter language code of the desired show"},
            "only_new": {"desc": "Discard shows that are already in your show list"},
            "exact": {"desc": "Match show with search exactly"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.valid_languages = sickchill.indexer.lang_dict()
        self.name, args = self.check_params(args, kwargs, "name", None, False, "string", [])
        self.lang, args = self.check_params(args, kwargs, "lang", settings.INDEXER_DEFAULT_LANGUAGE, False, "string", list(self.valid_languages))
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, False, "int", [])
        self.only_new, args = self.check_params(args, kwargs, "only_new", True, False, "bool", [])
        self.exact, args = self.check_params(args, kwargs, "exact", False, False, "bool", [])

    def run(self):
        """Search for a show with a given name on all the indexers, in a specific language"""

        results = []
        lang_id = self.valid_languages[self.lang]

        if self.name and not self.indexerid:  # only name was given
            search_results = sickchill.indexer.search_indexers_for_series_name(self.name, self.lang)
            for indexer, indexer_results in search_results.items():
                for result in indexer_results:
                    # Skip it if it's in our show list already, and we only want new shows
                    in_show_list = sickchill.show.Show.Show.find(settings.showList, int(result["id"])) is not None
                    if in_show_list and self.only_new:
                        continue

                    results.append(
                        {
                            indexer_ids[indexer]: result["id"],
                            "name": result["seriesName"],
                            "first_aired": result["firstAired"],
                            "indexer": indexer,
                            "in_show_list": in_show_list,
                        }
                    )

                return _responds(RESULT_SUCCESS, {"results": results, "langid": lang_id})

        elif self.indexerid:
            indexer, result = sickchill.indexer.search_indexers_for_series_id(indexerid=self.indexerid, language=self.lang)
            if not indexer:
                logger.warning(f"API :: Unable to find show with id {self.indexerid}")
                return _responds(RESULT_SUCCESS, {"results": [], "langid": lang_id})

            if not result.seriesName:
                logger.debug(f"API :: Found show with indexerid: {self.indexerid}, however it contained no show name")
                return _responds(RESULT_FAILURE, msg="Show contains no name, invalid result")

            results = [{indexer_ids[indexer]: result.id, "name": str(result.seriesName), "first_aired": result.firstAired, "indexer": indexer}]

            return _responds(RESULT_SUCCESS, {"results": results, "langid": lang_id})
        else:
            return _responds(RESULT_FAILURE, msg="Either a unique id or name is required!")


# noinspection PyAbstractClass
class CMDSickChillSearchTVDB(CMDSickChillSearchIndexers):
    _help = {
        "desc": "Search for a show with a given name on The TVDB, in a specific language",
        "optionalParameters": {
            "name": {"desc": "The name of the show you want to search for"},
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "lang": {"desc": "The 2-letter language code of the desired show"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.indexerid, args = self.check_params(args, kwargs, "tvdbid", None, False, "int", [])


# noinspection PyAbstractClass
class CMDSickChillSearchTVRAGE(CMDSickChillSearchIndexers):
    """
    Deprecated, TVRage is no more.
    """

    _help = {
        "desc": "Search for a show with a given name on TVRage, in a specific language. " "This command should not longer be used, as TVRage was shut down.",
        "optionalParameters": {
            "name": {"desc": "The name of the show you want to search for"},
            "lang": {"desc": "The 2-letter language code of the desired show"},
        },
    }

    def run(self):
        return _responds(RESULT_FAILURE, msg="TVRage is no more, invalid result")


# noinspection PyAbstractClass
class CMDSickChillSetDefaults(ApiCall):
    _help = {
        "desc": "Set SickChill's user default configuration value",
        "optionalParameters": {
            "initial": {"desc": "The initial quality of a show"},
            "archive": {"desc": "The archive quality of a show"},
            "future_show_paused": {"desc": "True to list paused shows in the coming episode, False otherwise"},
            "season_folders": {"desc": "Group episodes in season folders within the show directory"},
            "status": {"desc": "Status of missing episodes"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.initial, args = self.check_params(args, kwargs, "initial", [], False, "list", ALLOWED_QUALITY_LIST)
        self.archive, args = self.check_params(args, kwargs, "archive", [], False, "list", PREFERRED_QUALITY_LIST)

        self.future_show_paused, args = self.check_params(args, kwargs, "future_show_paused", None, False, "bool", [])
        self.season_folders, args = self.check_params(args, kwargs, "flatten_folders", not bool(settings.SEASON_FOLDERS_DEFAULT), False, "bool", [])
        self.season_folders, args = self.check_params(args, kwargs, "season_folders", self.season_folders, False, "bool", [])
        self.status, args = self.check_params(args, kwargs, "status", None, False, "string", ["wanted", "skipped", "archived", "ignored"])

    def run(self):
        """Set SickChill's user default configuration value"""

        i_quality_id = []
        a_quality_id = []

        if self.initial:
            # noinspection PyTypeChecker
            for quality in self.initial:
                i_quality_id.append(QUALITY_MAP[quality])
        if self.archive:
            # noinspection PyTypeChecker
            for quality in self.archive:
                a_quality_id.append(QUALITY_MAP[quality])

        if i_quality_id or a_quality_id:
            settings.QUALITY_DEFAULT = Quality.combineQualities(i_quality_id, a_quality_id)

        if self.status:
            self.status = status_to_code(self.status)

            # only allow the status options we want
            if self.status not in (WANTED, SKIPPED, ARCHIVED, IGNORED):
                raise ApiError("Status Prohibited")

            settings.STATUS_DEFAULT = self.status

        if self.season_folders is not None:
            settings.SEASON_FOLDERS_DEFAULT = int(self.season_folders)

        if self.future_show_paused is not None:
            settings.COMING_EPS_DISPLAY_PAUSED = int(self.future_show_paused)

        return _responds(RESULT_SUCCESS, msg="Saved defaults")


# noinspection PyAbstractClass
class CMDSickChillShutdown(ApiCall):
    _help = {"desc": "Shutdown SickChill"}

    def run(self):
        """Shutdown SickChill"""
        if not Shutdown.stop(settings.PID):
            return _responds(RESULT_FAILURE, msg="SickChill can not be shut down")

        return _responds(RESULT_SUCCESS, msg="SickChill is shutting down...")


# noinspection PyAbstractClass
class CMDSickChillUpdate(ApiCall):
    _help = {"desc": "Update SickChill to the latest version available"}

    def run(self):
        update_manager = UpdateManager()

        if update_manager.check_for_new_version():
            if update_manager.run_backup_if_safe():
                update_manager.update()
                return _responds(RESULT_SUCCESS, msg="SickChill is updating ...")
            return _responds(RESULT_FAILURE, msg="SickChill could not backup config ...")
        return _responds(RESULT_FAILURE, msg="SickChill is already up to date")


# noinspection PyAbstractClass
class CMDShow(ApiCall):
    _help = {
        "desc": "Get detailed information about a show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])

    def run(self):
        """Get detailed information about a show"""
        show_obj = Show.find(settings.showList, int(self.indexerid))
        if not show_obj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        show_dict = {
            "season_list": CMDShowSeasonList((), {"indexerid": self.indexerid}).run()["data"],
            "cache": CMDShowCache((), {"indexerid": self.indexerid}).run()["data"],
            "genre": show_obj.genre,
            "quality": get_quality_string(show_obj.quality),
        }

        any_qualities, best_qualities = _map_quality(show_obj.quality)
        show_dict["quality_details"] = {"initial": any_qualities, "archive": best_qualities}

        try:
            show_dict["location"] = show_obj.location
        except ShowDirectoryNotFoundException:
            show_dict["location"] = ""

        show_dict["language"] = show_obj.lang
        show_dict["show_name"] = show_obj.name
        show_dict["start_year"] = show_obj.startyear
        show_dict["paused"] = (0, 1)[show_obj.paused]
        show_dict["subtitles"] = (0, 1)[show_obj.subtitles]
        show_dict["air_by_date"] = (0, 1)[show_obj.air_by_date]
        show_dict["season_folders"] = (0, 1)[show_obj.season_folders]
        show_dict["sports"] = (0, 1)[show_obj.sports]
        show_dict["anime"] = (0, 1)[show_obj.anime]
        show_dict["airs"] = str(show_obj.airs).replace("am", " AM").replace("pm", " PM").replace("  ", " ")
        show_dict["dvdorder"] = (0, 1)[show_obj.dvdorder]

        if show_obj.rls_require_words:
            show_dict["rls_require_words"] = show_obj.rls_require_words.split(", ")
        else:
            show_dict["rls_require_words"] = []

        if show_obj.rls_prefer_words:
            show_dict["rls_prefer_words"] = show_obj.rls_prefer_words.split(", ")
        else:
            show_dict["rls_prefer_words"] = []

        if show_obj.rls_ignore_words:
            show_dict["rls_ignore_words"] = show_obj.rls_ignore_words.split(", ")
        else:
            show_dict["rls_ignore_words"] = []

        show_dict["scene"] = (0, 1)[show_obj.scene]
        # show_dict["archive_firstmatch"] = (0, 1)[show_obj.archive_firstmatch]
        # This might need to be here for 3rd part apps?
        show_dict["archive_firstmatch"] = 1

        show_dict["indexerid"] = show_obj.indexerid
        show_dict["tvdbid"] = show_obj.indexerid
        show_dict["imdbid"] = show_obj.imdb_id

        show_dict["network"] = show_obj.network
        if not show_dict["network"]:
            show_dict["network"] = ""
        show_dict["status"] = show_obj.status

        if try_int(show_obj.nextaired, 1) > 693595:
            dt_episode_airs = sbdatetime.sbdatetime.convert_to_setting(
                network_timezones.parse_date_time(show_obj.nextaired, show_dict["airs"], show_dict["network"])
            )
            show_dict["airs"] = sbdatetime.sbdatetime.sbftime(dt_episode_airs, t_preset=timeFormat).lstrip("0").replace(" 0", " ")
            show_dict["next_ep_airdate"] = sbdatetime.sbdatetime.sbfdate(dt_episode_airs, d_preset=dateFormat)
        else:
            show_dict["next_ep_airdate"] = ""

        return _responds(RESULT_SUCCESS, show_dict)


# noinspection PyAbstractClass
class CMDShowAddExisting(ApiCall):
    _help = {
        "desc": "Add an existing show in SickChill",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
            "location": {"desc": "Full path to the existing shows's folder"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "initial": {"desc": "The initial quality of the show"},
            "archive": {"desc": "The archive quality of the show"},
            "season_folders": {"desc": "True to group episodes in season folders, False otherwise"},
            "subtitles": {"desc": "True to search for subtitles, False otherwise"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "", [])
        self.location, args = self.check_params(args, kwargs, "location", None, True, "string", [])

        self.initial, args = self.check_params(args, kwargs, "initial", [], False, "list", ALLOWED_QUALITY_LIST)
        self.archive, args = self.check_params(args, kwargs, "archive", [], False, "list", PREFERRED_QUALITY_LIST)
        self.season_folders, args = self.check_params(args, kwargs, "flatten_folders", bool(settings.SEASON_FOLDERS_DEFAULT), False, "bool", [])
        self.season_folders, args = self.check_params(args, kwargs, "season_folders", self.season_folders, False, "bool", [])
        self.subtitles, args = self.check_params(args, kwargs, "subtitles", int(settings.USE_SUBTITLES), False, "int", [])

    def run(self):
        """Add an existing show in SickChill"""
        show_obj = Show.find(settings.showList, int(self.indexerid))
        if show_obj:
            return _responds(RESULT_FAILURE, msg="An existing indexerid already exists in the database")

        if not os.path.isdir(self.location):
            return _responds(RESULT_FAILURE, msg="Not a valid location")

        indexer_name = None
        indexer_result = CMDSickChillSearchIndexers(tuple(), {indexer_ids[self.indexer]: self.indexerid}).run()

        if indexer_result["result"] == result_type_map[RESULT_SUCCESS]:
            if not indexer_result["data"]["results"]:
                return _responds(RESULT_FAILURE, msg="Empty results returned, check indexerid and try again")
            if len(indexer_result["data"]["results"]) == 1 and "name" in indexer_result["data"]["results"][0]:
                indexer_name = indexer_result["data"]["results"][0]["name"]

        if not indexer_name:
            return _responds(RESULT_FAILURE, msg="Unable to retrieve information from indexer")

        # set indexer so we can pass it along when adding show to SC
        indexer = indexer_result["data"]["results"][0]["indexer"]

        # use default quality as a fail-safe
        new_quality = int(settings.QUALITY_DEFAULT)
        i_quality_id = []
        a_quality_id = []

        if self.initial:
            # noinspection PyTypeChecker
            for quality in self.initial:
                i_quality_id.append(QUALITY_MAP[quality])
        if self.archive:
            # noinspection PyTypeChecker
            for quality in self.archive:
                a_quality_id.append(QUALITY_MAP[quality])

        if i_quality_id or a_quality_id:
            new_quality = Quality.combineQualities(i_quality_id, a_quality_id)

        settings.showQueueScheduler.action.add_show(
            int(indexer),
            int(self.indexerid),
            self.location,
            default_status=settings.STATUS_DEFAULT,
            quality=new_quality,
            season_folders=int(self.season_folders),
            subtitles=self.subtitles,
            default_status_after=settings.STATUS_DEFAULT_AFTER,
        )

        return _responds(RESULT_SUCCESS, {"name": indexer_name}, indexer_name + " has been queued to be added")


# noinspection PyAbstractClass
class CMDShowAddNew(ApiCall):
    _help = {
        "desc": "Add a new show to SickChill",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "initial": {"desc": "The initial quality of the show"},
            "location": {"desc": "The path to the folder where the show should be created"},
            "archive": {"desc": "The archive quality of the show"},
            "season_folders": {"desc": "True to group episodes in season folders, False otherwise"},
            "status": {"desc": "The status of missing episodes"},
            "lang": {"desc": "The 2-letter language code of the desired show"},
            "subtitles": {"desc": "True to search for subtitles, False otherwise"},
            "anime": {"desc": "True to mark the show as an anime, False otherwise"},
            "scene": {"desc": "True if episodes search should be made by scene numbering, False otherwise"},
            "future_status": {"desc": "The status of future episodes"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.valid_languages = sickchill.indexer.lang_dict()
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        self.location, args = self.check_params(args, kwargs, "location", None, False, "string", [])
        self.initial, args = self.check_params(args, kwargs, "initial", None, False, "list", ALLOWED_QUALITY_LIST)
        self.archive, args = self.check_params(args, kwargs, "archive", None, False, "list", PREFERRED_QUALITY_LIST)
        self.season_folders, args = self.check_params(args, kwargs, "flatten_folders", bool(settings.SEASON_FOLDERS_DEFAULT), False, "bool", [])
        self.season_folders, args = self.check_params(args, kwargs, "season_folders", self.season_folders, False, "bool", [])
        self.status, args = self.check_params(args, kwargs, "status", None, False, "string", ["wanted", "skipped", "ignored"])
        self.lang, args = self.check_params(args, kwargs, "lang", settings.INDEXER_DEFAULT_LANGUAGE, False, "string", list(self.valid_languages))
        self.subtitles, args = self.check_params(args, kwargs, "subtitles", bool(settings.USE_SUBTITLES), False, "bool", [])
        self.anime, args = self.check_params(args, kwargs, "anime", bool(settings.ANIME_DEFAULT), False, "bool", [])
        self.scene, args = self.check_params(args, kwargs, "scene", bool(settings.SCENE_DEFAULT), False, "bool", [])
        self.future_status, args = self.check_params(args, kwargs, "future_status", None, False, "string", ["wanted", "skipped", "ignored"])

    def run(self):
        """Add a new show to SickChill"""
        show_obj = Show.find(settings.showList, int(self.indexerid))
        if show_obj:
            return _responds(RESULT_FAILURE, msg="An existing indexerid already exists in database")

        if not self.location:
            if settings.ROOT_DIRS != "":
                root_dirs = settings.ROOT_DIRS.split("|")
                root_dirs.pop(0)
                default_index = int(settings.ROOT_DIRS.split("|")[0])
                self.location = root_dirs[default_index]
            else:
                return _responds(RESULT_FAILURE, msg="Root directory is not set, please provide a location")

        if not os.path.isdir(self.location):
            return _responds(RESULT_FAILURE, msg="'" + self.location + "' is not a valid location")

        # use default quality as a fail-safe
        new_quality = int(settings.QUALITY_DEFAULT)
        i_quality_id = []
        a_quality_id = []

        if self.initial:
            # noinspection PyTypeChecker
            for quality in self.initial:
                i_quality_id.append(QUALITY_MAP[quality])
        if self.archive:
            # noinspection PyTypeChecker
            for quality in self.archive:
                a_quality_id.append(QUALITY_MAP[quality])

        if i_quality_id or a_quality_id:
            new_quality = Quality.combineQualities(i_quality_id, a_quality_id)

        # use default status as a fail-safe
        new_status = settings.STATUS_DEFAULT
        if self.status:
            self.status = status_to_code(self.status)

            # only allow the status options we want
            if self.status not in (WANTED, SKIPPED, IGNORED):
                return _responds(RESULT_FAILURE, msg="Status prohibited")
            new_status = self.status

        # use default status as a fail-safe
        default_ep_status_after = settings.STATUS_DEFAULT_AFTER
        if self.future_status:
            # convert the string status to a int
            self.future_status = status_to_code(self.future_status)

            # only allow the status options we want
            if self.future_status not in (WANTED, SKIPPED, IGNORED):
                return _responds(RESULT_FAILURE, msg="Status prohibited")
            default_ep_status_after = self.future_status

        indexer_name = None
        indexer_result = CMDSickChillSearchIndexers(tuple(), {indexer_ids[self.indexer]: self.indexerid, "lang": self.lang}).run()

        if indexer_result["result"] == result_type_map[RESULT_SUCCESS]:
            if not indexer_result["data"]["results"]:
                return _responds(RESULT_FAILURE, msg="Empty results returned, check indexerid and try again")
            if len(indexer_result["data"]["results"]) == 1 and "name" in indexer_result["data"]["results"][0]:
                indexer_name = indexer_result["data"]["results"][0]["name"]

        if not indexer_name:
            return _responds(RESULT_FAILURE, msg="Unable to retrieve information from indexer")

        # set indexer for found show so we can pass it along
        indexer = indexer_result["data"]["results"][0]["indexer"]

        # moved the logic check to the end in an attempt to eliminate empty directory being created from previous errors
        show_path = os.path.join(self.location, sanitize_filename(indexer_name))

        # don't create show dir if config says not to
        if settings.ADD_SHOWS_WO_DIR:
            logger.info("Skipping initial creation of " + show_path + " due to config.ini setting")
        else:
            dir_exists = helpers.makeDir(show_path)
            if not dir_exists:
                logger.exception("API :: Unable to create the folder " + show_path + ", can't add the show")
                return _responds(RESULT_FAILURE, {"path": show_path}, "Unable to create the folder " + show_path + ", can't add the show")
            else:
                helpers.chmodAsParent(show_path)

        settings.showQueueScheduler.action.add_show(
            int(indexer),
            int(self.indexerid),
            show_path,
            default_status=new_status,
            quality=new_quality,
            season_folders=int(self.season_folders),
            lang=self.lang,
            subtitles=self.subtitles,
            anime=self.anime,
            scene=self.scene,
            default_status_after=default_ep_status_after,
        )

        return _responds(RESULT_SUCCESS, {"name": indexer_name}, indexer_name + " has been queued to be added")


# noinspection PyAbstractClass
class CMDShowCache(ApiCall):
    _help = {
        "desc": "Check SickChill's cache to see if the images (poster, banner, fanart) for a show are valid",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])

    def run(self):
        """Check SickChill's cache to see if the images (poster, banner, fanart) for a show are valid"""
        show_obj = Show.find(settings.showList, int(self.indexerid))
        if not show_obj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        # TODO: catch if cache dir is missing/invalid.. so it doesn't break show/show.cache
        # return {"poster": 0, "banner": 0}

        has_poster = has_banner = has_fanart = has_poster_thumb = has_banner_thumb = 0

        if settings.IMAGE_CACHE.has_poster(show_obj.indexerid):
            has_poster = 1
        if settings.IMAGE_CACHE.has_poster_thumb(show_obj.indexerid):
            has_poster_thumb = 1

        if settings.IMAGE_CACHE.has_banner(show_obj.indexerid):
            has_banner = 1
        if settings.IMAGE_CACHE.has_banner_thumb(show_obj.indexerid):
            has_banner_thumb = 1

        if settings.IMAGE_CACHE.has_fanart(show_obj.indexerid):
            has_fanart = 1

        return _responds(
            RESULT_SUCCESS,
            {"poster": has_poster, "banner": has_banner, "fanart": has_fanart, "poster_thumb": has_poster_thumb, "banner_thumb": has_banner_thumb},
        )


# noinspection PyAbstractClass
class CMDShowDelete(ApiCall):
    _help = {
        "desc": "Delete a show in SickChill",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "removefiles": {"desc": "True to delete the files associated with the show, False otherwise. This can not be undone!"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        self.removefiles, args = self.check_params(args, kwargs, "removefiles", False, False, "bool", [])

    def run(self):
        """Delete a show in SickChill"""
        error, show = Show.delete(self.indexerid, self.removefiles)

        if error:
            return _responds(RESULT_FAILURE, msg=error)

        return _responds(RESULT_SUCCESS, msg="{0} has been queued to be deleted".format(show.name))


# noinspection PyAbstractClass
class CMDShowGetQuality(ApiCall):
    _help = {
        "desc": "Get the quality setting of a show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])

    def run(self):
        """Get the quality setting of a show"""
        show_obj = Show.find(settings.showList, int(self.indexerid))
        if not show_obj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        any_qualities, best_qualities = _map_quality(show_obj.quality)

        return _responds(RESULT_SUCCESS, {"initial": any_qualities, "archive": best_qualities})


# noinspection PyAbstractClass
class CMDShowGetPoster(ApiCall):
    _help = {
        "desc": "Get the poster of a show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "media_format": {"desc": '"normal" for normal size poster (default), "thumb" for small size poster'},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        self.tvdbid, args = self.check_params(args, kwargs, "tvdbid", None, False, "int", [])
        self.media_format, args = self.check_params(args, kwargs, "media_format", "normal", False, "string", ["normal", "thumb"])

    def run(self):
        """Get the poster a show"""
        method = (settings.IMAGE_CACHE.poster_path, settings.IMAGE_CACHE.poster_thumb_path)[self.media_format == "thumb"]
        return {
            "outputType": "image",
            "image": method(self.tvdbid or self.indexerid),
        }


# noinspection PyAbstractClass
class CMDShowGetBanner(ApiCall):
    _help = {
        "desc": "Get the banner of a show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "media_format": {"desc": '"normal" for normal size banner (default), "thumb" for small size banner'},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        self.tvdbid, args = self.check_params(args, kwargs, "tvdbid", None, False, "int", [])
        self.media_format, args = self.check_params(args, kwargs, "media_format", "normal", False, "string", ["normal", "thumb"])

    def run(self):
        """Get the banner of a show"""
        method = (settings.IMAGE_CACHE.banner_path, settings.IMAGE_CACHE.banner_thumb_path)[self.media_format == "thumb"]
        return {
            "outputType": "image",
            "image": method(self.tvdbid or self.indexerid),
        }


# noinspection PyAbstractClass
class CMDShowGetNetworkLogo(ApiCall):
    _help = {
        "desc": "Get the network logo of a show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        self.tvdbid, args = self.check_params(args, kwargs, "tvdbid", None, False, "int", [])

    def run(self):
        """
        :return: Get the network logo of a show
        """
        show = Show.find(settings.showList, self.tvdbid or self.indexerid)
        path = Path(settings.PROG_DIR) / "gui" / settings.GUI_NAME / "images" / "network"
        path /= show.network_logo_name + ".png"
        return {"outputType": "image", "image": path.resolve()}


# noinspection PyAbstractClass
class CMDShowGetFanArt(ApiCall):
    _help = {
        "desc": "Get the fan art of a show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        self.tvdbid, args = self.check_params(args, kwargs, "tvdbid", None, False, "int", [])

    def run(self):
        """Get the fan art of a show"""
        return {
            "outputType": "image",
            "image": settings.IMAGE_CACHE.fanart_path(self.tvdbid or self.indexerid),
        }


# noinspection PyAbstractClass
class CMDShowPause(ApiCall):
    _help = {
        "desc": "Pause or un-pause a show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "pause": {"desc": "True to pause the show, False otherwise"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        self.pause, args = self.check_params(args, kwargs, "pause", False, False, "bool", [])

    def run(self):
        """Pause or un-pause a show"""
        error, show = Show.pause(self.indexerid, self.pause)

        if error:
            return _responds(RESULT_FAILURE, msg=error)

        return _responds(RESULT_SUCCESS, msg="{0} has been {1}".format(show.name, ("resumed", "paused")[show.paused]))


# noinspection PyAbstractClass
class CMDShowRefresh(ApiCall):
    _help = {
        "desc": "Refresh a show in SickChill",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])

    def run(self):
        """Refresh a show in SickChill"""
        error, show = Show.refresh(self.indexerid)

        if error:
            return _responds(RESULT_FAILURE, msg=error)

        return _responds(RESULT_SUCCESS, msg="{0} has queued to be refreshed".format(show.name))


# noinspection PyAbstractClass
class CMDShowSeasonList(ApiCall):
    _help = {
        "desc": "Get the list of seasons of a show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {"tvdbid": {"desc": "thetvdb.com unique ID of a show"}, "sort": {"desc": "Return the seasons in ascending or descending order"}},
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        self.sort, args = self.check_params(args, kwargs, "sort", "desc", False, "string", ["asc", "desc"])

    def run(self):
        """Get the list of seasons of a show"""
        show_obj = Show.find(settings.showList, int(self.indexerid))
        if not show_obj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        main_db_con = db.DBConnection(row_type="dict")
        if self.sort == "asc":
            sql_results = main_db_con.select("SELECT DISTINCT season FROM tv_episodes WHERE showid = ? ORDER BY season ASC", [self.indexerid])
        else:
            sql_results = main_db_con.select("SELECT DISTINCT season FROM tv_episodes WHERE showid = ? ORDER BY season DESC", [self.indexerid])
        season_list = []  # a list with all season numbers
        for row in sql_results:
            season_list.append(int(row["season"]))

        return _responds(RESULT_SUCCESS, season_list)


# noinspection PyAbstractClass
class CMDShowSeasons(ApiCall):
    _help = {
        "desc": "Get the list of episodes for one or all seasons of a show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "season": {"desc": "The season number"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        self.season, args = self.check_params(args, kwargs, "season", None, False, "int", [])

    def run(self):
        """Get the list of episodes for one or all seasons of a show"""
        sho_obj = Show.find(settings.showList, int(self.indexerid))
        if not sho_obj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        main_db_con = db.DBConnection(row_type="dict")

        if self.season is None:
            sql_results = main_db_con.select(
                "SELECT name, episode, airdate, status, release_name, season, location, file_size, subtitles FROM tv_episodes WHERE showid = ?",
                [self.indexerid],
            )
            seasons = {}
            for row in sql_results:
                status, quality = Quality.splitCompositeStatus(int(row["status"]))
                row["status"] = statusStrings_bare[status]
                row["quality"] = get_quality_string(quality)
                if try_int(row["airdate"], 1) > 693595:  # 1900
                    dt_episode_airs = sbdatetime.sbdatetime.convert_to_setting(network_timezones.parse_date_time(row["airdate"], sho_obj.airs, sho_obj.network))
                    row["airdate"] = sbdatetime.sbdatetime.sbfdate(dt_episode_airs, d_preset=dateFormat)
                else:
                    row["airdate"] = "Never"
                cur_season = int(row["season"])
                cur_episode = int(row["episode"])
                del row["season"]
                del row["episode"]
                if cur_season not in seasons:
                    seasons[cur_season] = {}
                seasons[cur_season][cur_episode] = row

        else:
            sql_results = main_db_con.select(
                "SELECT name, episode, airdate, status, location, file_size, release_name, subtitles FROM tv_episodes WHERE showid = ? AND season = ?",
                [self.indexerid, self.season],
            )
            if not sql_results:
                return _responds(RESULT_FAILURE, msg="Season not found")
            seasons = {}
            for row in sql_results:
                cur_episode = int(row["episode"])
                del row["episode"]
                status, quality = Quality.splitCompositeStatus(int(row["status"]))
                row["status"] = statusStrings_bare[status]
                row["quality"] = get_quality_string(quality)
                if try_int(row["airdate"], 1) > 693595:  # 1900
                    dt_episode_airs = sbdatetime.sbdatetime.convert_to_setting(network_timezones.parse_date_time(row["airdate"], sho_obj.airs, sho_obj.network))
                    row["airdate"] = sbdatetime.sbdatetime.sbfdate(dt_episode_airs, d_preset=dateFormat)
                else:
                    row["airdate"] = "Never"
                if cur_episode not in seasons:
                    seasons[cur_episode] = {}
                seasons[cur_episode] = row

        return _responds(RESULT_SUCCESS, seasons)


# noinspection PyAbstractClass
class CMDShowSetQuality(ApiCall):
    _help = {
        "desc": "Set the quality setting of a show. If no quality is provided, the default user setting is used.",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "initial": {"desc": "The initial quality of the show"},
            "archive": {"desc": "The archive quality of the show"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        self.initial, args = self.check_params(args, kwargs, "initial", [], False, "list", ALLOWED_QUALITY_LIST)
        self.archive, args = self.check_params(args, kwargs, "archive", [], False, "list", PREFERRED_QUALITY_LIST)

    def run(self):
        """Set the quality setting of a show. If no quality is provided, the default user setting is used."""
        show_obj = Show.find(settings.showList, int(self.indexerid))
        if not show_obj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        # use default quality as a fail-safe
        new_quality = int(settings.QUALITY_DEFAULT)
        i_quality_id = []
        a_quality_id = []

        if self.initial:
            # noinspection PyTypeChecker
            for quality in self.initial:
                i_quality_id.append(QUALITY_MAP[quality])
        if self.archive:
            # noinspection PyTypeChecker
            for quality in self.archive:
                a_quality_id.append(QUALITY_MAP[quality])

        if i_quality_id or a_quality_id:
            new_quality = Quality.combineQualities(i_quality_id, a_quality_id)
        show_obj.quality = new_quality

        return _responds(RESULT_SUCCESS, msg=show_obj.name + " quality has been changed to " + get_quality_string(show_obj.quality))


# noinspection PyAbstractClass
class CMDShowStats(ApiCall):
    _help = {
        "desc": "Get episode statistics for a given show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])

    def run(self):
        """Get episode statistics for a given show"""
        show_obj = Show.find(settings.showList, int(self.indexerid))
        if not show_obj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        # show stats
        episode_status_counts_total = {"total": 0}
        for status in statusStrings_bare:
            if status in [UNKNOWN, DOWNLOADED, SNATCHED, SNATCHED_PROPER, ARCHIVED]:
                continue
            episode_status_counts_total[status] = 0

        # add all the downloaded qualities
        episode_qualities_counts_download = {"total": 0}
        for statusCode in Quality.DOWNLOADED + Quality.ARCHIVED:
            status, quality = Quality.splitCompositeStatus(statusCode)
            if quality in [Quality.NONE]:
                continue
            episode_qualities_counts_download[statusCode] = 0

        # add all snatched qualities
        episode_qualities_counts_snatch = {"total": 0}
        for statusCode in Quality.SNATCHED + Quality.SNATCHED_PROPER:
            status, quality = Quality.splitCompositeStatus(statusCode)
            if quality in [Quality.NONE]:
                continue
            episode_qualities_counts_snatch[statusCode] = 0

        main_db_con = db.DBConnection(row_type="dict")
        sql_results = main_db_con.select("SELECT status, season FROM tv_episodes WHERE season != 0 AND showid = ?", [self.indexerid])
        # the main loop that goes through all episodes
        for row in sql_results:
            status, quality = Quality.splitCompositeStatus(int(row["status"]))

            episode_status_counts_total["total"] += 1

            if status in Quality.DOWNLOADED + Quality.ARCHIVED:
                episode_qualities_counts_download["total"] += 1
                # noinspection PyTypeChecker
                episode_qualities_counts_download[int(row["status"])] += 1
            elif status in Quality.SNATCHED + Quality.SNATCHED_PROPER:
                episode_qualities_counts_snatch["total"] += 1
                # noinspection PyTypeChecker
                episode_qualities_counts_snatch[int(row["status"])] += 1
            elif status > 0:  # we don't count NONE = 0 = N/A
                episode_status_counts_total[status] += 1

        # the outgoing container
        episodes_stats = {"downloaded": {}}
        # turning codes into strings
        for statusCode in episode_qualities_counts_download:
            if statusCode == "total":
                episodes_stats["downloaded"]["total"] = episode_qualities_counts_download[statusCode]
                continue
            status, quality = Quality.splitCompositeStatus(int(statusCode))
            status_string = Quality.qualityStrings[quality].lower().replace(" ", "_").replace("(", "").replace(")", "")
            episodes_stats["downloaded"][status_string] = episode_qualities_counts_download[statusCode]

        episodes_stats["snatched"] = {}
        # turning codes into strings
        # and combining proper and normal
        for statusCode in episode_qualities_counts_snatch:
            if statusCode == "total":
                episodes_stats["snatched"]["total"] = episode_qualities_counts_snatch[statusCode]
                continue
            status, quality = Quality.splitCompositeStatus(int(statusCode))
            status_string = Quality.qualityStrings[quality].lower().replace(" ", "_").replace("(", "").replace(")", "")
            if Quality.qualityStrings[quality] in episodes_stats["snatched"]:
                episodes_stats["snatched"][status_string] += episode_qualities_counts_snatch[statusCode]
            else:
                episodes_stats["snatched"][status_string] = episode_qualities_counts_snatch[statusCode]

        for statusCode in episode_status_counts_total:
            if statusCode == "total":
                episodes_stats["total"] = episode_status_counts_total[statusCode]
                continue
            # status, quality = Quality.splitCompositeStatus(int(statusCode))
            status_string = statusStrings_bare[statusCode].lower().replace(" ", "_").replace("(", "").replace(")", "")
            episodes_stats[status_string] = episode_status_counts_total[statusCode]

        return _responds(RESULT_SUCCESS, episodes_stats)


# noinspection PyAbstractClass
class CMDShowUpdate(ApiCall):
    _help = {
        "desc": "Update a show in SickChill",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])

    def run(self):
        """Update a show in SickChill"""
        show_obj = Show.find(settings.showList, int(self.indexerid))
        if not show_obj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        try:
            settings.showQueueScheduler.action.update_show(show_obj, True)  # @UndefinedVariable
            return _responds(RESULT_SUCCESS, msg=str(show_obj.name) + " has queued to be updated")
        except CantUpdateShowException as error:
            logger.debug("API::Unable to update show: {0}".format(error))
            return _responds(RESULT_FAILURE, msg=f"Unable to update {show_obj.name}")


# noinspection PyAbstractClass
class CMDShows(ApiCall):
    _help = {
        "desc": "Get all shows in SickChill",
        "optionalParameters": {
            "sort": {"desc": "The sorting strategy to apply to the list of shows"},
            "paused": {"desc": "True: show paused, False: show un-paused, otherwise show all"},
        },
    }

    def __init__(self, args, kwargs):
        super().__init__(args, kwargs)
        self.sort, args = self.check_params(args, kwargs, "sort", "id", False, "string", ["id", "name"])
        self.paused, args = self.check_params(args, kwargs, "paused", None, False, "bool", [])

    def run(self):
        """Get all shows in SickChill"""
        shows = {}
        for curShow in settings.showList:
            # If self.paused is None: show all, 0: show un-paused, 1: show paused
            if self.paused is not None and self.paused != curShow.paused:
                continue

            show_dict = {
                "paused": (0, 1)[curShow.paused],
                "quality": get_quality_string(curShow.quality),
                "language": curShow.lang,
                "air_by_date": (0, 1)[curShow.air_by_date],
                "sports": (0, 1)[curShow.sports],
                "anime": (0, 1)[curShow.anime],
                "indexerid": curShow.indexerid,
                "tvdbid": curShow.indexerid,
                "network": curShow.network,
                "show_name": curShow.name,
                "status": curShow.status,
                "subtitles": (0, 1)[curShow.subtitles],
            }

            if try_int(curShow.nextaired, 1) > 693595:  # 1900
                dt_episode_airs = sbdatetime.sbdatetime.convert_to_setting(
                    network_timezones.parse_date_time(curShow.nextaired, curShow.airs, show_dict["network"])
                )
                show_dict["next_ep_airdate"] = sbdatetime.sbdatetime.sbfdate(dt_episode_airs, d_preset=dateFormat)
            else:
                show_dict["next_ep_airdate"] = ""

            show_dict["cache"] = CMDShowCache((), {"indexerid": curShow.indexerid}).run()["data"]
            if not show_dict["network"]:
                show_dict["network"] = ""
            if self.sort == "name":
                shows[curShow.name] = show_dict
            else:
                shows[curShow.indexerid] = show_dict

        return _responds(RESULT_SUCCESS, shows)


# noinspection PyAbstractClass
class CMDShowsStats(ApiCall):
    _help = {"desc": "Get the global shows and episodes statistics"}

    def run(self):
        """Get the global shows and episodes statistics"""
        stats = Show.overall_stats()

        return _responds(
            RESULT_SUCCESS,
            {
                "ep_downloaded": stats["episodes"]["downloaded"],
                "ep_snatched": stats["episodes"]["snatched"],
                "ep_total": stats["episodes"]["total"],
                "shows_active": stats["shows"]["active"],
                "shows_total": stats["shows"]["total"],
            },
        )


# WARNING: never define a cmd call string that contains a "_" (underscore)
# this is reserved for cmd indexes used while cmd chaining

# WARNING: never define a param name that contains a "." (dot)
# this is reserved for cmd namespaces used while cmd chaining
function_mapper = {
    "help": CMDHelp,
    "future": CMDComingEpisodes,
    "episode": CMDEpisode,
    "episode.search": CMDEpisodeSearch,
    "episode.setstatus": CMDEpisodeSetStatus,
    "episode.subtitlesearch": CMDSubtitleSearch,
    "exceptions": CMDExceptions,
    "history": CMDHistory,
    "history.clear": CMDHistoryClear,
    "history.trim": CMDHistoryTrim,
    "postprocess": CMDPostProcess,
    "failed": CMDFailed,
    "backlog": CMDBacklog,
    "logs": CMDLogs,
    "logs.clear": CMDLogsClear,
    "sc": CMDSickChill,
    "sc.addrootdir": CMDSickChillAddRootDir,
    "sc.checkversion": CMDSickChillCheckVersion,
    "sc.backup": CMDSickChillBackup,
    "sc.checkscheduler": CMDSickChillCheckScheduler,
    "sc.deleterootdir": CMDSickChillDeleteRootDir,
    "sc.getdefaults": CMDSickChillGetDefaults,
    "sc.getmessages": CMDSickChillGetMessages,
    "sc.getrootdirs": CMDSickChillGetRootDirs,
    "sc.pausebacklog": CMDSickChillPauseBacklog,
    "sc.ping": CMDSickChillPing,
    "sc.restart": CMDSickChillRestart,
    "sc.dailysearch": CMDDailySearch,
    "sc.propersearch": CMDProperSearch,
    "sc.subtitlesearch": CMDFullSubtitleSearch,
    "sc.searchindexers": CMDSickChillSearchIndexers,
    "sc.searchtvdb": CMDSickChillSearchTVDB,
    "sc.searchtvrage": CMDSickChillSearchTVRAGE,
    "sc.setdefaults": CMDSickChillSetDefaults,
    "sc.update": CMDSickChillUpdate,
    "sc.shutdown": CMDSickChillShutdown,
    "show": CMDShow,
    "show.addexisting": CMDShowAddExisting,
    "show.addnew": CMDShowAddNew,
    "show.cache": CMDShowCache,
    "show.delete": CMDShowDelete,
    "show.getquality": CMDShowGetQuality,
    "show.getposter": CMDShowGetPoster,
    "show.getbanner": CMDShowGetBanner,
    "show.getnetworklogo": CMDShowGetNetworkLogo,
    "show.getfanart": CMDShowGetFanArt,
    "show.pause": CMDShowPause,
    "show.refresh": CMDShowRefresh,
    "show.seasonlist": CMDShowSeasonList,
    "show.seasons": CMDShowSeasons,
    "show.setquality": CMDShowSetQuality,
    "show.stats": CMDShowStats,
    "show.update": CMDShowUpdate,
    "shows": CMDShows,
    "shows.stats": CMDShowsStats,
    # Compatibility with old 3rd party tools
    "sb": CMDSickChill,
    "sb.addrootdir": CMDSickChillAddRootDir,
    "sb.checkversion": CMDSickChillCheckVersion,
    "sb.backup": CMDSickChillBackup,
    "sb.checkscheduler": CMDSickChillCheckScheduler,
    "sb.deleterootdir": CMDSickChillDeleteRootDir,
    "sb.getdefaults": CMDSickChillGetDefaults,
    "sb.getmessages": CMDSickChillGetMessages,
    "sb.getrootdirs": CMDSickChillGetRootDirs,
    "sb.pausebacklog": CMDSickChillPauseBacklog,
    "sb.ping": CMDSickChillPing,
    "sb.restart": CMDSickChillRestart,
    "sb.dailysearch": CMDDailySearch,
    "sb.propersearch": CMDProperSearch,
    "sb.subtitlesearch": CMDFullSubtitleSearch,
    "sb.searchindexers": CMDSickChillSearchIndexers,
    "sb.searchtvdb": CMDSickChillSearchTVDB,
    "sb.searchtvrage": CMDSickChillSearchTVRAGE,
    "sb.setdefaults": CMDSickChillSetDefaults,
    "sb.update": CMDSickChillUpdate,
    "sb.shutdown": CMDSickChillShutdown,
}
