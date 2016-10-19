# coding=utf-8
# Author: Dennis Lutter <lad1337@gmail.com>
# Author: Jonathon Saine <thezoggy@gmail.com>
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

# TODO: break this up into separate files
# pylint: disable=line-too-long,too-many-lines,abstract-method
# pylint: disable=no-member,method-hidden,missing-docstring,invalid-name

import datetime
import io
import os
import re
import time
import traceback
import urllib

import sickbeard
from sickbeard import classes, db, helpers, image_cache, logger, network_timezones, processTV, sbdatetime, search_queue, \
    ui
from sickbeard.common import ARCHIVED, DOWNLOADED, FAILED, IGNORED, Overview, Quality, SKIPPED, SNATCHED, \
    SNATCHED_PROPER, UNAIRED, UNKNOWN, WANTED, statusStrings
from sickbeard.versionChecker import CheckVersion
from sickrage.helper.common import dateFormat, dateTimeFormat, pretty_file_size, sanitize_filename, timeFormat, try_int
from sickrage.helper.encoding import ek
from sickrage.helper.exceptions import CantUpdateShowException, ShowDirectoryNotFoundException, ex
from sickrage.helper.quality import get_quality_string
from sickrage.media.ShowBanner import ShowBanner
from sickrage.media.ShowFanArt import ShowFanArt
from sickrage.media.ShowNetworkLogo import ShowNetworkLogo
from sickrage.media.ShowPoster import ShowPoster
from sickrage.show.ComingEpisodes import ComingEpisodes
from sickrage.show.History import History
from sickrage.show.Show import Show
from sickrage.system.Restart import Restart
from sickrage.system.Shutdown import Shutdown

try:
    import json
except ImportError:
    # pylint: disable=import-error
    import simplejson as json

# pylint: disable=import-error
from tornado.web import RequestHandler

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


class ApiHandler(RequestHandler):
    """ api class that returns json results """
    version = 5  # use an int since float-point is unpredictable

    def __init__(self, *args, **kwargs):
        super(ApiHandler, self).__init__(*args, **kwargs)

    # def set_default_headers(self):
    #     self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')

    def get(self, *args, **kwargs):
        kwargs = self.request.arguments
        for arg, value in kwargs.iteritems():
            if len(value) == 1:
                kwargs[arg] = value[0]

        args = args[1:]

        # set the output callback
        # default json
        output_callback_dict = {
            'default': self._out_as_json,
            'image': self._out_as_image,
        }

        access_msg = u"API :: " + self.request.remote_ip + " - gave correct API KEY. ACCESS GRANTED"
        logger.log(access_msg, logger.DEBUG)

        # set the original call_dispatcher as the local _call_dispatcher
        _call_dispatcher = self.call_dispatcher
        # if profile was set wrap "_call_dispatcher" in the profile function
        if 'profile' in kwargs:
            from profilehooks import profile

            _call_dispatcher = profile(_call_dispatcher, immediate=True)
            del kwargs["profile"]

        try:
            out_dict = _call_dispatcher(args, kwargs)
        except Exception as e:  # real internal error oohhh nooo :(
            logger.log(u"API :: " + ex(e), logger.ERROR)
            error_data = {
                "error_msg": ex(e),
                "args": args,
                "kwargs": kwargs
            }
            out_dict = _responds(RESULT_FATAL, error_data,
                                 "SickRage encountered an internal error! Please report to the Devs")

        if 'outputType' in out_dict:
            output_callback = output_callback_dict[out_dict['outputType']]
        else:
            output_callback = output_callback_dict['default']

        try:
            self.finish(output_callback(out_dict))
        except Exception:
            pass

    def _out_as_image(self, _dict):
        self.set_header('Content-Type', _dict['image'].get_media_type())
        return _dict['image'].get_media()

    def _out_as_json(self, _dict):
        self.set_header("Content-Type", "application/json;charset=UTF-8")
        try:
            out = json.dumps(_dict, ensure_ascii=False, sort_keys=True)
            callback = self.get_query_argument('callback', None) or self.get_query_argument('jsonp', None)
            if callback:
                out = callback + '(' + out + ');'  # wrap with JSONP call if requested
        except Exception as e:  # if we fail to generate the output fake an error
            logger.log(u"API :: " + traceback.format_exc(), logger.DEBUG)
            out = '{{"result": "{0}", "message": "error while composing output: {1}"}}'.format(result_type_map[RESULT_ERROR], ex(e))
        return out

    def call_dispatcher(self, args, kwargs):  # pylint:disable=too-many-branches
        """ calls the appropriate CMD class
            looks for a cmd in args and kwargs
            or calls the TVDBShorthandWrapper when the first args element is a number
            or returns an error that there is no such cmd
        """
        logger.log(u"API :: all args: '" + str(args) + "'", logger.DEBUG)
        logger.log(u"API :: all kwargs: '" + str(kwargs) + "'", logger.DEBUG)

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

                logger.log(u"API :: " + cmd + ": cur_kwargs " + str(cur_kwargs), logger.DEBUG)
                if not (cmd in ('show.getbanner', 'show.getfanart', 'show.getnetworklogo', 'show.getposter') and
                        multi_commands):  # skip these cmd while chaining
                    try:
                        if cmd in function_mapper:
                            func = function_mapper.get(cmd)  # map function
                            func.rh = self  # add request handler to function
                            cur_out_dict = func(cur_args, cur_kwargs).run()  # call function and get response
                        elif _is_int(cmd):
                            cur_out_dict = TVDBShorthandWrapper(cur_args, cur_kwargs, cmd).run()
                        else:
                            cur_out_dict = _responds(RESULT_ERROR, "No such cmd: '" + cmd + "'")
                    except ApiError as error:  # Api errors that we raised, they are harmless
                        cur_out_dict = _responds(RESULT_ERROR, msg=ex(error))
                else:  # if someone chained one of the forbidden commands they will get an error for this one cmd
                    cur_out_dict = _responds(RESULT_ERROR, msg="The cmd '" + cmd + "' is not supported while chaining")

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
            out_dict = CMD_SickBeard(args, kwargs).run()

        return out_dict

    @staticmethod
    def filter_params(cmd, args, kwargs):
        """ return only params kwargs that are for cmd
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


class ApiCall(ApiHandler):

    _help = {"desc": "This command is not documented. Please report this to the developers."}

    def __init__(self, args, kwargs):
        # missing
        try:
            if self._missing:
                self.run = self.return_missing
        except AttributeError:
            pass

        # help
        if 'help' in kwargs:
            self.run = self.return_help

    def run(self):
        # override with real output function in subclass
        return {}

    def return_help(self):
        try:
            if self._requiredParams:
                pass
        except AttributeError:
            self._requiredParams = []
        try:
            if self._optionalParams:
                pass
        except AttributeError:
            self._optionalParams = []

        for paramDict, paramType in [(self._requiredParams, "requiredParameters"),
                                     (self._optionalParams, "optionalParameters")]:

            if paramType in self._help:
                for paramName in paramDict:
                    if paramName not in self._help[paramType]:
                        self._help[paramType][paramName] = {}
                    if paramDict[paramName]["allowedValues"]:
                        self._help[paramType][paramName]["allowedValues"] = paramDict[paramName]["allowedValues"]
                    else:
                        self._help[paramType][paramName]["allowedValues"] = "see desc"
                    self._help[paramType][paramName]["defaultValue"] = paramDict[paramName]["defaultValue"]
                    self._help[paramType][paramName]["type"] = paramDict[paramName]["type"]

            elif paramDict:
                for paramName in paramDict:
                    self._help[paramType] = {}
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

    def check_params(self, args, kwargs, key, default, required, arg_type, allowed_values):

        """ function to check passed params for the shorthand wrapper
            and to detect missing/required params
        """

        # auto-select indexer
        if key in indexer_ids:
            if "tvdbid" in kwargs:
                key = "tvdbid"

            self.indexer = indexer_ids.index(key)

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
        if required:
            try:
                self._missing
                self._requiredParams.append(key)
            except AttributeError:
                self._missing = []
                self._requiredParams = {key: {"allowedValues": allowed_values,
                                              "defaultValue": org_default,
                                              "type": arg_type}}

            if missing and key not in self._missing:
                self._missing.append(key)
        else:
            try:
                self._optionalParams[key] = {"allowedValues": allowed_values,
                                             "defaultValue": org_default,
                                             "type": arg_type}
            except AttributeError:
                self._optionalParams = {key: {"allowedValues": allowed_values,
                                              "defaultValue": org_default,
                                              "type": arg_type}}

        if default:
            default = self._check_param_type(default, key, arg_type)
            if arg_type == "bool":
                arg_type = []
            self._check_param_value(default, key, allowed_values)

        return default, args

    def _check_param_type(self, value, name, arg_type):
        """ checks if value can be converted / parsed to arg_type
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
            logger.log(u'API :: Invalid param type: "{0}" can not be checked. Ignoring it.'.format(str(arg_type)), logger.ERROR)

        if error:
            # this is a real ApiError !!
            raise ApiError(u'param "{0}" with given value "{1}" could not be parsed into "{2}"'.format(str(name), str(value), str(arg_type)))

        return value

    def _check_param_value(self, value, name, allowed_values):
        """ will check if value (or all values in it ) are in allowed values
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
                raise ApiError(u"param: '" + str(name) + "' with given value: '" + str(
                    value) + "' is out of allowed range '" + str(allowed_values) + "'")


class TVDBShorthandWrapper(ApiCall):
    _help = {"desc": "This is an internal function wrapper. Call the help command directly for more information."}

    def __init__(self, args, kwargs, sid):
        self.origArgs = args
        self.kwargs = kwargs
        self.sid = sid

        self.s, args = self.check_params(args, kwargs, "s", None, False, "ignore", [])
        self.e, args = self.check_params(args, kwargs, "e", None, False, "ignore", [])
        self.args = args

        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ internal function wrapper """
        args = (self.sid,) + self.origArgs
        if self.e:
            return CMD_Episode(args, self.kwargs).run()
        elif self.s:
            return CMD_ShowSeasons(args, self.kwargs).run()
        else:
            return CMD_Show(args, self.kwargs).run()


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
    return {"result": result_type_map[result_type],
            "message": msg,
            "data": {} if not data else data}


def _get_status_strings(s):
    return statusStrings[s]


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


