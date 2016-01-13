# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickrage.github.io/
# Git: https://github.com/SickRage/SickRage.git
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

"""
Common interface for Quality and Status
"""

# pylint: disable=line-too-long


import operator
from os import path
import platform
import re
import uuid

from hachoir_parser import createParser  # pylint: disable=import-error
from hachoir_metadata import extractMetadata  # pylint: disable=import-error
from hachoir_core.log import log  # pylint: disable=import-error

from fake_useragent import settings as UA_SETTINGS, UserAgent
from sickbeard.numdict import NumDict
from sickrage.helper.encoding import ek

# If some provider has an issue with functionality of SR, other than user agents, it's best to come talk to us rather than block.
# It is no different than us going to a provider if we have questions or issues. Be a team player here.
# This is disabled, was only added for testing, and has no config.ini or web ui setting. To enable, set SPOOF_USER_AGENT = True
SPOOF_USER_AGENT = False
INSTANCE_ID = str(uuid.uuid1())
USER_AGENT = ('SickRage/(' + platform.system() + '; ' + platform.release() + '; ' + INSTANCE_ID + ')')
UA_SETTINGS.DB = ek(path.abspath, ek(path.join, ek(path.dirname, __file__), '../lib/fake_useragent/ua.json'))
UA_POOL = UserAgent()
if SPOOF_USER_AGENT:
    USER_AGENT = UA_POOL.random

cpu_presets = {
    'HIGH': 5,
    'NORMAL': 2,
    'LOW': 1
}

# Other constants
MULTI_EP_RESULT = -1
SEASON_RESULT = -2

# Notification Types
NOTIFY_SNATCH = 1
NOTIFY_DOWNLOAD = 2
NOTIFY_SUBTITLE_DOWNLOAD = 3
NOTIFY_GIT_UPDATE = 4
NOTIFY_GIT_UPDATE_TEXT = 5
NOTIFY_LOGIN = 6
NOTIFY_LOGIN_TEXT = 7

notifyStrings = NumDict({
    NOTIFY_SNATCH: "Started Download",
    NOTIFY_DOWNLOAD: "Download Finished",
    NOTIFY_SUBTITLE_DOWNLOAD: "Subtitle Download Finished",
    NOTIFY_GIT_UPDATE: "SickRage Updated",
    NOTIFY_GIT_UPDATE_TEXT: "SickRage Updated To Commit#: ",
    NOTIFY_LOGIN: "SickRage new login",
    NOTIFY_LOGIN_TEXT: "New login from IP: {0}. http://geomaplookup.net/?ip={0}"
})

# Episode statuses
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
SNATCHED_BEST = 12  # episode re-downloaded using best quality

NAMING_REPEAT = 1
NAMING_EXTEND = 2
NAMING_DUPLICATE = 4
NAMING_LIMITED_EXTEND = 8
NAMING_SEPARATED_REPEAT = 16
NAMING_LIMITED_EXTEND_E_PREFIXED = 32

MULTI_EP_STRINGS = NumDict({
    NAMING_REPEAT: "Repeat",
    NAMING_SEPARATED_REPEAT: "Repeat (Separated)",
    NAMING_DUPLICATE: "Duplicate",
    NAMING_EXTEND: "Extend",
    NAMING_LIMITED_EXTEND: "Extend (Limited)",
    NAMING_LIMITED_EXTEND_E_PREFIXED: "Extend (Limited, E-prefixed)"
})


