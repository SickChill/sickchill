Sick Beard
=====

*SickBeard-TVRage  is currently in beta release stage. There may be severe bugs in it and at any given time it may not work at all.*

Sick Beard-TVRage is a PVR for torrent and newsgroup users. It watches for new episodes of your favorite shows and when they are posted it downloads them, sorts and renames them, and optionally generates metadata for them. It retrieves show information from theTVDB.com and TVRage.com.

!!! Please before using this with your existing database (sickbeard.db) please make a backup copy of it and delete any other database files such as cache.db and failed.db if present, we HIGHLY recommend starting out with no database files at all to make this a fresh start but the choice is at your own risk !!!

Features include:

* automatically retrieves new episode torrent or nzb files
* can scan your existing library and then download any old seasons or episodes you're missing
* can watch for better versions and upgrade your existing episodes (to from TV DVD/BluRay for example)
* XBMC library updates, poster/fanart downloads, and NFO/TBN generation
* configurable episode renaming
* sends NZBs directly to SABnzbd, prioritizes and categorizes them properly
* available for any platform, uses simple HTTP interface
* can notify XBMC, Growl, or Twitter when new episodes are downloaded
* specials and double episode support

XEM EDITION FEATURES ADDED:
- Automatic XEM Scene Numbering/Naming for seasons/episodes (ported from Bricky's fork).
- Failed handling now attempts to snatch a different release and excludes failed releases from future snatch attempts.
- Episode Status Manager now allows for mass failing seasons/episodes to force retrying to download new releases.
- DVD Order numbering for returning the results in DVD order instead of Air-By-Date order.
- Improved Failed handling code for both NZB and Torrent downloads.
- DupeKey/DupeScore for NZBGet 12+

TVRage EDITION FEATURES ADDED:
- Searches both TheTVDB.com and TVRage.com for shows, seasons, episodes
- Importing of existing video files now allows you to choose which indexer you wish to have SickBeard download its show info from.
- Your tvshow.nfo files are now tagged with a indexer key so that SickBeard can easily tell if the shows info comes from TheTVDB or TVRage.
- Failed download handling has been improved now for both NZB and Torrents.
- Sports shows are now able to be searched for and downloaded by both NZB and Torrent providers.

Sick Beard makes use of the following projects:

* [cherrypy][cherrypy]
* [Cheetah][cheetah]
* [simplejson][simplejson]
* [tvdb_api][tvdb_api]
* [ConfigObj][configobj]
* [SABnzbd+][sabnzbd]
* [jQuery][jquery]
* [Python GNTP][pythongntp]
* [SocksiPy][socks]
* [python-dateutil][dateutil]
* [jsonrpclib][jsonrpclib]
* [Subliminal][subliminal]

## Dependencies

To run Sick Beard from source you will need Python 2.6+ and Cheetah 2.1.0+. The [binary releases][googledownloads] are standalone.

## Bugs

If you find a bug please report [here][githubissues] on Github. Verify that it hasn't already been submitted and then [log a new bug][githubnewissue]. Be sure to provide a sickbeard log in debug mode where is the error evidence or it'll never get fixed.
[cherrypy]: http://www.cherrypy.org
[cheetah]: http://www.cheetahtemplate.org/
[simplejson]: http://code.google.com/p/simplejson/ 
[tvdb_api]: http://github.com/dbr/tvdb_api
[configobj]: http://www.voidspace.org.uk/python/configobj.html
[sabnzbd]: http://www.sabnzbd.org/
[jquery]: http://jquery.com
[pythongntp]: http://github.com/kfdm/gntp
[socks]: http://code.google.com/p/socksipy-branch/
[dateutil]: http://labix.org/python-dateutil
[googledownloads]: http://code.google.com/p/sickbeard/downloads/list
[githubissues]: https://github.com/echel0n/SickBeard-TVRage/issues?state=open
[githubnewissue]: https://github.com/echel0n/SickBeard-TVRage/issues/new
[jsonrpclib]: https://github.com/joshmarshall/jsonrpclib
[subliminal]: https://github.com/Diaoul/subliminal
