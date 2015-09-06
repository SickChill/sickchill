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

import os.path
import operator
import platform
import re
import uuid

from random import shuffle

SPOOF_USER_AGENT = False

# If some provider has an issue with functionality of SR, other than user agents, it's best to come talk to us rather than block.
# It is no different than us going to a provider if we have questions or issues. Be a team player here.
# This is disabled, was only added for testing, and has no config.ini or web ui setting. To enable, set SPOOF_USER_AGENT = True
user_agents = ['Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'
               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36'
               'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0'
               'Mozilla/5.0 (X11; Linux i586; rv:31.0) Gecko/20100101 Firefox/31.0'
               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A'
               'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5355d Safari/8536.25'
               'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko'
               'Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko'
              ]

INSTANCE_ID = str(uuid.uuid1())
USER_AGENT = ('SickRage/(' + platform.system() + '; ' + platform.release() + '; ' + INSTANCE_ID + ')')

if SPOOF_USER_AGENT:
    shuffle(user_agents)
    USER_AGENT = user_agents[0]

mediaExtensions = ['avi', 'mkv', 'mpg', 'mpeg', 'wmv',
                   'ogm', 'mp4', 'iso', 'img', 'divx',
                   'm2ts', 'm4v', 'ts', 'flv', 'f4v',
                   'mov', 'rmvb', 'vob', 'dvr-ms', 'wtv',
                   'ogv', '3gp', 'webm', 'tp']

subtitleExtensions = ['srt', 'sub', 'ass', 'idx', 'ssa']

cpu_presets = {'HIGH': 5,
               'NORMAL': 2,
               'LOW': 1
}

### Other constants
MULTI_EP_RESULT = -1
SEASON_RESULT = -2

### Notification Types
NOTIFY_SNATCH = 1
NOTIFY_DOWNLOAD = 2
NOTIFY_SUBTITLE_DOWNLOAD = 3
NOTIFY_GIT_UPDATE = 4
NOTIFY_GIT_UPDATE_TEXT = 5

notifyStrings = {}
notifyStrings[NOTIFY_SNATCH] = "Started Download"
notifyStrings[NOTIFY_DOWNLOAD] = "Download Finished"
notifyStrings[NOTIFY_SUBTITLE_DOWNLOAD] = "Subtitle Download Finished"
notifyStrings[NOTIFY_GIT_UPDATE] = "SickRage Updated"
notifyStrings[NOTIFY_GIT_UPDATE_TEXT] = "SickRage Updated To Commit#: "

### Episode statuses
UNKNOWN = -1  # should never happen
UNAIRED = 1  # episodes that haven't aired yet
SNATCHED = 2  # qualified with quality
WANTED = 3  # episodes we don't have but want to get
DOWNLOADED = 4  # qualified with quality
SKIPPED = 5  # episodes we don't want
ARCHIVED = 6  # episodes that you don't have locally (counts toward download completion stats)
IGNORED = 7  # episodes that you don't want included in your download stats
SNATCHED_PROPER = 9  # qualified with quality
SUBTITLED = 10  # qualified with quality
FAILED = 11  #episode downloaded or snatched we don't want
SNATCHED_BEST = 12  # episode redownloaded using best quality

NAMING_REPEAT = 1
NAMING_EXTEND = 2
NAMING_DUPLICATE = 4
NAMING_LIMITED_EXTEND = 8
NAMING_SEPARATED_REPEAT = 16
NAMING_LIMITED_EXTEND_E_PREFIXED = 32

multiEpStrings = {}
multiEpStrings[NAMING_REPEAT] = "Repeat"
multiEpStrings[NAMING_SEPARATED_REPEAT] = "Repeat (Separated)"
multiEpStrings[NAMING_DUPLICATE] = "Duplicate"
multiEpStrings[NAMING_EXTEND] = "Extend"
multiEpStrings[NAMING_LIMITED_EXTEND] = "Extend (Limited)"
multiEpStrings[NAMING_LIMITED_EXTEND_E_PREFIXED] = "Extend (Limited, E-prefixed)"


