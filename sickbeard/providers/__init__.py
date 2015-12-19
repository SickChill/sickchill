# coding=utf-8

# Author: Nic Wolfe <nic@wolfeden.ca>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from os import sys
from random import shuffle

import sickbeard
from sickbeard import logger
from sickbeard.providers import btn, newznab, rsstorrent, womble, thepiratebay, torrentleech, kat, iptorrents, torrentz, \
    omgwtfnzbs, scc, hdtorrents, torrentday, hdbits, hounddawgs, speedcd, nyaatorrents, animenzb, bluetigers, cpasbien, fnt, xthor, torrentbytes, \
    freshontv, titansoftv, morethantv, bitsoup, t411, tokyotoshokan, shazbat, rarbg, tntvillage, binsearch, torrentproject, extratorrent, \
    scenetime, btdigg, transmitthenet, tvchaosuk, bitcannon, pretome, gftracker, hdspace, newpct, elitetorrent, bitsnoop, danishbits, hd4free
from sickrage.providers import AlphaRatio

__all__ = [
    'womble', 'btn', 'thepiratebay', 'kat', 'torrentleech', 'scc', 'hdtorrents',
    'torrentday', 'hdbits', 'hounddawgs', 'iptorrents', 'omgwtfnzbs',
    'speedcd', 'nyaatorrents', 'animenzb', 'torrentbytes', 'freshontv', 'titansoftv',
    'morethantv', 'bitsoup', 't411', 'tokyotoshokan',
    'shazbat', 'rarbg', 'tntvillage', 'binsearch', 'bluetigers', 'cpasbien',
    'fnt', 'xthor', 'scenetime', 'btdigg', 'transmitthenet', 'tvchaosuk',
    'torrentproject', 'extratorrent', 'bitcannon', 'torrentz', 'pretome', 'gftracker',
    'hdspace', 'newpct', 'elitetorrent', 'bitsnoop', 'danishbits', 'hd4free'
] + [
    'AlphaRatio'
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
    return [x.provider for x in [getProviderModule(y) for y in __all__] if x]


def getProviderModule(name):
    prefixes = ['sickbeard.providers.', 'sickrage.providers.']

    for prefix in prefixes:
        if name in __all__ and prefix + name in sys.modules:
            return sys.modules[prefix + name]

    raise Exception(u'Can\'t find %s in %s' % (name, prefixes))


def getProviderClass(provider_id):
    providerMatch = [x for x in
                     sickbeard.providerList + sickbeard.newznabProviderList + sickbeard.torrentRssProviderList if
                     x and x.get_id() == provider_id]

    if len(providerMatch) != 1:
        return None
    else:
        return providerMatch[0]
