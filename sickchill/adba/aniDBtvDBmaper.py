from pathlib import Path

from . import aniDBfileInfo as fileInfo


class TvDBMap(object):
    def __init__(self, cache_dir: Path):
        self.xmlMap = fileInfo.read_tvdb_map_xml(cache_dir)

    def get_tvdb_for_anidb(self, anidb_id):
        return self._get_x_for_y(anidb_id, "anidbid", "tvdbid")

    def get_anidb_for_tvdb(self, tvdb_id):
        return self._get_x_for_y(tvdb_id, "tvdbid", "anidbid")

    def _get_x_for_y(self, xValue, x, y):
        # print("searching "+x+" with the value "+str(xValue)+" and want to give back "+y)
        xValue = str(xValue)
        for anime in self.xmlMap.findall("anime"):
            try:
                if anime.get(x, False) == xValue:
                    return int(anime.get(y, 0))
            except ValueError as error:
                continue
        return 0

    def get_season_episode_for_anidb_absolute_number(self, anidb_id, absoluteNumber):
        # NOTE: this cant be done without the length of each season from thetvdb
        # TODO: implement
        season = 0
        episode = 0

        for anime in self.xmlMap.findall("anime"):
            if int(anime.get("anidbid", False)) == anidb_id:
                defaultSeason = int(anime.get("defaulttvdbseason", 1))

        return season, episode

    @staticmethod
    def get_season_episode_for_tvdb_absoluteNumber(anidb_id, absoluteNumber):
        # TODO: implement
        season = 0
        episode = 0
        return season, episode
