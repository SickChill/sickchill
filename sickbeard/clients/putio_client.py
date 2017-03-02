# Author: Clinton Collins <clinton.collins@gmail.com>
# Medicine: Dustyn Gibson <miigotu@gmail.com>
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
from requests.compat import urlencode, urljoin, urlparse

from sickbeard import helpers
from sickbeard.clients.generic import GenericClient


class PutioAPI(GenericClient):
    def __init__(self, host=None, username=None, password=None):

        super(PutioAPI, self).__init__('put_io', host, username, password)

        self.client_id = 2392  # sickrage-ng
        self.redirect_uri = 'https://sickrage.github.io'
        self.url = 'https://api.put.io/login'
        self.auth_path = urljoin(self.url, '/v2/oauth2/authenticate')
        self.session.headers['Accept'] = 'application/json'

    @property
    def authentication_url(self):
        params = {
            'client_id': self.client_id,
            'response_type': 'token',
            'redirect_uri': self.redirect_uri
        }
        return self.auth_path + "?" + urlencode(params)

    def _get_auth(self):
        parsed_url = urlparse(self.authentication_url)
        post_data = {
            'name': self.username,
            'password': self.password,
            'next': parsed_url.path + '?' + parsed_url.query
        }

        try:
            response = self.session.post(self.url, data=post_data,
                                         allow_redirects=False)
            response.raise_for_status()

            response = self.session.get(response.headers['location'],
                                        allow_redirects=False)
            response.raise_for_status()

            resulting_uri = '{redirect_uri}#access_token=(.*)'.format(
                redirect_uri=re.escape(self.redirect_uri))

            self.auth = re.search(resulting_uri, response.headers['location']).group(1)

        except Exception as error:
            helpers.handle_requests_exception(error)
            self.auth = None

        return self.auth

    def _add_torrent_uri(self, result):
        self.url = 'https://api.put.io/v2/transfers/add'
        post_data = {
            'url': result.url,
            'save_parent_id': 0,
            'extract': True,
            'oauth_token': self.auth
        }
        if not self._request('POST', data=post_data):
            return False

        j = self.response.json()
        return j.get("transfer", {}).get('save_parent_id') == 0

    def _add_torrent_file(self, result):
        self.url = 'https://upload.put.io/v2/files/upload'
        post_data = {
            'parent_id': 0,
            'oauth_token': self.auth
        }
        files = {'file': (result.name + '.torrent', result.content)}
        if not self._request('POST', data=post_data, files=files):
            return False

        return self.response.json()['status'] == "OK"


api = PutioAPI()
