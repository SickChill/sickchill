#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# GuessIt - A library for guessing information from filenames
# Copyright (c) 2013 Nicolas Wack <wackou@gmail.com>
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

from .__version__ import __version__

__all__ = ['Guess', 'Language',
           'guess_file_info', 'guess_video_info',
           'guess_movie_info', 'guess_episode_info',
           'default_options']


# Do python3 detection before importing any other module, to be sure that
# it will then always be available
# with code from http://lucumr.pocoo.org/2011/1/22/forwards-compatible-python/
import sys
if sys.version_info[0] >= 3:  # pragma: no cover
    PY2, PY3 = False, True
    unicode_text_type = str
    native_text_type = str
    base_text_type = str

    def u(x):
        return str(x)

    def s(x):
        return x

    class UnicodeMixin(object):
        __str__ = lambda x: x.__unicode__()
    import binascii

    def to_hex(x):
        return binascii.hexlify(x).decode('utf-8')

else:   # pragma: no cover
    PY2, PY3 = True, False
    __all__ = [str(s) for s in __all__]  # fix imports for python2
    unicode_text_type = unicode
    native_text_type = str
    base_text_type = basestring

    def u(x):
        if isinstance(x, str):
            return x.decode('utf-8')
        if isinstance(x, list):
            return [u(s) for s in x]
        return unicode(x)

    def s(x):
        if isinstance(x, unicode):
            return x.encode('utf-8')
        if isinstance(x, list):
            return [s(y) for y in x]
        if isinstance(x, tuple):
            return tuple(s(y) for y in x)
        if isinstance(x, dict):
            return dict((s(key), s(value)) for key, value in x.items())
        return x

    class UnicodeMixin(object):
        __str__ = lambda x: unicode(x).encode('utf-8')

    def to_hex(x):
        return x.encode('hex')

    range = xrange


from guessit.guess import Guess, smart_merge
from guessit.language import Language
from guessit.matcher import IterativeMatcher
from guessit.textutils import clean_default, is_camel, from_camel
from copy import deepcopy
import babelfish
import os.path
import logging
from guessit.options import get_opts
import shlex
# Needed for guessit.plugins.transformers.reload() to be called.
from guessit.plugins import transformers

log = logging.getLogger(__name__)


class NullHandler(logging.Handler):
    def emit(self, record):
        pass

# let's be a nicely behaving library
h = NullHandler()
log.addHandler(h)


def _guess_filename(filename, options=None, **kwargs):
    mtree = _build_filename_mtree(filename, options=options, **kwargs)
    if options.get('split_camel'):
        _add_camel_properties(mtree, options=options)
    return mtree.matched()


def _build_filename_mtree(filename, options=None, **kwargs):
    mtree = IterativeMatcher(filename, options=options, **kwargs)
    second_pass_options = mtree.second_pass_options
    if second_pass_options:
        log.debug('Running 2nd pass with options: %s' % second_pass_options)
        merged_options = dict(options)
        merged_options.update(second_pass_options)
        mtree = IterativeMatcher(filename, options=merged_options, **kwargs)
    return mtree


def _add_camel_properties(mtree, options=None, **kwargs):
    prop = 'title' if mtree.matched().get('type') != 'episode' else 'series'
    value = mtree.matched().get(prop)
    _guess_camel_string(mtree, value, options=options, skip_title=False, **kwargs)

    for leaf in mtree.match_tree.unidentified_leaves():
        value = leaf.value
        _guess_camel_string(mtree, value, options=options, skip_title=True, **kwargs)


def _guess_camel_string(mtree, string, options=None, skip_title=False, **kwargs):
    if string and is_camel(string):
        log.debug('"%s" is camel cased. Try to detect more properties.' % (string,))
        uncameled_value = from_camel(string)
        merged_options = dict(options)
        if 'type' in mtree.match_tree.info:
            current_type = mtree.match_tree.info.get('type')
            if current_type and current_type != 'unknown':
                merged_options['type'] = current_type
        camel_tree = _build_filename_mtree(uncameled_value, options=merged_options, name_only=True, skip_title=skip_title, **kwargs)
        if len(camel_tree.matched()) > 0:
            mtree.matched().update(camel_tree.matched())
            return True
    return False