def _map_quality(show_obj):
    quality_map = _get_quality_map()

    any_qualities = []
    best_qualities = []

    i_quality_id, a_quality_id = Quality.splitQuality(int(show_obj))
    if i_quality_id:
        for quality in i_quality_id:
            any_qualities.append(quality_map[quality])
    if a_quality_id:
        for quality in a_quality_id:
            best_qualities.append(quality_map[quality])
    return any_qualities, best_qualities


def _get_quality_map():
    return {Quality.SDTV: 'sdtv',
            Quality.SDDVD: 'sddvd',
            Quality.HDTV: 'hdtv',
            Quality.RAWHDTV: 'rawhdtv',
            Quality.FULLHDTV: 'fullhdtv',
            Quality.HDWEBDL: 'hdwebdl',
            Quality.FULLHDWEBDL: 'fullhdwebdl',
            Quality.HDBLURAY: 'hdbluray',
            Quality.FULLHDBLURAY: 'fullhdbluray',
            Quality.UNKNOWN: 'unknown'}


def _get_root_dirs():
    if sickbeard.ROOT_DIRS == "":
        return {}

    root_dir = {}
    root_dirs = sickbeard.ROOT_DIRS.split('|')
    default_index = int(sickbeard.ROOT_DIRS.split('|')[0])

    root_dir["default_index"] = int(sickbeard.ROOT_DIRS.split('|')[0])
    # remove default_index value from list (this fixes the offset)
    root_dirs.pop(0)

    if len(root_dirs) < default_index:
        return {}

    # clean up the list - replace %xx escapes by their single-character equivalent
    root_dirs = [urllib.unquote_plus(x) for x in root_dirs]

    default_dir = root_dirs[default_index]

    dir_list = []
    for root_dir in root_dirs:
        valid = 1
        try:
            ek(os.listdir, root_dir)
        except Exception:
            valid = 0
        default = 0
        if root_dir is default_dir:
            default = 1

        cur_dir = {
            'valid': valid,
            'location': root_dir,
            'default': default
        }
        dir_list.append(cur_dir)

    return dir_list


class ApiError(Exception):
    """
    Generic API error
    """


class IntParseError(Exception):
    """
    A value could not be parsed into an int, but should be parse-able to an int
    """


# -------------------------------------------------------------------------------------#


class CMD_Help(ApiCall):
    _help = {
        "desc": "Get help about a given command",
        "optionalParameters": {
            "subject": {"desc": "The name of the command to get the help of"},
        }
    }

    def __init__(self, args, kwargs):
        # required
        # optional
        self.subject, args = self.check_params(args, kwargs, "subject", "help", False, "string", function_mapper.keys())
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Get help about a given command """
        if self.subject in function_mapper:
            out = _responds(RESULT_SUCCESS, function_mapper.get(self.subject)((), {"help": 1}).run())
        else:
            out = _responds(RESULT_FAILURE, msg="No such cmd")
        return out


class CMD_ComingEpisodes(ApiCall):
    _help = {
        "desc": "Get the coming episodes",
        "optionalParameters": {
            "sort": {"desc": "Change the sort order"},
            "type": {"desc": "One or more categories of coming episodes, separated by |"},
            "paused": {
                "desc": "0 to exclude paused shows, 1 to include them, or omitted to use SickRage default value"
            },
        }
    }

    def __init__(self, args, kwargs):
        # required
        # optional
        self.sort, args = self.check_params(args, kwargs, "sort", "date", False, "string", ComingEpisodes.sorts.keys())
        self.type, args = self.check_params(args, kwargs, "type", '|'.join(ComingEpisodes.categories), False, "list",
                                            ComingEpisodes.categories)
        self.paused, args = self.check_params(args, kwargs, "paused", bool(sickbeard.COMING_EPS_DISPLAY_PAUSED), False,
                                              "bool", [])
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Get the coming episodes """
        grouped_coming_episodes = ComingEpisodes.get_coming_episodes(self.type, self.sort, True, self.paused)
        data = {section: [] for section in grouped_coming_episodes.keys()}

        for section, coming_episodes in grouped_coming_episodes.iteritems():
            for coming_episode in coming_episodes:
                data[section].append({
                    'airdate': coming_episode['airdate'],
                    'airs': coming_episode['airs'],
                    'ep_name': coming_episode['name'],
                    'ep_plot': coming_episode['description'],
                    'episode': coming_episode['episode'],
                    'indexerid': coming_episode['indexer_id'],
                    'network': coming_episode['network'],
                    'paused': coming_episode['paused'],
                    'quality': coming_episode['quality'],
                    'season': coming_episode['season'],
                    'show_name': coming_episode['show_name'],
                    'show_status': coming_episode['status'],
                    'tvdbid': coming_episode['tvdbid'],
                    'weekday': coming_episode['weekday']
                })

        return _responds(RESULT_SUCCESS, data)


class CMD_Episode(ApiCall):
    _help = {
        "desc": "Get detailed information about an episode",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
            "season": {"desc": "The season number"},
            "episode": {"desc": "The episode number"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "full_path": {
                "desc": "Return the full absolute show location (if valid, and True), or the relative show location"
            },
        }
    }

    def __init__(self, args, kwargs):
        # required
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        self.s, args = self.check_params(args, kwargs, "season", None, True, "int", [])
        self.e, args = self.check_params(args, kwargs, "episode", None, True, "int", [])
        # optional
        self.fullPath, args = self.check_params(args, kwargs, "full_path", False, False, "bool", [])
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Get detailed information about an episode """
        show_obj = Show.find(sickbeard.showList, int(self.indexerid))
        if not show_obj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        main_db_con = db.DBConnection(row_type="dict")
        sql_results = main_db_con.select(
            "SELECT name, description, airdate, status, location, file_size, release_name, subtitles FROM tv_episodes WHERE showid = ? AND episode = ? AND season = ?",
            [self.indexerid, self.e, self.s])
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
        if try_int(episode['airdate'], 1) > 693595:  # 1900
            episode['airdate'] = sbdatetime.sbdatetime.sbfdate(sbdatetime.sbdatetime.convert_to_setting(
                network_timezones.parse_date_time(int(episode['airdate']), show_obj.airs, show_obj.network)), d_preset=dateFormat)
        else:
            episode['airdate'] = 'Never'

        status, quality = Quality.splitCompositeStatus(int(episode["status"]))
        episode["status"] = _get_status_strings(status)
        episode["quality"] = get_quality_string(quality)
        episode["file_size_human"] = pretty_file_size(episode["file_size"])

        return _responds(RESULT_SUCCESS, episode)


class CMD_EpisodeSearch(ApiCall):
    _help = {
        "desc": "Search for an episode. The response might take some time.",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
            "season": {"desc": "The season number"},
            "episode": {"desc": "The episode number"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, args, kwargs):
        # required
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        self.s, args = self.check_params(args, kwargs, "season", None, True, "int", [])
        self.e, args = self.check_params(args, kwargs, "episode", None, True, "int", [])
        # optional
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Search for an episode """
        show_obj = Show.find(sickbeard.showList, int(self.indexerid))
        if not show_obj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        # retrieve the episode object and fail if we can't get one
        ep_obj = show_obj.getEpisode(self.s, self.e)
        if isinstance(ep_obj, str):
            return _responds(RESULT_FAILURE, msg="Episode not found")

        # make a queue item for it and put it on the queue
        ep_queue_item = search_queue.ManualSearchQueueItem(show_obj, ep_obj)
        sickbeard.searchQueueScheduler.action.add_item(ep_queue_item)  # @UndefinedVariable

        # wait until the queue item tells us whether it worked or not
        while ep_queue_item.success is None:  # @UndefinedVariable
            time.sleep(1)

        # return the correct json value
        if ep_queue_item.success:
            status, quality = Quality.splitCompositeStatus(ep_obj.status)  # @UnusedVariable
            # TODO: split quality and status?
            return _responds(RESULT_SUCCESS, {"quality": get_quality_string(quality)},
                             "Snatched (" + get_quality_string(quality) + ")")

        return _responds(RESULT_FAILURE, msg='Unable to find episode')


class CMD_EpisodeSetStatus(ApiCall):
    _help = {
        "desc": "Set the status of an episode or a season (when no episode is provided)",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
            "season": {"desc": "The season number"},
            "status": {"desc": "The status of the episode or season"}
        },
        "optionalParameters": {
            "episode": {"desc": "The episode number"},
            "force": {"desc": "True to replace existing downloaded episode or season, False otherwise"},
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, args, kwargs):
        # required
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        self.s, args = self.check_params(args, kwargs, "season", None, True, "int", [])
        self.status, args = self.check_params(args, kwargs, "status", None, True, "string",
                                              ["wanted", "skipped", "ignored", "failed"])
        # optional
        self.e, args = self.check_params(args, kwargs, "episode", None, False, "int", [])
        self.force, args = self.check_params(args, kwargs, "force", False, False, "bool", [])
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Set the status of an episode or a season (when no episode is provided) """
        show_obj = Show.find(sickbeard.showList, int(self.indexerid))
        if not show_obj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        # convert the string status to a int
        for status in statusStrings:
            if str(statusStrings[status]).lower() == str(self.status).lower():
                self.status = status
                break
        else:  # if we don't break out of the for loop we got here.
            # the allowed values has at least one item that could not be matched against the internal status strings
            raise ApiError("The status string could not be matched to a status. Report to Devs!")

        ep_list = []
        if self.e:
            ep_obj = show_obj.getEpisode(self.s, self.e)
            if not ep_obj:
                return _responds(RESULT_FAILURE, msg="Episode not found")
            ep_list = [ep_obj]
        else:
            # get all episode numbers from self, season
            ep_list = show_obj.getAllEpisodes(season=self.s)

        def _ep_result(result_code, ep, msg=""):
            return {'season': ep.season, 'episode': ep.episode, 'status': _get_status_strings(ep.status),
                    'result': result_type_map[result_code], 'message': msg}

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
                    if self.e is not None:  # setting the status of an un-aired is only considered a failure if we directly wanted this episode, but is ignored on a season request
                        ep_results.append(
                            _ep_result(RESULT_FAILURE, ep_obj, "Refusing to change status because it is UN-AIRED"))
                        failure = True
                    continue

                if self.status == FAILED and not sickbeard.USE_FAILED_DOWNLOADS:
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
            for season, segment in segments.iteritems():
                cur_backlog_queue_item = search_queue.BacklogQueueItem(show_obj, segment)
                sickbeard.searchQueueScheduler.action.add_item(cur_backlog_queue_item)  # @UndefinedVariable

                logger.log(u"API :: Starting backlog for " + show_obj.name + " season " + str(
                    season) + " because some episodes were set to WANTED")

            extra_msg = " Backlog started"

        if failure:
            return _responds(RESULT_FAILURE, ep_results, 'Failed to set all or some status. Check data.' + extra_msg)
        else:
            return _responds(RESULT_SUCCESS, msg='All status set successfully.' + extra_msg)


class CMD_SubtitleSearch(ApiCall):
    _help = {
        "desc": "Search for an episode subtitles. The response might take some time.",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
            "season": {"desc": "The season number"},
            "episode": {"desc": "The episode number"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, args, kwargs):
        # required
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        self.s, args = self.check_params(args, kwargs, "season", None, True, "int", [])
        self.e, args = self.check_params(args, kwargs, "episode", None, True, "int", [])
        # optional
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Search for an episode subtitles """
        show_obj = Show.find(sickbeard.showList, int(self.indexerid))
        if not show_obj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        # retrieve the episode object and fail if we can't get one
        ep_obj = show_obj.getEpisode(self.s, self.e)
        if isinstance(ep_obj, str):
            return _responds(RESULT_FAILURE, msg="Episode not found")

        try:
            new_subtitles = ep_obj.download_subtitles()
        except Exception:
            return _responds(RESULT_FAILURE, msg='Unable to find subtitles')

        if new_subtitles:
            new_languages = [sickbeard.subtitles.name_from_code(code) for code in new_subtitles]
            status = 'New subtitles downloaded: {0}'.format(', '.join(new_languages))
            response = _responds(RESULT_SUCCESS, msg='New subtitles found')
        else:
            status = 'No subtitles downloaded'
            response = _responds(RESULT_FAILURE, msg='Unable to find subtitles')

        ui.notifications.message('Subtitles Search', status)

        return response