class Quality:
    NONE = 0  # 0
    SDTV = 1  # 1
    SDDVD = 1 << 1  # 2
    HDTV = 1 << 2  # 4
    RAWHDTV = 1 << 3  # 8  -- 720p/1080i mpeg2 (trollhd releases)
    FULLHDTV = 1 << 4  # 16 -- 1080p HDTV (QCF releases)
    HDWEBDL = 1 << 5  # 32
    FULLHDWEBDL = 1 << 6  # 64 -- 1080p web-dl
    HDBLURAY = 1 << 7  # 128
    FULLHDBLURAY = 1 << 8  # 256
    ANYHDTV = HDTV | FULLHDTV  # 20
    ANYWEBDL = HDWEBDL | FULLHDWEBDL  # 96
    ANYBLURAY = HDBLURAY | FULLHDBLURAY  # 384

    # put these bits at the other end of the spectrum, far enough out that they shouldn't interfere
    UNKNOWN = 1 << 15  # 32768

    qualityStrings = {NONE: "N/A",
                      UNKNOWN: "Unknown",
                      SDTV: "SDTV",
                      SDDVD: "SD DVD",
                      HDTV: "720p HDTV",
                      RAWHDTV: "RawHD",
                      FULLHDTV: "1080p HDTV",
                      HDWEBDL: "720p WEB-DL",
                      FULLHDWEBDL: "1080p WEB-DL",
                      HDBLURAY: "720p BluRay",
                      FULLHDBLURAY: "1080p BluRay"}

    combinedQualityStrings = {ANYHDTV: "HDTV",
                              ANYWEBDL: "WEB-DL",
                              ANYBLURAY: "BluRay"}

    cssClassStrings = {NONE: "N/A",
                       UNKNOWN: "Unknown",
                       SDTV: "SDTV",
                       SDDVD: "SDDVD",
                       HDTV: "HD720p",
                       RAWHDTV: "RawHD",
                       FULLHDTV: "HD1080p",
                       HDWEBDL: "HD720p",
                       FULLHDWEBDL: "HD1080p",
                       HDBLURAY: "HD720p",
                       FULLHDBLURAY: "HD1080p",
                       ANYHDTV: "any-hd",
                       ANYWEBDL: "any-hd",
                       ANYBLURAY: "any-hd"}

    statusPrefixes = {DOWNLOADED: "Downloaded",
                      SNATCHED: "Snatched",
                      SNATCHED_PROPER: "Snatched (Proper)",
                      FAILED: "Failed",
                      SNATCHED_BEST: "Snatched (Best)",
                      ARCHIVED: "Archived"}
    @staticmethod
    def _getStatusStrings(status):
        toReturn = {}
        for x in Quality.qualityStrings.keys():
            toReturn[Quality.compositeStatus(status, x)] = Quality.statusPrefixes[status] + " (" + \
                                                           Quality.qualityStrings[x] + ")"
        return toReturn

    @staticmethod
    def combineQualities(anyQualities, bestQualities):
        anyQuality = 0
        bestQuality = 0
        if anyQualities:
            anyQuality = reduce(operator.or_, anyQualities)
        if bestQualities:
            bestQuality = reduce(operator.or_, bestQualities)
        return anyQuality | (bestQuality << 16)

    @staticmethod
    def splitQuality(quality):
        anyQualities = []
        bestQualities = []
        for curQual in Quality.qualityStrings.keys():
            if curQual & quality:
                anyQualities.append(curQual)
            if curQual << 16 & quality:
                bestQualities.append(curQual)

        return (sorted(anyQualities), sorted(bestQualities))

    @staticmethod
    def nameQuality(name, anime=False):
        """
        Return The quality from an episode File renamed by SickRage
        If no quality is achieved it will try sceneQuality regex
        """

        #Try Scene names first
        quality = Quality.sceneQuality(name, anime)
        if quality != Quality.UNKNOWN:
            return quality

        quality = Quality.assumeQuality(name)
        if quality != Quality.UNKNOWN:
            return quality

        return Quality.UNKNOWN

    @staticmethod
    def sceneQuality(name, anime=False):
        """
        Return The quality from the scene episode File
        """
        if not name:
            return Quality.UNKNOWN

        name = os.path.basename(name)

        checkName = lambda list, func: func([re.search(x, name, re.I) for x in list])

        if anime:
            dvdOptions = checkName(["dvd", "dvdrip"], any)
            blueRayOptions = checkName(["BD", "blue?-?ray"], any)
            sdOptions = checkName(["360p", "480p", "848x480", "XviD"], any)
            hdOptions = checkName(["720p", "1280x720", "960x720"], any)
            fullHD = checkName(["1080p", "1920x1080"], any)

            if sdOptions and not blueRayOptions and not dvdOptions:
                return Quality.SDTV
            elif dvdOptions:
                return Quality.SDDVD
            elif hdOptions and not blueRayOptions and not fullHD:
                return Quality.HDTV
            elif fullHD and not blueRayOptions and not hdOptions:
                return Quality.FULLHDTV
            elif hdOptions and not blueRayOptions and not fullHD:
                return Quality.HDWEBDL
            elif blueRayOptions and hdOptions and not fullHD:
                return Quality.HDBLURAY
            elif blueRayOptions and fullHD and not hdOptions:
                return Quality.FULLHDBLURAY
            else:
                return Quality.UNKNOWN

        if checkName(["(pdtv|hdtv|dsr|tvrip).(xvid|x26[45]|h.?26[45])"], all) and not checkName(["(720|1080)[pi]"], all) and\
                not checkName(["hr.ws.pdtv.x26[45]"], any):
            return Quality.SDTV
        elif checkName(["web.dl|webrip", "xvid|x26[45]|h.?26[45]"], all) and not checkName(["(720|1080)[pi]"], all):
            return Quality.SDTV
        elif checkName(["(dvdrip|b[rd]rip|blue?-?ray)(.ws)?.(xvid|divx|x26[45])"], any) and not checkName(["(720|1080)[pi]"], all):
            return Quality.SDDVD
        elif checkName(["720p", "hdtv", "x26[45]"], all) or checkName(["hr.ws.pdtv.x26[45]"], any) and not checkName(
                ["1080[pi]"], all):
            return Quality.HDTV
        elif checkName(["720p|1080i", "hdtv", "mpeg-?2"], all) or checkName(["1080[pi].hdtv", "h.?26[45]"], all):
            return Quality.RAWHDTV
        elif checkName(["1080p", "hdtv", "x26[45]"], all):
            return Quality.FULLHDTV
        elif checkName(["720p", "web.dl|webrip"], all) or checkName(["720p", "itunes", "h.?26[45]"], all):
            return Quality.HDWEBDL
        elif checkName(["1080p", "web.dl|webrip"], all) or checkName(["1080p", "itunes", "h.?26[45]"], all):
            return Quality.FULLHDWEBDL
        elif checkName(["720p", "blue?-?ray|hddvd|b[rd]rip", "x26[45]"], all):
            return Quality.HDBLURAY
        elif checkName(["1080p", "blue?-?ray|hddvd|b[rd]rip", "x26[45]"], all):
            return Quality.FULLHDBLURAY
        else:
            return Quality.UNKNOWN

    @staticmethod
    def assumeQuality(name):
        quality = Quality.qualityFromFileMeta(name)
        if quality != Quality.UNKNOWN:
            return quality

        if name.lower().endswith(".ts"):
            return Quality.RAWHDTV
        else:
            return Quality.UNKNOWN

    @staticmethod
    def qualityFromFileMeta(filename):
        from hachoir_parser import createParser
        from hachoir_metadata import extractMetadata

        try:
            parser = createParser(filename)
        except Exception:
            parser = None

        if not parser:
            return Quality.UNKNOWN

        try:
            metadata = extractMetadata(parser)
        except Exception:
            metadata = None

        try:
            parser.stream._input.close()
        except:
            pass

        if not metadata:
            return Quality.UNKNOWN

        height = 0
        if metadata.has('height'):
            height = int(metadata.get('height') or 0)
        else:
            test = getattr(metadata, "iterGroups", None)
            if callable(test):
                for metagroup in metadata.iterGroups():
                    if metagroup.has('height'):
                        height = int(metagroup.get('height') or 0)

        if not height:
            return Quality.UNKNOWN

        if height > 1040:
            return Quality.FULLHDTV
        elif height > 680 and height < 760:
            return Quality.HDTV
        elif height < 680:
            return Quality.SDTV

        return Quality.UNKNOWN

    @staticmethod
    def compositeStatus(status, quality):
        return status + 100 * quality

    @staticmethod
    def qualityDownloaded(status):
        return (status - DOWNLOADED) / 100

    @staticmethod
    def splitCompositeStatus(status):
        """Returns a tuple containing (status, quality)"""
        if status == UNKNOWN:
            return (UNKNOWN, Quality.UNKNOWN)

        for x in sorted(Quality.qualityStrings.keys(), reverse=True):
            if status > x * 100:
                return (status - x * 100, x)

        return (status, Quality.NONE)

    @staticmethod
    def statusFromName(name, assume=True, anime=False):
        quality = Quality.nameQuality(name, anime)
        if assume and quality == Quality.UNKNOWN:
            quality = Quality.assumeQuality(name)
        return Quality.compositeStatus(DOWNLOADED, quality)

    DOWNLOADED = None
    SNATCHED = None
    SNATCHED_PROPER = None
    FAILED = None
    SNATCHED_BEST = None
    ARCHIVED = None

