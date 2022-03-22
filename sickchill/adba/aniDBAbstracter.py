import re
import string
from pathlib import Path

from . import aniDBfileInfo as fileInfo
from .aniDBerrors import AniDBIncorrectParameterError
from .aniDBfileInfo import read_anidb_xml
from .aniDBmapper import AniDBMapper
from .aniDBtvDBmaper import TvDBMap


class AniDBabstractObject(object):
    def __init__(self, aniDB, load=False):
        self.laoded = False
        self.aniDB = None
        self.rawData = None
        self.log = self._fake_log

        self.set_connection(aniDB)
        if load:
            self.load_data()

    def set_connection(self, anidb):
        self.aniDB = anidb
        if self.aniDB:
            self.log = self.aniDB.log
        else:
            self.log = self._fake_log

    def _fake_log(self, x=None):
        pass

    def _fill(self, dataline):
        for key in dataline:
            try:
                tmp_list = dataline[key].split("'")
                if len(tmp_list) > 1:
                    new_list = []
                    for i in tmp_list:
                        try:
                            new_list.append(int(i))
                        except Exception:
                            new_list.append(i)
                    self.__dict__[key] = new_list
                    continue
            except Exception:
                pass
            try:
                self.__dict__[key] = int(dataline[key])
            except Exception:
                self.__dict__[key] = dataline[key]
            key = property(lambda x: dataline[key])

    def __getattr__(self, name):
        try:
            return object.__getattribute__(self, name)
        except Exception:
            return None

    def _build_names(self):
        names = []
        names = self._easy_extend(names, self.english_name)
        names = self._easy_extend(names, self.short_name_list)
        names = self._easy_extend(names, self.synonym_list)
        names = self._easy_extend(names, self.other_name)

        self.allNames = names

    @staticmethod
    def _easy_extend(initialList, item):
        if item:
            if isinstance(item, list):
                initialList.extend(item)
            elif isinstance(item, str):
                initialList.append(item)

        return initialList

    def load_data(self):
        return False

    def add_notification(self):
        """
        type - Type of notification: type=>  0=all, 1=new, 2=group, 3=complete
        priority - low = 0, medium = 1, high = 2 (unconfirmed)

        """
        if self.aid:
            self.aniDB.notifyadd(aid=self.aid, type=1, priority=1)

    def del_notification(self):
        """
        type - Type of notification: type=>  0=all, 1=new, 2=group, 3=complete
        priority - low = 0, medium = 1, high = 2 (unconfirmed)

        """
        if self.aid:
            self.aniDB.notifydel(aid=self.aid, type=1, priority=1)


