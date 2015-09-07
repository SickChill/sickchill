#!/usr/bin/env python

# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of SickRage.
# DEPRECATION NOTICE: autoProcessTV is deprecated and will be removed
# from SickRage at 31-10-2015.
#
# Please switch to nzbToMedia from Clinton Hall, which is included in 
# the contrib folder
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import with_statement

import os.path
import sys

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), 'lib')))

try:
    import requests
except ImportError:
    print ("You need to install python requests library")
    sys.exit(1)

# Try importing Python 2 modules using new names
try:
    import ConfigParser as configparser
    import urllib2
    from urllib import urlencode

# On error import Python 3 modules
except ImportError:
    import configparser
    import urllib.request as urllib2
    from urllib.parse import urlencode

def processEpisode(dir_to_process, org_NZB_name=None, status=None):
    # Default values
    host = "localhost"
    port = "8081"
    username = ""
    password = ""
    ssl = 0
    web_root = "/"

    default_url = host + ":" + port + web_root
    if ssl:
        default_url = "https://" + default_url
    else:
        default_url = "http://" + default_url

    # Get values from config_file
    config = configparser.RawConfigParser()
    config_filename = os.path.join(os.path.dirname(sys.argv[0]), "autoProcessTV.cfg")

    if not os.path.isfile(config_filename):
        print ("ERROR: " + config_filename + " doesn\'t exist")
        print ("copy /rename " + config_filename + ".sample and edit\n")
        print ("Trying default url: " + default_url + "\n")

    else:
        try:
            print ("Loading config from " + config_filename + "\n")

            with open(config_filename, "r") as fp:
                config.readfp(fp)

            # Replace default values with config_file values
            host = config.get("SickBeard", "host")
            port = config.get("SickBeard", "port")
            username = config.get("SickBeard", "username")
            password = config.get("SickBeard", "password")

            try:
                ssl = int(config.get("SickBeard", "ssl"))

            except (configparser.NoOptionError, ValueError):
                pass

            try:
                web_root = config.get("SickBeard", "web_root")
                if not web_root.startswith("/"):
                    web_root = "/" + web_root

                if not web_root.endswith("/"):
                    web_root = web_root + "/"

            except configparser.NoOptionError:
                pass

        except EnvironmentError:
            e = sys.exc_info()[1]
            print ("Could not read configuration file: " + str(e))
            # There was a config_file, don't use default values but exit
            sys.exit(1)

    params = {}

    params['quiet'] = 1

    params['dir'] = dir_to_process
    if org_NZB_name != None:
        params['nzbName'] = org_NZB_name

    if status != None:
        params['failed'] = status

    if ssl:
        protocol = "https://"
    else:
        protocol = "http://"

    url = protocol + host + ":" + port + web_root + "home/postprocess/processEpisode"
    login_url = protocol + host + ":" + port + web_root + "login"

    print ("Opening URL: " + url)

    try:
        sess = requests.Session()
        sess.post(login_url, data={'username': username, 'password': password}, stream=True, verify=False)
        result = sess.get(url, params=params, stream=True, verify=False)

        for line in result.iter_lines():
            if line:
                print (line.strip())

    except IOError:
        e = sys.exc_info()[1]
        print ("Unable to open URL: " + str(e))
        sys.exit(1)


if __name__ == "__main__":
    print ("This module is supposed to be used as import in other scripts and not run standalone.")
    print ("Use sabToSickBeard instead.")
    sys.exit(1)