Quality.DOWNLOADED = [Quality.compositeStatus(DOWNLOADED, x) for x in Quality.qualityStrings.keys()]
Quality.SNATCHED = [Quality.compositeStatus(SNATCHED, x) for x in Quality.qualityStrings.keys()]
Quality.SNATCHED_PROPER = [Quality.compositeStatus(SNATCHED_PROPER, x) for x in Quality.qualityStrings.keys()]
Quality.FAILED = [Quality.compositeStatus(FAILED, x) for x in Quality.qualityStrings.keys()]
Quality.SNATCHED_BEST = [Quality.compositeStatus(SNATCHED_BEST, x) for x in Quality.qualityStrings.keys()]
Quality.ARCHIVED = [Quality.compositeStatus(ARCHIVED, x) for x in Quality.qualityStrings.keys()]

SD = Quality.combineQualities([Quality.SDTV, Quality.SDDVD], [])
HD = Quality.combineQualities(
    [Quality.HDTV, Quality.FULLHDTV, Quality.HDWEBDL, Quality.FULLHDWEBDL, Quality.HDBLURAY, Quality.FULLHDBLURAY],
    [])  # HD720p + HD1080p
HD720p = Quality.combineQualities([Quality.HDTV, Quality.HDWEBDL, Quality.HDBLURAY], [])
HD1080p = Quality.combineQualities([Quality.FULLHDTV, Quality.FULLHDWEBDL, Quality.FULLHDBLURAY], [])
ANY = Quality.combineQualities(
    [Quality.SDTV, Quality.SDDVD, Quality.HDTV, Quality.FULLHDTV, Quality.HDWEBDL, Quality.FULLHDWEBDL,
     Quality.HDBLURAY, Quality.FULLHDBLURAY, Quality.UNKNOWN], [])  # SD + HD