class CMD_Exceptions(ApiCall):
    _help = {
        "desc": "Get the scene exceptions for all or a given show",
        "optionalParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, args, kwargs):
        # required
        # optional
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, False, "int", [])

        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Get the scene exceptions for all or a given show """
        cache_db_con = db.DBConnection('cache.db', row_type='dict')

        if self.indexerid is None:
            sql_results = cache_db_con.select("SELECT show_name, indexer_id AS 'indexerid' FROM scene_exceptions")
            scene_exceptions = {}
            for row in sql_results:
                indexerid = row["indexerid"]
                if indexerid not in scene_exceptions:
                    scene_exceptions[indexerid] = []
                scene_exceptions[indexerid].append(row["show_name"])

        else:
            show_obj = Show.find(sickbeard.showList, int(self.indexerid))
            if not show_obj:
                return _responds(RESULT_FAILURE, msg="Show not found")

            sql_results = cache_db_con.select(
                "SELECT show_name, indexer_id AS 'indexerid' FROM scene_exceptions WHERE indexer_id = ?",
                [self.indexerid])
            scene_exceptions = []
            for row in sql_results:
                scene_exceptions.append(row["show_name"])

        return _responds(RESULT_SUCCESS, scene_exceptions)


class CMD_History(ApiCall):
    _help = {
        "desc": "Get the downloaded and/or snatched history",
        "optionalParameters": {
            "limit": {"desc": "The maximum number of results to return"},
            "type": {"desc": "Only get some entries. No value will returns every type"},
        }
    }

    def __init__(self, args, kwargs):
        # required
        # optional
        self.limit, args = self.check_params(args, kwargs, "limit", 100, False, "int", [])
        self.type, args = self.check_params(args, kwargs, "type", None, False, "string", ["downloaded", "snatched"])
        self.type = self.type.lower() if isinstance(self.type, str) else ''

        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Get the downloaded and/or snatched history """
        data = History().get(self.limit, self.type)
        results = []

        for row in data:
            status, quality = Quality.splitCompositeStatus(int(row["action"]))
            status = _get_status_strings(status)

            if self.type and not status.lower() == self.type:
                continue

            row["status"] = status
            row["quality"] = get_quality_string(quality)
            row["date"] = _history_date_to_datetime_form(str(row["date"]))

            del row["action"]

            _rename_element(row, "show_id", "indexerid")
            row["resource_path"] = ek(os.path.dirname, row["resource"])
            row["resource"] = ek(os.path.basename, row["resource"])

            # Add tvdbid for backward compatibility
            row['tvdbid'] = row['indexerid']
            results.append(row)

        return _responds(RESULT_SUCCESS, results)


class CMD_HistoryClear(ApiCall):
    _help = {"desc": "Clear the entire history"}

    def __init__(self, args, kwargs):
        # required
        # optional
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Clear the entire history """
        History().clear()

        return _responds(RESULT_SUCCESS, msg="History cleared")


class CMD_HistoryTrim(ApiCall):
    _help = {"desc": "Trim history entries older than 30 days"}

    def __init__(self, args, kwargs):
        # required
        # optional
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Trim history entries older than 30 days """
        History().trim()

        return _responds(RESULT_SUCCESS, msg='Removed history entries older than 30 days')


class CMD_Failed(ApiCall):
    _help = {
        "desc": "Get the failed downloads",
        "optionalParameters": {
            "limit": {"desc": "The maximum number of results to return"},
        }
    }

    def __init__(self, args, kwargs):
        # required
        # optional
        self.limit, args = self.check_params(args, kwargs, "limit", 100, False, "int", [])
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Get the failed downloads """

        failed_db_con = db.DBConnection('failed.db', row_type="dict")

        u_limit = min(int(self.limit), 100)
        if u_limit == 0:
            sql_results = failed_db_con.select("SELECT * FROM failed")
        else:
            sql_results = failed_db_con.select("SELECT * FROM failed LIMIT ?", [u_limit])

        return _responds(RESULT_SUCCESS, sql_results)


class CMD_Backlog(ApiCall):
    _help = {"desc": "Get the backlogged episodes"}

    def __init__(self, args, kwargs):
        # required
        # optional
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Get the backlogged episodes """

        shows = []

        main_db_con = db.DBConnection(row_type="dict")
        for curShow in sickbeard.showList:

            show_eps = []

            sql_results = main_db_con.select(
                "SELECT tv_episodes.*, tv_shows.paused FROM tv_episodes INNER JOIN tv_shows ON tv_episodes.showid = tv_shows.indexer_id WHERE showid = ? and paused = 0 ORDER BY season DESC, episode DESC",
                [curShow.indexerid])

            for curResult in sql_results:

                cur_ep_cat = curShow.getOverview(curResult["status"])
                if cur_ep_cat and cur_ep_cat in (Overview.WANTED, Overview.QUAL):
                    show_eps.append(curResult)

            if show_eps:
                shows.append({
                    "indexerid": curShow.indexerid,
                    "show_name": curShow.name,
                    "status": curShow.status,
                    "episodes": show_eps
                })

        return _responds(RESULT_SUCCESS, shows)


class CMD_Logs(ApiCall):
    _help = {
        "desc": "Get the logs",
        "optionalParameters": {
            "min_level": {
                "desc":
                    "The minimum level classification of log entries to return. "
                    "Each level inherits its above levels: debug < info < warning < error"
            },
        }
    }

    def __init__(self, args, kwargs):
        # required
        # optional
        self.min_level, args = self.check_params(args, kwargs, "min_level", "error", False, "string",
                                                 ["error", "warning", "info", "debug"])
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Get the logs """
        # 10 = Debug / 20 = Info / 30 = Warning / 40 = Error
        min_level = logger.LOGGING_LEVELS[str(self.min_level).upper()]

        data = []
        if ek(os.path.isfile, logger.log_file):
            with io.open(logger.log_file, 'r', encoding='utf-8') as f:
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


class CMD_LogsClear(ApiCall):
    _help = {
        "desc": "Clear the logs",
        "optionalParameters": {
            "level": {"desc": "The level of logs to clear"},
        },
    }

    def __init__(self, args, kwargs):
        # required
        # optional
        self.level, args = self.check_params(args, kwargs, "level", "warning", False, "string", ["warning", "error"])
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Clear the logs """
        if self.level == "error":
            msg = "Error logs cleared"

            classes.ErrorViewer.clear()
        elif self.level == "warning":
            msg = "Warning logs cleared"

            classes.WarningViewer.clear()
        else:
            return _responds(RESULT_FAILURE, msg="Unknown log level: {0}".format(self.level))

        return _responds(RESULT_SUCCESS, msg=msg)


class CMD_PostProcess(ApiCall):
    _help = {
        "desc": "Manually post-process the files in the download folder",
        "optionalParameters": {
            "path": {"desc": "The path to the folder to post-process"},
            "force_replace": {"desc": "Force already post-processed files to be post-processed again"},
            "return_data": {"desc": "Returns the result of the post-process"},
            "process_method": {"desc": "How should valid post-processed files be handled"},
            "is_priority": {"desc": "Replace the file even if it exists in a higher quality"},
            "failed": {"desc": "Mark download as failed"},
            "type": {"desc": "The type of post-process being requested"},
        }
    }

    def __init__(self, args, kwargs):
        # required
        # optional
        self.path, args = self.check_params(args, kwargs, "path", None, False, "string", [])
        self.force_replace, args = self.check_params(args, kwargs, "force_replace", False, False, "bool", [])
        self.return_data, args = self.check_params(args, kwargs, "return_data", False, False, "bool", [])
        self.process_method, args = self.check_params(args, kwargs, "process_method", False, False, "string",
                                                      ["copy", "symlink", "hardlink", "move"])
        self.is_priority, args = self.check_params(args, kwargs, "is_priority", False, False, "bool", [])
        self.failed, args = self.check_params(args, kwargs, "failed", False, False, "bool", [])
        self.type, args = self.check_params(args, kwargs, "type", "auto", None, "string", ["auto", "manual"])
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Manually post-process the files in the download folder """
        if not self.path and not sickbeard.TV_DOWNLOAD_DIR:
            return _responds(RESULT_FAILURE, msg="You need to provide a path or set TV Download Dir")

        if not self.path:
            self.path = sickbeard.TV_DOWNLOAD_DIR

        if not self.type:
            self.type = 'manual'

        data = processTV.processDir(self.path, process_method=self.process_method, force=self.force_replace,
                                    is_priority=self.is_priority, failed=self.failed, proc_type=self.type)

        if not self.return_data:
            data = ""

        return _responds(RESULT_SUCCESS, data=data, msg="Started post-process for {0}".format(self.path))


class CMD_SickBeard(ApiCall):
    _help = {"desc": "Get miscellaneous information about SickRage"}

    def __init__(self, args, kwargs):
        # required
        # optional
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ dGet miscellaneous information about SickRage """
        data = {"sr_version": sickbeard.BRANCH, "api_version": self.version,
                "api_commands": sorted(function_mapper.keys())}
        return _responds(RESULT_SUCCESS, data)


