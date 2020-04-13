# Copyright 2007-2019 Davide Alberani <da@erlug.linux.it>
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
This module provides the Character class, used to store information about
a given character.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from copy import deepcopy

from imdb._exceptions import IMDbParserError
from imdb.utils import _Container, analyze_name, build_name, cmpPeople, flatten


class Character(_Container):
    """A Character.

    Every information about a character can be accessed as::

        characterObject['information']

    to get a list of the kind of information stored in a
    Character object, use the keys() method; some useful aliases
    are defined (as "also known as" for the "akas" key);
    see the keys_alias dictionary.
    """
    # The default sets of information retrieved.
    default_info = ('main', 'filmography', 'biography')

    # Aliases for some not-so-intuitive keys.
    keys_alias = {
        'mini biography': 'biography',
        'bio': 'biography',
        'character biography': 'biography',
        'character biographies': 'biography',
        'biographies': 'biography',
        'character bio': 'biography',
        'aka': 'akas',
        'also known as': 'akas',
        'alternate names': 'akas',
        'personal quotes': 'quotes',
        'keys': 'keywords',
        'keyword': 'keywords'
    }

    keys_tomodify_list = ('biography', 'quotes')

    cmpFunct = cmpPeople

    def _init(self, **kwds):
        """Initialize a Character object.

        *characterID* -- the unique identifier for the character.
        *name* -- the name of the Character, if not in the data dictionary.
        *myName* -- the nickname you use for this character.
        *myID* -- your personal id for this character.
        *data* -- a dictionary used to initialize the object.
        *notes* -- notes about the given character.
        *accessSystem* -- a string representing the data access system used.
        *titlesRefs* -- a dictionary with references to movies.
        *namesRefs* -- a dictionary with references to persons.
        *charactersRefs* -- a dictionary with references to characters.
        *modFunct* -- function called returning text fields.
        """
        name = kwds.get('name')
        if name and 'name' not in self.data:
            self.set_name(name)
        self.characterID = kwds.get('characterID', None)
        self.myName = kwds.get('myName', '')

    def _reset(self):
        """Reset the Character object."""
        self.characterID = None
        self.myName = ''

    def set_name(self, name):
        """Set the name of the character."""
        try:
            d = analyze_name(name)
            self.data.update(d)
        except IMDbParserError:
            pass

    def _additional_keys(self):
        """Valid keys to append to the data.keys() list."""
        addkeys = []
        if 'name' in self.data:
            addkeys += ['long imdb name']
        if 'headshot' in self.data:
            addkeys += ['full-size headshot']
        return addkeys

    def _getitem(self, key):
        """Handle special keys."""
        # XXX: can a character have an imdbIndex?
        if 'name' in self.data:
            if key == 'long imdb name':
                return build_name(self.data)
        return None

    def getID(self):
        """Return the characterID."""
        return self.characterID

    def __bool__(self):
        """The Character is "false" if the self.data does not contain a name."""
        # XXX: check the name and the characterID?
        return bool(self.data.get('name'))

    def __contains__(self, item):
        """Return true if this Character was portrayed in the given Movie
        or it was impersonated by the given Person."""
        from .Movie import Movie
        from .Person import Person
        if isinstance(item, Person):
            for m in flatten(self.data, yieldDictKeys=True, scalar=Movie):
                if item.isSame(m.currentRole):
                    return True
        elif isinstance(item, Movie):
            for m in flatten(self.data, yieldDictKeys=True, scalar=Movie):
                if item.isSame(m):
                    return True
        elif isinstance(item, str):
            return item in self.data
        return False

    def isSameName(self, other):
        """Return true if two character have the same name
        and/or characterID."""
        if not isinstance(other, self.__class__):
            return False
        if 'name' in self.data and 'name' in other.data and \
                build_name(self.data, canonical=False) == build_name(other.data, canonical=False):
            return True
        if self.accessSystem == other.accessSystem and \
                self.characterID is not None and \
                self.characterID == other.characterID:
            return True
        return False
    isSameCharacter = isSameName

    def __deepcopy__(self, memo):
        """Return a deep copy of a Character instance."""
        c = Character(name='', characterID=self.characterID,
                      myName=self.myName, myID=self.myID,
                      data=deepcopy(self.data, memo),
                      notes=self.notes, accessSystem=self.accessSystem,
                      titlesRefs=deepcopy(self.titlesRefs, memo),
                      namesRefs=deepcopy(self.namesRefs, memo),
                      charactersRefs=deepcopy(self.charactersRefs, memo))
        c.current_info = list(self.current_info)
        c.set_mod_funct(self.modFunct)
        return c

    def __repr__(self):
        """String representation of a Character object."""
        return '<Character id:%s[%s] name:_%s_>' % (
            self.characterID, self.accessSystem, self.get('name')
        )

    def __str__(self):
        """Simply print the short name."""
        return self.get('name', '')

    def summary(self):
        """Return a string with a pretty-printed summary for the character."""
        if not self:
            return ''
        s = 'Character\n=====\nName: %s\n' % self.get('name', '')
        bio = self.get('biography')
        if bio:
            s += 'Biography: %s\n' % bio[0]
        filmo = self.get('filmography')
        if filmo:
            a_list = [x.get('long imdb canonical title', '') for x in filmo[:5]]
            s += 'Last movies with this character: %s.\n' % '; '.join(a_list)
        return s
