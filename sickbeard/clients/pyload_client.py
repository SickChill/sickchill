# coding=utf-8

# Author: Mr_Orange <mr_orange@hotmail.it>
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

import sickbeard
import json
from sickbeard.clients.generic import GenericClient
from sickbeard import logger, helpers

class PyLoadAPI(GenericClient):
    def __init__(self, host=None, username=None, password=None):

        super(PyLoadAPI, self).__init__('pyLoad', host, username, password)
        self.username = sickbeard.DDL_USERNAME
        self.password = sickbeard.DDL_PASSWORD
        self.host = sickbeard.DDL_HOST

    def _get_auth(self):
        try:
            post_data={'username':self.username,'password':self.password}

            self.response = self.session.request(
                "POST", self.host+"api/login", data=post_data, timeout=120)

            if self.response.text == "false":
                raise Exception('Login fail')

            self.cookies = self.response.cookies
            self.auth = self.response.text

        except Exception as error:
            helpers.handle_requests_exception(error)
            return False

        return self.auth

    def _add_uri(self, result):
        try:
            payload={
                "name":result.name,
                "links":[result.url]
            }
            payloadJSON = {k: json.dumps(v) for k, v in payload.items()}
            self.response = self.session.request(
                "POST", self.host+"api/addPackage", data=payloadJSON, timeout=120, cookies=self.cookies)
            return True

        except Exception as error:
            helpers.handle_requests_exception(error)
            return False

api = PyLoadAPI()