class CMD_SickBeardAddRootDir(ApiCall):
    _help = {
        "desc": "Add a new root (parent) directory to SickRage",
        "requiredParameters": {
            "location": {"desc": "The full path to the new root (parent) directory"},
        },
        "optionalParameters": {
            "default": {"desc": "Make this new location the default root (parent) directory"},
        }
    }

    def __init__(self, args, kwargs):
        # required
        self.location, args = self.check_params(args, kwargs, "location", None, True, "string", [])
        # optional
        self.default, args = self.check_params(args, kwargs, "default", False, False, "bool", [])
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Add a new root (parent) directory to SickRage """

        self.location = urllib.unquote_plus(self.location)
        location_matched = 0
        index = 0

        # disallow adding/setting an invalid dir
        if not ek(os.path.isdir, self.location):
            return _responds(RESULT_FAILURE, msg="Location is invalid")

        root_dirs = []

        if sickbeard.ROOT_DIRS == "":
            self.default = 1
        else:
            root_dirs = sickbeard.ROOT_DIRS.split('|')
            index = int(sickbeard.ROOT_DIRS.split('|')[0])
            root_dirs.pop(0)
            # clean up the list - replace %xx escapes by their single-character equivalent
            root_dirs = [urllib.unquote_plus(x) for x in root_dirs]
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

        root_dirs_new = [urllib.unquote_plus(x) for x in root_dirs]
        root_dirs_new.insert(0, index)
        root_dirs_new = '|'.join(unicode(x) for x in root_dirs_new)

        sickbeard.ROOT_DIRS = root_dirs_new
        return _responds(RESULT_SUCCESS, _get_root_dirs(), msg="Root directories updated")


class CMD_SickBeardCheckVersion(ApiCall):
    _help = {"desc": "Check if a new version of SickRage is available"}

    def __init__(self, args, kwargs):
        # required
        # optional
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        check_version = CheckVersion()
        needs_update = check_version.check_for_new_version()

        data = {
            "current_version": {
                "branch": check_version.get_branch(),
                "commit": check_version.updater.get_cur_commit_hash(),
                "version": check_version.updater.get_cur_version(),
            },
            "latest_version": {
                "branch": check_version.get_branch(),
                "commit": check_version.updater.get_newest_commit_hash(),
                "version": check_version.updater.get_newest_version(),
            },
            "commits_offset": check_version.updater.get_num_commits_behind(),
            "needs_update": needs_update,
        }

        return _responds(RESULT_SUCCESS, data)


class CMD_SickBeardCheckScheduler(ApiCall):
    _help = {"desc": "Get information about the scheduler"}

    def __init__(self, args, kwargs):
        # required
        # optional
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Get information about the scheduler """
        main_db_con = db.DBConnection()
        sql_results = main_db_con.select("SELECT last_backlog FROM info")

        backlog_paused = sickbeard.searchQueueScheduler.action.is_backlog_paused()  # @UndefinedVariable
        backlog_running = sickbeard.searchQueueScheduler.action.is_backlog_in_progress()  # @UndefinedVariable
        next_backlog = sickbeard.backlogSearchScheduler.nextRun().strftime(dateFormat).decode(sickbeard.SYS_ENCODING)

        data = {"backlog_is_paused": int(backlog_paused), "backlog_is_running": int(backlog_running),
                "last_backlog": _ordinal_to_date_form(sql_results[0]["last_backlog"]),
                "next_backlog": next_backlog}
        return _responds(RESULT_SUCCESS, data)


class CMD_SickBeardDeleteRootDir(ApiCall):
    _help = {
        "desc": "Delete a root (parent) directory from SickRage",
        "requiredParameters": {
            "location": {"desc": "The full path to the root (parent) directory to remove"},
        }
    }

    def __init__(self, args, kwargs):
        # required
        self.location, args = self.check_params(args, kwargs, "location", None, True, "string", [])
        # optional
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Delete a root (parent) directory from SickRage """
        if sickbeard.ROOT_DIRS == "":
            return _responds(RESULT_FAILURE, _get_root_dirs(), msg="No root directories detected")

        new_index = 0
        root_dirs_new = []
        root_dirs = sickbeard.ROOT_DIRS.split('|')
        index = int(root_dirs[0])
        root_dirs.pop(0)
        # clean up the list - replace %xx escapes by their single-character equivalent
        root_dirs = [urllib.unquote_plus(x) for x in root_dirs]
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

        root_dirs_new = [urllib.unquote_plus(x) for x in root_dirs_new]
        if len(root_dirs_new) > 0:
            root_dirs_new.insert(0, new_index)
        root_dirs_new = "|".join(unicode(x) for x in root_dirs_new)

        sickbeard.ROOT_DIRS = root_dirs_new
        # what if the root dir was not found?
        return _responds(RESULT_SUCCESS, _get_root_dirs(), msg="Root directory deleted")


class CMD_SickBeardGetDefaults(ApiCall):
    _help = {"desc": "Get SickRage's user default configuration value"}

    def __init__(self, args, kwargs):
        # required
        # optional
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Get SickRage's user default configuration value """

        any_qualities, best_qualities = _map_quality(sickbeard.QUALITY_DEFAULT)

        data = {"status": statusStrings[sickbeard.STATUS_DEFAULT].lower(),
                "flatten_folders": int(sickbeard.FLATTEN_FOLDERS_DEFAULT), "initial": any_qualities,
                "archive": best_qualities, "future_show_paused": int(sickbeard.COMING_EPS_DISPLAY_PAUSED)}
        return _responds(RESULT_SUCCESS, data)


class CMD_SickBeardGetMessages(ApiCall):
    _help = {"desc": "Get all messages"}

    def __init__(self, args, kwargs):
        # required
        # optional
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        messages = []
        for cur_notification in ui.notifications.get_notifications(self.rh.request.remote_ip):
            messages.append({"title": cur_notification.title,
                             "message": cur_notification.message,
                             "type": cur_notification.type})
        return _responds(RESULT_SUCCESS, messages)


class CMD_SickBeardGetRootDirs(ApiCall):
    _help = {"desc": "Get all root (parent) directories"}

    def __init__(self, args, kwargs):
        # required
        # optional
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Get all root (parent) directories """

        return _responds(RESULT_SUCCESS, _get_root_dirs())


class CMD_SickBeardPauseBacklog(ApiCall):
    _help = {
        "desc": "Pause or un-pause the backlog search",
        "optionalParameters": {
            "pause": {"desc": "True to pause the backlog search, False to un-pause it"}
        }
    }

    def __init__(self, args, kwargs):
        # required
        # optional
        self.pause, args = self.check_params(args, kwargs, "pause", False, False, "bool", [])
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Pause or un-pause the backlog search """
        if self.pause:
            sickbeard.searchQueueScheduler.action.pause_backlog()  # @UndefinedVariable
            return _responds(RESULT_SUCCESS, msg="Backlog paused")
        else:
            sickbeard.searchQueueScheduler.action.unpause_backlog()  # @UndefinedVariable
            return _responds(RESULT_SUCCESS, msg="Backlog un-paused")


class CMD_SickBeardPing(ApiCall):
    _help = {"desc": "Ping SickRage to check if it is running"}

    def __init__(self, args, kwargs):
        # required
        # optional
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Ping SickRage to check if it is running """
        if sickbeard.started:
            return _responds(RESULT_SUCCESS, {"pid": sickbeard.PID}, "Pong")
        else:
            return _responds(RESULT_SUCCESS, msg="Pong")


class CMD_SickBeardRestart(ApiCall):
    _help = {"desc": "Restart SickRage"}

    def __init__(self, args, kwargs):
        # required
        # optional
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Restart SickRage """
        if not Restart.restart(sickbeard.PID):
            return _responds(RESULT_FAILURE, msg='SickRage can not be restarted')

        return _responds(RESULT_SUCCESS, msg="SickRage is restarting...")


