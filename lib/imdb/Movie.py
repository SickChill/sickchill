# Copyright 2004-2018 Davide Alberani <da@erlug.linux.it>
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
This module provides the Movie class, used to store information about
a given movie.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from copy import deepcopy

from imdb import linguistics
from imdb.utils import _Container
from imdb.utils import analyze_title, build_title, canonicalTitle, cmpMovies, flatten


class Movie(_Container):
    """A Movie.

    Every information about a movie can be accessed as::

        movieObject['information']

    to get a list of the kind of information stored in a
    Movie object, use the keys() method; some useful aliases
    are defined (as "casting" for the "casting director" key); see
    the keys_alias dictionary.
    """
    # The default sets of information retrieved.
    default_info = ('main', 'plot')

    # Aliases for some not-so-intuitive keys.
    keys_alias = {
        'tv schedule': 'airing',
        'user rating': 'rating',
        'plot summary': 'plot',
        'plot summaries': 'plot',
        'directed by': 'director',
        'actors': 'cast',
        'actresses': 'cast',
        'aka': 'akas',
        'also known as': 'akas',
        'country': 'countries',
        'production country': 'countries',
        'production countries': 'countries',
        'genre': 'genres',
        'runtime': 'runtimes',
        'lang': 'languages',
        'color': 'color info',
        'cover': 'cover url',
        'full-size cover': 'full-size cover url',
        'seasons': 'number of seasons',
        'language': 'languages',
        'certificate': 'certificates',
        'certifications': 'certificates',
        'certification': 'certificates',
        'episodes number': 'number of episodes',
        'faq': 'faqs',
        'technical': 'tech',
        'frequently asked questions': 'faqs'
    }

    keys_tomodify_list = (
        'plot', 'trivia', 'alternate versions', 'goofs',
        'quotes', 'dvd', 'laserdisc', 'news', 'soundtrack',
        'crazy credits', 'business', 'supplements',
        'video review', 'faqs'
    )

    _image_key = 'cover url'

    cmpFunct = cmpMovies

    def _init(self, **kwds):
        """Initialize a Movie object.

        *movieID* -- the unique identifier for the movie.
        *title* -- the title of the Movie, if not in the data dictionary.
        *myTitle* -- your personal title for the movie.
        *myID* -- your personal identifier for the movie.
        *data* -- a dictionary used to initialize the object.
        *currentRole* -- a Character instance representing the current role
                         or duty of a person in this movie, or a Person
                         object representing the actor/actress who played
                         a given character in a Movie.  If a string is
                         passed, an object is automatically build.
        *roleID* -- if available, the characterID/personID of the currentRole
                    object.
        *roleIsPerson* -- when False (default) the currentRole is assumed
                          to be a Character object, otherwise a Person.
        *notes* -- notes for the person referred in the currentRole
                    attribute; e.g.: '(voice)'.
        *accessSystem* -- a string representing the data access system used.
        *titlesRefs* -- a dictionary with references to movies.
        *namesRefs* -- a dictionary with references to persons.
        *charactersRefs* -- a dictionary with references to characters.
        *modFunct* -- function called returning text fields.
        """
        title = kwds.get('title')
        if title and 'title' not in self.data:
            self.set_title(title)
        self.movieID = kwds.get('movieID', None)
        self.myTitle = kwds.get('myTitle', '')

    def _reset(self):
        """Reset the Movie object."""
        self.movieID = None
        self.myTitle = ''

    def set_title(self, title):
        """Set the title of the movie."""
        d_title = analyze_title(title)
        self.data.update(d_title)

    def _additional_keys(self):
        """Valid keys to append to the data.keys() list."""
        addkeys = []
        if 'title' in self.data:
            addkeys += ['canonical title', 'long imdb title',
                        'long imdb canonical title',
                        'smart canonical title',
                        'smart long imdb canonical title']
        if 'episode of' in self.data:
            addkeys += ['long imdb episode title', 'series title',
                        'canonical series title', 'episode title',
                        'canonical episode title',
                        'smart canonical series title',
                        'smart canonical episode title']
        if 'cover url' in self.data:
            addkeys += ['full-size cover url']
        return addkeys

    def guessLanguage(self):
        """Guess the language of the title of this movie; returns None
        if there are no hints."""
        lang = self.get('languages')
        if lang:
            lang = lang[0]
        else:
            country = self.get('countries')
            if country:
                lang = linguistics.COUNTRY_LANG.get(country[0])
        return lang

    def smartCanonicalTitle(self, title=None, lang=None):
        """Return the canonical title, guessing its language.
        The title can be forces with the 'title' argument (internally
        used) and the language can be forced with the 'lang' argument,
        otherwise it's auto-detected."""
        if title is None:
            title = self.data.get('title', '')
        if lang is None:
            lang = self.guessLanguage()
        return canonicalTitle(title, lang=lang)

    def _getSeriesTitle(self, obj):
        """Get the title from a Movie object or return the string itself."""
        if isinstance(obj, Movie):
            return obj.get('title', '')
        return obj

    def _getitem(self, key):
        """Handle special keys."""
        if 'episode of' in self.data:
            if key == 'long imdb episode title':
                return build_title(self.data)
            elif key == 'series title':
                return self._getSeriesTitle(self.data['episode of'])
            elif key == 'canonical series title':
                ser_title = self._getSeriesTitle(self.data['episode of'])
                return canonicalTitle(ser_title)
            elif key == 'smart canonical series title':
                ser_title = self._getSeriesTitle(self.data['episode of'])
                return self.smartCanonicalTitle(ser_title)
            elif key == 'episode title':
                return self.data.get('title', '')
            elif key == 'canonical episode title':
                return canonicalTitle(self.data.get('title', ''))
            elif key == 'smart canonical episode title':
                return self.smartCanonicalTitle(self.data.get('title', ''))
        if 'title' in self.data:
            if key == 'title':
                return self.data['title']
            elif key == 'long imdb title':
                return build_title(self.data)
            elif key == 'canonical title':
                return canonicalTitle(self.data['title'])
            elif key == 'smart canonical title':
                return self.smartCanonicalTitle(self.data['title'])
            elif key == 'long imdb canonical title':
                return build_title(self.data, canonical=True)
            elif key == 'smart long imdb canonical title':
                return build_title(self.data, canonical=True, lang=self.guessLanguage())
        if key == 'full-size cover url':
            return self.get_fullsizeURL()
        return None

    def getID(self):
        """Return the movieID."""
        return self.movieID

    def __bool__(self):
        """The Movie is "false" if the self.data does not contain a title."""
        # XXX: check the title and the movieID?
        return 'title' in self.data

    def isSameTitle(self, other):
        """Return true if this and the compared object have the same
        long imdb title and/or movieID.
        """
        # XXX: obsolete?
        if not isinstance(other, self.__class__):
            return False
        if 'title' in self.data and 'title' in other.data and \
                build_title(self.data, canonical=False) == build_title(other.data, canonical=False):
            return True
        if self.accessSystem == other.accessSystem and \
                self.movieID is not None and self.movieID == other.movieID:
            return True
        return False
    isSameMovie = isSameTitle   # XXX: just for backward compatiblity.

    def __contains__(self, item):
        """Return true if the given Person object is listed in this Movie,
        or if the the given Character is represented in this Movie."""
        from .Person import Person
        from .Character import Character
        from .Company import Company
        if isinstance(item, Person):
            for p in flatten(self.data, yieldDictKeys=True, scalar=Person,
                             toDescend=(list, dict, tuple, Movie)):
                if item.isSame(p):
                    return True
        elif isinstance(item, Character):
            for p in flatten(self.data, yieldDictKeys=True, scalar=Person,
                             toDescend=(list, dict, tuple, Movie)):
                if item.isSame(p.currentRole):
                    return True
        elif isinstance(item, Company):
            for c in flatten(self.data, yieldDictKeys=True, scalar=Company,
                             toDescend=(list, dict, tuple, Movie)):
                if item.isSame(c):
                    return True
        elif isinstance(item, str):
            return item in self.data
        return False

    def __deepcopy__(self, memo):
        """Return a deep copy of a Movie instance."""
        m = Movie(title='', movieID=self.movieID, myTitle=self.myTitle,
                  myID=self.myID, data=deepcopy(self.data, memo),
                  currentRole=deepcopy(self.currentRole, memo),
                  roleIsPerson=self._roleIsPerson,
                  notes=self.notes, accessSystem=self.accessSystem,
                  titlesRefs=deepcopy(self.titlesRefs, memo),
                  namesRefs=deepcopy(self.namesRefs, memo),
                  charactersRefs=deepcopy(self.charactersRefs, memo))
        m.current_info = list(self.current_info)
        m.set_mod_funct(self.modFunct)
        return m

    def __repr__(self):
        """String representation of a Movie object."""
        # XXX: add also currentRole and notes, if present?
        if 'long imdb episode title' in self:
            title = self.get('long imdb episode title')
        else:
            title = self.get('long imdb title')
        return '<Movie id:%s[%s] title:_%s_>' % (self.movieID, self.accessSystem, title)

    def __str__(self):
        """Simply print the short title."""
        return self.get('title', '')

    def summary(self):
        """Return a string with a pretty-printed summary for the movie."""
        if not self:
            return ''

        def _nameAndRole(personList, joiner=', '):
            """Build a pretty string with name and role."""
            nl = []
            for person in personList:
                n = person.get('name', '')
                if person.currentRole:
                    n += ' (%s)' % person.currentRole
                nl.append(n)
            return joiner.join(nl)
        s = 'Movie\n=====\nTitle: %s\n' % self.get('long imdb canonical title', '')
        genres = self.get('genres')
        if genres:
            s += 'Genres: %s.\n' % ', '.join(genres)
        director = self.get('director')
        if director:
            s += 'Director: %s.\n' % _nameAndRole(director)
        writer = self.get('writer')
        if writer:
            s += 'Writer: %s.\n' % _nameAndRole(writer)
        cast = self.get('cast')
        if cast:
            cast = cast[:5]
            s += 'Cast: %s.\n' % _nameAndRole(cast)
        runtime = self.get('runtimes')
        if runtime:
            s += 'Runtime: %s.\n' % ', '.join(runtime)
        countries = self.get('countries')
        if countries:
            s += 'Country: %s.\n' % ', '.join(countries)
        lang = self.get('languages')
        if lang:
            s += 'Language: %s.\n' % ', '.join(lang)
        rating = self.get('rating')
        if rating:
            s += 'Rating: %s' % rating
            nr_votes = self.get('votes')
            if nr_votes:
                s += ' (%s votes)' % nr_votes
            s += '.\n'
        plot = self.get('plot')
        if not plot:
            plot = self.get('plot summary')
            if plot:
                plot = [plot]
        if plot:
            plot = plot[0]
            i = plot.find('::')
            if i != -1:
                plot = plot[:i]
            s += 'Plot: %s' % plot
        return s
