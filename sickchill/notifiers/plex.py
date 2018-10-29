# coding=utf-8

# Author: Dustyn Gibson <miigotu@gmail.com>
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

import re

import six

import sickchill
from sickchill import common, logger
from sickchill.helpers import getURL, make_session
from sickchill.helper.exceptions import ex

try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree




class Notifier(object):
    def __init__(self):
        self.headers = {
            'X-Plex-Device-Name': 'SickChill',
            'X-Plex-Product': 'SickChill Notifier',
            'X-Plex-Client-Identifier': sickchill.common.USER_AGENT,
            'X-Plex-Version': '2016.02.10'
        }
        self.session = make_session()

    @staticmethod
    def _notify_pht(message, title='SickChill', host=None, username=None, password=None, force=False):  # pylint: disable=too-many-arguments
        """Internal wrapper for the notify_snatch and notify_download functions

        Args:
            message: Message body of the notice to send
            title: Title of the notice to send
            host: Plex Home Theater(s) host:port
            username: Plex username
            password: Plex password
            force: Used for the Test method to override config safety checks

        Returns:
            Returns a list results in the format of host:ip:result
            The result will either be 'OK' or False, this is used to be parsed by the calling function.

        """

        # suppress notifications if the notifier is disabled but the notify options are checked
        if not sickchill.USE_PLEX_CLIENT and not force:
            return False

        host = host or sickchill.PLEX_CLIENT_HOST
        username = username or sickchill.PLEX_CLIENT_USERNAME
        password = password or sickchill.PLEX_CLIENT_PASSWORD

        return sickchill.notifiers.kodi_notifier._notify_kodi(message, title=title, host=host, username=username, password=password, force=force, dest_app="PLEX")  # pylint: disable=protected-access

