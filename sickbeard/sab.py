# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickrage.github.io
# Git: https://github.com/SickRage/SickRage
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

import urllib
import httplib

import sickbeard
import datetime

import MultipartPostHandler
import urllib2
import cookielib

try:
    import json
except ImportError:
    import simplejson as json

from sickbeard.common import USER_AGENT
from sickbeard import logger
from sickrage.helper.exceptions import ex


def sendNZB(nzb):  # pylint:disable=too-many-return-statements, too-many-branches, too-many-statements
    """
    Sends an NZB to SABnzbd via the API.

    :param nzb: The NZBSearchResult object to send to SAB
    """

    # set up a dict with the URL params in it
    params = {}
    if sickbeard.SAB_USERNAME is not None:
        params['ma_username'] = sickbeard.SAB_USERNAME
    if sickbeard.SAB_PASSWORD is not None:
        params['ma_password'] = sickbeard.SAB_PASSWORD
    if sickbeard.SAB_APIKEY is not None:
        params['apikey'] = sickbeard.SAB_APIKEY
    category = sickbeard.SAB_CATEGORY
    if nzb.show.is_anime:
        category = sickbeard.SAB_CATEGORY_ANIME

    # if it aired more than 7 days ago, override with the backlog category IDs
    for curEp in nzb.episodes:
        if datetime.date.today() - curEp.airdate > datetime.timedelta(days=7):
            category = sickbeard.SAB_CATEGORY_BACKLOG
            if nzb.show.is_anime:
                category = sickbeard.SAB_CATEGORY_ANIME_BACKLOG

    if category is not None:
        params['cat'] = category

    # use high priority if specified (recently aired episode)
    if nzb.priority == 1:
        if sickbeard.SAB_FORCED == 1:
            params['priority'] = 2
        else:
            params['priority'] = 1

    # if it's a normal result we just pass SAB the URL
    if nzb.resultType == "nzb":
        # for newzbin results send the ID to sab specifically
        if nzb.provider.get_id() == 'newzbin':
            nzb_id = nzb.provider.getIDFromURL(nzb.url)
            if not nzb_id:
                logger.log(u"Unable to send NZB to sab, can't find ID in URL " + str(nzb.url), logger.ERROR)
                return False
            params['mode'] = 'addid'
            params['name'] = nzb_id
        else:
            params['mode'] = 'addurl'
            params['name'] = nzb.url

    # if we get a raw data result we want to upload it to SAB
    elif nzb.resultType == "nzbdata":
        params['mode'] = 'addfile'
        multiPartParams = {"nzbfile": (nzb.name + ".nzb", nzb.extraInfo[0])}

    url = sickbeard.SAB_HOST + "api?" + urllib.urlencode(params)

    logger.log(u"Sending NZB to SABnzbd")
    logger.log(u"URL: " + url, logger.DEBUG)

    try:
        # if we have the URL to an NZB then we've built up the SAB API URL already so just call it
        if nzb.resultType == "nzb":
            f = urllib.urlopen(url)

        # if we are uploading the NZB data to SAB then we need to build a little POST form and send it
        elif nzb.resultType == "nzbdata":
            cookies = cookielib.CookieJar()
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies),
                                          MultipartPostHandler.MultipartPostHandler)
            req = urllib2.Request(url,
                                  multiPartParams,
                                  headers={'User-Agent': USER_AGENT})

            f = opener.open(req)

    except (EOFError, IOError) as e:
        logger.log(u"Unable to connect to SAB: " + ex(e), logger.ERROR)
        return False

    except httplib.InvalidURL as e:
        logger.log(u"Invalid SAB host, check your config: " + ex(e), logger.ERROR)
        return False

    # this means we couldn't open the connection or something just as bad
    if f is None:
        logger.log(u"No data returned from SABnzbd, NZB not sent", logger.ERROR)
        return False

    # if we opened the URL connection then read the result from SAB
    try:
        result = f.readlines()
    except Exception as e:
        logger.log(u"Error trying to get result from SAB, NZB not sent: " + ex(e), logger.ERROR)
        return False

    # SAB shouldn't return a blank result, this most likely (but not always) means that it timed out and didn't recieve the NZB
    if len(result) == 0:
        logger.log(u"No data returned from SABnzbd, NZB not sent", logger.ERROR)
        return False

    # massage the result a little bit
    sabText = result[0].strip()

    logger.log(u"Result text from SAB: " + sabText, logger.DEBUG)

    # do some crude parsing of the result text to determine what SAB said
    if sabText == "ok":
        logger.log(u"NZB sent to SAB successfully", logger.DEBUG)
        return True
    elif sabText == "Missing authentication":
        logger.log(u"Incorrect username/password sent to SAB, NZB not sent", logger.ERROR)
        return False
    else:
        logger.log(u"Unknown failure sending NZB to sab. Return text is: " + sabText, logger.ERROR)
        return False


