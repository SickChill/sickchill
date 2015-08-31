#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# GuessIt - A library for guessing information from filenames
# Copyright (c) 2013 Nicolas Wack <wackou@gmail.com>
# Copyright (c) 2013 Rémi Alvergnat <toilal.dev@gmail.com>
#
# GuessIt is free software; you can redistribute it and/or modify it under
# the terms of the Lesser GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# GuessIt is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# Lesser GNU General Public License for more details.
#
# You should have received a copy of the Lesser GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import, division, print_function, unicode_literals
from collections import defaultdict
import logging
import os

from guessit import PY2, u, guess_file_info
from guessit.options import get_opts
from guessit.__version__ import __version__


def guess_file(filename, info='filename', options=None, **kwargs):
    options = options or {}
    filename = u(filename)

    if not options.get('yaml') and not options.get('show_property'):
        print('For:', filename)
    guess = guess_file_info(filename, info, options, **kwargs)

    if not options.get('unidentified'):
        try:
            del guess['unidentified']
        except KeyError:
            pass

    if options.get('show_property'):
        print(guess.get(options.get('show_property'), ''))
        return

    if options.get('yaml'):
        import yaml
        for k, v in guess.items():
            if isinstance(v, list) and len(v) == 1:
                guess[k] = v[0]
        ystr = yaml.safe_dump({filename: dict(guess)}, default_flow_style=False, allow_unicode=True)
        i = 0
        for yline in ystr.splitlines():
            if i == 0:
                print("? " + yline[:-1])
            elif i == 1:
                print(":" + yline[1:])
            else:
                print(yline)
            i += 1
        return
    print('GuessIt found:', guess.nice_string(options.get('advanced')))


def _supported_properties():
    all_properties = defaultdict(list)
    transformers_properties = []

    from guessit.plugins import transformers
    for transformer in transformers.all_transformers():
        supported_properties = transformer.supported_properties()
        transformers_properties.append((transformer, supported_properties))

        if isinstance(supported_properties, dict):
            for property_name, possible_values in supported_properties.items():
                all_properties[property_name].extend(possible_values)
        else:
            for property_name in supported_properties:
                all_properties[property_name] # just make sure it exists

    return all_properties, transformers_properties


def display_transformers():
    print('GuessIt transformers:')
    _, transformers_properties = _supported_properties()
    for transformer, _ in transformers_properties:
        print('[@] %s (%s)' % (transformer.name, transformer.priority))


def display_properties(options):
    values = options.values
    transformers = options.transformers
    name_only = options.name_only

    print('GuessIt properties:')
    all_properties, transformers_properties = _supported_properties()
    if name_only:
        # the 'container' property does not apply when using the --name-only
        # option
        del all_properties['container']

    if transformers:
        for transformer, properties_list in transformers_properties:
            print('[@] %s (%s)' % (transformer.name, transformer.priority))
            for property_name in properties_list:
                property_values = all_properties.get(property_name)
                print('  [+] %s' % (property_name,))
                if property_values and values:
                    _display_property_values(property_name, indent=4)
    else:
        properties_list = sorted(all_properties.keys())
        for property_name in properties_list:
            property_values = all_properties.get(property_name)
            print('  [+] %s' % (property_name,))
            if property_values and values:
                _display_property_values(property_name, indent=4)


def _display_property_values(property_name, indent=2):
    all_properties, _ = _supported_properties()
    property_values = all_properties.get(property_name)
    for property_value in property_values:
        print(indent * ' ' + '[!] %s' % (property_value,))