def guess_video_metadata(filename):
    """Gets the video metadata properties out of a given file. The file needs to
    exist on the filesystem to be able to be analyzed. An empty guess is
    returned otherwise.

    You need to have the Enzyme python package installed for this to work."""
    result = Guess()

    def found(prop, value):
        result[prop] = value
        log.debug('Found with enzyme %s: %s' % (prop, value))

    # first get the size of the file, in bytes
    try:
        size = os.stat(filename).st_size
        found('fileSize', size)

    except Exception as e:
        log.error('Cannot get video file size: %s' % e)
        # file probably does not exist, we might as well return now
        return result

    # then get additional metadata from the file using enzyme, if available
    try:
        import enzyme

        with open(filename) as f:
            mkv = enzyme.MKV(f)

            found('duration', mkv.info.duration.total_seconds())

            if mkv.video_tracks:
                video_track = mkv.video_tracks[0]

                # resolution
                if video_track.height in (480, 720, 1080):
                    if video_track.interlaced:
                        found('screenSize', '%di' % video_track.height)
                    else:
                        found('screenSize', '%dp' % video_track.height)
                else:
                    # TODO: do we want this?
                    #found('screenSize', '%dx%d' % (video_track.width, video_track.height))
                    pass

                # video codec
                if video_track.codec_id == 'V_MPEG4/ISO/AVC':
                    found('videoCodec', 'h264')
                elif video_track.codec_id == 'V_MPEG4/ISO/SP':
                    found('videoCodec', 'DivX')
                elif video_track.codec_id == 'V_MPEG4/ISO/ASP':
                    found('videoCodec', 'XviD')

            else:
                log.warning('MKV has no video track')

            if mkv.audio_tracks:
                audio_track = mkv.audio_tracks[0]
                # audio codec
                if audio_track.codec_id == 'A_AC3':
                    found('audioCodec', 'AC3')
                elif audio_track.codec_id == 'A_DTS':
                    found('audioCodec', 'DTS')
                elif audio_track.codec_id == 'A_AAC':
                    found('audioCodec', 'AAC')
            else:
                log.warning('MKV has no audio track')

            if mkv.subtitle_tracks:
                embedded_subtitle_languages = set()
                for st in mkv.subtitle_tracks:
                    try:
                        if st.language:
                            lang = babelfish.Language.fromalpha3b(st.language)
                        elif st.name:
                            lang = babelfish.Language.fromname(st.name)
                        else:
                            lang = babelfish.Language('und')

                    except babelfish.Error:
                        lang = babelfish.Language('und')

                    embedded_subtitle_languages.add(lang)

                found('subtitleLanguage', embedded_subtitle_languages)
            else:
                log.debug('MKV has no subtitle track')

        return result

    except ImportError:
        log.error('Cannot get video file metadata, missing dependency: enzyme')
        log.error('Please install it from PyPI, by doing eg: pip install enzyme')
        return result

    except IOError as e:
        log.error('Could not open file: %s' % filename)
        log.error('Make sure it exists and is available for reading on the filesystem')
        log.error('Error: %s' % e)
        return result

    except enzyme.Error as e:
        log.error('Cannot guess video file metadata')
        log.error('enzyme.Error while reading file: %s' % filename)
        log.error('Error: %s' % e)
        return result

default_options = {}


def guess_file_info(filename, info=None, options=None, **kwargs):
    """info can contain the names of the various plugins, such as 'filename' to
    detect filename info, or 'hash_md5' to get the md5 hash of the file.

    >>> testfile = os.path.join(os.path.dirname(__file__), 'test/dummy.srt')
    >>> g = guess_file_info(testfile, info = ['hash_md5', 'hash_sha1'])
    >>> g['hash_md5'], g['hash_sha1']
    ('64de6b5893cac24456c46a935ef9c359', 'a703fc0fa4518080505809bf562c6fc6f7b3c98c')
    """
    info = info or 'filename'
    options = options or {}

    if isinstance(options, base_text_type):
        args = shlex.split(options)
        options = vars(get_opts().parse_args(args))
    if default_options:
        if isinstance(default_options, base_text_type):
            default_args = shlex.split(default_options)
            merged_options = vars(get_opts().parse_args(default_args))
        else:
            merged_options = deepcopy(default_options)
        merged_options.update(options)
        options = merged_options

    result = []
    hashers = []

    # Force unicode as soon as possible
    filename = u(filename)

    if isinstance(info, base_text_type):
        info = [info]

    for infotype in info:
        if infotype == 'filename':
            result.append(_guess_filename(filename, options, **kwargs))

        elif infotype == 'hash_mpc':
            from guessit.hash_mpc import hash_file
            try:
                result.append(Guess({infotype: hash_file(filename)},
                                    confidence=1.0))
            except Exception as e:
                log.warning('Could not compute MPC-style hash because: %s' % e)

        elif infotype == 'hash_ed2k':
            from guessit.hash_ed2k import hash_file
            try:
                result.append(Guess({infotype: hash_file(filename)},
                                    confidence=1.0))
            except Exception as e:
                log.warning('Could not compute ed2k hash because: %s' % e)

        elif infotype.startswith('hash_'):
            import hashlib
            hashname = infotype[5:]
            try:
                hasher = getattr(hashlib, hashname)()
                hashers.append((infotype, hasher))
            except AttributeError:
                log.warning('Could not compute %s hash because it is not available from python\'s hashlib module' % hashname)

        elif infotype == 'video':
            g = guess_video_metadata(filename)
            if g:
                result.append(g)

        else:
            log.warning('Invalid infotype: %s' % infotype)

    # do all the hashes now, but on a single pass
    if hashers:
        try:
            blocksize = 8192
            hasherobjs = dict(hashers).values()

            with open(filename, 'rb') as f:
                chunk = f.read(blocksize)
                while chunk:
                    for hasher in hasherobjs:
                        hasher.update(chunk)
                    chunk = f.read(blocksize)

            for infotype, hasher in hashers:
                result.append(Guess({infotype: hasher.hexdigest()},
                                    confidence=1.0))
        except Exception as e:
            log.warning('Could not compute hash because: %s' % e)

    result = smart_merge(result)

    return result


def guess_video_info(filename, info=None, options=None, **kwargs):
    return guess_file_info(filename, info=info, options=options, type='video', **kwargs)


def guess_movie_info(filename, info=None, options=None, **kwargs):
    return guess_file_info(filename, info=info, options=options, type='movie', **kwargs)


def guess_episode_info(filename, info=None, options=None, **kwargs):
    return guess_file_info(filename, info=info, options=options, type='episode', **kwargs)
