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
import json
from base64 import b64encode

import sickbeard
from sickbeard import logger
from .generic import GenericClient

class PutioAPI(GenericClient):
    def __init__(self, host=None, username=None, password=None):

        super(PutioAPI, self).__init__('put_io', host, username, password)

        self.url = 'https://api.put.io/v2/oauth2/authenticate?client_id=2103&response_type=token&redirect_uri=http%3A%2F%2Fdevclinton.com'

    def _get_auth(self):

        post_data = {
            'name': self.username,
            'password': self.password,
            'next': '/v2/oauth2/authenticate?client_id=2103&response_type=token&redirect_uri=http://devclinton.com'
        }

        logger.log("Login Data: %s" % json.dumps(post_data), logger.INFO)

        try:
            self.response = self.session.get(self.url, timeout=120)
            logger.log("Getting authenicate page: %s" % self.response, logger.INFO)
            self.tok_response = self.session.post('https://api.put.io/login',
                data=post_data, allow_redirects=False)
            logger.log("PutIO Authencate Form: %s. Headers: %s " % ( self.tok_response, self.tok_response.headers )  , logger.INFO )
            logger.log("PutIO Authencate Form Body: \n%s " % ( self.tok_response.text )  , logger.INFO )
            logger.log("PutIO Url: %s" % self.tok_response.headers['location'], logger.INFO)
            self.tok_response = self.session.get(self.tok_response.headers['location'], allow_redirects=False)
            logger.log("PutIO Authencate Response: %s. Headers: %s " % ( self.tok_response, self.tok_response.headers )  , logger.INFO )
            self.auth = re.search('http://devclinton\.com#access_token=(.*)', self.tok_response.headers['location']).group(1)
            logger.log("PutIO Token: %s" % self.auth, logger.INFO)
        except Exception:
            logger.log("Putio Auth Error: %s" % Exception, logger.INFO)
            return None
        self.access_token = self.auth
        logger.log("Access Token: %s" % self.access_token , logger.INFO)
        return self.auth

# If we get an URL, it is easy peasy, and we use the
    def _add_torrent_uri(self, result):

        params={ 'oauth_token': self.auth }
        post_data = {
            'url': result.url,
            'save_parent_id': 0,
            'extract': True
        }
        logger.log("Put.io Transfer Params: %s" % post_data, logger.INFO)
        self.response = self.session.post('https://api.put.io/v2/transfers/add',  data=post_data, params=params)
        logger.log("Put.io Transfer Add Response: %s\n%s" % (self.response, self.response.text), logger.INFO)
        j = self.response.json()
        return "transfer" in j and j['transfer']['save_parent_id'] == 0

    def _add_torrent_file(self, result):
        post_data = { 'name': 'putio_torrent','parent': 0 }
        params={ 'oauth_token': self.auth }

        logger.log("Put.io Upload Params: %s" % post_data, logger.INFO)

        self.response = self.session.post('https://api.put.io/v2/files/upload?oauth_token=%s' % self.access_token,  data=post_data, files=('putio_torrent',result.name), params=params)
        logger.log("Put.io Upload Response: %s\n%s" % (self.response, self.response.text), logger.INFO)
        return self.response.json()['status'] == "OK"


api = PutioAPI()