class CMD_SickBeardSearchIndexers(ApiCall):
    _help = {
        "desc": "Search for a show with a given name on all the indexers, in a specific language",
        "optionalParameters": {
            "name": {"desc": "The name of the show you want to search for"},
            "indexerid": {"desc": "Unique ID of a show"},
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "lang": {"desc": "The 2-letter language code of the desired show"},
        }
    }

    def __init__(self, args, kwargs):
        self.valid_languages = sickbeard.indexerApi().config['langabbv_to_id']
        # required
        # optional
        self.name, args = self.check_params(args, kwargs, "name", None, False, "string", [])
        self.lang, args = self.check_params(args, kwargs, "lang", sickbeard.INDEXER_DEFAULT_LANGUAGE, False, "string",
                                            self.valid_languages.keys())
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, False, "int", [])

        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Search for a show with a given name on all the indexers, in a specific language """

        results = []
        lang_id = self.valid_languages[self.lang]

        if self.name and not self.indexerid:  # only name was given
            for _indexer in sickbeard.indexerApi().indexers if self.indexer == 0 else [int(self.indexer)]:
                indexer_api_params = sickbeard.indexerApi(_indexer).api_params.copy()

                indexer_api_params['language'] = self.lang or sickbeard.INDEXER_DEFAULT_LANGUAGE

                indexer_api_params['actors'] = False
                indexer_api_params['custom_ui'] = classes.AllShowsListUI

                t = sickbeard.indexerApi(_indexer).indexer(**indexer_api_params)

                try:
                    api_data = t[str(self.name).encode()]
                except (sickbeard.indexer_shownotfound, sickbeard.indexer_showincomplete, sickbeard.indexer_error):
                    logger.log(u"API :: Unable to find show with id " + str(self.indexerid), logger.WARNING)
                    continue

                for curSeries in api_data:
                    results.append({indexer_ids[_indexer]: int(curSeries['id']),
                                    "name": curSeries['seriesname'],
                                    "first_aired": curSeries['firstaired'],
                                    "indexer": int(_indexer)})

            return _responds(RESULT_SUCCESS, {"results": results, "langid": lang_id})

        elif self.indexerid:
            for _indexer in sickbeard.indexerApi().indexers if self.indexer == 0 else [int(self.indexer)]:
                indexer_api_params = sickbeard.indexerApi(_indexer).api_params.copy()

                indexer_api_params['language'] = self.lang or sickbeard.INDEXER_DEFAULT_LANGUAGE

                indexer_api_params['actors'] = False

                t = sickbeard.indexerApi(_indexer).indexer(**indexer_api_params)

                try:
                    my_show = t[int(self.indexerid)]
                except (sickbeard.indexer_shownotfound, sickbeard.indexer_showincomplete, sickbeard.indexer_error):
                    logger.log(u"API :: Unable to find show with id " + str(self.indexerid), logger.WARNING)
                    return _responds(RESULT_SUCCESS, {"results": [], "langid": lang_id})

                if not my_show.data['seriesname']:
                    logger.log(
                        u"API :: Found show with indexerid: " + str(
                            self.indexerid) + ", however it contained no show name", logger.DEBUG)
                    return _responds(RESULT_FAILURE, msg="Show contains no name, invalid result")

                # found show
                results = [{indexer_ids[_indexer]: int(my_show.data['id']),
                            "name": unicode(my_show.data['seriesname']),
                            "first_aired": my_show.data['firstaired'],
                            "indexer": int(_indexer)}]
                break

            return _responds(RESULT_SUCCESS, {"results": results, "langid": lang_id})
        else:
            return _responds(RESULT_FAILURE, msg="Either a unique id or name is required!")


class CMD_SickBeardSearchTVDB(CMD_SickBeardSearchIndexers):
    _help = {
        "desc": "Search for a show with a given name on The TVDB, in a specific language",
        "optionalParameters": {
            "name": {"desc": "The name of the show you want to search for"},
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "lang": {"desc": "The 2-letter language code of the desired show"},
        }
    }

    def __init__(self, args, kwargs):
        CMD_SickBeardSearchIndexers.__init__(self, args, kwargs)
        self.indexerid, args = self.check_params(args, kwargs, "tvdbid", None, False, "int", [])


class CMD_SickBeardSearchTVRAGE(CMD_SickBeardSearchIndexers):
    """
    Deprecated, TVRage is no more.
    """

    _help = {
        "desc":
            "Search for a show with a given name on TVRage, in a specific language. "
            "This command should not longer be used, as TVRage was shut down.",
        "optionalParameters": {
            "name": {"desc": "The name of the show you want to search for"},
            "lang": {"desc": "The 2-letter language code of the desired show"},
        }
    }

    def __init__(self, args, kwargs):
        # Leave this one as APICall so it doesnt try and search anything
        # pylint: disable=non-parent-init-called,super-init-not-called
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        return _responds(RESULT_FAILURE, msg="TVRage is no more, invalid result")


class CMD_SickBeardSetDefaults(ApiCall):
    _help = {
        "desc": "Set SickRage's user default configuration value",
        "optionalParameters": {
            "initial": {"desc": "The initial quality of a show"},
            "archive": {"desc": "The archive quality of a show"},
            "future_show_paused": {"desc": "True to list paused shows in the coming episode, False otherwise"},
            "flatten_folders": {"desc": "Flatten sub-folders within the show directory"},
            "status": {"desc": "Status of missing episodes"},
        }
    }

    def __init__(self, args, kwargs):
        # required
        # optional
        self.initial, args = self.check_params(args, kwargs, "initial", None, False, "list",
                                               ["sdtv", "sddvd", "hdtv", "rawhdtv", "fullhdtv", "hdwebdl",
                                                "fullhdwebdl", "hdbluray", "fullhdbluray", "unknown"])
        self.archive, args = self.check_params(args, kwargs, "archive", None, False, "list",
                                               ["sddvd", "hdtv", "rawhdtv", "fullhdtv", "hdwebdl",
                                                "fullhdwebdl", "hdbluray", "fullhdbluray"])
        self.future_show_paused, args = self.check_params(args, kwargs, "future_show_paused", None, False, "bool", [])
        self.flatten_folders, args = self.check_params(args, kwargs, "flatten_folders", None, False, "bool", [])
        self.status, args = self.check_params(args, kwargs, "status", None, False, "string",
                                              ["wanted", "skipped", "ignored"])
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Set SickRage's user default configuration value """

        quality_map = {'sdtv': Quality.SDTV,
                       'sddvd': Quality.SDDVD,
                       'hdtv': Quality.HDTV,
                       'rawhdtv': Quality.RAWHDTV,
                       'fullhdtv': Quality.FULLHDTV,
                       'hdwebdl': Quality.HDWEBDL,
                       'fullhdwebdl': Quality.FULLHDWEBDL,
                       'hdbluray': Quality.HDBLURAY,
                       'fullhdbluray': Quality.FULLHDBLURAY,
                       'unknown': Quality.UNKNOWN}

        i_quality_id = []
        a_quality_id = []

        if self.initial:
            for quality in self.initial:
                i_quality_id.append(quality_map[quality])
        if self.archive:
            for quality in self.archive:
                a_quality_id.append(quality_map[quality])

        if i_quality_id or a_quality_id:
            sickbeard.QUALITY_DEFAULT = Quality.combineQualities(i_quality_id, a_quality_id)

        if self.status:
            # convert the string status to a int
            for status in statusStrings:
                if statusStrings[status].lower() == str(self.status).lower():
                    self.status = status
                    break
            # this should be obsolete because of the above
            if self.status not in statusStrings:
                raise ApiError("Invalid Status")
            # only allow the status options we want
            if int(self.status) not in (3, 5, 6, 7):
                raise ApiError("Status Prohibited")
            sickbeard.STATUS_DEFAULT = self.status

        if self.flatten_folders is not None:
            sickbeard.FLATTEN_FOLDERS_DEFAULT = int(self.flatten_folders)

        if self.future_show_paused is not None:
            sickbeard.COMING_EPS_DISPLAY_PAUSED = int(self.future_show_paused)

        return _responds(RESULT_SUCCESS, msg="Saved defaults")


class CMD_SickBeardShutdown(ApiCall):
    _help = {"desc": "Shutdown SickRage"}

    def __init__(self, args, kwargs):
        # required
        # optional
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Shutdown SickRage """
        if not Shutdown.stop(sickbeard.PID):
            return _responds(RESULT_FAILURE, msg='SickRage can not be shut down')

        return _responds(RESULT_SUCCESS, msg="SickRage is shutting down...")


class CMD_SickBeardUpdate(ApiCall):
    _help = {"desc": "Update SickRage to the latest version available"}

    def __init__(self, args, kwargs):
        # required
        # optional
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        check_version = CheckVersion()

        if check_version.check_for_new_version():
            if check_version.run_backup_if_safe():
                check_version.update()

                return _responds(RESULT_SUCCESS, msg="SickRage is updating ...")

            return _responds(RESULT_FAILURE, msg="SickRage could not backup config ...")

        return _responds(RESULT_FAILURE, msg="SickRage is already up to date")


class CMD_Show(ApiCall):
    _help = {
        "desc": "Get detailed information about a show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, args, kwargs):
        # required
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        # optional
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Get detailed information about a show """
        show_obj = Show.find(sickbeard.showList, int(self.indexerid))
        if not show_obj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        show_dict = {
            "season_list": CMD_ShowSeasonList((), {"indexerid": self.indexerid}).run()["data"],
            "cache": CMD_ShowCache((), {"indexerid": self.indexerid}).run()["data"]
        }

        genre_list = []
        if show_obj.genre:
            genre_list_tmp = show_obj.genre.split("|")
            for genre in genre_list_tmp:
                if genre:
                    genre_list.append(genre)

        show_dict["genre"] = genre_list
        show_dict["quality"] = get_quality_string(show_obj.quality)

        any_qualities, best_qualities = _map_quality(show_obj.quality)
        show_dict["quality_details"] = {"initial": any_qualities, "archive": best_qualities}

        try:
            show_dict["location"] = show_obj.location
        except ShowDirectoryNotFoundException:
            show_dict["location"] = ""

        show_dict["language"] = show_obj.lang
        show_dict["show_name"] = show_obj.name
        show_dict["paused"] = (0, 1)[show_obj.paused]
        show_dict["subtitles"] = (0, 1)[show_obj.subtitles]
        show_dict["air_by_date"] = (0, 1)[show_obj.air_by_date]
        show_dict["flatten_folders"] = (0, 1)[show_obj.flatten_folders]
        show_dict["sports"] = (0, 1)[show_obj.sports]
        show_dict["anime"] = (0, 1)[show_obj.anime]
        show_dict["airs"] = str(show_obj.airs).replace('am', ' AM').replace('pm', ' PM').replace('  ', ' ')
        show_dict["dvdorder"] = (0, 1)[show_obj.dvdorder]

        if show_obj.rls_require_words:
            show_dict["rls_require_words"] = show_obj.rls_require_words.split(", ")
        else:
            show_dict["rls_require_words"] = []

        if show_obj.rls_ignore_words:
            show_dict["rls_ignore_words"] = show_obj.rls_ignore_words.split(", ")
        else:
            show_dict["rls_ignore_words"] = []

        show_dict["scene"] = (0, 1)[show_obj.scene]
        # show_dict["archive_firstmatch"] = (0, 1)[show_obj.archive_firstmatch]
        # This might need to be here for 3rd part apps?
        show_dict["archive_firstmatch"] = 1

        show_dict["indexerid"] = show_obj.indexerid
        show_dict["tvdbid"] = helpers.mapIndexersToShow(show_obj)[1]
        show_dict["imdbid"] = show_obj.imdbid

        show_dict["network"] = show_obj.network
        if not show_dict["network"]:
            show_dict["network"] = ""
        show_dict["status"] = show_obj.status

        if try_int(show_obj.nextaired, 1) > 693595:
            dt_episode_airs = sbdatetime.sbdatetime.convert_to_setting(
                network_timezones.parse_date_time(show_obj.nextaired, show_dict['airs'], show_dict['network']))
            show_dict['airs'] = sbdatetime.sbdatetime.sbftime(dt_episode_airs, t_preset=timeFormat).lstrip('0').replace(
                ' 0', ' ')
            show_dict['next_ep_airdate'] = sbdatetime.sbdatetime.sbfdate(dt_episode_airs, d_preset=dateFormat)
        else:
            show_dict['next_ep_airdate'] = ''

        return _responds(RESULT_SUCCESS, show_dict)


