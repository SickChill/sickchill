"""
parser.mobile package (imdb package).

This package provides the IMDbMobileAccessSystem class used to access
IMDb's data for mobile systems.
the imdb.IMDb function will return an instance of this class when
called with the 'accessSystem' argument set to "mobile".

Copyright 2005-2012 Davide Alberani <da@erlug.linux.it>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1335, USA
"""

import re
import logging
from urllib import unquote

from imdb.Movie import Movie
from imdb.utils import analyze_title, analyze_name, canonicalName, \
                        date_and_notes
from imdb._exceptions import IMDbDataAccessError
from imdb.parser.http import IMDbHTTPAccessSystem
from imdb.parser.http.utils import subXMLRefs, subSGMLRefs, build_person, \
                                    build_movie, re_spaces

# XXX NOTE: the first version of this module was heavily based on
#           regular expressions.  This new version replace regexps with
#           find() strings' method calls; despite being less flexible, it
#           seems to be at least as fast and, hopefully, much more
#           lightweight.  Yes: the regexp-based version was too heavyweight
#           for systems with very limited CPU power and memory footprint.
re_spacessub = re_spaces.sub
# Strip html.
re_unhtml = re.compile(r'<.+?>')
re_unhtmlsub = re_unhtml.sub
# imdb person or movie ids.
re_imdbID = re.compile(r'(?<=nm|tt|ch)([0-9]{7})\b')

# movie AKAs.
re_makas = re.compile('(<p class="find-aka">.*?</p>)')

# Remove episode numbers.
re_filmo_episodes = re.compile('<div class="filmo-episodes">.*?</div>',
        re.M | re.I)


def _unHtml(s):
    """Return a string without tags and no multiple spaces."""
    return subSGMLRefs(re_spacessub(' ', re_unhtmlsub('', s)).strip())


_inttype = type(0)

def _getTagsWith(s, cont, toClosure=False, maxRes=None):
    """Return the html tags in the 's' string containing the 'cont'
    string; if toClosure is True, everything between the opening
    tag and the closing tag is returned."""
    lres = []
    bi = s.find(cont)
    if bi != -1:
        btag = s[:bi].rfind('<')
        if btag != -1:
            if not toClosure:
                etag = s[bi+1:].find('>')
                if etag != -1:
                    endidx = bi+2+etag
                    lres.append(s[btag:endidx])
                    if maxRes is not None and len(lres) >= maxRes: return lres
                    lres += _getTagsWith(s[endidx:], cont,
                                        toClosure=toClosure)
            else:
                spaceidx = s[btag:].find(' ')
                if spaceidx != -1:
                    ctag = '</%s>' % s[btag+1:btag+spaceidx]
                    closeidx = s[bi:].find(ctag)
                    if closeidx != -1:
                        endidx = bi+closeidx+len(ctag)
                        lres.append(s[btag:endidx])
                        if maxRes is not None and len(lres) >= maxRes:
                            return lres
                        lres += _getTagsWith(s[endidx:], cont,
                                            toClosure=toClosure)
    return lres


def _findBetween(s, begins, ends, beginindx=0, maxRes=None, lres=None):
    """Return the list of strings from the 's' string which are included
    between the 'begins' and 'ends' strings."""
    if lres is None:
        lres = []
    bi = s.find(begins, beginindx)
    if bi != -1:
        lbegins = len(begins)
        if isinstance(ends, (list, tuple)):
            eset = [s.find(end, bi+lbegins) for end in ends]
            eset[:] = [x for x in eset if x != -1]
            if not eset: ei = -1
            else: ei = min(eset)
        else:
            ei = s.find(ends, bi+lbegins)
        if ei != -1:
            match = s[bi+lbegins:ei]
            lres.append(match)
            if maxRes is not None and len(lres) >= maxRes: return lres
            _findBetween(s, begins, ends, beginindx=ei, maxRes=maxRes,
                        lres=lres)
    return lres


