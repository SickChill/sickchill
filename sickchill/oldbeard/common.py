import operator
import platform
import re
import uuid
from functools import reduce
from os import path

from sickchill import settings, version
from sickchill.helper import video_screen_size
from sickchill.init_helpers import setup_gettext
from sickchill.recompiled import tags
from sickchill.tagger.episode import EpisodeTags

from .numdict import NumDict

setup_gettext()

INSTANCE_ID = str(uuid.uuid1())
USER_AGENT = "SickChill/{version} ({os} {architecture} {os_version}; {instance})".format(
    version=version.__version__, os=platform.system(), architecture=platform.machine(), os_version=platform.release(), instance=INSTANCE_ID
)

cpu_presets = {"HIGH": 5, "NORMAL": 2, "LOW": 1}

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
NOTIFY_POSTPROCESS = 8

notifyStrings = NumDict(
    {
        NOTIFY_SNATCH: _("Started Download"),
        NOTIFY_DOWNLOAD: _("Finished Download"),
        NOTIFY_SUBTITLE_DOWNLOAD: _("Subtitle Download Finished"),
        NOTIFY_GIT_UPDATE: _("SickChill Updated"),
        NOTIFY_GIT_UPDATE_TEXT: _("SickChill Updated To Commit#: "),
        NOTIFY_LOGIN: _("SickChill new login"),
        NOTIFY_LOGIN_TEXT: _("New login from IP: {0}. http://geomaplookup.net/?ip={0}"),
        NOTIFY_POSTPROCESS: _("Finished Post Processing"),
    }
)

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