class CMD_ShowAddExisting(ApiCall):
    _help = {
        "desc": "Add an existing show in SickRage",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
            "location": {"desc": "Full path to the existing shows's folder"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "initial": {"desc": "The initial quality of the show"},
            "archive": {"desc": "The archive quality of the show"},
            "flatten_folders": {"desc": "True to flatten the show folder, False otherwise"},
            "subtitles": {"desc": "True to search for subtitles, False otherwise"},
        }
    }

    def __init__(self, args, kwargs):
        # required
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "", [])
        self.location, args = self.check_params(args, kwargs, "location", None, True, "string", [])
        # optional
        self.initial, args = self.check_params(args, kwargs, "initial", None, False, "list",
                                               ["sdtv", "sddvd", "hdtv", "rawhdtv", "fullhdtv", "hdwebdl",
                                                "fullhdwebdl", "hdbluray", "fullhdbluray", "unknown"])
        self.archive, args = self.check_params(args, kwargs, "archive", None, False, "list",
                                               ["sddvd", "hdtv", "rawhdtv", "fullhdtv", "hdwebdl",
                                                "fullhdwebdl", "hdbluray", "fullhdbluray"])
        self.flatten_folders, args = self.check_params(args, kwargs, "flatten_folders",
                                                       bool(sickbeard.FLATTEN_FOLDERS_DEFAULT), False, "bool", [])
        self.subtitles, args = self.check_params(args, kwargs, "subtitles", int(sickbeard.USE_SUBTITLES),
                                                 False, "int", [])
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Add an existing show in SickRage """
        show_obj = Show.find(sickbeard.showList, int(self.indexerid))
        if show_obj:
            return _responds(RESULT_FAILURE, msg="An existing indexerid already exists in the database")

        if not ek(os.path.isdir, self.location):
            return _responds(RESULT_FAILURE, msg='Not a valid location')

        indexer_name = None
        indexer_result = CMD_SickBeardSearchIndexers([], {indexer_ids[self.indexer]: self.indexerid}).run()

        if indexer_result['result'] == result_type_map[RESULT_SUCCESS]:
            if not indexer_result['data']['results']:
                return _responds(RESULT_FAILURE, msg="Empty results returned, check indexerid and try again")
            if len(indexer_result['data']['results']) == 1 and 'name' in indexer_result['data']['results'][0]:
                indexer_name = indexer_result['data']['results'][0]['name']

        if not indexer_name:
            return _responds(RESULT_FAILURE, msg="Unable to retrieve information from indexer")

        # set indexer so we can pass it along when adding show to SR
        indexer = indexer_result['data']['results'][0]['indexer']

        quality_map = {'sdtv': Quality.SDTV,
                       'sddvd': Quality.SDDVD,
                       'hdtv': Quality.HDTV,
                       'rawhdtv': Quality.RAWHDTV,
                       'fullhdtv': Quality.FULLHDTV,
                       'hdwebdl': Quality.HDWEBDL,
                       'fullhdwebdl': Quality.FULLHDWEBDL,
                       'hdbluray': Quality.HDBLURAY,
                       'fullhdbluray': Quality.FULLHDBLURAY,
                       'unknown': Quality.UNKNOWN}

        # use default quality as a fail-safe
        new_quality = int(sickbeard.QUALITY_DEFAULT)
        i_quality_id = []
        a_quality_id = []

        if self.initial:
            for quality in self.initial:
                i_quality_id.append(quality_map[quality])
        if self.archive:
            for quality in self.archive:
                a_quality_id.append(quality_map[quality])

        if i_quality_id or a_quality_id:
            new_quality = Quality.combineQualities(i_quality_id, a_quality_id)

        sickbeard.showQueueScheduler.action.addShow(
            int(indexer), int(self.indexerid), self.location,
            default_status=sickbeard.STATUS_DEFAULT, quality=new_quality,
            flatten_folders=int(self.flatten_folders), subtitles=self.subtitles,
            default_status_after=sickbeard.STATUS_DEFAULT_AFTER
        )

        return _responds(RESULT_SUCCESS, {"name": indexer_name}, indexer_name + " has been queued to be added")


class CMD_ShowAddNew(ApiCall):
    _help = {
        "desc": "Add a new show to SickRage",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "initial": {"desc": "The initial quality of the show"},
            "location": {"desc": "The path to the folder where the show should be created"},
            "archive": {"desc": "The archive quality of the show"},
            "flatten_folders": {"desc": "True to flatten the show folder, False otherwise"},
            "status": {"desc": "The status of missing episodes"},
            "lang": {"desc": "The 2-letter language code of the desired show"},
            "subtitles": {"desc": "True to search for subtitles, False otherwise"},
            "anime": {"desc": "True to mark the show as an anime, False otherwise"},
            "scene": {"desc": "True if episodes search should be made by scene numbering, False otherwise"},
            "future_status": {"desc": "The status of future episodes"},
        }
    }

    def __init__(self, args, kwargs):
        self.valid_languages = sickbeard.indexerApi().config['langabbv_to_id']
        # required
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        # optional
        self.location, args = self.check_params(args, kwargs, "location", None, False, "string", [])
        self.initial, args = self.check_params(args, kwargs, "initial", None, False, "list",
                                               ["sdtv", "sddvd", "hdtv", "rawhdtv", "fullhdtv", "hdwebdl",
                                                "fullhdwebdl", "hdbluray", "fullhdbluray", "unknown"])
        self.archive, args = self.check_params(args, kwargs, "archive", None, False, "list",
                                               ["sddvd", "hdtv", "rawhdtv", "fullhdtv", "hdwebdl",
                                                "fullhdwebdl", "hdbluray", "fullhdbluray"])
        self.flatten_folders, args = self.check_params(args, kwargs, "flatten_folders",
                                                       bool(sickbeard.FLATTEN_FOLDERS_DEFAULT), False, "bool", [])
        self.status, args = self.check_params(args, kwargs, "status", None, False, "string",
                                              ["wanted", "skipped", "ignored"])
        self.lang, args = self.check_params(args, kwargs, "lang", sickbeard.INDEXER_DEFAULT_LANGUAGE, False, "string",
                                            self.valid_languages.keys())
        self.subtitles, args = self.check_params(args, kwargs, "subtitles", bool(sickbeard.USE_SUBTITLES),
                                                 False, "bool", [])
        self.anime, args = self.check_params(args, kwargs, "anime", bool(sickbeard.ANIME_DEFAULT), False,
                                             "bool", [])
        self.scene, args = self.check_params(args, kwargs, "scene", bool(sickbeard.SCENE_DEFAULT), False,
                                             "bool", [])
        self.future_status, args = self.check_params(args, kwargs, "future_status", None, False, "string",
                                                     ["wanted", "skipped", "ignored"])

        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Add a new show to SickRage """
        show_obj = Show.find(sickbeard.showList, int(self.indexerid))
        if show_obj:
            return _responds(RESULT_FAILURE, msg="An existing indexerid already exists in database")

        if not self.location:
            if sickbeard.ROOT_DIRS != "":
                root_dirs = sickbeard.ROOT_DIRS.split('|')
                root_dirs.pop(0)
                default_index = int(sickbeard.ROOT_DIRS.split('|')[0])
                self.location = root_dirs[default_index]
            else:
                return _responds(RESULT_FAILURE, msg="Root directory is not set, please provide a location")

        if not ek(os.path.isdir, self.location):
            return _responds(RESULT_FAILURE, msg="'" + self.location + "' is not a valid location")

        quality_map = {'sdtv': Quality.SDTV,
                       'sddvd': Quality.SDDVD,
                       'hdtv': Quality.HDTV,
                       'rawhdtv': Quality.RAWHDTV,
                       'fullhdtv': Quality.FULLHDTV,
                       'hdwebdl': Quality.HDWEBDL,
                       'fullhdwebdl': Quality.FULLHDWEBDL,
                       'hdbluray': Quality.HDBLURAY,
                       'fullhdbluray': Quality.FULLHDBLURAY,
                       'unknown': Quality.UNKNOWN}

        # use default quality as a fail-safe
        new_quality = int(sickbeard.QUALITY_DEFAULT)
        i_quality_id = []
        a_quality_id = []

        if self.initial:
            for quality in self.initial:
                i_quality_id.append(quality_map[quality])
        if self.archive:
            for quality in self.archive:
                a_quality_id.append(quality_map[quality])

        if i_quality_id or a_quality_id:
            new_quality = Quality.combineQualities(i_quality_id, a_quality_id)

        # use default status as a fail-safe
        new_status = sickbeard.STATUS_DEFAULT
        if self.status:
            # convert the string status to a int
            for status in statusStrings:
                if statusStrings[status].lower() == str(self.status).lower():
                    self.status = status
                    break

            if self.status not in statusStrings:
                raise ApiError("Invalid Status")

            # only allow the status options we want
            if int(self.status) not in (WANTED, SKIPPED, IGNORED):
                return _responds(RESULT_FAILURE, msg="Status prohibited")
            new_status = self.status

        # use default status as a fail-safe
        default_ep_status_after = sickbeard.STATUS_DEFAULT_AFTER
        if self.future_status:
            # convert the string status to a int
            for status in statusStrings:
                if statusStrings[status].lower() == str(self.future_status).lower():
                    self.future_status = status
                    break

            if self.future_status not in statusStrings:
                raise ApiError("Invalid Status")

            # only allow the status options we want
            if int(self.future_status) not in (WANTED, SKIPPED, IGNORED):
                return _responds(RESULT_FAILURE, msg="Status prohibited")
            default_ep_status_after = self.future_status

        indexer_name = None
        indexer_result = CMD_SickBeardSearchIndexers([], {indexer_ids[self.indexer]: self.indexerid, 'lang': self.lang}).run()

        if indexer_result['result'] == result_type_map[RESULT_SUCCESS]:
            if not indexer_result['data']['results']:
                return _responds(RESULT_FAILURE, msg="Empty results returned, check indexerid and try again")
            if len(indexer_result['data']['results']) == 1 and 'name' in indexer_result['data']['results'][0]:
                indexer_name = indexer_result['data']['results'][0]['name']

        if not indexer_name:
            return _responds(RESULT_FAILURE, msg="Unable to retrieve information from indexer")

        # set indexer for found show so we can pass it along
        indexer = indexer_result['data']['results'][0]['indexer']

        # moved the logic check to the end in an attempt to eliminate empty directory being created from previous errors
        show_path = ek(os.path.join, self.location, sanitize_filename(indexer_name))

        # don't create show dir if config says not to
        if sickbeard.ADD_SHOWS_WO_DIR:
            logger.log(u"Skipping initial creation of " + show_path + " due to config.ini setting")
        else:
            dir_exists = helpers.makeDir(show_path)
            if not dir_exists:
                logger.log(u"API :: Unable to create the folder " + show_path + ", can't add the show", logger.ERROR)
                return _responds(RESULT_FAILURE, {"path": show_path},
                                 "Unable to create the folder " + show_path + ", can't add the show")
            else:
                helpers.chmodAsParent(show_path)

        sickbeard.showQueueScheduler.action.addShow(
            int(indexer), int(self.indexerid), show_path, default_status=new_status,
            quality=new_quality, flatten_folders=int(self.flatten_folders),
            lang=self.lang, subtitles=self.subtitles, anime=self.anime,
            scene=self.scene, default_status_after=default_ep_status_after
        )

        return _responds(RESULT_SUCCESS, {"name": indexer_name}, indexer_name + " has been queued to be added")


