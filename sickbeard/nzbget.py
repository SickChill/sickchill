# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickrage.github.io
# Git: https://github.com/SickRage/SickRage.git
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

from __future__ import unicode_literals

import datetime
from base64 import standard_b64encode

from six.moves import http_client, xmlrpc_client

import sickbeard
from sickbeard import logger
from sickbeard.common import Quality
from sickrage.helper.common import try_int


def sendNZB(nzb, proper=False):  # pylint: disable=too-many-locals, too-many-statements, too-many-branches, too-many-return-statements
    '''
    Sends NZB to NZBGet client

    :param nzb: nzb object
    :param proper: True if this is a Proper download, False if not. Defaults to False
    '''
    if sickbeard.NZBGET_HOST is None:
        logger.log('No NZBget host found in configuration. Please configure it.', logger.WARNING)
        return False

    addToTop = False
    nzbgetprio = 0
    category = sickbeard.NZBGET_CATEGORY
    if nzb.show.is_anime:
        category = sickbeard.NZBGET_CATEGORY_ANIME

    url = 'http{0}://{1}:{2}@{3}/xmlrpc'.format(
        's' if sickbeard.NZBGET_USE_HTTPS else '',
        sickbeard.NZBGET_USERNAME,
        sickbeard.NZBGET_PASSWORD,
        sickbeard.NZBGET_HOST)

    nzbGetRPC = xmlrpc_client.ServerProxy(url)
    try:
        if nzbGetRPC.writelog('INFO', 'SickRage connected to drop off {0} any moment now.'.format(nzb.name + '.nzb')):
            logger.log('Successful connected to NZBget', logger.DEBUG)
        else:
            logger.log('Successful connected to NZBget, but unable to send a message', logger.WARNING)

    except http_client.socket.error:
        logger.log(
            'Please check your NZBget host and port (if it is running). NZBget is not responding to this combination',
            logger.WARNING)
        return False

    except xmlrpc_client.ProtocolError as e:
        if e.errmsg == 'Unauthorized':
            logger.log('NZBget username or password is incorrect.', logger.WARNING)
        else:
            logger.log('Protocol Error: ' + e.errmsg, logger.ERROR)
        return False

    dupekey = ''
    dupescore = 0
    # if it aired recently make it high priority and generate DupeKey/Score
    for curEp in nzb.episodes:
        if dupekey == '':
            if curEp.show.indexer == 1:
                dupekey = 'SickRage-' + str(curEp.show.indexerid)
            elif curEp.show.indexer == 2:
                dupekey = 'SickRage-tvr' + str(curEp.show.indexerid)
        dupekey += '-' + str(curEp.season) + '.' + str(curEp.episode)
        if datetime.date.today() - curEp.airdate <= datetime.timedelta(days=7):
            addToTop = True
            nzbgetprio = sickbeard.NZBGET_PRIORITY
        else:
            category = sickbeard.NZBGET_CATEGORY_BACKLOG
            if nzb.show.is_anime:
                category = sickbeard.NZBGET_CATEGORY_ANIME_BACKLOG

    if nzb.quality != Quality.UNKNOWN:
        dupescore = nzb.quality * 100
    if proper:
        dupescore += 10

    nzbcontent64 = None
    if nzb.resultType == 'nzbdata':
        data = nzb.extraInfo[0]
        nzbcontent64 = standard_b64encode(data)

    logger.log('Sending NZB to NZBget')
    logger.log('URL: ' + url, logger.DEBUG)

    try:
        # Find out if nzbget supports priority (Version 9.0+), old versions beginning with a 0.x will use the old command
        nzbget_version_str = nzbGetRPC.version()
        nzbget_version = try_int(nzbget_version_str[:nzbget_version_str.find('.')])
        if nzbget_version == 0:
            if nzbcontent64:
                nzbget_result = nzbGetRPC.append(nzb.name + '.nzb', category, addToTop, nzbcontent64)
            else:
                if nzb.resultType == 'nzb':
                    if not nzb.provider.login():
                        return False

                    data = nzb.provider.get_url(nzb.url, returns='content')
                    if data is None:
                        return False

                    nzbcontent64 = standard_b64encode(data)

                nzbget_result = nzbGetRPC.append(nzb.name + '.nzb', category, addToTop, nzbcontent64)
        elif nzbget_version == 12:
            if nzbcontent64 is not None:
                nzbget_result = nzbGetRPC.append(nzb.name + '.nzb', category, nzbgetprio, False,
                                                 nzbcontent64, False, dupekey, dupescore, 'score')
            else:
                nzbget_result = nzbGetRPC.appendurl(nzb.name + '.nzb', category, nzbgetprio, False,
                                                    nzb.url, False, dupekey, dupescore, 'score')
        # v13+ has a new combined append method that accepts both (url and content)
        # also the return value has changed from boolean to integer
        # (Positive number representing NZBID of the queue item. 0 and negative numbers represent error codes.)
        elif nzbget_version >= 13:
            nzbget_result = nzbGetRPC.append(nzb.name + '.nzb', nzbcontent64 if nzbcontent64 is not None else nzb.url,
                                             category, nzbgetprio, False, False, dupekey, dupescore,
                                             'score') > 0
        else:
            if nzbcontent64 is not None:
                nzbget_result = nzbGetRPC.append(nzb.name + '.nzb', category, nzbgetprio, False,
                                                 nzbcontent64)
            else:
                nzbget_result = nzbGetRPC.appendurl(nzb.name + '.nzb', category, nzbgetprio, False,
                                                    nzb.url)

        if nzbget_result:
            logger.log('NZB sent to NZBget successfully', logger.DEBUG)
            return True
        else:
            logger.log('NZBget could not add {0} to the queue'.format(nzb.name + '.nzb'), logger.WARNING)
            return False
    except Exception:
        logger.log('Connect Error to NZBget: could not add {0} to the queue'.format(nzb.name + '.nzb'), logger.WARNING)
        return False
