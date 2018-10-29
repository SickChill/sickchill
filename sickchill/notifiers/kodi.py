# coding=utf-8

# Author: Nic Wolfe <nic@wolfeden.ca>
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

from __future__ import print_function, unicode_literals

import base64
import socket
import time

import six
from six.moves import http_client, urllib

import sickchill
from sickchill import common, logger
from sickchill.helper.encoding import ss
from sickchill.helper.exceptions import ex

try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree

try:
    import json
except ImportError:
    import simplejson as json


class Notifier(object):

    def _get_kodi_version(self, host, username, password, dest_app="KODI"):
        """Returns KODI JSON-RPC API version (odd # = dev, even # = stable)

        Sends a request to the KODI host using the JSON-RPC to determine if
        the legacy API or if the JSON-RPC API functions should be used.

        Fallback to testing legacy HTTPAPI before assuming it is just a badly configured host.

        Args:
            host: KODI webserver host:port
            username: KODI webserver username
            password: KODI webserver password

        Returns:
            Returns API number or False

            List of possible known values:
                API | KODI Version
               -----+---------------
                 2  | v10 (Dharma)
                 3  | (pre Eden)
                 4  | v11 (Eden)
                 5  | (pre Frodo)
                 6  | v12 (Frodo) / v13 (Gotham)

        """

        # since we need to maintain python 2.5 compatibility we can not pass a timeout delay to urllib2 directly (python 2.6+)
        # override socket timeout to reduce delay for this call alone
        socket.setdefaulttimeout(10)

        checkCommand = '{"jsonrpc":"2.0","method":"JSONRPC.Version","id":1}'
        result = self._send_to_kodi_json(checkCommand, host, username, password, dest_app)

        # revert back to default socket timeout
        socket.setdefaulttimeout(sickchill.SOCKET_TIMEOUT)

        if result:
            return result["result"]["version"]
        else:
            # fallback to legacy HTTPAPI method
            testCommand = {'command': 'Help'}
            request = self._send_to_kodi(testCommand, host, username, password, dest_app)
            if request:
                # return a fake version number, so it uses the legacy method
                return 1
            else:
                return False

    def _notify_kodi(self, message, title="SickChill", host=None, username=None, password=None, force=False, dest_app="KODI"):  # pylint: disable=too-many-arguments
        """Internal wrapper for the notify_snatch and notify_download functions

        Detects JSON-RPC version then branches the logic for either the JSON-RPC or legacy HTTP API methods.

        Args:
            message: Message body of the notice to send
            title: Title of the notice to send
            host: KODI webserver host:port
            username: KODI webserver username
            password: KODI webserver password
            force: Used for the Test method to override config saftey checks

        Returns:
            Returns a list results in the format of host:ip:result
            The result will either be 'OK' or False, this is used to be parsed by the calling function.

        """

        # fill in omitted parameters
        if not host:
            host = sickchill.KODI_HOST
        if not username:
            username = sickchill.KODI_USERNAME
        if not password:
            password = sickchill.KODI_PASSWORD

        # suppress notifications if the notifier is disabled but the notify options are checked
        if not sickchill.USE_KODI and not force:
            logger.log("Notification for {0} not enabled, skipping this notification".format(dest_app), logger.DEBUG)
            return False

        result = ''
        for curHost in [x.strip() for x in host.split(",") if x.strip()]:
            logger.log("Sending {0} notification to '{1}' - {2}".format(dest_app, curHost, message), logger.DEBUG)

            kodiapi = self._get_kodi_version(curHost, username, password, dest_app)
            if kodiapi:
                if kodiapi <= 4:
                    logger.log("Detected {0} version <= 11, using {1} HTTP API".format(dest_app, dest_app), logger.DEBUG)
                    command = {'command': 'ExecBuiltIn',
                               'parameter': 'Notification(' + title.encode("utf-8") + ',' + message.encode(
                                   "utf-8") + ')'}
                    notifyResult = self._send_to_kodi(command, curHost, username, password)
                    if notifyResult:
                        result += curHost + ':' + str(notifyResult)
                else:
                    logger.log("Detected {0} version >= 12, using {1} JSON API".format(dest_app, dest_app), logger.DEBUG)
                    command = '{{"jsonrpc":"2.0","method":"GUI.ShowNotification","params":{{"title":"{0}","message":"{1}", "image": "{2}"}},"id":1}}'.format(
                        title.encode("utf-8"), message.encode("utf-8"), sickchill.LOGO_URL)
                    notifyResult = self._send_to_kodi_json(command, curHost, username, password, dest_app)
                    if notifyResult and notifyResult.get('result'):  # pylint: disable=no-member
                        result += curHost + ':' + notifyResult["result"].decode(sickchill.SYS_ENCODING)
            else:
                if sickchill.KODI_ALWAYS_ON or force:
                    logger.log("Failed to detect {0} version for '{1}', check configuration and try again.".format(dest_app, curHost), logger.WARNING)
                result += curHost + ':False'

        return result

    def _send_update_library(self, host, showName=None):
        """Internal wrapper for the update library function to branch the logic for JSON-RPC or legacy HTTP API

        Checks the KODI API version to branch the logic to call either the legacy HTTP API or the newer JSON-RPC over HTTP methods.

        Args:
            host: KODI webserver host:port
            showName: Name of a TV show to specifically target the library update for

        Returns:
            Returns True or False, if the update was successful

        """

        logger.log("Sending request to update library for KODI host: '{0}'".format(host), logger.DEBUG)

        kodiapi = self._get_kodi_version(host, sickchill.KODI_USERNAME, sickchill.KODI_PASSWORD)
        if kodiapi:
            if kodiapi <= 4:
                # try to update for just the show, if it fails, do full update if enabled
                if not self._update_library(host, showName) and sickchill.KODI_UPDATE_FULL:
                    logger.log("Single show update failed, falling back to full update", logger.DEBUG)
                    return self._update_library(host)
                else:
                    return True
            else:
                # try to update for just the show, if it fails, do full update if enabled
                if not self._update_library_json(host, showName) and sickchill.KODI_UPDATE_FULL:
                    logger.log("Single show update failed, falling back to full update", logger.DEBUG)
                    return self._update_library_json(host)
                else:
                    return True
        elif sickchill.KODI_ALWAYS_ON:
            logger.log("Failed to detect KODI version for '" + host + "', check configuration and try again.", logger.WARNING)

        return False

    # #############################################################################
    # Legacy HTTP API (pre KODI 12) methods
    ##############################################################################

    @staticmethod
    def _send_to_kodi(command, host=None, username=None, password=None, dest_app="KODI"):  # pylint: disable=too-many-arguments
        """Handles communication to KODI servers via HTTP API

        Args:
            command: Dictionary of field/data pairs, encoded via urllib and passed to the KODI API via HTTP
            host: KODI webserver host:port
            username: KODI webserver username
            password: KODI webserver password

        Returns:
            Returns response.result for successful commands or False if there was an error

        """

        # fill in omitted parameters
        if not username:
            username = sickchill.KODI_USERNAME
        if not password:
            password = sickchill.KODI_PASSWORD

        if not host:
            logger.log('No {0} host passed, aborting update'.format(dest_app), logger.WARNING)
            return False

        for key in command:
            if isinstance(command[key], six.text_type):
                command[key] = command[key].encode('utf-8')

        enc_command = urllib.parse.urlencode(command)
        logger.log("{0} encoded API command: {1!r}".format(dest_app, enc_command), logger.DEBUG)

        # url = 'http://%s/xbmcCmds/xbmcHttp/?%s' % (host, enc_command)  # maybe need for old plex?
        url = 'http://{0}/kodiCmds/kodiHttp/?{1}'.format(host, enc_command)
        try:
            req = urllib.request.Request(url)
            # if we have a password, use authentication
            if password:
                base64string = base64.encodestring('{0}:{1}'.format(username, password))[:-1]
                authheader = "Basic {0}".format(base64string)
                req.add_header("Authorization", authheader)
                logger.log("Contacting {0} (with auth header) via url: {1}".format(dest_app, ss(url)), logger.DEBUG)
            else:
                logger.log("Contacting {0} via url: {1}".format(dest_app, ss(url)), logger.DEBUG)

            try:
                response = urllib.request.urlopen(req)
            except (http_client.BadStatusLine, urllib.error.URLError) as e:
                logger.log("Couldn't contact {0} HTTP at {1!r} : {2!r}".format(dest_app, url, ex(e)), logger.DEBUG)
                return False

            result = response.read().decode(sickchill.SYS_ENCODING)
            response.close()

            logger.log("{0} HTTP response: {1}".format(dest_app, result.replace('\n', '')), logger.DEBUG)
            return result

        except Exception as e:
            logger.log("Couldn't contact {0} HTTP at {1!r} : {2!r}".format(dest_app, url, ex(e)), logger.DEBUG)
            return False

    def _update_library(self, host=None, showName=None):  # pylint: disable=too-many-locals, too-many-return-statements
        """Handles updating KODI host via HTTP API

        Attempts to update the KODI video library for a specific tv show if passed,
        otherwise update the whole library if enabled.

        Args:
            host: KODI webserver host:port
            showName: Name of a TV show to specifically target the library update for

        Returns:
            Returns True or False

        """

        if not host:
            logger.log('No KODI host passed, aborting update', logger.WARNING)
            return False

        logger.log("Updating KODI library via HTTP method for host: " + host, logger.DEBUG)

        # if we're doing per-show
        if showName:
            logger.log("Updating library in KODI via HTTP method for show " + showName, logger.DEBUG)

            pathSql = ('select path.strPath from path, tvshow, tvshowlinkpath where '
                      'tvshow.c00 = "{}" and tvshowlinkpath.idShow = tvshow.idShow '
                      'and tvshowlinkpath.idPath = path.idPath').format(showName)

            # use this to get xml back for the path lookups
            xmlCommand = {
                'command': 'SetResponseFormat(webheader;false;webfooter;false;header;<xml>;footer;</xml>;opentag;<tag>;closetag;</tag>;closefinaltag;false)'}
            # sql used to grab path(s)
            sqlCommand = {'command': 'QueryVideoDatabase({0})'.format(pathSql)}
            # set output back to default
            resetCommand = {'command': 'SetResponseFormat()'}

            # set xml response format, if this fails then don't bother with the rest
            request = self._send_to_kodi(xmlCommand, host)
            if not request:
                return False

            sqlXML = self._send_to_kodi(sqlCommand, host)
            request = self._send_to_kodi(resetCommand, host)

            if not sqlXML:
                logger.log("Invalid response for " + showName + " on " + host, logger.DEBUG)
                return False

            encSqlXML = urllib.parse.quote(sqlXML, ':\\/<>')
            try:
                et = etree.fromstring(encSqlXML)
            except SyntaxError as e:
                logger.log("Unable to parse XML returned from KODI: " + ex(e), logger.ERROR)
                return False

            paths = et.findall('.//field')

            if not paths:
                logger.log("No valid paths found for " + showName + " on " + host, logger.DEBUG)
                return False

            for path in paths:
                # we do not need it double-encoded, gawd this is dumb
                unEncPath = urllib.parse.unquote(path.text).decode(sickchill.SYS_ENCODING)
                logger.log("KODI Updating " + showName + " on " + host + " at " + unEncPath, logger.DEBUG)
                updateCommand = {'command': 'ExecBuiltIn', 'parameter': 'KODI.updatelibrary(video, {0})'.format(unEncPath)}
                request = self._send_to_kodi(updateCommand, host)
                if not request:
                    logger.log("Update of show directory failed on " + showName + " on " + host + " at " + unEncPath, logger.WARNING)
                    return False
                # sleep for a few seconds just to be sure kodi has a chance to finish each directory
                if len(paths) > 1:
                    time.sleep(5)
        # do a full update if requested
        else:
            logger.log("Doing Full Library KODI update on host: " + host, logger.DEBUG)
            updateCommand = {'command': 'ExecBuiltIn', 'parameter': 'KODI.updatelibrary(video)'}
            request = self._send_to_kodi(updateCommand, host)

            if not request:
                logger.log("KODI Full Library update failed on: " + host, logger.WARNING)
                return False

        return True

    ##############################################################################
    # JSON-RPC API (KODI 12+) methods
    ##############################################################################

    @staticmethod
    def _send_to_kodi_json(command, host=None, username=None, password=None, dest_app="KODI"):
        """Handles communication to KODI servers via JSONRPC

        Args:
            command: Dictionary of field/data pairs, encoded via urllib and passed to the KODI JSON-RPC via HTTP
            host: KODI webserver host:port
            username: KODI webserver username
            password: KODI webserver password

        Returns:
            Returns response.result for successful commands or False if there was an error

        """

        # fill in omitted parameters
        if not username:
            username = sickchill.KODI_USERNAME
        if not password:
            password = sickchill.KODI_PASSWORD

        if not host:
            logger.log('No {0} host passed, aborting update'.format(dest_app), logger.WARNING)
            return False

        command = command.encode('utf-8')
        logger.log("{0} JSON command: {1}".format(dest_app, command), logger.DEBUG)

        url = 'http://{0}/jsonrpc'.format(host)
        try:
            req = urllib.request.Request(url, command)
            req.add_header("Content-type", "application/json")
            # if we have a password, use authentication
            if password:
                base64string = base64.encodestring('{0}:{1}'.format(username, password))[:-1]
                authheader = "Basic {0}".format(base64string)
                req.add_header("Authorization", authheader)
                logger.log("Contacting {0} (with auth header) via url: {1}".format(dest_app, ss(url)), logger.DEBUG)
            else:
                logger.log("Contacting {0} via url: {1}".format(dest_app, ss(url)), logger.DEBUG)

            try:
                response = urllib.request.urlopen(req)
            except (http_client.BadStatusLine, urllib.error.URLError) as e:
                if sickchill.KODI_ALWAYS_ON:
                    logger.log("Error while trying to retrieve {0} API version for {1}: {2!r}".format(dest_app, host, ex(e)), logger.WARNING)
                return False

            # parse the json result
            try:
                result = json.load(response)
                response.close()
                logger.log("{0} JSON response: {1}".format(dest_app, result), logger.DEBUG)
                return result  # need to return response for parsing
            except ValueError as e:
                logger.log("Unable to decode JSON: " + str(response.read()), logger.WARNING)
                return False

        except IOError as e:
            if sickchill.KODI_ALWAYS_ON:
                logger.log("Warning: Couldn't contact {0} JSON API at {1}: {2!r}".format(dest_app, ss(url), ex(e)), logger.WARNING)
            return False

    def _update_library_json(self, host=None, showName=None):  # pylint: disable=too-many-return-statements, too-many-branches
        """Handles updating KODI host via HTTP JSON-RPC

        Attempts to update the KODI video library for a specific tv show if passed,
        otherwise update the whole library if enabled.

        Args:
            host: KODI webserver host:port
            showName: Name of a TV show to specifically target the library update for

        Returns:
            Returns True or False

        """

        if not host:
            logger.log('No KODI host passed, aborting update', logger.WARNING)
            return False

        logger.log("Updating KODI library via JSON method for host: " + host, logger.DEBUG)

        # if we're doing per-show
        if showName:
            showName = urllib.parse.unquote_plus(showName)
            tvshowid = -1
            path = ''

            logger.log("Updating library in KODI via JSON method for show " + showName, logger.DEBUG)

            # let's try letting kodi filter the shows
            showsCommand = '{"jsonrpc":"2.0","method":"VideoLibrary.GetTVShows","params":{"filter":{"field":"title","operator":"is","value":"%s"},"properties":["title"]},"id":"SickChill"}'

            # get tvshowid by showName
            showsResponse = self._send_to_kodi_json(showsCommand % showName, host)

            if showsResponse and "result" in showsResponse and "tvshows" in showsResponse["result"]:
                shows = showsResponse["result"]["tvshows"]
            else:
                # fall back to retrieving the entire show list
                showsCommand = '{"jsonrpc":"2.0","method":"VideoLibrary.GetTVShows","id":1}'
                showsResponse = self._send_to_kodi_json(showsCommand, host)

                if showsResponse and "result" in showsResponse and "tvshows" in showsResponse["result"]:
                    shows = showsResponse["result"]["tvshows"]
                else:
                    logger.log("KODI: No tvshows in KODI TV show list", logger.DEBUG)
                    return False

            for show in shows:
                if ("label" in show and show["label"] == showName) or ("title" in show and show["title"] == showName):
                    tvshowid = show["tvshowid"]
                    # set the path is we have it already
                    if "file" in show:
                        path = show["file"]

                    break

            # this can be big, so free some memory
            del shows

            # we didn't find the show (exact match), thus revert to just doing a full update if enabled
            if tvshowid == -1:
                logger.log('Exact show name not matched in KODI TV show list', logger.DEBUG)
                return False

            # lookup tv-show path if we don't already know it
            if not path:
                pathCommand = '{{"jsonrpc":"2.0","method":"VideoLibrary.GetTVShowDetails","params":{{"tvshowid":{0:d}, "properties": ["file"]}},"id":1}}'.format(tvshowid)
                pathResponse = self._send_to_kodi_json(pathCommand, host)

                path = pathResponse["result"]["tvshowdetails"]["file"]

            logger.log("Received Show: " + showName + " with ID: " + str(tvshowid) + " Path: " + path, logger.DEBUG)

            if not path:
                logger.log("No valid path found for " + showName + " with ID: " + str(tvshowid) + " on " + host, logger.WARNING)
                return False

            logger.log("KODI Updating " + showName + " on " + host + " at " + path, logger.DEBUG)
            updateCommand = '{{"jsonrpc":"2.0","method":"VideoLibrary.Scan","params":{{"directory":{0}}},"id":1}}'.format((json.dumps(path)))
            request = self._send_to_kodi_json(updateCommand, host)
            if not request:
                logger.log("Update of show directory failed on " + showName + " on " + host + " at " + path, logger.WARNING)
                return False

            # catch if there was an error in the returned request
            for r in request:
                if 'error' in r:
                    logger.log("Error while attempting to update show directory for " + showName + " on " + host + " at " + path, logger.WARNING)
                    return False

        # do a full update if requested
        else:
            logger.log("Doing Full Library KODI update on host: " + host, logger.DEBUG)
            updateCommand = '{"jsonrpc":"2.0","method":"VideoLibrary.Scan","id":1}'
            request = self._send_to_kodi_json(updateCommand, host)

            if not request:
                logger.log("KODI Full Library update failed on: " + host, logger.WARNING)
                return False

        return True

    ##############################################################################
    # Public functions which will call the JSON or Legacy HTTP API methods
    ##############################################################################

    def notify_snatch(self, ep_name):
        if sickchill.KODI_NOTIFY_ONSNATCH:
            self._notify_kodi(ep_name, common.notifyStrings[common.NOTIFY_SNATCH])

    def notify_download(self, ep_name):
        if sickchill.KODI_NOTIFY_ONDOWNLOAD:
            self._notify_kodi(ep_name, common.notifyStrings[common.NOTIFY_DOWNLOAD])

    def notify_subtitle_download(self, ep_name, lang):
        if sickchill.KODI_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notify_kodi(ep_name + ": " + lang, common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD])

    def notify_git_update(self, new_version="??"):
        if sickchill.USE_KODI:
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            self._notify_kodi(update_text + new_version, title)

    def notify_login(self, ipaddress=""):
        if sickchill.USE_KODI:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._notify_kodi(update_text.format(ipaddress), title)

    def test_notify(self, host, username, password):
        return self._notify_kodi("Testing KODI notifications from SickChill", "Test Notification", host, username, password, force=True)

    def update_library(self, showName=None):
        """Public wrapper for the update library functions to branch the logic for JSON-RPC or legacy HTTP API

        Checks the KODI API version to branch the logic to call either the legacy HTTP API or the newer JSON-RPC over HTTP methods.
        Do the ability of accepting a list of hosts delimited by comma, only one host is updated, the first to respond with success.
        This is a workaround for SQL backend users as updating multiple clients causes duplicate entries.
        Future plan is to revist how we store the host/ip/username/pw/options so that it may be more flexible.

        Args:
            showName: Name of a TV show to specifically target the library update for

        Returns:
            Returns True or False

        """

        if sickchill.USE_KODI and sickchill.KODI_UPDATE_LIBRARY:
            if not sickchill.KODI_HOST:
                logger.log("No KODI hosts specified, check your settings", logger.DEBUG)
                return False

            # either update each host, or only attempt to update until one successful result
            result = 0
            for host in [x.strip() for x in sickchill.KODI_HOST.split(",")]:
                if self._send_update_library(host, showName):
                    if sickchill.KODI_UPDATE_ONLYFIRST:
                        logger.log("Successfully updated '" + host + "', stopped sending update library commands.", logger.DEBUG)
                        return True
                else:
                    if sickchill.KODI_ALWAYS_ON:
                        logger.log("Failed to detect KODI version for '" + host + "', check configuration and try again.", logger.WARNING)
                    result += 1

            # needed for the 'update kodi' submenu command
            # as it only cares of the final result vs the individual ones
            if result == 0:
                return True
            else:
                return False
