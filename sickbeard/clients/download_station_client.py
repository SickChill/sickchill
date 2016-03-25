# coding=utf-8
# Authors:
# Pedro Jose Pereira Vieito <pvieito@gmail.com> (Twitter: @pvieito)
#
# URL: https://github.com/mr-orange/Sick-Beard
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
from sickbeard.clients.generic import GenericClient


class DownloadStationAPI(GenericClient):

    def __init__(self, host=None, username=None, password=None):

        super(DownloadStationAPI, self).__init__('DownloadStation', host, username, password)

        self.urls = {
            'login': urljoin(self.host, 'webapi/auth.cgi'),
            'task': urljoin(self.host, 'webapi/DownloadStation/task.cgi'),
            'info': urljoin(self.host, '/webapi/DownloadStation/info.cgi'),
            'dsminfo': urljoin(self.host, '/webapi/entry.cgi')
        }

        self.url = self.urls['task']

        self.error_map = {
            100: 'Unknown error',
            101: 'Invalid parameter',
            102: 'The requested API does not exist',
            103: 'The requested method does not exist',
            104: 'The requested version does not support the functionality',
            105: 'The logged in session does not have permission',
            106: 'Session timeout',
            107: 'Session interrupted by duplicate login'
        }
        self.checked_destination = False
        self.destination = sickbeard.TORRENT_PATH

    def _check_response(self):
        try:
            jdata = self.response.json()
        except ValueError:
            self.session.cookies.clear()
            self.auth = False
            return self.auth

        self.auth = jdata.get('success')
        if not self.auth:
            error_code = jdata.get('error', {}).get('code')
            sickbeard.logger.log('{}'.format(self.error_map.get(error_code, jdata)))
            self.session.cookies.clear()

        return self.auth

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

        try:
            self.response = self.session.get(self.urls['login'], params=params, verify=False)
            self.response.raise_for_status()
        except Exception as error:
            sickbeard.helpers.handle_requests_exception(error)
            self.session.cookies.clear()
            self.auth = False
            return self.auth

        return self._check_response()

    def _add_torrent_uri(self, result):

        data = {
            'api': 'SYNO.DownloadStation.Task',
            'version': '1',
            'method': 'create',
            'session': 'DownloadStation',
            'uri': result.url
        }

        if not self._check_destination():
            return False

        if sickbeard.TORRENT_PATH:
            data['destination'] = sickbeard.TORRENT_PATH

        self._request(method='post', data=data)
        return self._check_response()

    def _add_torrent_file(self, result):

        data = {
            'api': 'SYNO.DownloadStation.Task',
            'version': '1',
            'method': 'create',
            'session': 'DownloadStation',
        }

        if not self._check_destination():
            return False

        if sickbeard.TORRENT_PATH:
            data['destination'] = sickbeard.TORRENT_PATH

        files = {'file': (result.name + '.torrent', result.content)}

        self._request(method='post', data=data, files=files)
        return self._check_response()

    def _check_destination(self):  # pylint: disable=too-many-return-statements, too-many-branches
        if not (self.auth or self._get_auth()):
            return False

        if self.checked_destination and self.destination == sickbeard.TORRENT_PATH:
            return True

        params = {
            'api': 'SYNO.DSM.Info',
            'version': 2,
            'method': 'getinfo',
            'session': 'DownloadStation'
        }

        try:
            self.response = self.session.get(self.urls['dsminfo'], params=params, verify=False, timeout=120)
            self.response.raise_for_status()
        except Exception as error:
            sickbeard.helpers.handle_requests_exception(error)
            self.session.cookies.clear()
            self.auth = False
            return False

        destination = ''
        if self._check_response():
            jdata = self.response.json()
            version_string = jdata.get('data', {}).get('version_string')
            if not version_string:
                sickbeard.logger.log('Could not get the version_string from DSM: {0}'.format(jdata))
                return False

            if version_string.startswith('DSM 6'):
                #  This is DSM6, lets make sure the location is relative
                if sickbeard.TORRENT_PATH:
                    if os.path.isabs(sickbeard.TORRENT_PATH):
                        sickbeard.TORRENT_PATH = re.sub(r'^/volume\d/', '', sickbeard.TORRENT_PATH).lstrip('/')
                else:
                    #  Since they didnt specify the location in the settings, lets make sure the default is relative,
                    #  Or forcefully set the location setting in SickRage
                    params.update({
                        'method': 'getconfig',
                        'version': 2
                    })

                    try:
                        self.response = self.session.get(self.urls['info'], params=params, verify=False, timeout=120)
                        self.response.raise_for_status()
                    except Exception as error:
                        sickbeard.helpers.handle_requests_exception(error)
                        self.session.cookies.clear()
                        self.auth = False
                        return False

                    if self._check_response():
                        jdata = self.response.json()
                        destination = jdata.get('data', {}).get('default_destination')
                        if destination:
                            if os.path.isabs(destination):
                                sickbeard.TORRENT_PATH = re.sub(r'^/volume\d/', '', destination).lstrip('/')
                        else:
                            sickbeard.logger.log('default_destination could not be determined for DSM6: {0}'.format(jdata))
                            return False

        if destination or sickbeard.TORRENT_PATH:
            sickbeard.logger.log('Destination is now {0}'.format(sickbeard.TORRENT_PATH or destination))

        self.checked_destination = True
        self.destination = sickbeard.TORRENT_PATH
        return True

api = DownloadStationAPI()