def _checkSabResponse(f):
    """
    Check response from SAB

    :param f: Response from SAV
    :return: a list of (Boolean, string) which is True if SAB is not reporting an error
    """
    try:
        result = f.readlines()
    except Exception as e:
        logger.log(u"Error trying to get result from SAB" + ex(e), logger.ERROR)
        return False, "Error from SAB"

    if len(result) == 0:
        logger.log(u"No data returned from SABnzbd, NZB not sent", logger.ERROR)
        return False, "No data from SAB"

    sabText = result[0].strip()
    sabJson = {}
    try:
        sabJson = json.loads(sabText)
    except ValueError as e:
        pass

    if sabText == "Missing authentication":
        logger.log(u"Incorrect username/password sent to SAB", logger.ERROR)
        return False, "Incorrect username/password sent to SAB"
    elif 'error' in sabJson:
        logger.log(sabJson['error'], logger.ERROR)
        return False, sabJson['error']
    else:
        return True, sabText


def _sabURLOpenSimple(url):
    """
    Open a connection to SAB

    :param url: URL where SAB is at
    :return: (boolean, string) list, True if connection can be made
    """
    try:
        f = urllib.urlopen(url)
    except (EOFError, IOError) as e:
        logger.log(u"Unable to connect to SAB: " + ex(e), logger.ERROR)
        return False, "Unable to connect"
    except httplib.InvalidURL as e:
        logger.log(u"Invalid SAB host, check your config: " + ex(e), logger.ERROR)
        return False, "Invalid SAB host"
    if f is None:
        logger.log(u"No data returned from SABnzbd", logger.ERROR)
        return False, "No data returned from SABnzbd"
    else:
        return True, f


def getSabAccesMethod(host=None):
    """
    Find out how we should connect to SAB

    :param host: hostname where SAB lives
    :param username: username to use
    :param password: password to use
    :param apikey: apikey to use
    :return: (boolean, string) with True if method was successful
    """
    url = host + "api?mode=auth"

    result, f = _sabURLOpenSimple(url)
    if not result:
        return False, f

    result, sabText = _checkSabResponse(f)
    if not result:
        return False, sabText

    return True, sabText


def testAuthentication(host=None, username=None, password=None, apikey=None):
    """
    Sends a simple API request to SAB to determine if the given connection information is connect

    :param host: The host where SAB is running (incl port)
    :param username: The username to use for the HTTP request
    :param password: The password to use for the HTTP request
    :param apikey: The API key to provide to SAB
    :return: A tuple containing the success boolean and a message
    """

    # build up the URL parameters
    params = {
        'mode': 'queue',
        'output': 'json',
        'ma_username': username,
        'ma_password': password,
        'apikey': apikey
    }
    url = host + "api?" + urllib.urlencode(params)

    # send the test request
    logger.log(u"SABnzbd test URL: " + url, logger.DEBUG)
    result, f = _sabURLOpenSimple(url)
    if not result:
        return False, f

    # check the result and determine if it's good or not
    result, sabText = _checkSabResponse(f)
    if not result:
        return False, sabText

    return True, "Success"
