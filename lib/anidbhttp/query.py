# coding: utf-8
# TODO parse characters
import xml.etree.ElementTree as ET
import requests
try:
    import StringIO
except ImportError:
    import io as StringIO
import datetime

from . import model, cache, exceptions

__all__ = ["set_client", "search", "query", "QUERY_ANIME", "QUERY_CATEGORIES",
            "QUERY_RANDOMRECOMMENDATION", "QUERY_HOT"]

SEARCH_URL = "http://anisearch.outrance.pl?task=search&query=%s"
ANIDB_URL = \
"http://api.anidb.net:9001/httpapi?client=%s&clientver=%i&protover=1&request=%s"

#: Query type used for retrieving information about an anime
QUERY_ANIME = 1

#: Query type used to retrieve the list of categories
QUERY_CATEGORIES = 2

#: Query type to retrieve a random recommendation
QUERY_RANDOMRECOMMENDATION = 3

#: Query type for hot anime
QUERY_HOT = 4

class AnidbQuery(object):
    def __init__(self, name, version):
        """
        Set the `client` and `clientversion` parameters used in the HTTP request to
        the AniDB.
        """
        self.CLIENT = name
        self.CLIENTVERSION = version

    def set_client(self, name, version):
        """
        Set the `client` and `clientversion` parameters used in the HTTP request to
        the AniDB.
        """
        self.CLIENT = name
        self.CLIENTVERSION = version
    
    def search(self, title, exact=False):
        """
        Search for an anime.
    
        :param title: The anime to search for
        :param exact: Boolean. Whether or not to only return exact matches
        :rtype: List of :class:`anidb.model.Anime`
        """
        if exact:
            title = "\\" + title
        result = requests.get(SEARCH_URL % title)
        return self._handle_response(result)
    
    def query(self, type=QUERY_ANIME, aid=None, **kwargs):
        """
        Query AniDB for information about the anime identified by *aid* or the
        complete list of categories.
    
        :param type: One of QUERY_CATEGORIES, QUERY_ANIME, QUERY_RANDOMRECOMMENDATION, QUERY_HOT
        :param aid: If *type* is QUERY_ANIME, the aid of the anime
        :param kwargs: Any kwargs you want to pass to :func:`requests.get`
        :raises: ValueError if `anidb.CLIENT` or `anidb.CLIENTVERSION` are not set
        :rtype: :class:`anidb.model.Anime` or a list of
                :class:`anidb.model.Category`
        """
        if self.CLIENT is None or self.CLIENTVERSION is None:
            raise ValueError(
                    "You need to assign values to both CLIENT and CLIENTVERSION")
        if type == QUERY_ANIME:
            if aid is None:
                raise TypeError("aid can't be None")
            else:
                cacheresult = cache.get(aid)
                if cacheresult is not None:
                    return cacheresult
    
                response = self._get("anime", params={"aid": aid}, **kwargs)
                result = self._handle_response(response)
                cache.save(aid, result)
                return result
        else:
            response = None
            if type == QUERY_CATEGORIES:
                response = self._get("categorylist", **kwargs)
            elif type == QUERY_RANDOMRECOMMENDATION:
                response = self._get("randomrecommendtion", **kwargs)
            elif type == QUERY_HOT:
                response = self._get("hotanime", **kwargs)
            else:
                raise ValueError("unknown query type")
            return self._handle_response(response)
    
    def _get(self, request, **kwargs):
        return requests.get(ANIDB_URL % (self.CLIENT, self.CLIENTVERSION, request), **kwargs)
    
    def _handle_response(self, response):
        if response.content == "<error>Banned</error>":
            raise exceptions.BannedException()
        
        if response.content == "<error>Client Values Missing or Invalid</error>":
            raise exceptions.ClientMissingException()
        # TODO raise an exception or something
        if response.status_code != 200:
            return None
        # TODO xml: is only used in lang, drop it
        t =  response.content.replace("xml:", "")
        tree = ET.ElementTree(file=StringIO.StringIO(t))
        return self.parse(tree.getroot())
    
    def parse(self, tree):
        """
        Parse all the elements in an :class:`xml.etree.ElementTree.Element`
        """
        if tree.tag in ("animetitles", "randomrecommendation", "hotanime"):
            return self.parse_list(tree)
        elif tree.tag in "anime":
            return self.parse_element(tree)
        elif tree.tag == "recommendation":
            return self.parse_anime(tree[0])
        # TODO categorylist
    
    def parse_list(self, tree):
        result = []
        for elem in tree:
            t = self.parse(elem)
            result.append(t)
        return result
    
    def parse_element(self, elem):
        """docstring for parse_element"""
        if elem.tag == "anime":
            return self.parse_anime(elem)
        elif elem.tag == "categorylist":
            return self.parse(elem)
        elif elem.tag == "category":
            return self.parse_category(elem)
    
    def parse_anime(self, anime):
        """
        Parses an anime Element
    
        :param anime: An anime :class:`xml.etree.ElementTree.Element`
        :rtype: :class:`anidb.model.Anime`
        """
        # Anisearch has "aid" attributes ... 
        if "aid" in anime.attrib:
            result = model.Anime(anime.attrib["aid"])
        # ... anidb has just "id"
        else:
            result = model.Anime(anime.attrib["id"])
        result.set_tvdbid()
        for elem in anime:
            # AniDB returns an element "titles" with lots of "title" subelements
            if elem.tag == "titles":
                for t_elem in elem:
                    t = self.parse_title(t_elem)
                    result.add_title(t)
            # AniSearch has "title" subelements on "anime"
            elif elem.tag == "title":
                t = self.parse_title(elem)
                result.add_title(t)
            elif elem.tag in ("type", "episodecount", "startdate", "enddate"):
                setattr(result, elem.tag, elem.text)
            elif elem.tag == "episodecount":
                result.episodecount = elem.text
            elif elem.tag == "ratings":
                for r in elem:
                    if r.tag in ("permanent", "temporary", "review"):
                        result.set_rating(r.tag, r.attrib["count"], float(r.text))
            elif elem.tag == "categories":
                for c in self.parse_categorylist(elem):
                    result.add_category(c)
            elif elem.tag == "episodes":
                for e in elem:
                    result.add_episode(self.parse_episode(e))
            elif elem.tag == "tags":
                for tag in self.parse_tags(elem):
                    result.add_tag(tag)
            elif elem.tag == "picture":
                result.set_picture(elem.text)
        return result
    
    def parse_categorylist(self, categorylist):
        for c in categorylist:
            yield self.parse_category(c)
    
    def parse_category(self, category):
        """
        Parse a category element
    
        :param category: A category :class:`xml.etree.ElementTree.Element`
        :rtype: :class:`anidb.model.Category`
        """
        result = model.Category(category.attrib["id"])
        for elem in category:
            setattr(result, elem.tag, elem.text)
        if category.attrib["hentai"] == "true":
            result.hentai = True
        result.weight = category.attrib["weight"]
        if "parentid" in category.attrib:
            result.parentid = category.attrib["parentid"]
        return result
    
    def parse_episode(self, episode):
        ep = model.Episode(episode.attrib["id"])
        for elem in episode:
            if elem.tag in ("length", "epno"):
                setattr(ep, elem.tag, elem.text)
            elif elem.tag == "airdate":
                y, m, d = elem.text.split("-")
                ep.airdate = datetime.datetime(int(y), int(m), int(d))
            elif elem.tag == "rating":
                ep.set_rating(elem.attrib["votes"], elem.text)
            elif elem.tag == "title":
                t = self.parse_title(elem)
                ep.add_title(t)
        return ep
    
    def parse_title(self, elem):
        """
        Parse a <title> element
    
        :rtype: :class:`anidb.model.Title`
        """
        t = model.Title(lang = elem.attrib["lang"],
                  title = elem.text)
        if "type" in elem.attrib:
            t.type = elem.attrib["type"]
        if "exact" in elem.attrib:
            t.exact = True
        return t
    
    def parse_tags(self, elem):
        for t in elem:
            yield self.parse_tag(t)
    
    def parse_tag(self, elem):
        t = model.Tag(elem.attrib["id"])
        t.approval = elem.attrib["approval"]
        if elem.attrib["spoiler"].lower() == "true":
            t.spoiler = True
        for e in elem:
            setattr(t, e.tag, e.text)
        return t