MULTI_EP_STRINGS = NumDict(
    {
        NAMING_REPEAT: _("Repeat"),
        NAMING_SEPARATED_REPEAT: _("Repeat (Separated)"),
        NAMING_DUPLICATE: _("Duplicate"),
        NAMING_EXTEND: _("Extend"),
        NAMING_LIMITED_EXTEND: _("Extend (Limited)"),
        NAMING_LIMITED_EXTEND_E_PREFIXED: _("Extend (Limited, E-prefixed)"),
    }
)


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
    UHD_4K_TV = 1 << 9  # 512 -- 2160p aka 4K UHD aka UHD-1
    UHD_4K_WEBDL = 1 << 10  # 1024
    UHD_4K_BLURAY = 1 << 11  # 2048
    UHD_8K_TV = 1 << 12  # 4096 -- 4320p aka 8K UHD aka UHD-2
    UHD_8K_WEBDL = 1 << 13  # 8192
    UHD_8K_BLURAY = 1 << 14  # 16384
    ANYHDTV = HDTV | FULLHDTV  # 20
    ANYWEBDL = HDWEBDL | FULLHDWEBDL  # 96
    ANYBLURAY = HDBLURAY | FULLHDBLURAY  # 384

    # put these bits at the other end of the spectrum, far enough out that they shouldn't interfere
    UNKNOWN = 1 << 15  # 32768

    qualityStrings = NumDict(
        {
            # None: "None",
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
            FULLHDBLURAY: "1080p BluRay",
            UHD_4K_TV: "4K UHD TV",
            UHD_8K_TV: "8K UHD TV",
            UHD_4K_WEBDL: "4K UHD WEB-DL",
            UHD_8K_WEBDL: "8K UHD WEB-DL",
            UHD_4K_BLURAY: "4K UHD BluRay",
            UHD_8K_BLURAY: "8K UHD BluRay",
        }
    )

    sceneQualityStrings = NumDict(
        {
            # None: "None",
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
            FULLHDBLURAY: "1080p BluRay",
            UHD_4K_TV: "4K UHD TV",
            UHD_8K_TV: "8K UHD TV",
            UHD_4K_WEBDL: "4K UHD WEB-DL",
            UHD_8K_WEBDL: "8K UHD WEB-DL",
            UHD_4K_BLURAY: "4K UHD BluRay",
            UHD_8K_BLURAY: "8K UHD BluRay",
        }
    )

    combinedQualityStrings = NumDict({ANYHDTV: "HDTV", ANYWEBDL: "WEB-DL", ANYBLURAY: "BluRay"})

    cssClassStrings = NumDict(
        {
            # None: "None",
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
            UHD_4K_TV: "UHD-4K",
            UHD_8K_TV: "UHD-8K",
            UHD_4K_WEBDL: "UHD-4K",
            UHD_8K_WEBDL: "UHD-8K",
            UHD_4K_BLURAY: "UHD-4K",
            UHD_8K_BLURAY: "UHD-8K",
            ANYHDTV: "any-hd",
            ANYWEBDL: "any-hd",
            ANYBLURAY: "any-hd",
        }
    )

    statusPrefixes = NumDict(
        {
            DOWNLOADED: _("Downloaded"),
            SNATCHED: _("Snatched"),
            SNATCHED_PROPER: _("Snatched (Proper)"),
            FAILED: _("Failed"),
            SNATCHED_BEST: _("Snatched (Best)"),
            ARCHIVED: _("Archived"),
        }
    )

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
                to_return[comp] = "{0} ({1})".format(stat, qual)
        return to_return

    @staticmethod
    def combineQualities(allowed_qualities, preferred_qualities):
        any_quality = 0
        best_quality = 0
        if allowed_qualities:
            any_quality = reduce(operator.or_, allowed_qualities)
        if preferred_qualities:
            best_quality = reduce(operator.or_, preferred_qualities)
        return any_quality | (best_quality << 16)

    @staticmethod
    def splitQuality(quality):
        if quality is None:
            quality = Quality.NONE
        allowed_qualities = []
        preferred_qualities = []
        for cur_qual in Quality.qualityStrings:
            if cur_qual is None:
                cur_qual = Quality.NONE
            if cur_qual & quality:
                allowed_qualities.append(cur_qual)
            if cur_qual << 16 & quality:
                preferred_qualities.append(cur_qual)

        return sorted(allowed_qualities), sorted(preferred_qualities)

    @staticmethod
    def nameQuality(name, anime=False):
        """
        Return The quality from an episode File renamed by SickChill
        If no quality is achieved it will try scene_quality regex

        :param name: to parse
        :param anime: Boolean to indicate if the show we're resolving is Anime
        :return: Quality prefix
        """

        # Try Scene names first
        quality = Quality.scene_quality(name, anime)
        if quality != Quality.UNKNOWN:
            return quality

        quality = Quality.qualityFromFileMeta(name)
        if quality != Quality.UNKNOWN:
            return quality

        if name.lower().endswith(".ts"):
            return Quality.RAWHDTV
        else:
            return Quality.UNKNOWN

    @staticmethod
    def scene_quality(name, anime=False):
        """
        Return The quality from the scene episode File

        :param name: Episode filename to analyse
        :param anime: Boolean to indicate if the show we're resolving is Anime
        :return: Quality
        """

        if not name:
            return Quality.UNKNOWN

        name = path.basename(name)

        result = None
        ep = EpisodeTags(name)

        if anime:
            sd_options = tags.anime_sd.search(name)
            hd_options = tags.anime_hd.search(name)
            full_hd = tags.anime_fullhd.search(name)
            ep.rex["bluray"] = tags.anime_bluray

            # BluRay
            if ep.bluray and (full_hd or hd_options):
                result = Quality.FULLHDBLURAY if full_hd else Quality.HDBLURAY
            # HD TV
            elif not ep.bluray and (full_hd or hd_options):
                result = Quality.FULLHDTV if full_hd else Quality.HDTV
            # SD DVD
            elif ep.dvd:
                result = Quality.SDDVD
            # SD TV
            elif sd_options:
                result = Quality.SDTV
        elif ep.hevc and not settings.QUALITY_ALLOW_HEVC:
            result = Quality.UNKNOWN
        elif ep.mpeg:
            result = Quality.RAWHDTV
        # Is it UHD?
        elif ep.vres in {2160, 4320} and ep.scan == "p":
            # BluRay
            full_res = ep.vres == 4320
            if ep.bluray:
                result = (Quality.UHD_4K_BLURAY, Quality.UHD_8K_BLURAY)[full_res]
            # WEB-DL
            elif ep.itunes or ep.amazon or ep.netflix or ep.web:
                result = (Quality.UHD_4K_WEBDL, Quality.UHD_8K_WEBDL)[full_res]
            # HDTV
            elif ep.tv == "hd" or ep.trueHD:
                result = (Quality.UHD_4K_TV, Quality.UHD_8K_TV)[full_res]
        elif ep.vres in {1080, 720}:
            if ep.scan == "p":
                # BluRay
                full_res = ep.vres == 1080
                if ep.bluray or ep.hddvd:
                    result = (Quality.HDBLURAY, Quality.FULLHDBLURAY)[full_res]
                # WEB-DL
                elif ep.itunes or ep.amazon or ep.netflix or ep.web:
                    result = (Quality.HDWEBDL, Quality.FULLHDWEBDL)[full_res]
                # HDTV
                elif ep.tv == "hd" or ep.hevc or ep.trueHD:
                    result = (Quality.HDTV, Quality.FULLHDTV)[full_res]  # 1080 HDTV h264
                # MPEG2 encoded
                elif all([full_res, ep.tv == "hd", ep.mpeg]):
                    result = Quality.RAWHDTV
                elif all([not full_res, ep.tv == "hd", ep.mpeg]):
                    result = Quality.RAWHDTV
            elif (ep.res == "1080i") and ep.tv == "hd" and (ep.mpeg or (ep.raw and ep.avc_non_free)):
                result = Quality.RAWHDTV
        elif not ep.vres and ep.netflix or ep.amazon or ep.itunes:
            result = Quality.HDWEBDL
        elif ep.hrws:
            result = Quality.HDTV

        # Is it SD?
        elif ep.xvid or ep.avc:
            # SD DVD
            if ep.dvd or ep.bluray:
                result = Quality.SDDVD
            # SDTV
            elif ep.res == "480p" or any([ep.tv, ep.sat, ep.web]):
                result = Quality.SDTV
        elif ep.dvd:
            # SD DVD
            result = Quality.SDDVD
        elif ep.tv:
            # SD TV/HD TV
            result = (Quality.SDTV, Quality.HDTV)[ep.tv == "hd"]
        elif ep.raw or ep.mpeg:
            # RawHD
            result = Quality.RAWHDTV

        return Quality.UNKNOWN if result is None else result

    @staticmethod
    def qualityFromFileMeta(filename):
        """
        Get quality file file metadata

        :param filename: Filename to analyse
        :return: Quality prefix
        """

        height = video_screen_size(filename)[1]
        if not height:
            return Quality.UNKNOWN

        base_filename = path.basename(filename)
        bluray = re.search(r"blue?-?ray|hddvd|b[rd](rip|mux)", base_filename, re.I) is not None
        webdl = re.search(r"web.?dl|web(rip|mux|hd)", base_filename, re.I) is not None

        ret = Quality.UNKNOWN
        if 3240 < height:
            ret = ((Quality.UHD_8K_TV, Quality.UHD_8K_BLURAY)[bluray], Quality.UHD_8K_WEBDL)[webdl]
        if 1620 < height <= 3240:
            ret = ((Quality.UHD_4K_TV, Quality.UHD_4K_BLURAY)[bluray], Quality.UHD_4K_WEBDL)[webdl]
        elif 800 < height <= 1620:
            ret = ((Quality.FULLHDTV, Quality.FULLHDBLURAY)[bluray], Quality.FULLHDWEBDL)[webdl]
        elif 680 < height <= 800:
            ret = ((Quality.HDTV, Quality.HDBLURAY)[bluray], Quality.HDWEBDL)[webdl]
        elif height <= 680:
            ret = (Quality.SDTV, Quality.SDDVD)[re.search(r"dvd|b[rd]rip|blue?-?ray", base_filename, re.I) is not None]

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
        status = int(status)
        if status == UNKNOWN:
            return UNKNOWN, Quality.UNKNOWN

        for q in sorted(Quality.qualityStrings, reverse=True):
            if status > q * 100:
                return status - q * 100, q

        return status, Quality.NONE

    @staticmethod
    def sceneQualityFromName(name, quality):
        """
        Get scene naming parameters from filename and quality

        :param name: Filename to check
        :param quality: int of quality to make sure we get the right rip type
        :return: encoder type for scene quality naming
        """
        codec_list = ["xvid", "divx"]
        x264_list = ["x264", "x 264", "x.264"]
        h264_list = ["h264", "h 264", "h.264", "avc"]
        x265_list = ["x265", "x 265", "x.265"]
        h265_list = ["h265", "h 265", "h.265", "hevc"]
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
                found_codec = "XviD"
            elif codec_list[1] in found_codec:
                found_codec = "DivX"
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
    def statusFromName(name, anime=False):
        """
        Get a status object from filename

        :param name: Filename to check
        :param anime: boolean to enable anime parsing
        :return: Composite status/quality object
        """
        return Quality.compositeStatus(DOWNLOADED, Quality.nameQuality(name, anime))

    DOWNLOADED = None
    SNATCHED = None
    SNATCHED_PROPER = None
    FAILED = None
    SNATCHED_BEST = None
    ARCHIVED = None


