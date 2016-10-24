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

import os
import re
import json
from base64 import b64encode

import sickbeard
from sickbeard.clients.generic import GenericClient
import myjdapi

class JdownloaderAPI(GenericClient):
    def __init__(self, host=None, username=None, password=None):

        super(JdownloaderAPI, self).__init__('Jdownloader', host, username, password)
        self.username = sickbeard.DDL_USERNAME
        self.password = sickbeard.DDL_PASSWORD
        self.deviceName = sickbeard.JDOWNLOADER_DEVICE_NAME
        self.autostart = bool(sickbeard.JDOWNLOADER_AUTO_START)
        self.packageName = "Sickrage autograb"

        self.jd = myjdapi.Myjdapi()
        self.jd.set_app_key("Sickrage")

    def _get_auth(self):
        try:
            self.jd.connect(self.username, self.password)
        except Exception:
            return False

        return True

    def _add_uri(self, result):
        device=self.jd.get_device(self.deviceName)
        try:
            device.linkgrabber.add_links([{"autostart" : self.autostart, "links" : result.url, "packageName" : self.packageName }])
        except Exception:
            return False

        return True

api = JdownloaderAPI()