##############################################################################
# Public functions
##############################################################################

    def notify_snatch(self, ep_name):
        if sickchill.PLEX_NOTIFY_ONSNATCH:
            self._notify_pht(ep_name, common.notifyStrings[common.NOTIFY_SNATCH])

    def notify_download(self, ep_name):
        if sickchill.PLEX_NOTIFY_ONDOWNLOAD:
            self._notify_pht(ep_name, common.notifyStrings[common.NOTIFY_DOWNLOAD])

    def notify_subtitle_download(self, ep_name, lang):
        if sickchill.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notify_pht(ep_name + ': ' + lang, common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD])

    def notify_git_update(self, new_version='??'):
        if sickchill.NOTIFY_ON_UPDATE:
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            if update_text and title and new_version:
                self._notify_pht(update_text + new_version, title)

    def notify_login(self, ipaddress=""):
        if sickchill.NOTIFY_ON_LOGIN:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            if update_text and title and ipaddress:
                self._notify_pht(update_text.format(ipaddress), title)

    def test_notify_pht(self, host, username, password):
        return self._notify_pht('This is a test notification from SickChill',
                                'Test Notification', host, username, password, force=True)

    def test_notify_pms(self, host, username, password, plex_server_token):
        return self.update_library(host=host, username=username, password=password,
                                   plex_server_token=plex_server_token, force=True)

    def update_library(self, ep_obj=None, host=None,  # pylint: disable=too-many-arguments, too-many-locals, too-many-statements, too-many-branches
                       username=None, password=None,
                       plex_server_token=None, force=False):

        """Handles updating the Plex Media Server host via HTTP API

        Plex Media Server currently only supports updating the whole video library and not a specific path.

        Returns:
            Returns None for no issue, else a string of host with connection issues

        """

        if not (sickchill.USE_PLEX_SERVER and sickchill.PLEX_UPDATE_LIBRARY) and not force:
            return None

        host = host or sickchill.PLEX_SERVER_HOST
        if not host:
            logger.log('PLEX: No Plex Media Server host specified, check your settings', logger.DEBUG)
            return False

        if not self.get_token(username, password, plex_server_token):
            logger.log('PLEX: Error getting auth token for Plex Media Server, check your settings', logger.WARNING)
            return False

        file_location = '' if not ep_obj else ep_obj.location
        host_list = {x.strip() for x in host.split(',') if x.strip()}
        hosts_all = hosts_match = {}
        hosts_failed = set()

        for cur_host in host_list:

            url = 'http{0}://{1}/library/sections'.format(('', 's')[sickchill.PLEX_SERVER_HTTPS], cur_host)
            try:
                xml_response = getURL(url, headers=self.headers, session=self.session, returns='text', verify=False,
                                      allow_proxy=False)
                if not xml_response:
                    logger.log('PLEX: Error while trying to contact Plex Media Server: {0}'.format
                               (cur_host), logger.WARNING)
                    hosts_failed.add(cur_host)
                    continue

                media_container = etree.fromstring(xml_response)
            except IOError as error:
                logger.log('PLEX: Error while trying to contact Plex Media Server: {0}'.format
                           (ex(error)), logger.WARNING)
                hosts_failed.add(cur_host)
                continue
            except Exception as error:
                if 'invalid token' in str(error):
                    logger.log('PLEX: Please set TOKEN in Plex settings: ', logger.WARNING)
                else:
                    logger.log('PLEX: Error while trying to contact Plex Media Server: {0}'.format
                               (ex(error)), logger.WARNING)
                hosts_failed.add(cur_host)
                continue

            sections = media_container.findall('.//Directory')
            if not sections:
                logger.log('PLEX: Plex Media Server not running on: {0}'.format
                           (cur_host), logger.DEBUG)
                hosts_failed.add(cur_host)
                continue

            for section in sections:
                if 'show' == section.attrib['type']:

                    keyed_host = [(str(section.attrib['key']), cur_host)]
                    hosts_all.update(keyed_host)
                    if not file_location:
                        continue

                    for section_location in section.findall('.//Location'):
                        section_path = re.sub(r'[/\\]+', '/', section_location.attrib['path'].lower())
                        section_path = re.sub(r'^(.{,2})[/\\]', '', section_path)
                        location_path = re.sub(r'[/\\]+', '/', file_location.lower())
                        location_path = re.sub(r'^(.{,2})[/\\]', '', location_path)

                        if section_path in location_path:
                            hosts_match.update(keyed_host)

        if force:
            return (', '.join(set(hosts_failed)), None)[not len(hosts_failed)]

        if hosts_match:
            logger.log('PLEX: Updating hosts where TV section paths match the downloaded show: ' + ', '.join(set(hosts_match)), logger.DEBUG)
        else:
            logger.log('PLEX: Updating all hosts with TV sections: ' + ', '.join(set(hosts_all)), logger.DEBUG)

        hosts_try = (hosts_match.copy(), hosts_all.copy())[not len(hosts_match)]
        for section_key, cur_host in six.iteritems(hosts_try):

            url = 'http{0}://{1}/library/sections/{2}/refresh'.format(('', 's')[sickchill.PLEX_SERVER_HTTPS], cur_host, section_key)
            try:
                getURL(url, headers=self.headers, session=self.session, returns='text', verify=False, allow_proxy=False)
            except Exception as error:
                logger.log('PLEX: Error updating library section for Plex Media Server: {0}'.format
                           (ex(error)), logger.WARNING)
                hosts_failed.add(cur_host)

        return (', '.join(set(hosts_failed)), None)[not len(hosts_failed)]

    def get_token(self, username=None, password=None, plex_server_token=None):
        username = username or sickchill.PLEX_SERVER_USERNAME
        password = password or sickchill.PLEX_SERVER_PASSWORD
        plex_server_token = plex_server_token or sickchill.PLEX_SERVER_TOKEN

        if plex_server_token:
            self.headers['X-Plex-Token'] = plex_server_token

        if 'X-Plex-Token' in self.headers:
            return True

        if not (username and password):
            return True

        logger.log('PLEX: fetching plex.tv credentials for user: ' + username, logger.DEBUG)

        params = {
            'user[login]': username,
            'user[password]': password
        }

        try:
            response = getURL('https://plex.tv/users/sign_in.json',
                              post_data=params,
                              headers=self.headers,
                              session=self.session,
                              returns='json',
                              allow_proxy=False)

            self.headers['X-Plex-Token'] = response['user']['authentication_token']

        except Exception as error:
            self.headers.pop('X-Plex-Token', '')
            logger.log('PLEX: Error fetching credentials from from plex.tv for user {0}: {1}'.format
                       (username, error), logger.DEBUG)

        return 'X-Plex-Token' in self.headers
