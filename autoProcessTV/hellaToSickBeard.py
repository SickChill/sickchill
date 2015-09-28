#!/usr/bin/env python2.7

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


import sys

import autoProcessTV

if len(sys.argv) < 4:
    print "No folder supplied - is this being called from HellaVCR?"
    sys.exit()
else:
    autoProcessTV.processEpisode(sys.argv[3], sys.argv[2])
