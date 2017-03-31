# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
#
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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

from os import sys
from random import shuffle

import sickbeard
from sickbeard.providers import btn, thepiratebay, torrentleech, iptorrents, torrentz, \
    omgwtfnzbs, scc, hdtorrents, torrentday, hdbits, hounddawgs, speedcd, nyaatorrents, xthor, abnormal, torrentbytes, cpasbien,\
    torrent9, freshontv, morethantv, t411, tokyotoshokan, shazbat, rarbg, alpharatio, tntvillage, binsearch, torrentproject, extratorrent, \
    scenetime, transmitthenet, tvchaosuk, bitcannon, pretome, gftracker, hdspace, newpct, elitetorrent, danishbits, hd4free, limetorrents, \
    norbits, horriblesubs, filelist, skytorrents, ncore, archetorrent, hdtorrents_it, immortalseed, ilcorsaronero

__all__ = [
    'btn', 'thepiratebay', 'torrentleech', 'scc', 'hdtorrents',
    'torrentday', 'hdbits', 'hounddawgs', 'iptorrents', 'omgwtfnzbs',
    'speedcd', 'nyaatorrents', 'torrentbytes', 'freshontv', 'cpasbien',
    'torrent9','morethantv', 't411', 'tokyotoshokan', 'alpharatio',
    'shazbat', 'rarbg', 'tntvillage', 'binsearch',
    'xthor', 'abnormal', 'scenetime', 'transmitthenet', 'tvchaosuk',
    'torrentproject', 'extratorrent', 'bitcannon', 'torrentz', 'pretome', 'gftracker',
    'hdspace', 'newpct', 'elitetorrent', 'danishbits', 'hd4free', 'limetorrents',
    'norbits', 'horriblesubs', 'filelist', 'skytorrents', 'ncore', 'archetorrent', 'hdtorrents_it',
    'immortalseed', 'ilcorsaronero'
]


def sortedProviderList(randomize=False):
    initialList = sickbeard.providerList + sickbeard.newznabProviderList + sickbeard.torrentRssProviderList
    providerDict = dict(zip([x.get_id() for x in initialList], initialList))

    newList = []

    # add all modules in the priority list, in order
    for curModule in sickbeard.PROVIDER_ORDER:
        if curModule in providerDict:
            newList.append(providerDict[curModule])

    # add all enabled providers first
    for curModule in providerDict:
        if providerDict[curModule] not in newList and providerDict[curModule].is_enabled():
            newList.append(providerDict[curModule])

    # add any modules that are missing from that list
    for curModule in providerDict:
        if providerDict[curModule] not in newList:
            newList.append(providerDict[curModule])

    if randomize:
        shuffle(newList)

    return newList


def makeProviderList():
    return [x.provider for x in (getProviderModule(y) for y in __all__) if x]


def getProviderModule(name):
    name = name.lower()
    prefix = "sickbeard.providers."
    if name in __all__ and prefix + name in sys.modules:
        return sys.modules[prefix + name]
    else:
        raise Exception("Can't find " + prefix + name + " in " + "Providers")


def getProviderClass(provider_id):
    providerMatch = [x for x in
                     sickbeard.providerList + sickbeard.newznabProviderList + sickbeard.torrentRssProviderList if
                     x and x.get_id() == provider_id]

    if len(providerMatch) != 1:
        return None
    else:
        return providerMatch[0]


def check_enabled_providers():
    if not sickbeard.DEVELOPER:
        backlog_enabled, daily_enabled = False, False
        for provider in sortedProviderList():
            if provider.is_active():
                if provider.enable_daily:
                    daily_enabled = True

                if provider.enable_backlog:
                    backlog_enabled = True

                if backlog_enabled and daily_enabled:
                    break

        if not (daily_enabled and backlog_enabled):
            formatted_msg = "No NZB/Torrent providers found or enabled for {0}.<br/>".format(
                (("daily searches and backlog searches", "daily searches")[backlog_enabled], "backlog searches")[daily_enabled])
            formatted_msg += "Please <a href=\"" + sickbeard.WEB_ROOT + "/config/providers/\">check your settings</a>."
            sickbeard.helpers.add_site_message(formatted_msg, 'danger')
        else:
            sickbeard.helpers.remove_site_message(begins="No NZB/Torrent providers found or enabled for")
