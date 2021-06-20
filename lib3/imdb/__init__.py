# Copyright 2004-2020 Davide Alberani <da@erlug.linux.it>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""
This package can be used to retrieve information about a movie or a person
from the IMDb database. It can fetch data through different media such as
the IMDb web pages, or a SQL database.
"""

from __future__ import absolute_import, division, print_function, unicode_literals
from imdb.version import __version__

__all__ = ['IMDb', 'IMDbError', 'Movie', 'Person', 'Character', 'Company',
           'available_access_systems']

VERSION = __version__


import os
import sys
from pkgutil import find_loader
from types import MethodType, FunctionType

from imdb._logging import imdbpyLogger as _imdb_logger
from imdb._exceptions import IMDbDataAccessError, IMDbError
from imdb import Character, Company, Movie, Person
from imdb.utils import build_company_name, build_name, build_title

PY2 = sys.hexversion < 0x3000000

if PY2:
    import ConfigParser as configparser
else:
    import configparser


_aux_logger = _imdb_logger.getChild('aux')

# URLs of the main pages for movies, persons, characters and queries.
imdbURL_base = 'https://www.imdb.com/'

# NOTE: the urls below will be removed in a future version.
#       please use the values in the 'urls' attribute
#       of the IMDbBase subclass instance.
# http://www.imdb.com/title/
imdbURL_movie_base = '%stitle/' % imdbURL_base
# http://www.imdb.com/title/tt%s/
imdbURL_movie_main = imdbURL_movie_base + 'tt%s/'
# http://www.imdb.com/name/
imdbURL_person_base = '%sname/' % imdbURL_base
# http://www.imdb.com/name/nm%s/
imdbURL_person_main = imdbURL_person_base + 'nm%s/'
# http://www.imdb.com/character/
imdbURL_character_base = '%scharacter/' % imdbURL_base
# http://www.imdb.com/character/ch%s/
imdbURL_character_main = imdbURL_character_base + 'ch%s/'
# http://www.imdb.com/company/
imdbURL_company_base = '%scompany/' % imdbURL_base
# http://www.imdb.com/company/co%s/
imdbURL_company_main = imdbURL_company_base + 'co%s/'
# http://www.imdb.com/keyword/%s/
imdbURL_keyword_main = imdbURL_base + 'search/keyword/?keywords=%s'
# http://www.imdb.com/chart/top
imdbURL_top250 = imdbURL_base + 'chart/top'
# http://www.imdb.com/chart/bottom
imdbURL_bottom100 = imdbURL_base + 'chart/bottom'
# http://www.imdb.com/find?%s
imdbURL_find = imdbURL_base + 'find?%s'
# http://www.imdb.com/list/
imdbURL_list_base = imdbURL_base + 'list/'

# Name of the configuration file.
confFileName = 'imdbpy.cfg'


class ConfigParserWithCase(configparser.ConfigParser):
    """A case-sensitive parser for configuration files."""
    def __init__(self, defaults=None, confFile=None, *args, **kwds):
        """Initialize the parser.

        *defaults* -- defaults values.
        *confFile* -- the file (or list of files) to parse."""
        if PY2:
            configparser.ConfigParser.__init__(self, defaults=defaults)
        else:
            super(configparser.ConfigParser, self).__init__(defaults=defaults)
        if confFile is None:
            dotFileName = '.' + confFileName
            # Current and home directory.
            confFile = [os.path.join(os.getcwd(), confFileName),
                        os.path.join(os.getcwd(), dotFileName),
                        os.path.join(os.path.expanduser('~'), confFileName),
                        os.path.join(os.path.expanduser('~'), dotFileName)]
            if os.name == 'posix':
                sep = getattr(os.path, 'sep', '/')
                # /etc/ and /etc/conf.d/
                confFile.append(os.path.join(sep, 'etc', confFileName))
                confFile.append(os.path.join(sep, 'etc', 'conf.d', confFileName))
            else:
                # etc subdirectory of sys.prefix, for non-unix systems.
                confFile.append(os.path.join(sys.prefix, 'etc', confFileName))
        for fname in confFile:
            try:
                self.read(fname)
            except (configparser.MissingSectionHeaderError,
                    configparser.ParsingError) as e:
                _aux_logger.warn('Troubles reading config file: %s' % e)
            # Stop at the first valid file.
            if self.has_section('imdbpy'):
                break

    def optionxform(self, optionstr):
        """Option names are case sensitive."""
        return optionstr

    def _manageValue(self, value):
        """Custom substitutions for values."""
        if not isinstance(value, str):
            return value
        vlower = value.lower()
        if vlower in ('1', 'on', 'false', '0', 'off', 'yes', 'no', 'true'):
            return self._convert_to_boolean(vlower)
        elif vlower == 'none':
            return None
        return value

    def get(self, section, option, *args, **kwds):
        """Return the value of an option from a given section."""
        value = configparser.ConfigParser.get(self, section, option, *args, **kwds)
        return self._manageValue(value)

    def items(self, section, *args, **kwds):
        """Return a list of (key, value) tuples of items of the
        given section."""
        if section != 'DEFAULT' and not self.has_section(section):
            return []
        keys = configparser.ConfigParser.options(self, section)
        return [(k, self.get(section, k, *args, **kwds)) for k in keys]

    def getDict(self, section):
        """Return a dictionary of items of the specified section."""
        return dict(self.items(section))


def IMDb(accessSystem=None, *arguments, **keywords):
    """Return an instance of the appropriate class.
    The accessSystem parameter is used to specify the kind of
    the preferred access system."""
    if accessSystem is None or accessSystem in ('auto', 'config'):
        try:
            cfg_file = ConfigParserWithCase(*arguments, **keywords)
            # Parameters set by the code take precedence.
            kwds = cfg_file.getDict('imdbpy')
            if 'accessSystem' in kwds:
                accessSystem = kwds['accessSystem']
                del kwds['accessSystem']
            else:
                accessSystem = 'http'
            kwds.update(keywords)
            keywords = kwds
        except Exception as e:
            _imdb_logger.warn('Unable to read configuration file; complete error: %s' % e)
            # It just LOOKS LIKE a bad habit: we tried to read config
            # options from some files, but something is gone horribly
            # wrong: ignore everything and pretend we were called with
            # the 'http' accessSystem.
            accessSystem = 'http'
    if 'loggingLevel' in keywords:
        _imdb_logger.setLevel(keywords['loggingLevel'])
        del keywords['loggingLevel']
    if 'loggingConfig' in keywords:
        logCfg = keywords['loggingConfig']
        del keywords['loggingConfig']
        try:
            import logging.config
            logging.config.fileConfig(os.path.expanduser(logCfg))
        except Exception as e:
            _imdb_logger.warn('unable to read logger config: %s' % e)
    if accessSystem in ('http', 'https', 'web', 'html'):
        from .parser.http import IMDbHTTPAccessSystem
        return IMDbHTTPAccessSystem(*arguments, **keywords)
    if accessSystem in ('s3', 's3dataset', 'imdbws'):
        from .parser.s3 import IMDbS3AccessSystem
        return IMDbS3AccessSystem(*arguments, **keywords)
    elif accessSystem in ('sql', 'db', 'database'):
        try:
            from .parser.sql import IMDbSqlAccessSystem
        except ImportError:
            raise IMDbError('the sql access system is not installed')
        return IMDbSqlAccessSystem(*arguments, **keywords)
    else:
        raise IMDbError('unknown kind of data access system: "%s"' % accessSystem)


def available_access_systems():
    """Return the list of available data access systems."""
    asList = []
    if find_loader('imdb.parser.http') is not None:
        asList.append('http')
    if find_loader('imdb.parser.sql') is not None:
        asList.append('sql')
    return asList


# XXX: I'm not sure this is a good guess.
#      I suppose that an argument of the IMDb function can be used to
#      set a default encoding for the output, and then Movie, Person and
#      Character objects can use this default encoding, returning strings.
#      Anyway, passing unicode strings to search_movie(), search_person()
#      and search_character() methods is always safer.
encoding = getattr(sys.stdin, 'encoding', '') or sys.getdefaultencoding()


class IMDbBase:
    """The base class used to search for a movie/person/character and
    to get a Movie/Person/Character object.

    This class cannot directly fetch data of any kind and so you
    have to search the "real" code into a subclass."""

    # The name of the preferred access system (MUST be overridden
    # in the subclasses).
    accessSystem = 'UNKNOWN'

    # Whether to re-raise caught exceptions or not.
    _reraise_exceptions = False

    def __init__(self, defaultModFunct=None, results=20, keywordsResults=100,
                 *arguments, **keywords):
        """Initialize the access system.
        If specified, defaultModFunct is the function used by
        default by the Person, Movie and Character objects, when
        accessing their text fields.
        """
        # The function used to output the strings that need modification (the
        # ones containing references to movie titles and person names).
        self._defModFunct = defaultModFunct
        # Number of results to get.
        try:
            results = int(results)
        except (TypeError, ValueError):
            results = 20
        if results < 1:
            results = 20
        self._results = results
        try:
            keywordsResults = int(keywordsResults)
        except (TypeError, ValueError):
            keywordsResults = 100
        if keywordsResults < 1:
            keywordsResults = 100
        self._keywordsResults = keywordsResults
        self._reraise_exceptions = keywords.get('reraiseExceptions') or False
        self.set_imdb_urls(keywords.get('imdbURL_base') or imdbURL_base)

    def set_imdb_urls(self, imdbURL_base):
        """Set the urls used accessing the IMDb site."""
        imdbURL_base = imdbURL_base.strip().strip('"\'')
        if not imdbURL_base.startswith(('https://', 'http://')):
            imdbURL_base = 'https://%s' % imdbURL_base
        if not imdbURL_base.endswith('/'):
            imdbURL_base = '%s/' % imdbURL_base
        # http://www.imdb.com/title/
        imdbURL_movie_base = '%stitle/' % imdbURL_base
        # http://www.imdb.com/title/tt%s/
        imdbURL_movie_main = imdbURL_movie_base + 'tt%s/'
        # http://www.imdb.com/name/
        imdbURL_person_base = '%sname/' % imdbURL_base
        # http://www.imdb.com/name/nm%s/
        imdbURL_person_main = imdbURL_person_base + 'nm%s/'
        # http://www.imdb.com/character/
        imdbURL_character_base = '%scharacter/' % imdbURL_base
        # http://www.imdb.com/character/ch%s/
        imdbURL_character_main = imdbURL_character_base + 'ch%s/'
        # http://www.imdb.com/company/
        imdbURL_company_base = '%scompany/' % imdbURL_base
        # http://www.imdb.com/company/co%s/
        imdbURL_company_main = imdbURL_company_base + 'co%s/'
        # http://www.imdb.com/keyword/%s/
        imdbURL_keyword_main = imdbURL_base + '/search/keyword?keywords=%s'
        # http://www.imdb.com/chart/top
        imdbURL_top250 = imdbURL_base + 'chart/top'
        # http://www.imdb.com/chart/bottom
        imdbURL_bottom100 = imdbURL_base + 'chart/bottom'
        # http://www.imdb.com/chart/moviemeter
        imdbURL_moviemeter100 = imdbURL_base + 'chart/moviemeter'
        # http://www.imdb.com/chart/tvmeter
        imdbURL_tvmeter100 = imdbURL_base + 'chart/tvmeter'
        # http://www.imdb.com/chart/toptv
        imdbURL_toptv250 = imdbURL_base + 'chart/toptv'
        # https://www.imdb.com/india/top-rated-indian-movies
        imdbURL_topindian250 = imdbURL_base + 'india/top-rated-indian-movies'
        # http://www.imdb.com/find?%s
        imdbURL_find = imdbURL_base + 'find?%s'
        # http://www.imdb.com/search/title?%s
        imdbURL_search_movie_advanced = imdbURL_base + 'search/title/?%s'
        # http://www.imdb.com/list/
        imdbURL_list_base = imdbURL_base + 'list/'
        self.urls = dict(
            movie_base=imdbURL_movie_base,
            movie_main=imdbURL_movie_main,
            person_base=imdbURL_person_base,
            person_main=imdbURL_person_main,
            character_base=imdbURL_character_base,
            character_main=imdbURL_character_main,
            company_base=imdbURL_company_base,
            company_main=imdbURL_company_main,
            keyword_main=imdbURL_keyword_main,
            top250=imdbURL_top250,
            bottom100=imdbURL_bottom100,
            moviemeter100=imdbURL_moviemeter100,
            tvmeter100=imdbURL_tvmeter100,
            toptv250=imdbURL_toptv250,
            topindian250=imdbURL_topindian250,
            find=imdbURL_find,
            movie_list=imdbURL_list_base,
            search_movie_advanced=imdbURL_search_movie_advanced)

    def _normalize_movieID(self, movieID):
        """Normalize the given movieID."""
        # By default, do nothing.
        return movieID

    def _normalize_personID(self, personID):
        """Normalize the given personID."""
        # By default, do nothing.
        return personID

    def _normalize_characterID(self, characterID):
        """Normalize the given characterID."""
        # By default, do nothing.
        return characterID

    def _normalize_companyID(self, companyID):
        """Normalize the given companyID."""
        # By default, do nothing.
        return companyID

    def _get_real_movieID(self, movieID):
        """Handle title aliases."""
        # By default, do nothing.
        return movieID

    def _get_real_personID(self, personID):
        """Handle name aliases."""
        # By default, do nothing.
        return personID

    def _get_real_characterID(self, characterID):
        """Handle character name aliases."""
        # By default, do nothing.
        return characterID

    def _get_real_companyID(self, companyID):
        """Handle company name aliases."""
        # By default, do nothing.
        return companyID

    def _get_infoset(self, prefname):
        """Return methods with the name starting with prefname."""
        infoset = []
        excludes = ('%sinfoset' % prefname,)
        preflen = len(prefname)
        for name in dir(self.__class__):
            if name.startswith(prefname) and name not in excludes:
                member = getattr(self.__class__, name)
                if isinstance(member, (MethodType, FunctionType)):
                    infoset.append(name[preflen:].replace('_', ' '))
        return infoset

    def get_movie_infoset(self):
        """Return the list of info set available for movies."""
        return self._get_infoset('get_movie_')

    def get_person_infoset(self):
        """Return the list of info set available for persons."""
        return self._get_infoset('get_person_')

    def get_character_infoset(self):
        """Return the list of info set available for characters."""
        return self._get_infoset('get_character_')

    def get_company_infoset(self):
        """Return the list of info set available for companies."""
        return self._get_infoset('get_company_')

    def get_movie(self, movieID, info=Movie.Movie.default_info, modFunct=None):
        """Return a Movie object for the given movieID.

        The movieID is something used to univocally identify a movie;
        it can be the imdbID used by the IMDb web server, a file
        pointer, a line number in a file, an ID in a database, etc.

        info is the list of sets of information to retrieve.

        If specified, modFunct will be the function used by the Movie
        object when accessing its text fields (like 'plot')."""
        movieID = self._normalize_movieID(movieID)
        movieID = self._get_real_movieID(movieID)
        movie = Movie.Movie(movieID=movieID, accessSystem=self.accessSystem)
        modFunct = modFunct or self._defModFunct
        if modFunct is not None:
            movie.set_mod_funct(modFunct)
        self.update(movie, info)
        return movie

    get_episode = get_movie

    def _search_movie(self, title, results):
        """Return a list of tuples (movieID, {movieData})"""
        # XXX: for the real implementation, see the method of the
        #      subclass, somewhere under the imdb.parser package.
        raise NotImplementedError('override this method')

    def search_movie(self, title, results=None, _episodes=False):
        """Return a list of Movie objects for a query for the given title.
        The results argument is the maximum number of results to return."""
        if results is None:
            results = self._results
        try:
            results = int(results)
        except (ValueError, OverflowError):
            results = 20
        if not _episodes:
            res = self._search_movie(title, results)
        else:
            res = self._search_episode(title, results)
        return [Movie.Movie(movieID=self._get_real_movieID(mi),
                data=md, modFunct=self._defModFunct,
                accessSystem=self.accessSystem) for mi, md in res][:results]

    def _get_movie_list(self, list_, results):
        """Return a list of tuples (movieID, {movieData})"""
        # XXX: for the real implementation, see the method of the
        #      subclass, somewhere under the imdb.parser package.
        raise NotImplementedError('override this method')

    def get_movie_list(self, list_, results=None):
        """Return a list of Movie objects for a list id as input """
        res = self._get_movie_list(list_, results)
        return [Movie.Movie(movieID=self._get_real_movieID(mi),
                data=md, modFunct=self._defModFunct,
                accessSystem=self.accessSystem) for mi, md in res][:results]

    def _search_movie_advanced(self, title=None, adult=None, results=None, sort=None, sort_dir=None):
        """Return a list of tuples (movieID, {movieData})"""
        # XXX: for the real implementation, see the method of the
        #      subclass, somewhere under the imdb.parser package.
        raise NotImplementedError('override this method')

    def search_movie_advanced(self, title=None, adult=None, results=None, sort=None, sort_dir=None):
        """Return a list of Movie objects for a query for the given title.
        The results argument is the maximum number of results to return."""
        if results is None:
            results = self._results
        try:
            results = int(results)
        except (ValueError, OverflowError):
            results = 20
        res = self._search_movie_advanced(title=title, adult=adult, results=results, sort=sort, sort_dir=sort_dir)
        return [Movie.Movie(movieID=self._get_real_movieID(mi),
                data=md, modFunct=self._defModFunct,
                accessSystem=self.accessSystem) for mi, md in res][:results]

    def _search_episode(self, title, results):
        """Return a list of tuples (movieID, {movieData})"""
        # XXX: for the real implementation, see the method of the
        #      subclass, somewhere under the imdb.parser package.
        raise NotImplementedError('override this method')

    def search_episode(self, title, results=None):
        """Return a list of Movie objects for a query for the given title.
        The results argument is the maximum number of results to return;
        this method searches only for titles of tv (mini) series' episodes."""
        return self.search_movie(title, results=results, _episodes=True)

    def get_person(self, personID, info=Person.Person.default_info, modFunct=None):
        """Return a Person object for the given personID.

        The personID is something used to univocally identify a person;
        it can be the imdbID used by the IMDb web server, a file
        pointer, a line number in a file, an ID in a database, etc.

        info is the list of sets of information to retrieve.

        If specified, modFunct will be the function used by the Person
        object when accessing its text fields (like 'mini biography')."""
        personID = self._normalize_personID(personID)
        personID = self._get_real_personID(personID)
        person = Person.Person(personID=personID, accessSystem=self.accessSystem)
        modFunct = modFunct or self._defModFunct
        if modFunct is not None:
            person.set_mod_funct(modFunct)
        self.update(person, info)
        return person

    def _search_person(self, name, results):
        """Return a list of tuples (personID, {personData})"""
        # XXX: for the real implementation, see the method of the
        #      subclass, somewhere under the imdb.parser package.
        raise NotImplementedError('override this method')

    def search_person(self, name, results=None):
        """Return a list of Person objects for a query for the given name.

        The results argument is the maximum number of results to return."""
        if results is None:
            results = self._results
        try:
            results = int(results)
        except (ValueError, OverflowError):
            results = 20
        res = self._search_person(name, results)
        return [Person.Person(personID=self._get_real_personID(pi),
                data=pd, modFunct=self._defModFunct,
                accessSystem=self.accessSystem) for pi, pd in res][:results]

    def get_character(self, characterID, info=Character.Character.default_info,
                      modFunct=None):
        """Return a Character object for the given characterID.

        The characterID is something used to univocally identify a character;
        it can be the imdbID used by the IMDb web server, a file
        pointer, a line number in a file, an ID in a database, etc.

        info is the list of sets of information to retrieve.

        If specified, modFunct will be the function used by the Character
        object when accessing its text fields (like 'biography')."""
        characterID = self._normalize_characterID(characterID)
        characterID = self._get_real_characterID(characterID)
        character = Character.Character(characterID=characterID,
                                        accessSystem=self.accessSystem)
        modFunct = modFunct or self._defModFunct
        if modFunct is not None:
            character.set_mod_funct(modFunct)
        self.update(character, info)
        return character

    def _search_character(self, name, results):
        """Return a list of tuples (characterID, {characterData})"""
        # XXX: for the real implementation, see the method of the
        #      subclass, somewhere under the imdb.parser package.
        raise NotImplementedError('override this method')

    def search_character(self, name, results=None):
        """Return a list of Character objects for a query for the given name.

        The results argument is the maximum number of results to return."""
        if results is None:
            results = self._results
        try:
            results = int(results)
        except (ValueError, OverflowError):
            results = 20
        res = self._search_character(name, results)
        return [Character.Character(characterID=self._get_real_characterID(pi),
                data=pd, modFunct=self._defModFunct,
                accessSystem=self.accessSystem) for pi, pd in res][:results]

    def get_company(self, companyID, info=Company.Company.default_info,
                    modFunct=None):
        """Return a Company object for the given companyID.

        The companyID is something used to univocally identify a company;
        it can be the imdbID used by the IMDb web server, a file
        pointer, a line number in a file, an ID in a database, etc.

        info is the list of sets of information to retrieve.

        If specified, modFunct will be the function used by the Company
        object when accessing its text fields (none, so far)."""
        companyID = self._normalize_companyID(companyID)
        companyID = self._get_real_companyID(companyID)
        company = Company.Company(companyID=companyID, accessSystem=self.accessSystem)
        modFunct = modFunct or self._defModFunct
        if modFunct is not None:
            company.set_mod_funct(modFunct)
        self.update(company, info)
        return company

    def _search_company(self, name, results):
        """Return a list of tuples (companyID, {companyData})"""
        # XXX: for the real implementation, see the method of the
        #      subclass, somewhere under the imdb.parser package.
        raise NotImplementedError('override this method')

    def search_company(self, name, results=None):
        """Return a list of Company objects for a query for the given name.

        The results argument is the maximum number of results to return."""
        if results is None:
            results = self._results
        try:
            results = int(results)
        except (ValueError, OverflowError):
            results = 20
        res = self._search_company(name, results)
        return [Company.Company(companyID=self._get_real_companyID(pi),
                data=pd, modFunct=self._defModFunct,
                accessSystem=self.accessSystem) for pi, pd in res][:results]

    def _search_keyword(self, keyword, results):
        """Return a list of 'keyword' strings."""
        # XXX: for the real implementation, see the method of the
        #      subclass, somewhere under the imdb.parser package.
        raise NotImplementedError('override this method')

    def search_keyword(self, keyword, results=None):
        """Search for existing keywords, similar to the given one."""
        if results is None:
            results = self._keywordsResults
        try:
            results = int(results)
        except (ValueError, OverflowError):
            results = 100
        return self._search_keyword(keyword, results)

    def _get_keyword(self, keyword, results, page):
        """Return a list of tuples (movieID, {movieData})"""
        # XXX: for the real implementation, see the method of the
        #      subclass, somewhere under the imdb.parser package.
        raise NotImplementedError('override this method')

    def get_keyword(self, keyword, results=None, page=None):
        """Return a list of movies for the given keyword."""
        if results is None:
            results = self._keywordsResults
        try:
            results = int(results)
        except (ValueError, OverflowError):
            results = 100
        res = self._get_keyword(keyword, results, page)
        return [Movie.Movie(movieID=self._get_real_movieID(mi),
                data=md, modFunct=self._defModFunct,
                accessSystem=self.accessSystem) for mi, md in res][:results]

    def _get_top_bottom_movies(self, kind):
        """Return the list of the top 250 or bottom 100 movies."""
        # XXX: for the real implementation, see the method of the
        #      subclass, somewhere under the imdb.parser package.
        #      This method must return a list of (movieID, {movieDict})
        #      tuples.  The kind parameter can be 'top' or 'bottom'.
        raise NotImplementedError('override this method')

    def get_top250_movies(self):
        """Return the list of the top 250 movies."""
        res = self._get_top_bottom_movies('top')
        return [Movie.Movie(movieID=self._get_real_movieID(mi),
                data=md, modFunct=self._defModFunct,
                accessSystem=self.accessSystem) for mi, md in res]

    def get_bottom100_movies(self):
        """Return the list of the bottom 100 movies."""
        res = self._get_top_bottom_movies('bottom')
        return [Movie.Movie(movieID=self._get_real_movieID(mi),
                data=md, modFunct=self._defModFunct,
                accessSystem=self.accessSystem) for mi, md in res]

    def get_top250_tv(self):
        """Return the list of the top 250 tv shows."""
        res = self._get_top_bottom_movies('toptv')
        return [Movie.Movie(movieID=self._get_real_movieID(mi),
                data=md, modFunct=self._defModFunct,
                accessSystem=self.accessSystem) for mi, md in res]

    def get_popular100_movies(self):
        """Return the list of the 100 most popular movies."""
        res = self._get_top_bottom_movies('moviemeter')
        return [Movie.Movie(movieID=self._get_real_movieID(mi),
                data=md, modFunct=self._defModFunct,
                accessSystem=self.accessSystem) for mi, md in res]

    def get_popular100_tv(self):
        """Return the list of the 100 most popular tv shows."""
        res = self._get_top_bottom_movies('tvmeter')
        return [Movie.Movie(movieID=self._get_real_movieID(mi),
                data=md, modFunct=self._defModFunct,
                accessSystem=self.accessSystem) for mi, md in res]

    def get_top250_indian_movies(self):
        """Return the list of the top 250 indian movies."""
        res = self._get_top_bottom_movies('topindian250')
        return [Movie.Movie(movieID=self._get_real_movieID(mi),
                data=md, modFunct=self._defModFunct,
                accessSystem=self.accessSystem) for mi, md in res]


    def new_movie(self, *arguments, **keywords):
        """Return a Movie object."""
        # XXX: not really useful...
        return Movie.Movie(accessSystem=self.accessSystem, *arguments, **keywords)

    def new_person(self, *arguments, **keywords):
        """Return a Person object."""
        # XXX: not really useful...
        return Person.Person(accessSystem=self.accessSystem, *arguments, **keywords)

    def new_character(self, *arguments, **keywords):
        """Return a Character object."""
        # XXX: not really useful...
        return Character.Character(accessSystem=self.accessSystem, *arguments, **keywords)

    def new_company(self, *arguments, **keywords):
        """Return a Company object."""
        # XXX: not really useful...
        return Company.Company(accessSystem=self.accessSystem, *arguments, **keywords)

    def update(self, mop, info=None, override=0):
        """Given a Movie, Person, Character or Company object with only
        partial information, retrieve the required set of information.

        info is the list of sets of information to retrieve.

        If override is set, the information are retrieved and updated
        even if they're already in the object."""
        # XXX: should this be a method of the Movie/Person/Character/Company
        #      classes?  NO!  What for instances created by external functions?
        mopID = None
        prefix = ''
        if isinstance(mop, Movie.Movie):
            mopID = mop.movieID
            prefix = 'movie'
        elif isinstance(mop, Person.Person):
            mopID = mop.personID
            prefix = 'person'
        elif isinstance(mop, Character.Character):
            mopID = mop.characterID
            prefix = 'character'
        elif isinstance(mop, Company.Company):
            mopID = mop.companyID
            prefix = 'company'
        else:
            raise IMDbError('object ' + repr(mop) +
                            ' is not a Movie, Person, Character or Company instance')
        if mopID is None:
            # XXX: enough?  It's obvious that there are Characters
            #      objects without characterID, so I think they should
            #      just do nothing, when an i.update(character) is tried.
            if prefix == 'character':
                return
            raise IMDbDataAccessError('supplied object has null movieID, personID or companyID')
        if mop.accessSystem == self.accessSystem:
            aSystem = self
        else:
            aSystem = IMDb(mop.accessSystem)
        if info is None:
            info = mop.default_info
        elif info == 'all':
            if isinstance(mop, Movie.Movie):
                info = self.get_movie_infoset()
            elif isinstance(mop, Person.Person):
                info = self.get_person_infoset()
            elif isinstance(mop, Character.Character):
                info = self.get_character_infoset()
            else:
                info = self.get_company_infoset()
        if not isinstance(info, (tuple, list)):
            info = (info,)
        res = {}
        for i in info:
            if i in mop.current_info and not override:
                continue
            if not i:
                continue
            _imdb_logger.debug('retrieving "%s" info set', i)
            try:
                method = getattr(aSystem, 'get_%s_%s' % (prefix, i.replace(' ', '_')))
            except AttributeError:
                _imdb_logger.error('unknown information set "%s"', i)
                # Keeps going.
                method = lambda *x: {}
            try:
                ret = method(mopID)
            except Exception:
                _imdb_logger.critical(
                    'caught an exception retrieving or parsing "%s" info set'
                    ' for mopID "%s" (accessSystem: %s)',
                    i, mopID, mop.accessSystem, exc_info=True
                )
                ret = {}
                # If requested by the user, reraise the exception.
                if self._reraise_exceptions:
                    raise
            keys = None
            if 'data' in ret:
                res.update(ret['data'])
                if isinstance(ret['data'], dict):
                    keys = list(ret['data'].keys())
            if 'info sets' in ret:
                for ri in ret['info sets']:
                    mop.add_to_current_info(ri, keys, mainInfoset=i)
            else:
                mop.add_to_current_info(i, keys)
            if 'titlesRefs' in ret:
                mop.update_titlesRefs(ret['titlesRefs'])
            if 'namesRefs' in ret:
                mop.update_namesRefs(ret['namesRefs'])
            if 'charactersRefs' in ret:
                mop.update_charactersRefs(ret['charactersRefs'])
        mop.set_data(res, override=0)

    def update_series_seasons(self, mop, season_nums, override=0):
        """Given a Movie object with only retrieve the season data.

        season_nums is the list of the specific seasons to retrieve.

        If override is set, the information are retrieved and updated
        even if they're already in the object."""
        mopID = None
        if isinstance(mop, Movie.Movie):
            mopID = mop.movieID
        else:
            raise IMDbError('object ' + repr(mop) + ' is not a Movie instance')
        if mopID is None:
            raise IMDbDataAccessError('supplied object has null movieID, personID or companyID')
        if mop.accessSystem == self.accessSystem:
            aSystem = self
        else:
            aSystem = IMDb(mop.accessSystem)

        info = 'episodes'

        res = {}

        if info in mop.current_info and not override:
            return
        _imdb_logger.debug('retrieving "%s" info set', info)
        try:
            method = getattr(aSystem, 'get_movie_episodes')
        except AttributeError:
            _imdb_logger.error('unknown information set "%s"', info)
            # Keeps going.
            method = lambda *x: {}
        try:
            ret = method(mopID, season_nums)
        except Exception:
            _imdb_logger.critical(
                'caught an exception retrieving or parsing "%s" info set'
                ' for mopID "%s" (accessSystem: %s)',
                info, mopID, mop.accessSystem, exc_info=True
            )
            ret = {}
            # If requested by the user, reraise the exception.
            if self._reraise_exceptions:
                raise
        keys = None
        if 'data' in ret:
            res.update(ret['data'])
            if isinstance(ret['data'], dict):
                keys = list(ret['data'].keys())
        if 'info sets' in ret:
            for ri in ret['info sets']:
                mop.add_to_current_info(ri, keys, mainInfoset=info)
        else:
            mop.add_to_current_info(info, keys)
        if 'titlesRefs' in ret:
            mop.update_titlesRefs(ret['titlesRefs'])
        if 'namesRefs' in ret:
            mop.update_namesRefs(ret['namesRefs'])
        if 'charactersRefs' in ret:
            mop.update_charactersRefs(ret['charactersRefs'])
        mop.set_data(res, override=0)

    def get_imdbMovieID(self, movieID):
        """Translate a movieID in an imdbID (the ID used by the IMDb
        web server); must be overridden by the subclass."""
        # XXX: for the real implementation, see the method of the
        #      subclass, somewhere under the imdb.parser package.
        raise NotImplementedError('override this method')

    def get_imdbPersonID(self, personID):
        """Translate a personID in a imdbID (the ID used by the IMDb
        web server); must be overridden by the subclass."""
        # XXX: for the real implementation, see the method of the
        #      subclass, somewhere under the imdb.parser package.
        raise NotImplementedError('override this method')

    def get_imdbCharacterID(self, characterID):
        """Translate a characterID in a imdbID (the ID used by the IMDb
        web server); must be overridden by the subclass."""
        # XXX: for the real implementation, see the method of the
        #      subclass, somewhere under the imdb.parser package.
        raise NotImplementedError('override this method')

    def get_imdbCompanyID(self, companyID):
        """Translate a companyID in a imdbID (the ID used by the IMDb
        web server); must be overridden by the subclass."""
        # XXX: for the real implementation, see the method of the
        #      subclass, somewhere under the imdb.parser package.
        raise NotImplementedError('override this method')

    def _searchIMDb(self, kind, ton, title_kind=None):
        """Search the IMDb www server for the given title or name."""
        if not ton:
            return None
        ton = ton.strip('"')
        aSystem = IMDb()
        if kind == 'tt':
            searchFunct = aSystem.search_movie
            check = 'long imdb title'
        elif kind == 'nm':
            searchFunct = aSystem.search_person
            check = 'long imdb name'
        elif kind == 'char':
            searchFunct = aSystem.search_character
            check = 'long imdb name'
        elif kind == 'co':
            # XXX: are [COUNTRY] codes included in the results?
            searchFunct = aSystem.search_company
            check = 'long imdb name'
        try:
            searchRes = searchFunct(ton)
        except IMDbError:
            return None
        # When only one result is returned, assume it was from an
        # exact match.
        if len(searchRes) == 1:
            return searchRes[0].getID()
        title_only_matches = []
        for item in searchRes:
            # Return the first perfect match.
            if item[check].strip('"') == ton:
                # For titles do additional check for kind
                if kind != 'tt' or title_kind == item['kind']:
                    return item.getID()
                elif kind == 'tt':
                    title_only_matches.append(item.getID())
        # imdbpy2sql.py could detected wrong type, so if no title and kind
        # matches found - collect all results with title only match
        # Return list of IDs if multiple matches (can happen when searching
        # titles with no title_kind specified)
        # Example: DB: Band of Brothers "tv series" vs "tv mini-series"
        if title_only_matches:
            if len(title_only_matches) == 1:
                return title_only_matches[0]
            else:
                return title_only_matches
        return None

    def title2imdbID(self, title, kind=None):
        """Translate a movie title (in the plain text data files format)
        to an imdbID.
        Try an Exact Primary Title search on IMDb;
        return None if it's unable to get the imdbID;
        Always specify kind: movie, tv series, video game etc. or search can
        return list of IDs if multiple matches found
        """
        return self._searchIMDb('tt', title, kind)

    def name2imdbID(self, name):
        """Translate a person name in an imdbID.
        Try an Exact Primary Name search on IMDb;
        return None if it's unable to get the imdbID."""
        return self._searchIMDb('nm', name)

    def character2imdbID(self, name):
        """Translate a character name in an imdbID.
        Try an Exact Primary Name search on IMDb;
        return None if it's unable to get the imdbID."""
        return self._searchIMDb('char', name)

    def company2imdbID(self, name):
        """Translate a company name in an imdbID.
        Try an Exact Primary Name search on IMDb;
        return None if it's unable to get the imdbID."""
        return self._searchIMDb('co', name)

    def get_imdbID(self, mop):
        """Return the imdbID for the given Movie, Person, Character or Company
        object."""
        imdbID = None
        if mop.accessSystem == self.accessSystem:
            aSystem = self
        else:
            aSystem = IMDb(mop.accessSystem)
        if isinstance(mop, Movie.Movie):
            if mop.movieID is not None:
                imdbID = aSystem.get_imdbMovieID(mop.movieID)
            else:
                imdbID = aSystem.title2imdbID(build_title(mop, canonical=0,
                                                          ptdf=0, appendKind=False),
                                              mop['kind'])
        elif isinstance(mop, Person.Person):
            if mop.personID is not None:
                imdbID = aSystem.get_imdbPersonID(mop.personID)
            else:
                imdbID = aSystem.name2imdbID(build_name(mop, canonical=False))
        elif isinstance(mop, Character.Character):
            if mop.characterID is not None:
                imdbID = aSystem.get_imdbCharacterID(mop.characterID)
            else:
                # canonical=0 ?
                imdbID = aSystem.character2imdbID(build_name(mop, canonical=False))
        elif isinstance(mop, Company.Company):
            if mop.companyID is not None:
                imdbID = aSystem.get_imdbCompanyID(mop.companyID)
            else:
                imdbID = aSystem.company2imdbID(build_company_name(mop))
        else:
            raise IMDbError('object ' + repr(mop) +
                            ' is not a Movie, Person or Character instance')
        return imdbID

    def get_imdbURL(self, mop):
        """Return the main IMDb URL for the given Movie, Person,
        Character or Company object, or None if unable to get it."""
        imdbID = self.get_imdbID(mop)
        if imdbID is None:
            return None
        if isinstance(mop, Movie.Movie):
            url_firstPart = imdbURL_movie_main
        elif isinstance(mop, Person.Person):
            url_firstPart = imdbURL_person_main
        elif isinstance(mop, Character.Character):
            url_firstPart = imdbURL_character_main
        elif isinstance(mop, Company.Company):
            url_firstPart = imdbURL_company_main
        else:
            raise IMDbError('object ' + repr(mop) +
                            ' is not a Movie, Person, Character or Company instance')
        return url_firstPart % imdbID

    def get_special_methods(self):
        """Return the special methods defined by the subclass."""
        sm_dict = {}
        base_methods = []
        for name in dir(IMDbBase):
            member = getattr(IMDbBase, name)
            if isinstance(member, (MethodType, FunctionType)):
                base_methods.append(name)
        for name in dir(self.__class__):
            if name.startswith('_') or name in base_methods or \
                    name.startswith('get_movie_') or \
                    name.startswith('get_person_') or \
                    name.startswith('get_company_') or \
                    name.startswith('get_character_'):
                continue
            member = getattr(self.__class__, name)
            if isinstance(member, (MethodType, FunctionType)):
                sm_dict.update({name: member.__doc__})
        return sm_dict
