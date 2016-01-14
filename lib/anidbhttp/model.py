import re
import os
from sickrage.helper.encoding import ek
import sickbeard
from sickbeard import helpers
import requests
from sickbeard.helpers import anon_url

__all__ = ["Anime", "Category", "Title", "Episode", "Tag"]

class Entity(object):
    def __init__(self, id):
        self._id = int(id)
        self.session = requests.Session()

    @property
    def id(self):
        """The id of this entity"""
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

class Titled(object):
    """
    Base class for all classes with a `titles` attribute
    """
    def __init__(self):
        self.titles = {}

    def add_title(self, title):
        """
        Add a new title to this entity

        :param title: The title to add
        """
        assert title.lang is not None
        assert title.title is not None
        if title.lang in self.titles:
            self.titles[title.lang].append(title)
        else:
            self.titles[title.lang] = [title]

class Typed(object):
    """
    Base class for all classes with a `type` attribute
    """
    def __init__(self):
        self._type = None

    @property
    def type(self):
        """The type property"""
        return self._type

    @type.setter
    def type(self, value):
        self._type = value

class Named(object):
    """
    Base class for all classes with a `name` attribute
    """
    def __init__(self):
        self.name = None

    @property
    def name(self):
        """The name property"""
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

class Described(object):
    """
    Base class for all classes with a `description` attribute
    """
    def __init__(self):
        self._description = None

    @property
    def description(self):
        """The description property"""
        return self._description

    @description.setter
    def description(self, value):
        self._description = value

class Anime(Entity, Titled, Typed, Described):
    """
    An anime. Identified by an `aid`
    """
    def __init__(self, aid):
        Entity.__init__(self, aid)
        Titled.__init__(self)
        Typed.__init__(self)
        Described.__init__(self)
        self._type = None
        self._tvdbid = None
        self._episodecount = None
        self._episodes = {}
        self._startdate = None
        self._enddate = None
        self._categories = []
        self._tags = []
        self._picture = None
        self._image_path = None
        self._url = "https://anidb.net/perl-bin/animedb.pl?show=anime&aid={0}".format(self.id)
        self._ratings = {
                    "permanent":
                    { "count": None, "rating": None},
                    "temporary":
                    { "count": None, "rating": None},
                    "review":
                    { "count": None, "rating": None}
                }


    def add_category(self, category):
        """
        Add a new category to this anime

        :param category: The category to add
        """
        if not isinstance(category, Category):
            raise TypeError("Category expected")
        else:
            self._categories.append(category)

    def add_episode(self, episode):
        """
        Adds an episode to this anime

        :param episode: :class:`anidb.model.Episode`
        """
        if isinstance(episode, Episode):
            self._episodes[episode.epno] = Episode
        else:
            raise TypeError("Episode expected")

    def set_rating(self, which, count, rating):
        """
        Set the rating of this anime

        :param which: Which rating. Either `temporary`, `permanent` or
                      `reviews`
        :param count: The number of votes
        :param rating: The rating
        """
        if which in self._ratings.keys():
            self._ratings[which]["count"] = float(count)
            self._ratings[which]["rating"] = rating
        else:
            raise ValueError("Unknown kind of rating")

    def add_tag(self, tag):
        """
        Adds a tag to this anime

        :param tag: A :class:`anidb.model.Tag`
        """
        self._tags.append(tag)
    
    def set_picture(self, picture):
        """
        Set the cover picture of this anime

        :param picture: the image filename
        """
        self._picture = picture
        self.cache_image("http://img7.anidb.net/pics/anime/{0}".format(picture))
        self._image_path = ek(os.path.join, 'images', 'anidb', ek(os.path.basename, self._picture))
    
    def set_tvdbid(self):
        """
        Tries to get the thtvdb id from the anime-list.xml
        Requires the adba package for this functionality

        No params required.
        """
        from adba.aniDBtvDBmaper import TvDBMap
        self._tvdbid = TvDBMap().get_tvdb_for_anidb(self.id) if self.id else None
        
    def cache_image(self, image_url):
        """
        Store cache of image in cache dir
        :param image_url: Source URL
        """
        path = ek(os.path.abspath, ek(os.path.join, sickbeard.CACHE_DIR, 'images', 'anidb'))

        if not ek(os.path.exists, path):
            ek(os.makedirs, path)

        full_path = ek(os.path.join, path, ek(os.path.basename, image_url))

        if not ek(os.path.isfile, full_path):
            helpers.download_file(image_url, full_path, session=self.session)
        
    @property
    def episodecount(self):
        """The episodecount property"""
        return self._episodecount

    @episodecount.setter
    def episodecount(self, value):
        self._episodecount = int(value)

    @property
    def startdate(self):
        """The startdate property"""
        return self._startdate

    @startdate.setter
    def startdate(self, value):
        self._startdate = value

    @property
    def enddate(self):
        """The enddate property"""
        return self._enddate

    @enddate.setter
    def enddate(self, value):
        self._enddate = value

    @property
    def ratings(self):
        """The ratings property"""
        return self._ratings

    @property
    def episodes(self):
        """The episodes property"""
        return self._episodes

    @property
    def categories(self):
        """The categories property"""
        return self._categories

    @property
    def tags(self):
        """The tags property"""
        return self._tags
    
    @property
    def picture(self):
        """The Picture property"""
        return self._picture
    
    @property
    def image_path(self):
        """The image_path property"""
        return self._image_path
    
    @property
    def url(self):
        """The url property"""
        return self._url
    
    @property
    def tvdbid(self):
        """The tvdbid mapped property"""
        return self._tvdbid