def run_demo(episodes=True, movies=True, options=None):
    # NOTE: tests should not be added here but rather in the tests/ folder
    #       this is just intended as a quick example
    if episodes:
        testeps = ['Series/Californication/Season 2/Californication.2x05.Vaginatown.HDTV.XviD-0TV.[tvu.org.ru].avi',
                   'Series/dexter/Dexter.5x02.Hello,.Bandit.ENG.-.sub.FR.HDTV.XviD-AlFleNi-TeaM.[tvu.org.ru].avi',
                   'Series/Treme/Treme.1x03.Right.Place,.Wrong.Time.HDTV.XviD-NoTV.[tvu.org.ru].avi',
                   'Series/Duckman/Duckman - 101 (01) - 20021107 - I, Duckman.avi',
                   'Series/Duckman/Duckman - S1E13 Joking The Chicken (unedited).avi',
                   'Series/Simpsons/The_simpsons_s13e18_-_i_am_furious_yellow.mpg',
                   'Series/Simpsons/Saison 12 Français/Simpsons,.The.12x08.A.Bas.Le.Sergent.Skinner.FR.[tvu.org.ru].avi',
                   'Series/Dr._Slump_-_002_DVB-Rip_Catalan_by_kelf.avi',
                   'Series/Kaamelott/Kaamelott - Livre V - Second Volet - HD 704x396 Xvid 2 pass - Son 5.1 - TntRip by Slurm.avi']

        for f in testeps:
            print('-' * 80)
            guess_file(f, options=options, type='episode')

    if movies:
        testmovies = ['Movies/Fear and Loathing in Las Vegas (1998)/Fear.and.Loathing.in.Las.Vegas.720p.HDDVD.DTS.x264-ESiR.mkv',
                      'Movies/El Dia de la Bestia (1995)/El.dia.de.la.bestia.DVDrip.Spanish.DivX.by.Artik[SEDG].avi',
                      'Movies/Blade Runner (1982)/Blade.Runner.(1982).(Director\'s.Cut).CD1.DVDRip.XviD.AC3-WAF.avi',
                      'Movies/Dark City (1998)/Dark.City.(1998).DC.BDRip.720p.DTS.X264-CHD.mkv',
                      'Movies/Sin City (BluRay) (2005)/Sin.City.2005.BDRip.720p.x264.AC3-SEPTiC.mkv',
                      'Movies/Borat (2006)/Borat.(2006).R5.PROPER.REPACK.DVDRip.XviD-PUKKA.avi',
                      '[XCT].Le.Prestige.(The.Prestige).DVDRip.[x264.HP.He-Aac.{Fr-Eng}.St{Fr-Eng}.Chaps].mkv',
                      'Battle Royale (2000)/Battle.Royale.(Batoru.Rowaiaru).(2000).(Special.Edition).CD1of2.DVDRiP.XviD-[ZeaL].avi',
                      'Movies/Brazil (1985)/Brazil_Criterion_Edition_(1985).CD2.English.srt',
                      'Movies/Persepolis (2007)/[XCT] Persepolis [H264+Aac-128(Fr-Eng)+ST(Fr-Eng)+Ind].mkv',
                      'Movies/Toy Story (1995)/Toy Story [HDTV 720p English-Spanish].mkv',
                      'Movies/Pirates of the Caribbean: The Curse of the Black Pearl (2003)/Pirates.Of.The.Carribean.DC.2003.iNT.DVDRip.XviD.AC3-NDRT.CD1.avi',
                      'Movies/Office Space (1999)/Office.Space.[Dual-DVDRip].[Spanish-English].[XviD-AC3-AC3].[by.Oswald].avi',
                      'Movies/The NeverEnding Story (1984)/The.NeverEnding.Story.1.1984.DVDRip.AC3.Xvid-Monteque.avi',
                      'Movies/Juno (2007)/Juno KLAXXON.avi',
                      'Movies/Chat noir, chat blanc (1998)/Chat noir, Chat blanc - Emir Kusturica (VO - VF - sub FR - Chapters).mkv',
                      'Movies/Wild Zero (2000)/Wild.Zero.DVDivX-EPiC.srt',
                      'Movies/El Bosque Animado (1987)/El.Bosque.Animado.[Jose.Luis.Cuerda.1987].[Xvid-Dvdrip-720x432].avi',
                      'testsmewt_bugs/movies/Baraka_Edition_Collector.avi'
                      ]

        for f in testmovies:
            print('-' * 80)
            guess_file(f, options=options, type='movie')


def submit_bug(filename, options):
    import requests  # only import when needed
    from requests.exceptions import RequestException

    try:
        opts = dict((k, v) for k, v in options.__dict__.items()
                    if v and k != 'submit_bug')

        r = requests.post('http://guessit.io/bugs', {'filename': filename,
                                                         'version': __version__,
                                                         'options': str(opts)})
        if r.status_code == 200:
            print('Successfully submitted file: %s' % r.text)
        else:
            print('Could not submit bug at the moment, please try again later: %s %s' % (r.status_code, r.reason))

    except RequestException as e:
        print('Could not submit bug at the moment, please try again later: %s' % e)


def main(args=None, setup_logging=True):
    if setup_logging:
        from guessit import slogging
        slogging.setup_logging()

    if PY2:  # pragma: no cover
        import codecs
        import locale
        import sys

        # see http://bugs.python.org/issue2128
        if os.name == 'nt':
            for i, a in enumerate(sys.argv):
                sys.argv[i] = a.decode(locale.getpreferredencoding())

        # see https://github.com/wackou/guessit/issues/43
        # and http://stackoverflow.com/questions/4545661/unicodedecodeerror-when-redirecting-to-file
        # Wrap sys.stdout into a StreamWriter to allow writing unicode.
        sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout)

    # Needed for guessit.plugins.transformers.reload() to be called.
    from guessit.plugins import transformers

    if args:
        options = get_opts().parse_args(args)
    else:  # pragma: no cover
        options = get_opts().parse_args()
    if options.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    help_required = True
    if options.properties or options.values:
        display_properties(options)
        help_required = False
    elif options.transformers:
        display_transformers()
        help_required = False

    if options.demo:
        run_demo(episodes=True, movies=True, options=vars(options))
        help_required = False

    if options.version:
        print('+-------------------------------------------------------+')
        print('+                   GuessIt ' + __version__ + (28-len(__version__)) * ' ' + '+')
        print('+-------------------------------------------------------+')
        print('|      Please report any bug or feature request at      |')
        print('|       https://github.com/wackou/guessit/issues.       |')
        print('+-------------------------------------------------------+')
        help_required = False

    if options.yaml:
        try:
            import yaml, babelfish
            def default_representer(dumper, data):
                return dumper.represent_str(str(data))
            yaml.SafeDumper.add_representer(babelfish.Language, default_representer)
            yaml.SafeDumper.add_representer(babelfish.Country, default_representer)
        except ImportError:  # pragma: no cover
            print('PyYAML not found. Using default output.')

    filenames = []
    if options.filename:
        filenames.extend(options.filename)
    if options.input_file:
        input_file = open(options.input_file, 'r')
        try:
            filenames.extend([line.strip() for line in input_file.readlines()])
        finally:
            input_file.close()

    filenames = filter(lambda f: f, filenames)

    if filenames:
        if options.submit_bug:
            for filename in filenames:
                help_required = False
                submit_bug(filename, options)
        else:
            for filename in filenames:
                help_required = False
                guess_file(filename,
                           info=options.info.split(','),
                           options=vars(options))

    if help_required:  # pragma: no cover
        get_opts().print_help()

if __name__ == '__main__':
    main()