class Quality(object):
    """
    Determine quality and set status codes
    """
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

    qualityStrings = NumDict({
        None: "None",
        NONE: "N/A",
        UNKNOWN: "Unknown",
        SDTV: "SDTV",
        SDDVD: "SD DVD",
        HDTV: "720p HDTV",
        RAWHDTV: "RawHD",
        FULLHDTV: "1080p HDTV",
        HDWEBDL: "720p WEB-DL",
        FULLHDWEBDL: "1080p WEB-DL",
        HDBLURAY: "720p BluRay",
        FULLHDBLURAY: "1080p BluRay"
    })

    sceneQualityStrings = NumDict({
        None: "None",
        NONE: "N/A",
        UNKNOWN: "Unknown",
        SDTV: "HDTV",
        SDDVD: "",
        HDTV: "720p HDTV",
        RAWHDTV: "1080i HDTV",
        FULLHDTV: "1080p HDTV",
        HDWEBDL: "720p WEB-DL",
        FULLHDWEBDL: "1080p WEB-DL",
        HDBLURAY: "720p BluRay",
        FULLHDBLURAY: "1080p BluRay"
    })

    combinedQualityStrings = NumDict({
        ANYHDTV: "HDTV",
        ANYWEBDL: "WEB-DL",
        ANYBLURAY: "BluRay"
    })

    cssClassStrings = NumDict({
        None: "None",
        NONE: "N/A",
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
        ANYBLURAY: "any-hd"
    })

    statusPrefixes = NumDict({
        DOWNLOADED: "Downloaded",
        SNATCHED: "Snatched",
        SNATCHED_PROPER: "Snatched (Proper)",
        FAILED: "Failed",
        SNATCHED_BEST: "Snatched (Best)",
        ARCHIVED: "Archived"
    })

    @staticmethod
    def _getStatusStrings(status):
        """
        Returns string values associated with Status prefix

        :param status: Status prefix to resolve
        :return: Human readable status value
        """
        to_return = {}
        for quality in Quality.qualityStrings:
            if quality is not None:
                stat = Quality.statusPrefixes[status]
                qual = Quality.qualityStrings[quality]
                comp = Quality.compositeStatus(status, quality)
                to_return[comp] = '%s (%s)' % (stat, qual)
        return to_return

    @staticmethod
    def combineQualities(any_qualities, best_qualities):
        any_quality = 0
        best_quality = 0
        if any_qualities:
            any_quality = reduce(operator.or_, any_qualities)
        if best_qualities:
            best_quality = reduce(operator.or_, best_qualities)
        return any_quality | (best_quality << 16)

    @staticmethod
    def splitQuality(quality):
        if quality is None:
            quality = Quality.NONE
        allowed_qualities = []
        prefferred_qualities = []
        for cur_qual in Quality.qualityStrings:
            if cur_qual is None:
                cur_qual = Quality.NONE
            if cur_qual & quality:
                allowed_qualities.append(cur_qual)
            if cur_qual << 16 & quality:
                prefferred_qualities.append(cur_qual)

        return sorted(allowed_qualities), sorted(prefferred_qualities)

    @staticmethod
    def nameQuality(name, anime=False):
        """
        Return The quality from an episode File renamed by SickRage
        If no quality is achieved it will try sceneQuality regex

        :param name: to parse
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
    def sceneQuality(name, anime=False):  # pylint: disable=too-many-branches
        """
        Return The quality from the scene episode File

        :param name: Episode filename to analyse
        :param anime: Boolean to indicate if the show we're resolving is Anime
        :return: Quality prefix
        """

        ret = Quality.UNKNOWN
        if not name:
            return ret

        name = ek(path.basename, name)

        check_name = lambda regex_list, func: func([re.search(regex, name, re.I) for regex in regex_list])

        if anime:
            dvd_options = check_name([r"dvd", r"dvdrip"], any)
            bluray_options = check_name([r"BD", r"blue?-?ray"], any)
            sd_options = check_name([r"360p", r"480p", r"848x480", r"XviD"], any)
            hd_options = check_name([r"720p", r"1280x720", r"960x720"], any)
            full_hd = check_name([r"1080p", r"1920x1080"], any)

            if sd_options and not bluray_options and not dvd_options:
                ret = Quality.SDTV
            elif dvd_options:
                ret = Quality.SDDVD
            elif hd_options and not bluray_options and not full_hd:
                ret = Quality.HDTV
            elif full_hd and not bluray_options and not hd_options:
                ret = Quality.FULLHDTV
            elif hd_options and not bluray_options and not full_hd:
                ret = Quality.HDWEBDL
            elif bluray_options and hd_options and not full_hd:
                ret = Quality.HDBLURAY
            elif bluray_options and full_hd and not hd_options:
                ret = Quality.FULLHDBLURAY

            return ret

        if check_name([r"480p|web.?dl|web(rip|mux|hd)|[sph]d.?tv|dsr|tv(rip|mux)|satrip", r"xvid|divx|[xh].?26[45]"], all) and not check_name([r"(720|1080)[pi]"], all) and not check_name([r"hr.ws.pdtv.[xh].?26[45]"], any):
            ret = Quality.SDTV
        elif check_name([r"dvd(rip|mux)|b[rd](rip|mux)|blue?-?ray", r"xvid|divx|[xh].?26[45]"], all) and not check_name([r"(720|1080)[pi]"], all) and not check_name([r"hr.ws.pdtv.[xh].?26[45]"], any):
            ret = Quality.SDDVD
        elif check_name([r"720p", r"hd.?tv", r"[xh].?26[45]"], all) or check_name([r"hr.ws.pdtv.[xh].?26[45]"], any) and not check_name([r"1080[pi]"], all):
            ret = Quality.HDTV
        elif check_name([r"720p|1080i", r"hd.?tv", r"mpeg-?2"], all) or check_name([r"1080[pi].hdtv", r"h.?26[45]"], all):
            ret = Quality.RAWHDTV
        elif check_name([r"1080p", r"hd.?tv", r"[xh].?26[45]"], all):
            ret = Quality.FULLHDTV
        elif check_name([r"720p", r"web.?dl|web(rip|mux|hd)"], all) or check_name([r"720p", r"itunes", r"[xh].?26[45]"], all):
            ret = Quality.HDWEBDL
        elif check_name([r"1080p", r"web.?dl|web(rip|mux|hd)"], all) or check_name([r"1080p", r"itunes", r"[xh].?26[45]"], all):
            ret = Quality.FULLHDWEBDL
        elif check_name([r"720p", r"blue?-?ray|hddvd|b[rd](rip|mux)", r"[xh].?26[45]"], all):
            ret = Quality.HDBLURAY
        elif check_name([r"1080p", r"blue?-?ray|hddvd|b[rd](rip|mux)", r"[xh].?26[45]"], all):
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
    def qualityFromFileMeta(filename):  # pylint: disable=too-many-branches
        """
        Get quality file file metadata

        :param filename: Filename to analyse
        :return: Quality prefix
        """

        log.use_print = False

        try:
            parser = createParser(filename)
        except Exception:  # pylint: disable=broad-except
            parser = None

        if not parser:
            return Quality.UNKNOWN

        try:
            metadata = extractMetadata(parser)
        except Exception:  # pylint: disable=broad-except
            metadata = None

        try:
            parser.stream._input.close()  # pylint: disable=protected-access
        except Exception:  # pylint: disable=broad-except
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

        base_filename = ek(path.basename, filename)
        bluray = re.search(r"blue?-?ray|hddvd|b[rd](rip|mux)", base_filename, re.I) is not None
        webdl = re.search(r"web.?dl|web(rip|mux|hd)", base_filename, re.I) is not None

        ret = Quality.UNKNOWN
        if height > 1000:
            ret = ((Quality.FULLHDTV, Quality.FULLHDBLURAY)[bluray], Quality.FULLHDWEBDL)[webdl]
        elif 680 < height < 800:
            ret = ((Quality.HDTV, Quality.HDBLURAY)[bluray], Quality.HDWEBDL)[webdl]
        elif height < 680:
            ret = (Quality.SDTV, Quality.SDDVD)[re.search(r'dvd|b[rd]rip|blue?-?ray', base_filename, re.I) is not None]

        return ret

    @staticmethod
    def compositeStatus(status, quality):
        if quality is None:
            quality = Quality.NONE
        return status + 100 * quality

    @staticmethod
    def qualityDownloaded(status):
        return (status - DOWNLOADED) / 100

    @staticmethod
    def splitCompositeStatus(status):
        """
        Split a composite status code into a status and quality.

        :param status: to split
        :returns: a tuple containing (status, quality)
        """
        status = long(status)
        if status == UNKNOWN:
            return UNKNOWN, Quality.UNKNOWN

        for q in sorted(Quality.qualityStrings.keys(), reverse=True):
            if status > q * 100:
                return status - q * 100, q

        return status, Quality.NONE

    @staticmethod
    def sceneQualityFromName(name, quality):  # pylint: disable=too-many-branches
        """
        Get scene naming parameters from filename and quality

        :param name: Filename to check
        :param quality: int of quality to make sure we get the right rip type
        :return: encoder type for scene quality naming
        """
        codec_list = ['xvid', 'divx']
        x264_list = ['x264', 'x 264', 'x.264']
        h264_list = ['h264', 'h 264', 'h.264', 'avc']
        x265_list = ['x265', 'x 265', 'x.265']
        h265_list = ['h265', 'h 265', 'h.265', 'hevc']
        codec_list += x264_list + h264_list + x265_list + h265_list

        found_codecs = {}
        found_codec = None

        for codec in codec_list:
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
            if codec_list[0] in found_codec:
                found_codec = 'XviD'
            elif codec_list[1] in found_codec:
                found_codec = 'DivX'
            elif found_codec in x264_list:
                found_codec = x264_list[0]
            elif found_codec in h264_list:
                found_codec = h264_list[0]
            elif found_codec in x265_list:
                found_codec = x265_list[0]
            elif found_codec in h265_list:
                found_codec = h265_list[0]

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

Quality.DOWNLOADED = [Quality.compositeStatus(DOWNLOADED, x) for x in Quality.qualityStrings]
Quality.SNATCHED = [Quality.compositeStatus(SNATCHED, x) for x in Quality.qualityStrings]
Quality.SNATCHED_PROPER = [Quality.compositeStatus(SNATCHED_PROPER, x) for x in Quality.qualityStrings]
Quality.FAILED = [Quality.compositeStatus(FAILED, x) for x in Quality.qualityStrings]
Quality.SNATCHED_BEST = [Quality.compositeStatus(SNATCHED_BEST, x) for x in Quality.qualityStrings]
Quality.ARCHIVED = [Quality.compositeStatus(ARCHIVED, x) for x in Quality.qualityStrings]

HD720p = Quality.combineQualities([Quality.HDTV, Quality.HDWEBDL, Quality.HDBLURAY], [])
HD1080p = Quality.combineQualities([Quality.FULLHDTV, Quality.FULLHDWEBDL, Quality.FULLHDBLURAY], [])

SD = Quality.combineQualities([Quality.SDTV, Quality.SDDVD], [])
HD = Quality.combineQualities([HD720p, HD1080p], [])
ANY = Quality.combineQualities([SD, HD], [])

# legacy template, cant remove due to reference in mainDB upgrade?
BEST = Quality.combineQualities([Quality.SDTV, Quality.HDTV, Quality.HDWEBDL], [Quality.HDTV])

qualityPresets = (SD, HD, HD720p, HD1080p, ANY)
qualityPresetStrings = NumDict({
    SD: "SD",
    HD: "HD",
    HD720p: "HD720p",
    HD1080p: "HD1080p",
    ANY: "Any"
})


class StatusStrings(NumDict):
    """
    Dictionary containing strings for status codes
    """
    # todo: Make views return Qualities too

    qualities = Quality.DOWNLOADED + Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST + Quality.ARCHIVED + Quality.FAILED

    def __missing__(self, key):
        """
        If the key is not found try to determine a status from Quality

        :param key: A numeric key or None
        :raise KeyError: if the key is invalid and can't be determined from Quality
        """
        key = self.numeric(key)  # try to convert the key to a number which will raise KeyError if it can't
        if key in self.qualities:  # the key wasn't found locally so check in qualities
            status, quality = Quality.splitCompositeStatus(key)
            return self[status] if not quality else self[status] + " (" + Quality.qualityStrings[quality] + ")"
        else:  # the key wasn't found in qualities either
            raise KeyError(key)  # ... so the key is invalid

    def __contains__(self, key):
        try:
            key = self.numeric(key)
            return key in self.data or key in self.qualities
        except KeyError:
            return False

# Assign strings to statuses
statusStrings = StatusStrings({
    UNKNOWN: "Unknown",
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


class Overview(object):  # pylint: disable=too-few-public-methods
    UNAIRED = UNAIRED  # 1
    SNATCHED = SNATCHED  # 2
    WANTED = WANTED  # 3
    GOOD = DOWNLOADED  # 4
    SKIPPED = SKIPPED  # 5
    SNATCHED_PROPER = SNATCHED_PROPER  # 9
    SNATCHED_BEST = SNATCHED_BEST  # 12

    # Should suffice!
    QUAL = 50

    overviewStrings = NumDict({
        SKIPPED: "skipped",
        WANTED: "wanted",
        QUAL: "qual",
        GOOD: "good",
        UNAIRED: "unaired",
        SNATCHED: "snatched",
        # we can give these a different class later, otherwise
        # breaks checkboxes in displayShow for showing different statuses
        SNATCHED_BEST: "snatched",
        SNATCHED_PROPER: "snatched"
    })

countryList = {
    'Australia': 'AU',
    'Canada': 'CA',
    'USA': 'US'
}