Quality.DOWNLOADED = [Quality.compositeStatus(DOWNLOADED, x) for x in Quality.qualityStrings if x is not None]
Quality.SNATCHED = [Quality.compositeStatus(SNATCHED, x) for x in Quality.qualityStrings if x is not None]
Quality.SNATCHED_BEST = [Quality.compositeStatus(SNATCHED_BEST, x) for x in Quality.qualityStrings if x is not None]
Quality.SNATCHED_PROPER = [Quality.compositeStatus(SNATCHED_PROPER, x) for x in Quality.qualityStrings if x is not None]
Quality.FAILED = [Quality.compositeStatus(FAILED, x) for x in Quality.qualityStrings if x is not None]
Quality.ARCHIVED = [Quality.compositeStatus(ARCHIVED, x) for x in Quality.qualityStrings if x is not None]

Quality.DOWNLOADED.sort()
Quality.SNATCHED.sort()
Quality.SNATCHED_BEST.sort()
Quality.SNATCHED_PROPER.sort()
Quality.FAILED.sort()
Quality.ARCHIVED.sort()

HD720p = Quality.combineQualities([Quality.HDTV, Quality.HDWEBDL, Quality.HDBLURAY], [])
HD1080p = Quality.combineQualities([Quality.FULLHDTV, Quality.FULLHDWEBDL, Quality.FULLHDBLURAY], [])
UHD_4K = Quality.combineQualities([Quality.UHD_4K_TV, Quality.UHD_4K_WEBDL, Quality.UHD_4K_BLURAY], [])
UHD_8K = Quality.combineQualities([Quality.UHD_8K_TV, Quality.UHD_8K_WEBDL, Quality.UHD_8K_BLURAY], [])