class CMD_ShowCache(ApiCall):
    _help = {
        "desc": "Check SickRage's cache to see if the images (poster, banner, fanart) for a show are valid",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, args, kwargs):
        # required
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        # optional
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Check SickRage's cache to see if the images (poster, banner, fanart) for a show are valid """
        show_obj = Show.find(sickbeard.showList, int(self.indexerid))
        if not show_obj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        # TODO: catch if cache dir is missing/invalid.. so it doesn't break show/show.cache
        # return {"poster": 0, "banner": 0}

        cache_obj = image_cache.ImageCache()

        has_poster = 0
        has_banner = 0

        if ek(os.path.isfile, cache_obj.poster_path(show_obj.indexerid)):
            has_poster = 1
        if ek(os.path.isfile, cache_obj.banner_path(show_obj.indexerid)):
            has_banner = 1

        return _responds(RESULT_SUCCESS, {"poster": has_poster, "banner": has_banner})


class CMD_ShowDelete(ApiCall):
    _help = {
        "desc": "Delete a show in SickRage",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "removefiles": {
                "desc": "True to delete the files associated with the show, False otherwise. This can not be undone!"
            },
        }
    }

    def __init__(self, args, kwargs):
        # required
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        # optional
        self.removefiles, args = self.check_params(args, kwargs, "removefiles", False, False, "bool", [])
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Delete a show in SickRage """
        error, show = Show.delete(self.indexerid, self.removefiles)

        if error:
            return _responds(RESULT_FAILURE, msg=error)

        return _responds(RESULT_SUCCESS, msg='{0} has been queued to be deleted'.format(show.name))


class CMD_ShowGetQuality(ApiCall):
    _help = {
        "desc": "Get the quality setting of a show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, args, kwargs):
        # required
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        # optional
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Get the quality setting of a show """
        show_obj = Show.find(sickbeard.showList, int(self.indexerid))
        if not show_obj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        any_qualities, best_qualities = _map_quality(show_obj.quality)

        return _responds(RESULT_SUCCESS, {"initial": any_qualities, "archive": best_qualities})


