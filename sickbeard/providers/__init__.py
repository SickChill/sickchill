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

from __future__ import unicode_literals

from os import sys
from random import shuffle

import sickbeard
from sickbeard.providers import (abnormal, alpharatio, archetorrent, binsearch, bitcannon, btn, cpasbien, danishbits, elitetorrent, filelist, gftracker,
                                 hd4free, hdbits, hdspace, hdtorrents, hdtorrents_it, horriblesubs, hounddawgs, ilcorsaronero, immortalseed, iptorrents,
                                 limetorrents, morethantv, ncore, nebulance, newpct, norbits, nyaa, omgwtfnzbs, pretome, rarbg, scc, scenetime, shazbat,
                                 skytorrents, speedcd, thepiratebay, tntvillage, tokyotoshokan, torrent9, torrentbytes, torrentday, torrentleech,
                                 torrentproject, torrentz, tvchaosuk, xthor, t411si)

__all__ = [
    'abnormal', 'alpharatio', 'archetorrent', 'binsearch', 'bitcannon', 'btn', 'cpasbien', 'danishbits',
    'elitetorrent', 'filelist', 'gftracker', 'hd4free', 'hdbits', 'hdspace', 'hdtorrents', 'hdtorrents_it',
    'horriblesubs', 'hounddawgs', 'ilcorsaronero', 'immortalseed', 'iptorrents', 'limetorrents', 'morethantv',
    'ncore', 'nebulance', 'newpct', 'norbits', 'nyaa', 'omgwtfnzbs', 'pretome', 'rarbg', 'scc', 'scenetime',
    'shazbat', 'skytorrents', 'speedcd', 'thepiratebay', 'tntvillage', 'tokyotoshokan', 'torrent9',
    'torrentbytes', 'torrentday', 'torrentleech', 'torrentproject', 'torrentz', 'tvchaosuk', 'xthor', 't411si'
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
            searches = ((_('daily searches and backlog searches'), _('daily searches'))[backlog_enabled],
                        _('backlog searches'))[daily_enabled]
            formatted_msg = _('No NZB/Torrent providers found or enabled for {searches}.<br/>'
                              'Please <a href="{web_root}/config/providers/">check your settings</a>.')
            sickbeard.helpers.add_site_message(formatted_msg.format(searches=searches, web_root=sickbeard.WEB_ROOT),
                                               tag='no_providers_enabled', level='danger')
        else:
            sickbeard.helpers.remove_site_message(tag='no_providers_enabled')
