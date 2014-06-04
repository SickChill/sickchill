SickRage
=====

SickRage is a Video File Manager for TV Shows, It watches for new episodes of your favorite shows and when they are posted it does its magic.

*SickRage  is currently in beta release stage. There may be severe bugs in it and at any given time it may not work at all.*

There are currently a lot of changes that we're working on, which affect the very core of how SickRage works. We're doing this to lay the groundwork
for making SickRage seriously more awesome, scalable and resource-friendly than it already is.
 
While we're doing this, please expect SickRage do strange things, or maybe even not work at all. In any case, we need your help. If you see SickRage behaving weird, check if someone has reported it, and if not, open a new issue. There is little to no use to report "software should be stable". We will focus on that later, not now.

!!! Please before using this with your existing database (sickbeard.db) please make a backup copy of it and delete any other database files such as cache.db and failed.db if present, we HIGHLY recommend starting out with no database files at all to make this a fresh start but the choice is at your own risk !!!

FEATURES:
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

## Dependencies

To run SickRage from source you will need Python 2.6+ and Cheetah 2.1.0+.

## Forums

Any questions or setup info your looking for can be found at out forums https://www.sickrage.tv
<br>
If you find a bug please report at our forums https://sickrage.tv/forums/forum/help-support/bug-issue-reports
<br>
Be sure to provide a sickrage log in debug mode where is the error evidence or it'll never get fixed.
