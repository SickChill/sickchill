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
from sickbeard.providers import btn, womble, thepiratebay, torrentleech, kat, iptorrents, torrentz, \
    omgwtfnzbs, scc, hdtorrents, torrentday, hdbits, hounddawgs, speedcd, nyaatorrents, bluetigers, xthor, abnormal, phxbit, torrentbytes, cpasbien,\
    freshontv, morethantv, bitsoup, t411, tokyotoshokan, shazbat, rarbg, alpharatio, tntvillage, binsearch, torrentproject, extratorrent, \
    scenetime, btdigg, transmitthenet, tvchaosuk, bitcannon, pretome, gftracker, hdspace, newpct, elitetorrent, bitsnoop, danishbits, hd4free, limetorrents, \
    norbits, ilovetorrents

__all__ = [
    'womble', 'btn', 'thepiratebay', 'kat', 'torrentleech', 'scc', 'hdtorrents',
    'torrentday', 'hdbits', 'hounddawgs', 'iptorrents', 'omgwtfnzbs',
    'speedcd', 'nyaatorrents', 'torrentbytes', 'freshontv', 'cpasbien',
    'morethantv', 'bitsoup', 't411', 'tokyotoshokan', 'alpharatio',
    'shazbat', 'rarbg', 'tntvillage', 'binsearch', 'bluetigers',
    'xthor', 'abnormal', 'phxbit', 'scenetime', 'btdigg', 'transmitthenet', 'tvchaosuk',
    'torrentproject', 'extratorrent', 'bitcannon', 'torrentz', 'pretome', 'gftracker',
    'hdspace', 'newpct', 'elitetorrent', 'bitsnoop', 'danishbits', 'hd4free', 'limetorrents',
    'norbits', 'ilovetorrents'
]


def sortedProviderList(randomize=False):
    initialList = sickbeard.provider_list + sickbeard.newznab_provider_list + sickbeard.torrent_rss_provider_list
    providerDict = dict(zip([x.get_id() for x in initialList], initialList))

    newList = []

    # add all modules in the priority list, in order
    for cur_module in sickbeard.PROVIDER_ORDER:
        if cur_module in providerDict:
            newList.append(providerDict[cur_module])

    # add all enabled providers first
    for cur_module in providerDict:
        if providerDict[cur_module] not in newList and providerDict[cur_module].is_enabled():
            newList.append(providerDict[cur_module])

    # add any modules that are missing from that list
    for cur_module in providerDict:
        if providerDict[cur_module] not in newList:
            newList.append(providerDict[cur_module])

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
                     sickbeard.provider_list + sickbeard.newznab_provider_list + sickbeard.torrent_rss_provider_list if
                     x and x.get_id() == provider_id]

    if len(providerMatch) != 1:
        return None
    else:
        return providerMatch[0]
