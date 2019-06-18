# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickchill.github.io
#
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.
# pylint: disable=abstract-method,too-many-lines, R

from __future__ import print_function, unicode_literals

from authentication import KeyHandler
from webapi import (ApiCall, ApiError, ApiHandler, CMDBacklog, CMDComingEpisodes, CMDDailySearch, CMDEpisode, CMDEpisodeSearch, CMDEpisodeSetStatus,
                    CMDExceptions, CMDFailed, CMDFullSubtitleSearch, CMDHelp, CMDHistory, CMDHistoryClear, CMDHistoryTrim, CMDLogs, CMDLogsClear,
                    CMDPostProcess, CMDProperSearch, CMDShow, CMDShowAddExisting, CMDShowAddNew, CMDShowCache, CMDShowDelete, CMDShowGetBanner,
                    CMDShowGetFanArt, CMDShowGetNetworkLogo, CMDShowGetPoster, CMDShowGetQuality, CMDShowPause, CMDShowRefresh, CMDShows, CMDShowSeasonList,
                    CMDShowSeasons, CMDShowSetQuality, CMDShowsStats, CMDShowStats, CMDShowUpdate, CMDSickBeard, CMDSickBeardAddRootDir,
                    CMDSickBeardCheckScheduler, CMDSickBeardCheckVersion, CMDSickBeardDeleteRootDir, CMDSickBeardGetDefaults, CMDSickBeardGetMessages,
                    CMDSickBeardGetRootDirs, CMDSickBeardPauseBacklog, CMDSickBeardPing, CMDSickBeardRestart, CMDSickBeardSearchIndexers,
                    CMDSickBeardSearchTVDB, CMDSickBeardSearchTVRAGE, CMDSickBeardSetDefaults, CMDSickBeardShutdown, CMDSickBeardUpdate, CMDSubtitleSearch,
                    function_mapper, TVDBShorthandWrapper)