SD = Quality.combineQualities([Quality.SDTV, Quality.SDDVD], [])
HD = Quality.combineQualities([HD720p, HD1080p], [])
UHD = Quality.combineQualities([UHD_4K, UHD_8K], [])
ANY = Quality.combineQualities([SD, HD, UHD], [])

# legacy template, cant remove due to reference in mainDB upgrade?
BEST = Quality.combineQualities([Quality.SDTV, Quality.HDTV, Quality.HDWEBDL], [Quality.HDTV])

qualityPresets = (
    ANY,
    SD,
    HD,
    HD720p,
    HD1080p,
    UHD,
    UHD_4K,
    UHD_8K,
)

qualityPresetStrings = NumDict(
    {
        SD: "SD",
        HD: "HD",
        HD720p: "HD720p",
        HD1080p: "HD1080p",
        UHD: "UHD",
        UHD_4K: "UHD-4K",
        UHD_8K: "UHD-8K",
        ANY: "Any",
    }
)


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
statusStrings_bare = StatusStrings(
    {
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
        SNATCHED_BEST: "Snatched (Best)",
    }
)

statusStrings = StatusStrings({key: _(value) for key, value in statusStrings_bare.items()})

cssStatusStrings = NumDict(
    {
        DOWNLOADED: "downloaded",
        SNATCHED: "snatched",
        SNATCHED_PROPER: "snatched-proper",
        FAILED: "failed",
        SNATCHED_BEST: "snatched-best",
        ARCHIVED: "archived",
        WANTED: "wanted",
    }
)


class Overview(object):
    UNAIRED = UNAIRED  # 1
    SNATCHED = SNATCHED  # 2
    WANTED = WANTED  # 3
    GOOD = DOWNLOADED  # 4
    SKIPPED = SKIPPED  # 5
    SNATCHED_PROPER = SNATCHED_PROPER  # 9
    SNATCHED_BEST = SNATCHED_BEST  # 12

    # Should suffice!
    QUAL = 50

    overviewStrings = NumDict(
        {
            SKIPPED: "skipped",
            WANTED: "wanted",
            QUAL: "qual",
            GOOD: "good",
            UNAIRED: "unaired",
            SNATCHED: "snatched",
            # we can give these a different class later, otherwise
            # breaks checkboxes in displayShow for showing different statuses
            SNATCHED_BEST: "snatched",
            SNATCHED_PROPER: "snatched",
        }
    )


countryList = {"Australia": "AU", "Canada": "CA", "USA": "US"}