class CMD_ShowGetPoster(ApiCall):
    _help = {
        "desc": "Get the poster of a show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, args, kwargs):
        # required
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        # optional
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Get the poster a show """
        return {
            'outputType': 'image',
            'image': ShowPoster(self.indexerid),
        }


class CMD_ShowGetBanner(ApiCall):
    _help = {
        "desc": "Get the banner of a show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, args, kwargs):
        # required
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        # optional
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Get the banner of a show """
        return {
            'outputType': 'image',
            'image': ShowBanner(self.indexerid),
        }


class CMD_ShowGetNetworkLogo(ApiCall):
    _help = {
        "desc": "Get the network logo of a show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, args, kwargs):
        # required
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        # optional
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """
        :return: Get the network logo of a show
        """
        return {
            'outputType': 'image',
            'image': ShowNetworkLogo(self.indexerid),
        }


class CMD_ShowGetFanArt(ApiCall):
    _help = {
        "desc": "Get the fan art of a show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, args, kwargs):
        # required
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        # optional
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Get the fan art of a show """
        return {
            'outputType': 'image',
            'image': ShowFanArt(self.indexerid),
        }


class CMD_ShowPause(ApiCall):
    _help = {
        "desc": "Pause or un-pause a show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "pause": {"desc": "True to pause the show, False otherwise"},
        }
    }

    def __init__(self, args, kwargs):
        # required
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        # optional
        self.pause, args = self.check_params(args, kwargs, "pause", False, False, "bool", [])
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Pause or un-pause a show """
        error, show = Show.pause(self.indexerid, self.pause)

        if error:
            return _responds(RESULT_FAILURE, msg=error)

        return _responds(RESULT_SUCCESS, msg='{0} has been {1}'.format(show.name, ('resumed', 'paused')[show.paused]))


class CMD_ShowRefresh(ApiCall):
    _help = {
        "desc": "Refresh a show in SickRage",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, args, kwargs):
        # required
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        # optional
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Refresh a show in SickRage """
        error, show = Show.refresh(self.indexerid)

        if error:
            return _responds(RESULT_FAILURE, msg=error)

        return _responds(RESULT_SUCCESS, msg='{0} has queued to be refreshed'.format(show.name))


class CMD_ShowSeasonList(ApiCall):
    _help = {
        "desc": "Get the list of seasons of a show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "sort": {"desc": "Return the seasons in ascending or descending order"}
        }
    }

    def __init__(self, args, kwargs):
        # required
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        # optional
        self.sort, args = self.check_params(args, kwargs, "sort", "desc", False, "string", ["asc", "desc"])
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Get the list of seasons of a show """
        show_obj = Show.find(sickbeard.showList, int(self.indexerid))
        if not show_obj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        main_db_con = db.DBConnection(row_type="dict")
        if self.sort == "asc":
            sql_results = main_db_con.select("SELECT DISTINCT season FROM tv_episodes WHERE showid = ? ORDER BY season ASC",
                                             [self.indexerid])
        else:
            sql_results = main_db_con.select("SELECT DISTINCT season FROM tv_episodes WHERE showid = ? ORDER BY season DESC",
                                             [self.indexerid])
        season_list = []  # a list with all season numbers
        for row in sql_results:
            season_list.append(int(row["season"]))

        return _responds(RESULT_SUCCESS, season_list)


class CMD_ShowSeasons(ApiCall):
    _help = {
        "desc": "Get the list of episodes for one or all seasons of a show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "season": {"desc": "The season number"},
        }
    }

    def __init__(self, args, kwargs):
        # required
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        # optional
        self.season, args = self.check_params(args, kwargs, "season", None, False, "int", [])
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Get the list of episodes for one or all seasons of a show """
        sho_obj = Show.find(sickbeard.showList, int(self.indexerid))
        if not sho_obj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        main_db_con = db.DBConnection(row_type="dict")

        if self.season is None:
            sql_results = main_db_con.select(
                "SELECT name, episode, airdate, status, release_name, season, location, file_size, subtitles FROM tv_episodes WHERE showid = ?",
                [self.indexerid])
            seasons = {}
            for row in sql_results:
                status, quality = Quality.splitCompositeStatus(int(row["status"]))
                row["status"] = _get_status_strings(status)
                row["quality"] = get_quality_string(quality)
                if try_int(row['airdate'], 1) > 693595:  # 1900
                    dt_episode_airs = sbdatetime.sbdatetime.convert_to_setting(
                        network_timezones.parse_date_time(row['airdate'], sho_obj.airs, sho_obj.network))
                    row['airdate'] = sbdatetime.sbdatetime.sbfdate(dt_episode_airs, d_preset=dateFormat)
                else:
                    row['airdate'] = 'Never'
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
                [self.indexerid, self.season])
            if not sql_results:
                return _responds(RESULT_FAILURE, msg="Season not found")
            seasons = {}
            for row in sql_results:
                cur_episode = int(row["episode"])
                del row["episode"]
                status, quality = Quality.splitCompositeStatus(int(row["status"]))
                row["status"] = _get_status_strings(status)
                row["quality"] = get_quality_string(quality)
                if try_int(row['airdate'], 1) > 693595:  # 1900
                    dt_episode_airs = sbdatetime.sbdatetime.convert_to_setting(
                        network_timezones.parse_date_time(row['airdate'], sho_obj.airs, sho_obj.network))
                    row['airdate'] = sbdatetime.sbdatetime.sbfdate(dt_episode_airs, d_preset=dateFormat)
                else:
                    row['airdate'] = 'Never'
                if cur_episode not in seasons:
                    seasons[cur_episode] = {}
                seasons[cur_episode] = row

        return _responds(RESULT_SUCCESS, seasons)


class CMD_ShowSetQuality(ApiCall):
    _help = {
        "desc": "Set the quality setting of a show. If no quality is provided, the default user setting is used.",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
            "initial": {"desc": "The initial quality of the show"},
            "archive": {"desc": "The archive quality of the show"},
        }
    }

    def __init__(self, args, kwargs):
        # required
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        # optional
        # this for whatever reason removes hdbluray not sdtv... which is just wrong. reverting to previous code.. plus we didnt use the new code everywhere.
        # self.archive, args = self.check_params(args, kwargs, "archive", None, False, "list", _get_quality_map().values()[1:])
        self.initial, args = self.check_params(args, kwargs, "initial", None, False, "list",
                                               ["sdtv", "sddvd", "hdtv", "rawhdtv", "fullhdtv", "hdwebdl",
                                                "fullhdwebdl", "hdbluray", "fullhdbluray", "unknown"])
        self.archive, args = self.check_params(args, kwargs, "archive", None, False, "list",
                                               ["sddvd", "hdtv", "rawhdtv", "fullhdtv", "hdwebdl",
                                                "fullhdwebdl",
                                                "hdbluray", "fullhdbluray"])
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Set the quality setting of a show. If no quality is provided, the default user setting is used. """
        show_obj = Show.find(sickbeard.showList, int(self.indexerid))
        if not show_obj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        quality_map = {'sdtv': Quality.SDTV,
                       'sddvd': Quality.SDDVD,
                       'hdtv': Quality.HDTV,
                       'rawhdtv': Quality.RAWHDTV,
                       'fullhdtv': Quality.FULLHDTV,
                       'hdwebdl': Quality.HDWEBDL,
                       'fullhdwebdl': Quality.FULLHDWEBDL,
                       'hdbluray': Quality.HDBLURAY,
                       'fullhdbluray': Quality.FULLHDBLURAY,
                       'unknown': Quality.UNKNOWN}

        # use default quality as a fail-safe
        new_quality = int(sickbeard.QUALITY_DEFAULT)
        i_quality_id = []
        a_quality_id = []

        if self.initial:
            for quality in self.initial:
                i_quality_id.append(quality_map[quality])
        if self.archive:
            for quality in self.archive:
                a_quality_id.append(quality_map[quality])

        if i_quality_id or a_quality_id:
            new_quality = Quality.combineQualities(i_quality_id, a_quality_id)
        show_obj.quality = new_quality

        return _responds(RESULT_SUCCESS,
                         msg=show_obj.name + " quality has been changed to " + get_quality_string(show_obj.quality))


class CMD_ShowStats(ApiCall):
    _help = {
        "desc": "Get episode statistics for a given show",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, args, kwargs):
        # required
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        # optional
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Get episode statistics for a given show """
        show_obj = Show.find(sickbeard.showList, int(self.indexerid))
        if not show_obj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        # show stats
        episode_status_counts_total = {"total": 0}
        for status in statusStrings:
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
        sql_results = main_db_con.select("SELECT status, season FROM tv_episodes WHERE season != 0 AND showid = ?",
                                         [self.indexerid])
        # the main loop that goes through all episodes
        for row in sql_results:
            status, quality = Quality.splitCompositeStatus(int(row["status"]))

            episode_status_counts_total["total"] += 1

            if status in Quality.DOWNLOADED + Quality.ARCHIVED:
                episode_qualities_counts_download["total"] += 1
                episode_qualities_counts_download[int(row["status"])] += 1
            elif status in Quality.SNATCHED + Quality.SNATCHED_PROPER:
                episode_qualities_counts_snatch["total"] += 1
                episode_qualities_counts_snatch[int(row["status"])] += 1
            elif status == 0:  # we don't count NONE = 0 = N/A
                pass
            else:
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

        # episodes_stats["total"] = {}
        for statusCode in episode_status_counts_total:
            if statusCode == "total":
                episodes_stats["total"] = episode_status_counts_total[statusCode]
                continue
            status, quality = Quality.splitCompositeStatus(int(statusCode))
            status_string = statusStrings[statusCode].lower().replace(" ", "_").replace("(", "").replace(
                ")", "")
            episodes_stats[status_string] = episode_status_counts_total[statusCode]

        return _responds(RESULT_SUCCESS, episodes_stats)


class CMD_ShowUpdate(ApiCall):
    _help = {
        "desc": "Update a show in SickRage",
        "requiredParameters": {
            "indexerid": {"desc": "Unique ID of a show"},
        },
        "optionalParameters": {
            "tvdbid": {"desc": "thetvdb.com unique ID of a show"},
        }
    }

    def __init__(self, args, kwargs):
        # required
        self.indexerid, args = self.check_params(args, kwargs, "indexerid", None, True, "int", [])
        # optional
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Update a show in SickRage """
        show_obj = Show.find(sickbeard.showList, int(self.indexerid))
        if not show_obj:
            return _responds(RESULT_FAILURE, msg="Show not found")

        try:
            sickbeard.showQueueScheduler.action.updateShow(show_obj, True)  # @UndefinedVariable
            return _responds(RESULT_SUCCESS, msg=str(show_obj.name) + " has queued to be updated")
        except CantUpdateShowException as e:
            logger.log(u"API::Unable to update show: {0}".format(e), logger.DEBUG)
            return _responds(RESULT_FAILURE, msg="Unable to update " + str(show_obj.name))


class CMD_Shows(ApiCall):
    _help = {
        "desc": "Get all shows in SickRage",
        "optionalParameters": {
            "sort": {"desc": "The sorting strategy to apply to the list of shows"},
            "paused": {"desc": "True: show paused, False: show un-paused, otherwise show all"},
        },
    }

    def __init__(self, args, kwargs):
        # required
        # optional
        self.sort, args = self.check_params(args, kwargs, "sort", "id", False, "string", ["id", "name"])
        self.paused, args = self.check_params(args, kwargs, "paused", None, False, "bool", [])
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Get all shows in SickRage """
        shows = {}
        for curShow in sickbeard.showList:
            # If self.paused is None: show all, 0: show un-paused, 1: show paused
            if self.paused is not None and self.paused != curShow.paused:
                continue

            indexer_show = helpers.mapIndexersToShow(curShow)

            show_dict = {
                "paused": (0, 1)[curShow.paused],
                "quality": get_quality_string(curShow.quality),
                "language": curShow.lang,
                "air_by_date": (0, 1)[curShow.air_by_date],
                "sports": (0, 1)[curShow.sports],
                "anime": (0, 1)[curShow.anime],
                "indexerid": curShow.indexerid,
                "tvdbid": indexer_show[1],
                "network": curShow.network,
                "show_name": curShow.name,
                "status": curShow.status,
                "subtitles": (0, 1)[curShow.subtitles],
            }

            if try_int(curShow.nextaired, 1) > 693595:  # 1900
                dt_episode_airs = sbdatetime.sbdatetime.convert_to_setting(
                    network_timezones.parse_date_time(curShow.nextaired, curShow.airs, show_dict['network']))
                show_dict['next_ep_airdate'] = sbdatetime.sbdatetime.sbfdate(dt_episode_airs, d_preset=dateFormat)
            else:
                show_dict['next_ep_airdate'] = ''

            show_dict["cache"] = CMD_ShowCache((), {"indexerid": curShow.indexerid}).run()["data"]
            if not show_dict["network"]:
                show_dict["network"] = ""
            if self.sort == "name":
                shows[curShow.name] = show_dict
            else:
                shows[curShow.indexerid] = show_dict

        return _responds(RESULT_SUCCESS, shows)


class CMD_ShowsStats(ApiCall):
    _help = {"desc": "Get the global shows and episodes statistics"}

    def __init__(self, args, kwargs):
        # required
        # optional
        # super, missing, help
        ApiCall.__init__(self, args, kwargs)

    def run(self):
        """ Get the global shows and episodes statistics """
        stats = Show.overall_stats()

        return _responds(RESULT_SUCCESS, {
            'ep_downloaded': stats['episodes']['downloaded'],
            'ep_snatched': stats['episodes']['snatched'],
            'ep_total': stats['episodes']['total'],
            'shows_active': stats['shows']['active'],
            'shows_total': stats['shows']['total'],
        })


# WARNING: never define a cmd call string that contains a "_" (underscore)
# this is reserved for cmd indexes used while cmd chaining

# WARNING: never define a param name that contains a "." (dot)
# this is reserved for cmd namespaces used while cmd chaining
function_mapper = {
    "help": CMD_Help,
    "future": CMD_ComingEpisodes,
    "episode": CMD_Episode,
    "episode.search": CMD_EpisodeSearch,
    "episode.setstatus": CMD_EpisodeSetStatus,
    "episode.subtitlesearch": CMD_SubtitleSearch,
    "exceptions": CMD_Exceptions,
    "history": CMD_History,
    "history.clear": CMD_HistoryClear,
    "history.trim": CMD_HistoryTrim,
    "failed": CMD_Failed,
    "backlog": CMD_Backlog,
    "logs": CMD_Logs,
    "logs.clear": CMD_LogsClear,
    "sb": CMD_SickBeard,
    "postprocess": CMD_PostProcess,
    "sb.addrootdir": CMD_SickBeardAddRootDir,
    "sb.checkversion": CMD_SickBeardCheckVersion,
    "sb.checkscheduler": CMD_SickBeardCheckScheduler,
    "sb.deleterootdir": CMD_SickBeardDeleteRootDir,
    "sb.getdefaults": CMD_SickBeardGetDefaults,
    "sb.getmessages": CMD_SickBeardGetMessages,
    "sb.getrootdirs": CMD_SickBeardGetRootDirs,
    "sb.pausebacklog": CMD_SickBeardPauseBacklog,
    "sb.ping": CMD_SickBeardPing,
    "sb.restart": CMD_SickBeardRestart,
    "sb.searchindexers": CMD_SickBeardSearchIndexers,
    "sb.searchtvdb": CMD_SickBeardSearchTVDB,
    "sb.searchtvrage": CMD_SickBeardSearchTVRAGE,
    "sb.setdefaults": CMD_SickBeardSetDefaults,
    "sb.update": CMD_SickBeardUpdate,
    "sb.shutdown": CMD_SickBeardShutdown,
    "show": CMD_Show,
    "show.addexisting": CMD_ShowAddExisting,
    "show.addnew": CMD_ShowAddNew,
    "show.cache": CMD_ShowCache,
    "show.delete": CMD_ShowDelete,
    "show.getquality": CMD_ShowGetQuality,
    "show.getposter": CMD_ShowGetPoster,
    "show.getbanner": CMD_ShowGetBanner,
    "show.getnetworklogo": CMD_ShowGetNetworkLogo,
    "show.getfanart": CMD_ShowGetFanArt,
    "show.pause": CMD_ShowPause,
    "show.refresh": CMD_ShowRefresh,
    "show.seasonlist": CMD_ShowSeasonList,
    "show.seasons": CMD_ShowSeasons,
    "show.setquality": CMD_ShowSetQuality,
    "show.stats": CMD_ShowStats,
    "show.update": CMD_ShowUpdate,
    "shows": CMD_Shows,
    "shows.stats": CMD_ShowsStats
}
