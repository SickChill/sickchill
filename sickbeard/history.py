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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import db
import datetime

from sickbeard.common import SNATCHED, SUBTITLED, FAILED, Quality
from sickbeard import encodingKludge as ek
from sickrage.show.History import History


def _logHistoryItem(action, showid, season, episode, quality, resource, provider, version=-1):
    logDate = datetime.datetime.today().strftime(History.date_format)
    resource = ek.ss(resource)

    myDB = db.DBConnection()
    myDB.action(
        "INSERT INTO history (action, date, showid, season, episode, quality, resource, provider, version) VALUES (?,?,?,?,?,?,?,?,?)",
        [action, logDate, showid, season, episode, quality, resource, provider, version])


def logSnatch(searchResult):
    for curEpObj in searchResult.episodes:

        showid = int(curEpObj.show.indexerid)
        season = int(curEpObj.season)
        episode = int(curEpObj.episode)
        quality = searchResult.quality
        version = searchResult.version

        providerClass = searchResult.provider
        if providerClass != None:
            provider = providerClass.name
        else:
            provider = "unknown"

        action = Quality.compositeStatus(SNATCHED, searchResult.quality)

        resource = searchResult.name

        _logHistoryItem(action, showid, season, episode, quality, resource, provider, version)


def logDownload(episode, filename, new_ep_quality, release_group=None, version=-1):
    showid = int(episode.show.indexerid)
    season = int(episode.season)
    epNum = int(episode.episode)

    quality = new_ep_quality

    # store the release group as the provider if possible
    if release_group:
        provider = release_group
    else:
        provider = -1

    action = episode.status

    _logHistoryItem(action, showid, season, epNum, quality, filename, provider, version)


def logSubtitle(showid, season, episode, status, subtitleResult):
    resource = subtitleResult.language.opensubtitles
    provider = subtitleResult.provider_name

    status, quality = Quality.splitCompositeStatus(status)
    action = Quality.compositeStatus(SUBTITLED, quality)

    _logHistoryItem(action, showid, season, episode, quality, resource, provider)


def logFailed(epObj, release, provider=None):
    showid = int(epObj.show.indexerid)
    season = int(epObj.season)
    epNum = int(epObj.episode)
    status, quality = Quality.splitCompositeStatus(epObj.status)
    action = Quality.compositeStatus(FAILED, quality)

    _logHistoryItem(action, showid, season, epNum, quality, release, provider)