# legacy template, cant remove due to reference in mainDB upgrade?
BEST = Quality.combineQualities([Quality.SDTV, Quality.HDTV, Quality.HDWEBDL], [Quality.HDTV])

qualityPresets = (SD, HD, HD720p, HD1080p, ANY)
qualityPresetStrings = {SD: "SD",
                        HD: "HD",
                        HD720p: "HD720p",
                        HD1080p: "HD1080p",
                        ANY: "Any"}


class StatusStrings:
    def __init__(self):
        self.statusStrings = {UNKNOWN: "Unknown",
                              UNAIRED: "Unaired",
                              SNATCHED: "Snatched",
                              DOWNLOADED: "Downloaded",
                              SKIPPED: "Skipped",
                              SNATCHED_PROPER: "Snatched (Proper)",
                              WANTED: "Wanted",
                              ARCHIVED: "Archived",
                              IGNORED: "Ignored",
                              SUBTITLED: "Subtitled",
                              FAILED: "Failed",
                              SNATCHED_BEST: "Snatched (Best)"}

    def __getitem__(self, name):
        if name in Quality.DOWNLOADED + Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST + Quality.ARCHIVED:
            status, quality = Quality.splitCompositeStatus(name)
            if quality == Quality.NONE:
                return self.statusStrings[status]
            else:
                return self.statusStrings[status] + " (" + Quality.qualityStrings[quality] + ")"
        else:
            return self.statusStrings[name] if self.statusStrings.has_key(name) else ''

    def has_key(self, name):
        return name in self.statusStrings or name in Quality.DOWNLOADED or name in Quality.SNATCHED or name in Quality.SNATCHED_PROPER or name in Quality.SNATCHED_BEST


statusStrings = StatusStrings()


class Overview:
    UNAIRED = UNAIRED  # 1
    QUAL = 2
    WANTED = WANTED  # 3
    GOOD = 4
    SKIPPED = SKIPPED  # 5

    # For both snatched statuses. Note: SNATCHED/QUAL have same value and break dict.
    SNATCHED = SNATCHED_PROPER = SNATCHED_BEST  # 9

    overviewStrings = {SKIPPED: "skipped",
                       WANTED: "wanted",
                       QUAL: "qual",
                       GOOD: "good",
                       UNAIRED: "unaired",
                       SNATCHED: "snatched"}

# Get our xml namespaces correct for lxml
XML_NSMAP = {'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
             'xsd': 'http://www.w3.org/2001/XMLSchema'}

countryList = {'Australia': 'AU',
               'Canada': 'CA',
               'USA': 'US'
}
