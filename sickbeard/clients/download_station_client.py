# coding=utf-8
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
# GNU General Public License for more details
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.
#
# Uses the Synology Download Station API: http://download.synology.com/download/Document/DeveloperGuide/Synology_Download_Station_Web_API.pdf

from __future__ import unicode_literals
from requests.compat import urljoin
import os
import re

import sickbeard
from sickbeard import logger
from sickbeard.clients.generic import GenericClient


class DownloadStationAPI(GenericClient):

    def __init__(self, host=None, username=None, password=None):

        super(DownloadStationAPI, self).__init__('DownloadStation', host, username, password)

        self.urls = {
            'login': urljoin(self.host, 'webapi/auth.cgi'),
            'task': urljoin(self.host, 'webapi/DownloadStation/task.cgi'),
        }

        self.url = self.urls['task']

        generic_errors = {
            100: 'Unknown error',
            101: 'Invalid parameter',
            102: 'The requested API does not exist',
            103: 'The requested method does not exist',
            104: 'The requested version does not support the functionality',
            105: 'The logged in session does not have permission',
            106: 'Session timeout',
            107: 'Session interrupted by duplicate login',
        }
        self.error_map = {
            'create': {
                400: 'File upload failed',
                401: 'Max number of tasks reached',
                402: 'Destination denied',
                403: 'Destination does not exist',
                404: 'Invalid task id',
                405: 'Invalid task action',
                406: 'No default destination',
                407: 'Set destination failed',
                408: 'File does not exist'
            },
            'login': {
                400: 'No such account or incorrect password',
                401: 'Account disabled',
                402: 'Permission denied',
                403: '2-step verification code required',
                404: 'Failed to authenticate 2-step verification code'
            }
        }
        for api_method in self.error_map:
            self.error_map[api_method].update(generic_errors)

        self._task_post_data = {
            'api': 'SYNO.DownloadStation.Task',
            'version': '1',
            'method': 'create',
            'session': 'DownloadStation',
        }

    def _check_response(self, data=None, files=None):
        try:
            jdata = self.response.json()
        except (ValueError, AttributeError):
            logger.log('Could not convert response to json, check the host:port: {0!r}'.format(self.response))
            return False

        if not jdata.get('success'):
            error_code = jdata.get('error', {}).get('code')
            if error_code == 403 and sickbeard.TORRENT_PATH and (data or {}).get('destination') == sickbeard.TORRENT_PATH and os.path.isabs(sickbeard.TORRENT_PATH):
                data['destination'] = re.sub(r'^/volume\d/', '', sickbeard.TORRENT_PATH).lstrip('/')
                self._request(method='post', data=data, files=files)

                try:
                    jdata = self.response.json()
                except ValueError:
                    return False

                if jdata.get('success'):
                    sickbeard.TORRENT_PATH = data['destination']

        if not jdata.get('success'):
            error_code = jdata.get('error', {}).get('code')
            api_method = (data or {}).get('method', 'login')
            log_string = self.error_map.get(api_method)[error_code]
            logger.log('{0}'.format(log_string))

        return jdata.get('success')

    def _get_auth(self):
        if self.session.cookies and self.auth:
            return self.auth

        params = {
            'api': 'SYNO.API.Auth',
            'version': 2,
            'method': 'login',
            'account': self.username.encode('utf-8') if isinstance(self.username, unicode) else self.username,
            'passwd': self.password.encode('utf-8') if isinstance(self.password, unicode) else self.password,
            'session': 'DownloadStation',
            'format': 'cookie'
        }

        self.response = self.session.get(self.urls['login'], params=params, verify=False)

        self.auth = self._check_response()
        return self.auth

    def _add_torrent_uri(self, result):
        data = self._task_post_data
        data['uri'] = result.url

        if sickbeard.TORRENT_PATH:
            data['destination'] = sickbeard.TORRENT_PATH

        self._request(method='post', data=data)
        return self._check_response(data)

    def _add_torrent_file(self, result):
        data = self._task_post_data

        if sickbeard.TORRENT_PATH:
            data['destination'] = sickbeard.TORRENT_PATH

        if result.resultType.startswith('nzb'):
            files = {'file': (result.name + '.nzb', result.extraInfo[0])}
        else:
            files = {'file': (result.name + '.torrent', result.content)}

        self._request(method='post', data=data, files=files)
        return self._check_response(data, files)

    def sendNZB(self, result):

        logger.log('Calling {0} Client'.format(self.name), logger.DEBUG)

        if not (self.auth or self._get_auth()):
            logger.log('{0}: Authentication Failed'.format(self.name), logger.WARNING)
            return False

        if result.resultType == 'nzb':
            return self._add_torrent_uri(result)
        elif result.resultType == 'nzbdata':
            return self._add_torrent_file(result)

api = DownloadStationAPI()
