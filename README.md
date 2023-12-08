# SickChill

---

###  Important Notice*
Issue/Bug tracking, feature requests, support, and developer communication is moving strictly to [discord](https://discord.gg/FXre9qkHwE) - please start making the habit to go there, rather than creating issues on GitHub. After a period of time GitHub issue tracker, discussions, and other social features will be disabled on GitHub.

---
[![Language](https://img.shields.io/github/languages/top/sickchill/sickchill?logo=python&style=plastic)](https://python.org)
[![Build Status](https://img.shields.io/github/actions/workflow/status/sickchill/sickchill/pythonpackage.yml?logo=github&style=plastic)](https://github.com/SickChill/SickChill/actions/workflows/pythonpackage.yml?query=branch%3Amaster)
[![Release Date](https://img.shields.io/github/release-date/sickchill/sickchill?logo=github&style=plastic)](https://github.com/SickChill/sickchill/releases)
[![Last Commit](https://img.shields.io/github/last-commit/sickchill/sickchill?logo=github&style=plastic)](https://github.com/SickChill/sickchill/commits/master)
[![Commits Since](https://img.shields.io/github/commits-since/sickchill/sickchill/latest/develop?logo=github&sort=date&style=plastic)](https://github.com/SickChill/sickchill/commits/master)
[![Discord](https://img.shields.io/discord/502612977271439372?label=Discord&logo=discord&style=plastic)](https://discord.gg/FXre9qkHwE)
[![Donate](https://img.shields.io/badge/$_donations-needed-green.svg?style=plastic)](https://github.com/SickChill/SickChill/wiki/Donations)

---

### Automatic Video Library Manager for TV Shows. It watches for new episodes of your favorite shows, and when they are posted it does its magic.

### Features
 - Kodi/XBMC library updates, poster/banner/fanart downloads, and NFO/TBN generation
 - Configurable automatic episode renaming, sorting, and other processing
 - Easily see what episodes you're missing, are airing soon, and more
 - Automatic torrent/nzb searching, sending to your client, and processing at the qualities you want
 - Largest list of supported torrent, newznab, and torznab providers - both public and private
 - Can notify Kodi, XBMC, Growl, Trakt, Twitter, and more when new episodes are available
 - Searches [TheTVDB](https://thetvdb.com), [AniDB.net](https://anidb.net), [iMDB](https://imdb.com), [FanArt.tv](https://fanart.tv), and more for shows, seasons, episodes, and metadata
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

### Important Links
* [Installation & Configuration](https://github.com/SickChill/SickChill/wiki/Installation-&-Configuration-Guides)
* [Wiki](https://github.com/SickChill/SickChill/wiki)
* [FAQ](https://github.com/SickChill/SickChill/wiki/FAQ%27s-and-Fixes)
* [Issue Tracker](https://discord.gg/FXre9qkHwE)
* [Feature Requests](https://discord.gg/FXre9qkHwE)
* [Supported providers](https://github.com/SickChill/SickChill/wiki/SickChill-Search-Providers)
* [News](https://github.com/SickChill/sickchill.github.io/blob/master/sickchill-news/news.md)
* [Changelog](https://github.com/SickChill/SickChill/blob/master/CHANGES.md)
* [Network Timezones](https://github.com/SickChill/sickchill.github.io/tree/master/sc_network_timezones)
* [Scene Exceptions](https://github.com/SickChill/sickchill.github.io/tree/master/scene_exceptions)

### Dependencies

To run SickChill you will need Python 3.8+, preferably 3.11 or newer. PyPy (python 3.7-3.9) 7.8.x+ is also supported.

### Important notes on switching from other forks

Before using this with your existing database (`sickbeard.db`) please make a backup copy of it and delete any other database files such as cache.db and failed.db if present.
We HIGHLY recommend starting out with no database files at all to make this a fresh start but the choice is at your own risk.

### Huge thanks to [JetBrains](https://jb.gg/OpenSourceSupport) for providing "All Products Pack" licenses free of charge for SickChill developers as part of their support of OSS.
<a href="https://jb.gg/OpenSourceSupport"><img src="https://resources.jetbrains.com/storage/products/company/brand/logos/jb_beam.svg" width="60" height="60"><img src="https://resources.jetbrains.com/storage/products/company/brand/logos/jb_square.svg" width="60" height="60"><img src="https://resources.jetbrains.com/storage/products/company/brand/logos/PyCharm_icon.svg" width="60" height="60"><img src="https://resources.jetbrains.com/storage/products/company/brand/logos/IntelliJ_IDEA_icon.svg" width="60" height="60"></a>
