Enzyme
======

Enzyme is a Python module to parse video metadata.

.. image:: https://travis-ci.org/Diaoul/enzyme.png?branch=master
    :target: https://travis-ci.org/Diaoul/enzyme


Usage
-----
Parse a MKV file::

    >>> with open('How.I.Met.Your.Mother.S08E21.720p.HDTV.X264-DIMENSION.mkv', 'rb') as f:
    ...    mkv = enzyme.MKV(f)
    ... 
    >>> mkv.info
    <Info [title=None, duration=0:20:56.005000, date=2013-04-15 14:06:50]>
    >>> mkv.video_tracks
    [<VideoTrack [1, 1280x720, V_MPEG4/ISO/AVC, name=None, language=eng]>]
    >>> mkv.audio_tracks
    [<AudioTrack [2, 6 channel(s), 48000Hz, A_AC3, name=None, language=und]>]


License
-------
Apache2


Changelog
=========

0.4.1
-----
**release date:** 2013-11-05

* Fix parsing nested SeekHead elements
* Make parsing nested SeekHead elements optional


0.4.0
-----
**release date:** 2013-10-30

* Import exceptions under enzyme namespace
* Change repr format
* Rename base exception
* Remove test file


0.3.1
-----
**release date:** 2013-10-20

* Fix package distribution


0.3
---
**release date:** 2013-05-18

* Complete refactoring, for the old enzyme see https://github.com/Diaoul/enzyme-old


