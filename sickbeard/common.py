# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickrage.tv/
# Git: https://github.com/SiCKRAGETV/SickRage.git
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
from UserDict import UserDict

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
FAILED = 11  # episode downloaded or snatched we don't want
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

# pylint: disable=W0232
class Quality(object):
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

    sceneQualityStrings = {NONE: "N/A",
                           UNKNOWN: "Unknown",
                           SDTV: "HDTV",
                           SDDVD: "",
                           HDTV: "720p HDTV",
                           RAWHDTV: "1080i HDTV",
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
        """
        Returns string values associated with Status prefix

        :param status: Status prefix to resolve
        :return: Human readable status value
        """
        toReturn = {}
        for q in Quality.qualityStrings.keys():
            toReturn[Quality.compositeStatus(status, q)] = Quality.statusPrefixes[status] + " (" + \
                                                           Quality.qualityStrings[q] + ")"
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

        :param anime: Boolean to indicate if the show we're resolving is Anime
        :return: Quality prefix
        """

        # Try Scene names first
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

        :param name: Episode filename to analyse
        :param anime: Boolean to indicate if the show we're resolving is Anime
        :return: Quality prefix
        """

        # pylint: disable=R0912

        ret = Quality.UNKNOWN
        if not name:
            return ret

        name = os.path.basename(name)

        checkName = lambda list, func: func([re.search(x, name, re.I) for x in list])

        if anime:
            dvdOptions = checkName([r"dvd", r"dvdrip"], any)
            blueRayOptions = checkName([r"BD", r"blue?-?ray"], any)
            sdOptions = checkName([r"360p", r"480p", r"848x480", r"XviD"], any)
            hdOptions = checkName([r"720p", r"1280x720", r"960x720"], any)
            fullHD = checkName([r"1080p", r"1920x1080"], any)

            if sdOptions and not blueRayOptions and not dvdOptions:
                ret = Quality.SDTV
            elif dvdOptions:
                ret = Quality.SDDVD
            elif hdOptions and not blueRayOptions and not fullHD:
                ret = Quality.HDTV
            elif fullHD and not blueRayOptions and not hdOptions:
                ret = Quality.FULLHDTV
            elif hdOptions and not blueRayOptions and not fullHD:
                ret = Quality.HDWEBDL
            elif blueRayOptions and hdOptions and not fullHD:
                ret = Quality.HDBLURAY
            elif blueRayOptions and fullHD and not hdOptions:
                ret = Quality.FULLHDBLURAY

            return ret

        if (checkName([r"480p|web.?dl|web(rip|mux|hd)|[sph]d.?tv|dsr|tv(rip|mux)|satrip", r"xvid|divx|[xh].?26[45]"], all)
                and not checkName([r"(720|1080)[pi]"], all) and not checkName([r"hr.ws.pdtv.[xh].?26[45]"], any)):
            ret = Quality.SDTV
        elif (checkName([r"dvd(rip|mux)|b[rd](rip|mux)|blue?-?ray", r"xvid|divx|[xh].?26[45]"], all)
              and not checkName([r"(720|1080)[pi]"], all) and not checkName([r"hr.ws.pdtv.[xh].?26[45]"], any)):
            ret = Quality.SDDVD
        elif (checkName([r"720p", r"hd.?tv", r"[xh].?26[45]"], all) or checkName([r"hr.ws.pdtv.[xh].?26[45]"], any)
              and not checkName([r"1080[pi]"], all)):
            ret = Quality.HDTV
        elif checkName([r"720p|1080i", r"hd.?tv", r"mpeg-?2"], all) or checkName([r"1080[pi].hdtv", r"h.?26[45]"], all):
            ret = Quality.RAWHDTV
        elif checkName([r"1080p", r"hd.?tv", r"[xh].?26[45]"], all):
            ret = Quality.FULLHDTV
        elif checkName([r"720p", r"web.?dl|web(rip|mux|hd)"], all) or checkName([r"720p", r"itunes", r"[xh].?26[45]"], all):
            ret = Quality.HDWEBDL
        elif checkName([r"1080p", r"web.?dl|web(rip|mux|hd)"], all) or checkName([r"1080p", r"itunes", r"[xh].?26[45]"], all):
            ret = Quality.FULLHDWEBDL
        elif checkName([r"720p", r"blue?-?ray|hddvd|b[rd](rip|mux)", r"[xh].?26[45]"], all):
            ret = Quality.HDBLURAY
        elif checkName([r"1080p", r"blue?-?ray|hddvd|b[rd](rip|mux)", r"[xh].?26[45]"], all):
            ret = Quality.FULLHDBLURAY

        return ret

    @staticmethod
    def assumeQuality(name):
        """
        Assume a quality from file extension if we cannot resolve it otherwise

        :param name: File name of episode to analyse
        :return: Quality prefix
        """
        quality = Quality.qualityFromFileMeta(name)
        if quality != Quality.UNKNOWN:
            return quality

        if name.lower().endswith(".ts"):
            return Quality.RAWHDTV
        else:
            return Quality.UNKNOWN

    @staticmethod
    def qualityFromFileMeta(filename):
        """
        Get quality file file metadata

        :param filename: Filename to analyse
        :return: Quality prefix
        """

        # pylint: disable=R0912

        from hachoir_parser import createParser
        from hachoir_metadata import extractMetadata
        from hachoir_core.log import log
        log.use_print = False

        try:
            parser = createParser(filename)
        # pylint: disable=W0703
        except Exception:
            parser = None

        if not parser:
            return Quality.UNKNOWN

        try:
            metadata = extractMetadata(parser)
        # pylint: disable=W0703
        except Exception:
            metadata = None

        try:
            # pylint: disable=W0212
            parser.stream._input.close()
        # pylint: disable=W0703
        except Exception:
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

        base_filename = os.path.basename(filename)
        bluray = re.search(r"blue?-?ray|hddvd|b[rd](rip|mux)", base_filename, re.I) is not None
        webdl = re.search(r"web.?dl|web(rip|mux|hd)", base_filename, re.I) is not None

        ret = Quality.UNKNOWN
        if height > 1000:
            ret = ((Quality.FULLHDTV, Quality.FULLHDBLURAY)[bluray], Quality.FULLHDWEBDL)[webdl]
        elif height > 680 and height < 800:
            ret = ((Quality.HDTV, Quality.HDBLURAY)[bluray], Quality.HDWEBDL)[webdl]
        elif height < 680:
            ret = (Quality.SDTV, Quality.SDDVD)[re.search(r'dvd|b[rd]rip|blue?-?ray', base_filename, re.I) is not None]

        return ret

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

        for q in sorted(Quality.qualityStrings.keys(), reverse=True):
            if status > q * 100:
                return (status - q * 100, q)

        return (status, Quality.NONE)

    @staticmethod
    def sceneQualityFromName(name, quality):
        """
        Get scene naming parameters from filename and quality

        :param name: Filename to check
        :param quality: int of quality to make sure we get the right rip type
        :return: encoder type for scene quality naming
        """
        codecList = ['xvid', 'divx']
        x264List = ['x264', 'x 264', 'x.264']
        h264List = ['h264', 'h 264', 'h.264', 'avc']
        x265List = ['x265', 'x 265', 'x.265']
        h265List = ['h265', 'h 265', 'h.265', 'hevc']
        codecList.extend(x264List + h264List + x265List + h265List)

        found_codecs = {}
        found_codec = None

        for codec in codecList:
            if codec in name.lower():
                found_codecs[name.lower().rfind(codec)] = codec

        if found_codecs:
            sorted_codecs = sorted(found_codecs, reverse=True)
            found_codec = found_codecs[list(sorted_codecs)[0]]

        # 2 corresponds to SDDVD quality
        if quality == 2:
            if re.search(r"b(r|d|rd)?(-| |\.)?(rip|mux)", name.lower()):
                rip_type = " BDRip"
            elif re.search(r"(dvd)(-| |\.)?(rip|mux)?", name.lower()):
                rip_type = " DVDRip"
            else:
                rip_type = ""

        if found_codec:
            if codecList[0] in found_codec:
                found_codec = 'XviD'
            elif codecList[1] in found_codec:
                found_codec = 'DivX'
            elif found_codec in x264List:
                found_codec = x264List[0]
            elif found_codec in h264List:
                found_codec = h264List[0]
            elif found_codec in x265List:
                found_codec = x265List[0]
            elif found_codec in h265List:
                found_codec = h265List[0]

            if quality == 2:
                return rip_type + " " + found_codec
            else:
                return " " + found_codec
        elif quality == 2:
            return rip_type
        else:
            return ""

    @staticmethod
    def statusFromName(name, assume=True, anime=False):
        """
        Get a status object from filename

        :param name: Filename to check
        :param assume: boolean to assume quality by extension if we can't figure it out
        :param anime: boolean to enable anime parsing
        :return: Composite status/quality object
        """
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

HD720p = Quality.combineQualities([Quality.HDTV, Quality.HDWEBDL, Quality.HDBLURAY], [])
HD1080p = Quality.combineQualities([Quality.FULLHDTV, Quality.FULLHDWEBDL, Quality.FULLHDBLURAY], [])

SD = Quality.combineQualities([Quality.SDTV, Quality.SDDVD], [])
HD = Quality.combineQualities([HD720p, HD1080p], [])
ANY = Quality.combineQualities([SD, HD], [])

# legacy template, cant remove due to reference in mainDB upgrade?
BEST = Quality.combineQualities([Quality.SDTV, Quality.HDTV, Quality.HDWEBDL], [Quality.HDTV])

qualityPresets = (SD, HD, HD720p, HD1080p, ANY)
qualityPresetStrings = {SD: "SD",
                        HD: "HD",
                        HD720p: "HD720p",
                        HD1080p: "HD1080p",
                        ANY: "Any"}


class StatusStrings(UserDict):
    """
    Dictionary containing strings for status codes

    Keys must be convertible to int or a ValueError will be raised.  This is intentional to match old functionality until
    the old StatusStrings is fully deprecated, then we will raise a KeyError instead, where appropriate.

    Membership checks using __contains__ (i.e. 'x in y') do not raise a ValueError to match expected dict functionality
    """
    # todo: Deprecate StatusStrings().statusStrings and use StatusStrings() directly
    # todo: Deprecate .has_key and switch to 'x in y'
    # todo: Switch from raising ValueError to a saner KeyError
    # todo: Raise KeyError when unable to resolve a missing key instead of returning ''
    # todo: Make key of None match dict() functionality

    @property
    def statusStrings(self):  # for backwards compatibility
        return self.data

    def __setitem__(self, key, value):
        self.data[int(key)] = value  # make sure all keys being assigned values are ints

    def __missing__(self, key):
        """
        If the key is not found, search for the missing key in qualities

        Keys must be convertible to int or a ValueError will be raised.  This is intentional to match old functionality until
        the old StatusStrings is fully deprecated, then we will raise a KeyError instead, where appropriate.
        """
        if isinstance(key, int):  # if the key is already an int...
            if key in self.keys() + Quality.DOWNLOADED + Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST + Quality.ARCHIVED:
                status, quality = Quality.splitCompositeStatus(key)
                if quality == Quality.NONE:  # If a Quality is not listed... (shouldn't this be 'if not quality:'?)
                    return self[status]  # ...return the status...
                else:
                    return self[status] + " (" + Quality.qualityStrings[quality] + ")"  # ...otherwise append the quality to the status
            else:
                return ''  # return '' to match old functionality when the numeric key is not found
        return self[int(key)]  # Since the key was not an int, let's try int(key) instead

    # Keep this until all has_key() checks are converted to 'key in dict'
    # or else has_keys() won't search __missing__ for keys
    def has_key(self, key):
        """
        Override has_key() to test membership using an 'x in y' search

        Keys must be convertible to int or a ValueError will be raised.  This is intentional to match old functionality until
        the old StatusStrings is fully deprecated, then we will raise a KeyError instead, where appropriate.
        """
        return key in self  # This will raise a ValueError if __missing__ can't convert the key to int

    def __contains__(self, key):
        """
        Checks for existence of key

        Unlike has_key() and __missing__() this will NOT raise a ValueError to match expected functionality
        when checking for 'key in dict'
        """
        try:
            # This will raise a ValueError if we can't convert the key to int
            return ((int(key) in self.data) or
                    (int(key) in Quality.DOWNLOADED + Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST + Quality.ARCHIVED))
        except ValueError:  # The key is not numeric and since we only want numeric keys...
            # ...and we don't want this function to fail...
            pass  # ...suppress the ValueError and do nothing, the key does not exist

statusStrings = StatusStrings(
    {UNKNOWN: "Unknown",
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
     SNATCHED_BEST: "Snatched (Best)"
     })

# pylint: disable=R0903
class Overview(object):

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
