SickChill [![Build Status](https://travis-ci.org/SickChill/SickChill.svg?branch=master)](https://travis-ci.org/SickChill/SickChill) [![Build status](https://ci.appveyor.com/api/projects/status/s8bb0iqroecnhya2/branch/master?svg=true)](https://ci.appveyor.com/project/miigotu/SickChill/branch/master) [![XO code style](https://img.shields.io/badge/code_style-XO-5ed9c7.svg)](https://github.com/sindresorhus/xo) [![Donate](https://img.shields.io/badge/donations-appreciated-green.svg)](https://github.com/SickChill/SickChill/wiki/Donations)
====================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================

#### Please do not confuse us with SickRageTV aka Sickrage.ca, which took over the `sickrage/sickrage` repository in Oct 2018
#### We will never mine bitcoin on your machine, charge for a "service" or to use the software.
#### We will never store your information, especially site logins to private trackers.
#### We believe in honesty and loyalty and privacy.

Automatic Video Library Manager for TV Shows. It watches for new episodes of your favorite shows, and when they are posted it does its magic.

#### Features
 - Kodi/XBMC library updates, poster/banner/fanart downloads, and NFO/TBN generation
 - Configurable automatic episode renaming, sorting, and other processing
 - Easily see what episodes you're missing, are airing soon, and more
 - Automatic torrent/nzb searching, downloading, and processing at the qualities you want
 - Largest list of supported torrent and nzb providers, both public and private
 - Can notify Kodi, XBMC, Growl, Trakt, Twitter, and more when new episodes are available
 - Searches TheTVDB.com and AniDB.net for shows, seasons, episodes, and metadata
 - Episode status management allows for mass failing seasons/episodes to force retrying
 - DVD Order numbering for returning the results in DVD order instead of Air-By-Date order
 - Allows you to choose which indexer to have SickChill search its show info from when importing
 - Automatic XEM Scene Numbering/Naming for seasons/episodes
 - Available for any platform, uses a simple HTTP interface
 - Specials and multi-episode torrent/nzb support
 - Automatic subtitles matching and downloading
 - Improved failed download handling
 - DupeKey/DupeScore for NZBGet 12+
 - Real SSL certificate validation
 - Supports Anime shows

#### Installation/Setup

Visit the [Installation & Configuration guides page](https://github.com/SickChill/SickChill/wiki/Installation-&-Configuration-Guides) on our wiki

#### Dependencies

To run SickChill you will need Python 3.6+

#### More info

* [Wiki](https://github.com/SickChill/SickChill/wiki)

* [FAQ](https://github.com/SickChill/SickChill/wiki/FAQ%27s-and-Fixes)

* [Issue Tracker](https://github.com/SickChill/SickChill/issues)

#### Important notes on switching from other forks

Before using this with your existing database (`sickbeard.db`) please make a backup copy of it and delete any other database files such as cache.db and failed.db if present.

We HIGHLY recommend starting out with no database files at all to make this a fresh start but the choice is at your own risk.

#### Supported providers

A full list can be found here: [Link](https://github.com/SickChill/SickChill/wiki/SickChill-Search-Providers)

#### News and Changelog
[news.md and CHANGES.md have moved to a separate repo, click here](https://github.com/SickChill/SickChill.github.io)