class IMDbMobileAccessSystem(IMDbHTTPAccessSystem):
    """The class used to access IMDb's data through the web for
    mobile terminals."""

    accessSystem = 'mobile'
    _mobile_logger = logging.getLogger('imdbpy.parser.mobile')

    def __init__(self, isThin=0, *arguments, **keywords):
        self.accessSystem = 'mobile'
        IMDbHTTPAccessSystem.__init__(self, isThin, *arguments, **keywords)

    def _clean_html(self, html):
        """Normalize the retrieve html."""
        html = re_spaces.sub(' ', html)
        # Remove silly &nbsp;&raquo; chars.
        html = html.replace('&nbsp;&raquo;', '')
        return subXMLRefs(html)

    def _mretrieve(self, url, size=-1):
        """Retrieve an html page and normalize it."""
        cont = self._retrieve(url, size=size)
        return self._clean_html(cont)

    def _getPersons(self, s, sep='<br/>'):
        """Return a list of Person objects, from the string s; items
        are assumed to be separated by the sep string."""
        names = s.split(sep)
        pl = []
        plappend = pl.append
        counter = 1
        for name in names:
            pid = re_imdbID.findall(name)
            if not pid: continue
            characters = _getTagsWith(name, 'class="char"',
                                        toClosure=True, maxRes=1)
            chpids = []
            if characters:
                for ch in characters[0].split(' / '):
                    chid = re_imdbID.findall(ch)
                    if not chid:
                        chpids.append(None)
                    else:
                        chpids.append(chid[-1])
            if not chpids:
                chpids = None
            elif len(chpids) == 1:
                chpids = chpids[0]
            name = _unHtml(name)
            # Catch unclosed tags.
            gt_indx = name.find('>')
            if gt_indx != -1:
                name = name[gt_indx+1:].lstrip()
            if not name: continue
            if name.endswith('...'):
                name = name[:-3]
            p = build_person(name, personID=str(pid[0]), billingPos=counter,
                            modFunct=self._defModFunct, roleID=chpids,
                            accessSystem=self.accessSystem)
            plappend(p)
            counter += 1
        return pl

    def _search_movie(self, title, results):
        ##params = urllib.urlencode({'tt': 'on','mx': str(results),'q': title})
        ##params = 'q=%s&tt=on&mx=%s' % (urllib.quote_plus(title), str(results))
        ##cont = self._mretrieve(imdbURL_search % params)
        cont = subXMLRefs(self._get_search_content('tt', title, results))
        title = _findBetween(cont, '<title>', '</title>', maxRes=1)
        res = []
        if not title:
            self._mobile_logger.error('no title tag searching for movie %s',
                                    title)
            return res
        tl = title[0].lower()
        if not tl.startswith('find - imdb'):
            # a direct hit!
            title = _unHtml(title[0])
            mid = None
            midtag = _getTagsWith(cont, 'rel="canonical"', maxRes=1)
            if midtag:
                mid = _findBetween(midtag[0], '/title/tt', '/', maxRes=1)
            if not (mid and title):
                self._mobile_logger.error('no direct hit title/movieID for' \
                                            ' title %s', title)
                return res
            if cont.find('<span class="tv-extra">TV mini-series</span>') != -1:
                title += ' (mini)'
            res[:] = [(str(mid[0]), analyze_title(title))]
        else:
            # XXX: this results*3 prevents some recursion errors, but...
            #      it's not exactly understandable (i.e.: why 'results' is
            #      not enough to get all the results?)
            lis = _findBetween(cont, 'td class="result_text">', '</td>',
                                maxRes=results*3)
            for li in lis:
                akas = re_makas.findall(li)
                for idx, aka in enumerate(akas):
                    aka = aka.replace('" - ', '::', 1)
                    aka = _unHtml(aka)
                    if aka.startswith('aka "'):
                        aka = aka[5:].strip()
                    if aka[-1] == '"':
                        aka = aka[:-1]
                    akas[idx] = aka
                imdbid = re_imdbID.findall(li)
                li = re_makas.sub('', li)
                mtitle = _unHtml(li)
                if not (imdbid and mtitle):
                    self._mobile_logger.debug('no title/movieID parsing' \
                                            ' %s searching for title %s', li,
                                            title)
                    continue
                mtitle = mtitle.replace('(TV mini-series)', '(mini)')
                resd = analyze_title(mtitle)
                if akas:
                    resd['akas'] = akas
                res.append((str(imdbid[0]), resd))
        return res

    def get_movie_main(self, movieID):
        cont = self._mretrieve(self.urls['movie_main'] % movieID + 'maindetails')
        title = _findBetween(cont, '<title>', '</title>', maxRes=1)
        if not title:
            raise IMDbDataAccessError('unable to get movieID "%s"' % movieID)
        title = _unHtml(title[0])
        if title.endswith(' - IMDb'):
            title = title[:-7]
        if cont.find('<span class="tv-extra">TV mini-series</span>') != -1:
            title += ' (mini)'
        d = analyze_title(title)
        kind = d.get('kind')
        tv_series = _findBetween(cont, 'TV Series:</h5>', '</a>', maxRes=1)
        if tv_series: mid = re_imdbID.findall(tv_series[0])
        else: mid = None
        if tv_series and mid:
            s_title = _unHtml(tv_series[0])
            s_data = analyze_title(s_title)
            m = Movie(movieID=str(mid[0]), data=s_data,
                        accessSystem=self.accessSystem,
                        modFunct=self._defModFunct)
            d['kind'] = kind = u'episode'
            d['episode of'] = m
        if kind in ('tv series', 'tv mini series'):
            years = _findBetween(cont, '<h1>', '</h1>', maxRes=1)
            if years:
                years[:] = _findBetween(years[0], 'TV series', '</span>',
                                        maxRes=1)
                if years:
                    d['series years'] = years[0].strip()
        air_date = _findBetween(cont, 'Original Air Date:</h5>', '</div>',
                                maxRes=1)
        if air_date:
            air_date = air_date[0]
            vi = air_date.find('(')
            if vi != -1:
                date = _unHtml(air_date[:vi]).strip()
                if date != '????':
                    d['original air date'] = date
                air_date = air_date[vi:]
                season = _findBetween(air_date, 'Season', ',', maxRes=1)
                if season:
                    season = season[0].strip()
                    try: season = int(season)
                    except: pass
                    if season or type(season) is _inttype:
                        d['season'] = season
                episode = _findBetween(air_date, 'Episode', ')', maxRes=1)
                if episode:
                    episode = episode[0].strip()
                    try: episode = int(episode)
                    except: pass
                    if episode or type(season) is _inttype:
                        d['episode'] = episode
        direct = _findBetween(cont, '<h5>Director', ('</div>', '<br/> <br/>'),
                                maxRes=1)
        if direct:
            direct = direct[0]
            h5idx = direct.find('/h5>')
            if h5idx != -1:
                direct = direct[h5idx+4:]
            direct = self._getPersons(direct)
            if direct: d['director'] = direct
        if kind in ('tv series', 'tv mini series', 'episode'):
            if kind != 'episode':
                seasons = _findBetween(cont, 'Seasons:</h5>', '</div>',
                                        maxRes=1)
                if seasons:
                    d['number of seasons'] = seasons[0].count('|') + 1
            creator = _findBetween(cont, 'Created by</h5>', ('class="tn15more"',
                                                            '</div>',
                                                            '<br/> <br/>'),
                                                            maxRes=1)
            if not creator:
                # They change 'Created by' to 'Creator' and viceversa
                # from time to time...
                # XXX: is 'Creators' also used?
                creator = _findBetween(cont, 'Creator:</h5>',
                                        ('class="tn15more"', '</div>',
                                        '<br/> <br/>'), maxRes=1)
            if creator:
                creator = creator[0]
                if creator.find('tn15more'): creator = '%s>' % creator
                creator = self._getPersons(creator)
                if creator: d['creator'] = creator
        writers = _findBetween(cont, '<h5>Writer', ('</div>', '<br/> <br/>'),
                                maxRes=1)
        if writers:
            writers = writers[0]
            h5idx = writers.find('/h5>')
            if h5idx != -1:
                writers = writers[h5idx+4:]
            writers = self._getPersons(writers)
            if writers: d['writer'] = writers
        cvurl = _getTagsWith(cont, 'name="poster"', toClosure=True, maxRes=1)
        if cvurl:
            cvurl = _findBetween(cvurl[0], 'src="', '"', maxRes=1)
            if cvurl: d['cover url'] = cvurl[0]
        genres = _findBetween(cont, 'href="/genre/', '"')
        if genres:
            d['genres'] = list(set(genres))
        ur = _findBetween(cont, 'id="star-bar-user-rate">', '</div>',
                            maxRes=1)
        if ur:
            rat = _findBetween(ur[0], '<b>', '</b>', maxRes=1)
            if rat:
                if rat:
                    d['rating'] = rat[0].strip()
                else:
                    self._mobile_logger.warn('wrong rating: %s', rat)
            vi = ur[0].rfind('href="ratings"')
            if vi != -1 and ur[0][vi+10:].find('await') == -1:
                try:
                    votes = _findBetween(ur[0][vi:], "title='",
                                        " IMDb", maxRes=1)
                    votes = int(votes[0].replace(',', ''))
                    d['votes'] = votes
                except (ValueError, IndexError):
                    self._mobile_logger.warn('wrong votes: %s', ur)
        top250 = _findBetween(cont, 'href="/chart/top?', '</a>', maxRes=1)
        if top250:
            fn = top250[0].rfind('#')
            if fn != -1:
                try:
                    td = int(top250[0][fn+1:])
                    d['top 250 rank'] = td
                except ValueError:
                    self._mobile_logger.warn('wrong top250: %s', top250)
        castdata = _findBetween(cont, 'Cast overview', '</table>', maxRes=1)
        if not castdata:
            castdata = _findBetween(cont, 'Credited cast', '</table>', maxRes=1)
        if not castdata:
            castdata = _findBetween(cont, 'Complete credited cast', '</table>',
                                    maxRes=1)
        if not castdata:
            castdata = _findBetween(cont, 'Series Cast Summary', '</table>',
                                    maxRes=1)
        if not castdata:
            castdata = _findBetween(cont, 'Episode Credited cast', '</table>',
                                    maxRes=1)
        if castdata:
            castdata = castdata[0]
            # Reintegrate the fist tag.
            fl = castdata.find('href=')
            if fl != -1: castdata = '<a ' + castdata[fl:]
            # Exclude the 'rest of cast listed alphabetically' row.
            smib = castdata.find('<tr><td align="center" colspan="4"><small>')
            if smib != -1:
                smie = castdata.rfind('</small></td></tr>')
                if smie != -1:
                    castdata = castdata[:smib].strip() + \
                                castdata[smie+18:].strip()
            castdata = castdata.replace('/tr> <tr', '/tr><tr')
            cast = self._getPersons(castdata, sep='</tr><tr')
            if cast: d['cast'] = cast
        akas = _findBetween(cont, 'Also Known As:</h5>', '</div>', maxRes=1)
        if akas:
            # For some reason, here <br> is still used in place of <br/>.
            akas[:] = [x for x in akas[0].split('<br>') if x.strip()]
            akas = [_unHtml(x).replace('" - ','::', 1).lstrip('"').strip()
                    for x in akas]
            if 'See more' in akas: akas.remove('See more')
            akas[:] = [x for x in akas if x]
            if akas:
                d['akas'] = akas
        mpaa = _findBetween(cont, 'MPAA</a>:', '</div>', maxRes=1)
        if mpaa: d['mpaa'] = _unHtml(mpaa[0])
        runtimes = _findBetween(cont, 'Runtime:</h5>', '</div>', maxRes=1)
        if runtimes:
            runtimes = runtimes[0]
            runtimes = [x.strip().replace(' min', '').replace(' (', '::(', 1)
                    for x in runtimes.split('|')]
            d['runtimes'] = [_unHtml(x).strip() for x in runtimes]
        if kind == 'episode':
            # number of episodes.
            epsn = _findBetween(cont, 'title="Full Episode List">', '</a>',
                                maxRes=1)
            if epsn:
                epsn = epsn[0].replace(' Episodes', '').strip()
                if epsn:
                    try:
                        epsn = int(epsn)
                    except:
                        self._mobile_logger.warn('wrong episodes #: %s', epsn)
                    d['number of episodes'] = epsn
        country = _findBetween(cont, 'Country:</h5>', '</div>', maxRes=1)
        if country:
            country[:] = country[0].split(' | ')
            country[:] = ['<a %s' % x for x in country if x]
            country[:] = [_unHtml(x.replace(' <i>', '::')) for x in country]
            if country: d['countries'] = country
        lang = _findBetween(cont, 'Language:</h5>', '</div>', maxRes=1)
        if lang:
            lang[:] = lang[0].split(' | ')
            lang[:] = ['<a %s' % x for x in lang if x]
            lang[:] = [_unHtml(x.replace(' <i>', '::')) for x in lang]
            if lang: d['languages'] = lang
        col = _findBetween(cont, '"/search/title?colors=', '</div>')
        if col:
            col[:] = col[0].split(' | ')
            col[:] = ['<a %s' % x for x in col if x]
            col[:] = [_unHtml(x.replace(' <i>', '::')) for x in col]
            if col: d['color info'] = col
        sm = _findBetween(cont, '/search/title?sound_mixes=', '</div>',
                            maxRes=1)
        if sm:
            sm[:] = sm[0].split(' | ')
            sm[:] = ['<a %s' % x for x in sm if x]
            sm[:] = [_unHtml(x.replace(' <i>', '::')) for x in sm]
            if sm: d['sound mix'] = sm
        cert = _findBetween(cont, 'Certification:</h5>', '</div>', maxRes=1)
        if cert:
            cert[:] = cert[0].split(' | ')
            cert[:] = [_unHtml(x.replace(' <i>', '::')) for x in cert]
            if cert: d['certificates'] = cert
        plotoutline = _findBetween(cont, 'Plot:</h5>', ['<a ', '</div>'],
                                    maxRes=1)
        if plotoutline:
            plotoutline = plotoutline[0].strip()
            plotoutline = plotoutline.rstrip('|').rstrip()
            if plotoutline: d['plot outline'] = _unHtml(plotoutline)
        aratio = _findBetween(cont, 'Aspect Ratio:</h5>', ['<a ', '</div>'],
                            maxRes=1)
        if aratio:
            aratio = aratio[0].strip().replace(' (', '::(', 1)
            if aratio:
                d['aspect ratio'] = _unHtml(aratio)
        return {'data': d}

    def get_movie_plot(self, movieID):
        cont = self._mretrieve(self.urls['movie_main'] % movieID + 'plotsummary')
        plot = _findBetween(cont, '<p class="plotpar">', '</p>')
        plot[:] = [_unHtml(x) for x in plot]
        for i in xrange(len(plot)):
            p = plot[i]
            wbyidx = p.rfind(' Written by ')
            if wbyidx != -1:
                plot[i] = '%s::%s' % \
                        (p[:wbyidx].rstrip(),
                    p[wbyidx+12:].rstrip().replace('{','<').replace('}','>'))
        if plot: return {'data': {'plot': plot}}
        return {'data': {}}

    def _search_person(self, name, results):
        ##params = urllib.urlencode({'nm': 'on', 'mx': str(results), 'q': name})
        ##params = 'q=%s&nm=on&mx=%s' % (urllib.quote_plus(name), str(results))
        ##cont = self._mretrieve(imdbURL_search % params)
        cont = subXMLRefs(self._get_search_content('nm', name, results))
        name = _findBetween(cont, '<title>', '</title>', maxRes=1)
        res = []
        if not name:
            self._mobile_logger.warn('no title tag searching for name %s', name)
            return res
        nl = name[0].lower()
        if not nl.startswith('find - imdb'):
            # a direct hit!
            name = _unHtml(name[0])
            name = name.replace('- Filmography by type' , '').strip()
            pid = None
            pidtag = _getTagsWith(cont, 'rel="canonical"', maxRes=1)
            if pidtag:
                pid = _findBetween(pidtag[0], '/name/nm', '/', maxRes=1)
            if not (pid and name):
                self._mobile_logger.error('no direct hit name/personID for' \
                                            ' name %s', name)
                return res
            res[:] = [(str(pid[0]), analyze_name(name, canonical=1))]
        else:
            lis = _findBetween(cont, 'td class="result_text">', '</td>',
                                maxRes=results*3)
            for li in lis:
                akas = _findBetween(li, '<em>"', '"</em>')
                for sep in ['<small', '<br> aka', '<br> birth name']:
                    sepIdx = li.find(sep)
                    if sepIdx != -1:
                        li = li[:sepIdx]
                pid = re_imdbID.findall(li)
                pname = _unHtml(li)
                if not (pid and pname):
                    self._mobile_logger.debug('no name/personID parsing' \
                                            ' %s searching for name %s', li,
                                            name)
                    continue
                resd = analyze_name(pname, canonical=1)
                if akas:
                    resd['akas'] = akas
                res.append((str(pid[0]), resd))
        return res

    def get_person_main(self, personID, _parseChr=False):
        if not _parseChr:
            url = self.urls['person_main'] % personID + 'maindetails'
        else:
            url = self.urls['character_main'] % personID
        s = self._mretrieve(url)
        r = {}
        name = _findBetween(s, '<title>', '</title>', maxRes=1)
        if not name:
            if _parseChr: w = 'characterID'
            else: w = 'personID'
            raise IMDbDataAccessError('unable to get %s "%s"' % (w, personID))
        name = _unHtml(name[0].replace(' - IMDb', ''))
        if _parseChr:
            name = name.replace('(Character)', '').strip()
            name = name.replace('- Filmography by type', '').strip()
        else:
            name = name.replace('- Filmography by', '').strip()
        r = analyze_name(name, canonical=not _parseChr)
        for dKind in ('Born', 'Died'):
            date = _findBetween(s, '%s:</h4>' % dKind.capitalize(),
                                ('<div class', '</div>', '<br/><br/>'), maxRes=1)
            if date:
                date = _unHtml(date[0])
                if date:
                    #date, notes = date_and_notes(date)
                    # TODO: fix to handle real names.
                    date_notes = date.split(' in ', 1)
                    notes = u''
                    date = date_notes[0]
                    if len(date_notes) == 2:
                        notes = date_notes[1]
                    dtitle = 'birth'
                    if dKind == 'Died':
                        dtitle = 'death'
                    if date:
                        r['%s date' % dtitle] = date
                    if notes:
                        r['%s notes' % dtitle] = notes
        akas = _findBetween(s, 'Alternate Names:</h4>', ('</div>',
                            '<br/><br/>'), maxRes=1)
        if akas:
            akas = akas[0]
            if akas:
                akas = _unHtml(akas)
            if akas.find(' | ') != -1:
                akas = akas.split(' | ')
            else:
                akas = akas.split(' / ')
            if akas: r['akas'] = filter(None, [x.strip() for x in akas])
        hs = _findBetween(s, "rel='image_src'", '>', maxRes=1)
        if not hs:
            hs = _findBetween(s, 'rel="image_src"', '>', maxRes=1)
        if not hs:
            hs = _findBetween(s, '<a name="headshot"', '</a>', maxRes=1)
        if hs:
            hsl = _findBetween(hs[0], "href='", "'", maxRes=1)
            if not hsl:
                hsl = _findBetween(hs[0], 'href="', '"', maxRes=1)
            if hsl and 'imdb-share-logo' not in hsl[0]:
                r['headshot'] = hsl[0]
        # Build a list of tuples such [('hrefLink', 'section name')]
        workkind = _findBetween(s, 'id="jumpto_', '</a>')
        ws = []
        for work in workkind:
            sep = '" >'
            if '">' in work:
                sep = '">'
            wsplit = work.split(sep, 1)
            if len(wsplit) == 2:
                sect = wsplit[0]
                if '"' in sect:
                    sect = sect[:sect.find('"')]
                ws.append((sect, wsplit[1].lower()))
        # XXX: I think "guest appearances" are gone.
        if s.find('<a href="#guest-appearances"') != -1:
            ws.append(('guest-appearances', 'notable tv guest appearances'))
        #if _parseChr:
        #    ws.append(('filmography', 'filmography'))
        for sect, sectName in ws:
            raws = u''
            if sectName == 'self':
                sect = 'Self'
            # Everything between the current section link and the end
            # of the <ol> tag.
            if _parseChr and sect == 'filmography':
                inisect = s.find('<div class="filmo">')
            else:
                inisect = s.find('<a name="%s' % sect)
            if inisect != -1:
                endsect = s[inisect:].find('<div id="filmo-head-')
                if endsect == -1:
                    endsect = s[inisect:].find('<div class="article"')
                if endsect != -1: raws = s[inisect:inisect+endsect]
            #if not raws: continue
            mlist = _findBetween(raws, '<div class="filmo-row',
                    ('<div class="clear"/>',))
            for m in mlist:
                fCB = m.find('>')
                if fCB != -1:
                    m = m[fCB+1:].lstrip()
                m = re_filmo_episodes.sub('', m)
                # For every movie in the current section.
                movieID = re_imdbID.findall(m)
                if not movieID:
                    self._mobile_logger.debug('no movieID in %s', m)
                    continue
                m = m.replace('<br/>', ' .... ', 1)
                if not _parseChr:
                    chrIndx = m.find(' .... ')
                else:
                    chrIndx = m.find(' Played by ')
                chids = []
                if chrIndx != -1:
                    chrtxt = m[chrIndx+6:]
                    if _parseChr:
                        chrtxt = chrtxt[5:]
                    for ch in chrtxt.split(' / '):
                        chid = re_imdbID.findall(ch)
                        if not chid:
                            chids.append(None)
                        else:
                            chids.append(chid[-1])
                if not chids:
                    chids = None
                elif len(chids) == 1:
                    chids = chids[0]
                movieID = str(movieID[0])
                # Search the status.
                stidx = m.find('<i>')
                status = u''
                if stidx != -1:
                    stendidx = m.rfind('</i>')
                    if stendidx != -1:
                        status = _unHtml(m[stidx+3:stendidx])
                        m = m.replace(m[stidx+3:stendidx], '')
                year = _findBetween(m, 'year_column">', '</span>', maxRes=1)
                if year:
                    year = year[0]
                    m = m.replace('<span class="year_column">%s</span>' % year,
                            '')
                else:
                    year = None
                m = _unHtml(m)
                if not m:
                    self._mobile_logger.warn('no title for movieID %s', movieID)
                    continue
                movie = build_movie(m, movieID=movieID, status=status,
                                    roleID=chids, modFunct=self._defModFunct,
                                    accessSystem=self.accessSystem,
                                    _parsingCharacter=_parseChr, year=year)
                sectName = sectName.split(':')[0]
                r.setdefault(sectName, []).append(movie)
        # If available, take the always correct name from a form.
        itag = _getTagsWith(s, 'NAME="primary"', maxRes=1)
        if not itag:
            itag = _getTagsWith(s, 'name="primary"', maxRes=1)
        if itag:
            vtag = _findBetween(itag[0], 'VALUE="', ('"', '>'), maxRes=1)
            if not vtag:
                vtag = _findBetween(itag[0], 'value="', ('"', '>'), maxRes=1)
            if vtag:
                try:
                    vtag = unquote(str(vtag[0]))
                    vtag = unicode(vtag, 'latin_1')
                    r.update(analyze_name(vtag))
                except UnicodeEncodeError:
                    pass
        return {'data': r, 'info sets': ('main', 'filmography')}

    def get_person_biography(self, personID):
        cont = self._mretrieve(self.urls['person_main'] % personID + 'bio')
        d = {}
        spouses = _findBetween(cont, 'Spouse</h5>', ('</table>', '</dd>'),
                                maxRes=1)
        if spouses:
            sl = []
            for spouse in spouses[0].split('</tr>'):
                if spouse.count('</td>') > 1:
                    spouse = spouse.replace('</td>', '::</td>', 1)
                spouse = _unHtml(spouse)
                spouse = spouse.replace(':: ', '::').strip()
                if spouse: sl.append(spouse)
            if sl: d['spouse'] = sl
        nnames = _findBetween(cont, '<h5>Nickname</h5>', ('<br/> <br/>','<h5>'),
                                maxRes=1)
        if nnames:
            nnames = nnames[0]
            if nnames:
                nnames = [x.strip().replace(' (', '::(', 1)
                            for x in nnames.split('<br/>')]
                if nnames:
                    d['nick names'] = nnames
        misc_sects = _findBetween(cont, '<h5>', '<br/>')
        misc_sects[:] = [x.split('</h5>') for x in misc_sects]
        misc_sects[:] = [x for x in misc_sects if len(x) == 2]
        for sect, data in misc_sects:
            sect = sect.lower().replace(':', '').strip()
            if d.has_key(sect) and sect != 'mini biography': continue
            elif sect in ('spouse', 'nickname'): continue
            if sect == 'salary': sect = 'salary history'
            elif sect == 'where are they now': sect = 'where now'
            elif sect == 'personal quotes': sect = 'quotes'
            data = data.replace('</p><p>', '::')
            data = data.replace('<br><br>', ' ') # for multi-paragraphs 'bio'
            data = data.replace('</td> <td valign="top">', '@@@@')
            data = data.replace('</td> </tr>', '::')
            data = _unHtml(data)
            data = [x.strip() for x in data.split('::')]
            data[:] = [x.replace('@@@@', '::') for x in data if x]
            if sect == 'height' and data: data = data[0]
            elif sect == 'birth name': data = canonicalName(data[0])
            elif sect == 'date of birth':
                date, notes = date_and_notes(data[0])
                if date:
                    d['birth date'] = date
                if notes:
                    d['birth notes'] = notes
                continue
            elif sect == 'date of death':
                date, notes = date_and_notes(data[0])
                if date:
                    d['death date'] = date
                if notes:
                    d['death notes'] = notes
                continue
            elif sect == 'mini biography':
                ndata = []
                for bio in data:
                    byidx = bio.rfind('IMDb Mini Biography By')
                    if byidx != -1:
                        bioAuth = bio[:byidx].rstrip()
                    else:
                        bioAuth = 'Anonymous'
                    bio = u'%s::%s' % (bioAuth, bio[byidx+23:].lstrip())
                    ndata.append(bio)
                data[:] = ndata
                if 'mini biography' in d:
                    d['mini biography'].append(ndata[0])
                    continue
            d[sect] = data
        return {'data': d}

    def _search_character(self, name, results):
        cont = subXMLRefs(self._get_search_content('ch', name, results))
        name = _findBetween(cont, '<title>', '</title>', maxRes=1)
        res = []
        if not name:
            self._mobile_logger.error('no title tag searching character %s',
                                    name)
            return res
        nl = name[0].lower()
        if not nl.startswith('find - imdb'):
            # a direct hit!
            name = _unHtml(name[0]).replace('(Character)', '').strip()
            pid = None
            pidtag = _getTagsWith(cont, 'rel="canonical"', maxRes=1)
            if pidtag:
                pid = _findBetween(pidtag[0], '/character/ch', '/', maxRes=1)
            if not (pid and name):
                self._mobile_logger.error('no direct hit name/characterID for' \
                                            ' character %s', name)
                return res
            res[:] = [(str(pid[0]), analyze_name(name))]
        else:
            lis = _findBetween(cont, '<td class="result_text"',
                                ['<small', '</td>', '<br'])
            for li in lis:
                li = '<%s' % li
                pid = re_imdbID.findall(li)
                pname = _unHtml(li)
                if not (pid and pname):
                    self._mobile_logger.debug('no name/characterID' \
                                            ' parsing %s searching for' \
                                            ' character %s', li, name)
                    continue
                res.append((str(pid[0]), analyze_name(pname)))
        return res

    def get_character_main(self, characterID):
        return self.get_person_main(characterID, _parseChr=True)

    def get_character_biography(self, characterID):
        cont = self._mretrieve(self.urls['character_main'] % characterID + 'bio')
        d = {}
        intro = _findBetween(cont, '<div class="display">',
                            ('<span>', '<h4>'), maxRes=1)
        if intro:
            intro = _unHtml(intro[0]).strip()
            if intro:
                d['introduction'] = intro
        tocidx = cont.find('<table id="toc..')
        if tocidx != -1:
            cont = cont[tocidx:]
        bios = _findBetween(cont, '<h4>', ('<h4>', '</div>'))
        if bios:
            for bio in bios:
                bio = bio.replace('</h4>', '::')
                bio = bio.replace('\n', ' ')
                bio = bio.replace('<br>', '\n')
                bio = bio.replace('<br/>', '\n')
                bio = subSGMLRefs(re_unhtmlsub('', bio).strip())
                bio = bio.replace(' ::', '::').replace(':: ', '::')
                bio = bio.replace('::', ': ', 1)
                if bio:
                    d.setdefault('biography', []).append(bio)
        return {'data': d}