class Anime(AniDBabstractObject):
    def __init__(self, aniDB, cache_dir: Path, name=None, aid=None, tvdbid=None, paramsA=None, autoCorrectName=False, load=False):
        if not cache_dir.is_dir():
            raise
        self.cache_dir = cache_dir / "anime"
        self.cache_dir = self.cache_dir.absolute()

        if not self.cache_dir.is_dir():
            self.cache_dir.mkdir()

        self.mapper = AniDBMapper()

        self.tvDBMap = TvDBMap(cache_dir=self.cache_dir)
        self.allAnimeXML = None

        self.name = name
        self.aid = aid
        self.tvdb_id = tvdbid
        self.release_groups = []

        if self.tvdb_id and not self.aid:
            self.aid = self.tvDBMap.get_anidb_for_tvdb(self.tvdb_id)

        if not (self.name or self.aid):
            raise AniDBIncorrectParameterError("No aid or name available")

        if not self.aid:
            self.aid = self._get_aid_from_xml(self.name)
        if not self.name or autoCorrectName:
            self.name = self._get_name_from_xml(self.aid)

        if not (self.name or self.aid):
            raise ValueError

        if not self.tvdb_id:
            self.tvdb_id = self.tvDBMap.get_tvdb_for_anidb(self.aid)

        if not paramsA:
            self.bitCode = "b2f0e0fc000000"
            self.params = self.mapper.getAnimeCodesA(self.bitCode)
        else:
            self.paramsA = paramsA
            self.bitCode = self.mapper.getAnimeBitsA(self.paramsA)

        super().__init__(aniDB, load)

    def load_data(self):
        """load the data from anidb"""

        if not (self.name or self.aid):
            raise ValueError

        self.rawData = self.aniDB.anime(aid=self.aid, aname=self.name, amask=self.bitCode)
        if self.rawData.datalines:
            self._fill(self.rawData.datalines[0])
            self._builPreSequal()
            self.laoded = True

    def get_groups(self):
        if not self.aid:
            return []
        self.rawData = self.aniDB.groupstatus(aid=self.aid)
        for line in self.rawData.datalines:
            self.release_groups.append({"name": line["name"], "rating": line["rating"], "range": line["episode_range"]})
        return sorted(self.release_groups, key=lambda x: x["name"].lower())

    # TODO: refactor and use the new functions in anidbFileinfo
    def _get_aid_from_xml(self, name):
        if not self.allAnimeXML:
            self.allAnimeXML = read_anidb_xml(self.cache_dir)

        regex = re.compile(rf"( \(\d{4}\))|[{re.escape(string.punctuation)}]")  # remove any punctuation and e.g. ' (2011)'
        # regex = re.compile('[%s]'  % re.escape(string.punctuation)) # remove any punctuation and e.g. ' (2011)'
        name = regex.sub("", name.lower())
        lastAid = 0
        for element in self.allAnimeXML.iter():
            if element.get("aid", False):
                lastAid = int(element.get("aid"))
            if element.text:
                testname = regex.sub("", element.text.lower())

                if testname == name:
                    return lastAid
        return 0

    # TODO: refactor and use the new functions in anidbFileinfo
    def _get_name_from_xml(self, aid, onlyMain=True):
        if not self.allAnimeXML:
            self.allAnimeXML = read_anidb_xml(self.cache_dir)

        for anime in self.allAnimeXML.findall("anime"):
            if int(anime.get("aid", False)) == aid:
                for title in anime.iter():
                    currentLang = title.get("{http://www.w3.org/XML/1998/namespace}lang", False)
                    currentType = title.get("type", False)
                    if (currentLang == "en" and not onlyMain) or currentType == "main":
                        return title.text
        return ""

    def _builPreSequal(self):
        if self.related_aid_list and self.related_aid_type:
            try:
                for i in range(len(self.related_aid_list)):
                    if self.related_aid_type[i] == 2:
                        self.__dict__["prequal"] = self.related_aid_list[i]
                    elif self.related_aid_type[i] == 1:
                        self.__dict__["sequal"] = self.related_aid_list[i]
            except Exception:
                if self.related_aid_type == 2:
                    self.__dict__["prequal"] = self.related_aid_list
                elif self.str_related_aid_type == 1:
                    self.__dict__["sequal"] = self.related_aid_list


class Episode(AniDBabstractObject):
    def __init__(self, aniDB, number=None, epid=None, file_path: Path = None, fid=None, epno=None, paramsA=None, paramsF=None, load=False, calculate=False):
        self.mapper = AniDBMapper()
        self.epid = epid
        self.file_path = file_path
        self.fid = fid
        self.epno = epno

        if calculate:
            self.ed2k, self.size = self._calculate_file_stuff

        if not paramsA:
            self.bitCodeA = "C000F0C0"
            self.paramsA = self.mapper.getFileCodesA(self.bitCodeA)
        else:
            self.paramsA = paramsA
            self.bitCodeA = self.mapper.getFileBitsA(self.paramsA)

        if not paramsF:
            self.bitCodeF = "7FF8FEF8"
            self.paramsF = self.mapper.getFileCodesF(self.bitCodeF)
        else:
            self.paramsF = paramsF
            self.bitCodeF = self.mapper.getFileBitsF(self.paramsF)

        super().__init__(aniDB, load)

    def load_data(self):
        """load the data from anidb"""
        self.ed2k, self.size = self._calculate_file_stuff

        self.rawData = self.aniDB.file(
            fid=self.fid,
            size=self.size,
            ed2k=self.ed2k,
            aid=self.aid,
            aname=None,
            gid=None,
            gname=None,
            epno=self.epno,
            fmask=self.bitCodeF,
            amask=self.bitCodeA,
        )
        self._fill(self.rawData.datalines[0])
        self._build_names()
        self.laoded = True

    def add_to_mylist(self, status=None):
        """
        status:
        0    unknown    - state is unknown or the user doesn't want to provide this information (default)
        1    on hdd    - the file is stored on hdd
        2    on cd    - the file is stored on cd
        3    deleted    - the file has been deleted or is not available for other reasons (i.e. reencoded)

        """
        self.ed2k, self.size = self._calculate_file_stuff

        try:
            self.aniDB.mylistadd(size=self.size, ed2k=self.ed2k, state=status)
        except Exception as e:
            self.log("exception msg: " + str(e))
        else:
            # TODO: add the name or something
            self.log("Added the episode to anidb")

    @property
    def _calculate_file_stuff(self):
        if not (self.file_path and self.file_path.is_file()):
            return None, None

        if self.ed2k and self.size:
            return self.ed2k, self.size

        self.log("Calculating the ed2k. Please wait...")
        ed2k = fileInfo.get_file_hash(self.file_path)
        size = self.file_path.stat().st_size
        return ed2k, size