class Episode(Entity, Titled):
    """
    An episode. Identified by an `id`
    """
    def __init__(self, id):
        Entity.__init__(self, id)
        Titled.__init__(self)
        self._length = None
        self._airdate = None
        self._epno = None
        self._rating = None

    def set_rating(self, votes, rating):
        self._rating = (int(votes), float(rating))


    @property
    def epno(self):
        """The epno property"""
        return self._epno

    @epno.setter
    def epno(self, value):
        self._epno = value

    @property
    def airdate(self):
        """The airdate property"""
        return self._airdate

    @airdate.setter
    def airdate(self, value):
        self._airdate = value

    @property
    def length(self):
        """The length property"""
        return self._length

    @length.setter
    def length(self, value):
        self._length = value

class Category(Entity, Named, Described):
    """
    An AniDB category
    """
    def __init__(self, id):
        Entity.__init__(self, id)
        Named.__init__(self)
        Described.__init__(self)
        self._hentai = False
        self._weight = 0
        self._name = None
        self._description = None
        self._parentid = None

    @property
    def hentai(self):
        """
        Whether or not this category contains hentai material

        :rtype: Boolean
        """
        return self._hentai

    @hentai.setter
    def hentai(self, value):
        self._hentai = value

    @property
    def weight(self):
        return self._weight

    @weight.setter
    def weight(self, value):
        self._weight = value

    @property
    def parentid(self):
        """The parentid property"""
        return self._parentid

    @parentid.setter
    def parentid(self, value):
        self._parentid = value

class Title(Typed):
    def __init__(self, lang, type=None, title=None, exact=False):
        Typed.__init__(self)
        assert lang is not None
        self._lang = lang
        self._type = type
        self._title = title
        self._exact = exact

    def __str__(self):
        return self._title

    @property
    def lang(self):
        """
        The language of the title. A complete list is available at `the
        AniDB wiki <http://wiki.anidb.net/w/User:Eloyard/anititles_dump>`_
        """
        return self._lang

    @lang.setter
    def lang(self, value):
        self._lang = value

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value

    @property
    def exact(self):
        """
        Whether or not this is an exact match, in case the correspondig
        :class:`anidb.model.Anime` object was retrieved via a search.

        :rtype: Boolean
        """
        return self._exact

    @exact.setter
    def exact(self, value):
        self._exact = value

class Tag(Entity, Named, Described):
    def __init__(self, id):
        Entity.__init__(self, id)
        Named.__init__(self)
        Described.__init__(self)
        self._spoiler = False
        self._approval = None
        self._count = None

    @property
    def count(self):
        """The count property"""
        return self._count

    @count.setter
    def count(self, value):
        self._count = int(value)

    @property
    def spoiler(self):
        """The spoiler property"""
        return self._spoiler

    @spoiler.setter
    def spoiler(self, value):
        self._spoiler = value

    @property
    def approval(self):
        """The approval property"""
        return self._approval

    @approval.setter
    def approval(self, value):
        self._approval = int(value)
