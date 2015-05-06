SickRage
=====
Video File Manager for TV Shows, It watches for new episodes of your favorite shows and when they are posted it does its magic.

## Branch Build Status
[![Build Status](https://travis-ci.org/SiCKRAGETV/SickRage.svg?branch=develop)](https://travis-ci.org/SiCKRAGETV/SickRage)

## Features
 - XBMC library updates, poster/fanart downloads, and NFO/TBN generation
 - configurable episode renaming
 - available for any platform, uses simple HTTP interface
 - can notify XBMC, Growl, or Twitter when new episodes are available
 - specials and double episode support
 - Automatic XEM Scene Numbering/Naming for seasons/episodes
 - Episode Status Manager now allows for mass failing seasons/episodes to force retrying.
 - DVD Order numbering for returning the results in DVD order instead of Air-By-Date order.
 - Improved Failed handling code for shows.
 - DupeKey/DupeScore for NZBGet 12+
 - Searches both TheTVDB.com, TVRage.com and AniDB.net for shows, seasons, episodes
 - Importing of existing video files now allows you to choose which indexer you wish to have SickBeard search its show info from.
 - Your tvshow.nfo files are now tagged with a indexer key so that SickBeard can easily tell if the shows info comes from TheTVDB or TVRage.
 - Sports shows are now able to be searched for..

## Screenshots
-[Desktop (Full-HD)](http://imgur.com/a/4fpBk)<br>
-[Mobile](http://imgur.com/a/WPyG6)

## Dependencies
 To run SickRage from source you will need Python 2.6+, Cheetah 2.1.0+, and PyOpenSSL 0.13.1 or lower.

## Forums
 Any questions or setup info your looking for can be found at out forums https://www.sickrage.tv

## Bug/Issues
[SickRage Issue Tracker](https://github.com/SiCKRAGETV/sickrage-issues)

## FAQ

https://github.com/SiCKRAGETV/SickRage/wiki/Frequently-Asked-Questions

## Wiki

https://github.com/SiCKRAGETV/SickRage/wiki

## Important
Please before using this with your existing database (sickbeard.db) please make a backup copy of it and delete any other database files such as cache.db and failed.db if present, we HIGHLY recommend starting out with no database files at all to make this a fresh start but the choice is at your own risk
