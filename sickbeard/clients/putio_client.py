# Author: Clinton Collins <clinton.collins@gmail.com>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import re
import urllib

from sickbeard import logger
from .generic import GenericClient

# Base of our Put.io APIs
PUTIO_BASE_URL='https://api.put.io/v2'
# API Client ID that is registerd on put.io
API_CLIENT_ID='2392'
# API Client URL registered with put.io
API_CLIENT_REGISTERED_URL='https://sickrage.github.io'

class PutioAPI(GenericClient):
    def __init__(self, host=None, username=None, password=None):
        super(PutioAPI, self).__init__('put_io', host, username, password)
        self.url = '{}/oauth2/authenticate?client_id={}&response_type=token&redirect_uri={}'.format(
            PUTIO_BASE_URL,API_CLIENT_ID, urllib.urlencode(API_CLIENT_REGISTERED_URL))

    def _get_auth(self):

        post_data = {
            'name': self.username,
            'password': self.password,
            'next': '/v2/oauth2/authenticate?client_id={}&response_type=token&redirect_uri={}'.format(
                API_CLIENT_ID,API_CLIENT_REGISTERED_URL)
        }
        try:
            self.response = self.session.get(self.url, timeout=120)
            self.tok_response = self.session.post('https://api.put.io/login',
                                                  data=post_data, allow_redirects=False)
            self.tok_response = self.session.get(self.tok_response.headers['location'], allow_redirects=False)
            self.auth = re.search('{}#access_token=(.*)'.format(re.escape(API_CLIENT_REGISTERED_URL)),
                                  self.tok_response.headers['location']).group(1)
        except Exception:
            logger.log("Putio Auth Error: {}".format(Exception), logger.INFO)
            return None
        self.access_token = self.auth
        logger.log("Putio Access Token: {}".format(self.access_token) , logger.INFO)
        return self.auth

    # If we get an URL, it is easy peasy since Put.io will grab it for us.
    def _add_torrent_uri(self, result):
        params={ 'oauth_token': self.auth }
        post_data = {
            'url': result.url,
            'save_parent_id': 0,
            'extract': True
        }
        self.response = self.session.post('{}/transfers/add'.format(PUTIO_BASE_URL),  data=post_data, params=params)
        j = self.response.json()
        return "transfer" in j and j['transfer']['save_parent_id'] == 0

    # We got a Torrent file, so upload that file to Put.io
    def _add_torrent_file(self, result):
        post_data = { 'name': 'putio_torrent','parent': 0 }
        params={ 'oauth_token': self.auth }

        self.response = self.session.post('{}/files/upload?oauth_token={}'.format(PUTIO_BASE_URL,self.access_token),
                                          data=post_data, files=('putio_torrent',result.name), params=params)
        return self.response.json()['status'] == "OK"

api = PutioAPI()
