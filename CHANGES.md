### 4.0.13 (2014-03-22)

[full changelog](https://github.com/SiCKRAGETV/SickRage/compare/v4.0.12...v4.0.13)

* Fix HDTorrents proper search
* Fix restart page
* Fix comingEpisodes JS when manual search
* Fix properfinder thread not starting or stopping when status changed.
* Fix webapi errors about sqlite3
* Fix network sorting with small poster, banner in home
* Fix network sorting with comingEpisodes
* Fix default for new special status (default is SKIPPED)
* Fix subliminal not working properly on Windows.
* Fix proper find not working for private trackers
* Fix error in decryption of git passwords (Important: if you encrypted your password before this update then you need to re-enter the git password for it to work again
* Added possibility to blacklist show in trending
* Added scraper for MoreThan.TV.
* Added 'tp' (Beyond TV) to mediaExtensions
* Added AnimeNZB provider
* Added message about TVRAGE don't support banner/posters
* Added Log directory to config page (useful when use don't know the location of log files)
* Added shutdown option instead of restart after update (Added Checkbox in Config - General - Advanced "Restart Only") - usefull for NAS
* Added setting "Coming Episodes Missed Range" to UI (default is 7) If you have a missed episode older than 7 days, I won't show in coming episodes
* Added subtitle status to mass edit page (show if subtitle is enable/disable for that show)
* Added Percent to Footer and Link to Snatched
* Added T411 Provider subcategory 639 (tv-show not tv-series)
* Added a check for the ssl warning for providers proxies
* Hide bad shows (title is null) from Trakt Recommendations
* Hide subtitle setting if subtitle feature not enabled
* Hide webroot in /config if is not enabled
* Hide "Find Propers Search" if its disable
* Use SickRage date preset config to show trakt first aired in recommendations
* Updated mass edit text "Subtitle" to "Search Subtitle" - the action is force search subtitles
* Update Wombles for tv-x264 and tv-dvd
* Minor adjustments in editshow page
* Re-arrange items so proper settings be in sequence in search settings
* Removed hardlink and symlink from actions if Win32
* Removed Fanzub (shutdown)
* PP: Add option to delete files/folders when using manual Post Processing
    * Adds a checkbox to delete files/folders just like auto Processing does
    * Defaults to off
* PP Changed failure handling:
    * Will now continue if an error is encountered with a single file
    * Will skip only the current folder when syncfiles are encountered
    * Will show a summary at the end of Post Processing listing all failed items (files and folders) with the reason for failing.
* PP: Option to not delete empty folders during Post Processing
    * Adds option to not delete empty folders to Post Processing Config.
    * Only valid when Auto Post Processing, manual overrides the setting.
* New Feature: DisplayShow: Manual Search ask 2 questions (please give us feedback!):
    * If failed enable, ask to mark release failed Yes/No.
    * If to download: include current quality in new search or search only for higher quality
* New Feature: Added option to use forced priority in SAB (starts download even then SAB is paused)
* New Feature: Added the ability to choose displaying columns in home page


### 4.0.12 (2014-03-15)

[full changelog](https://github.com/SiCKRAGETV/SickRage/compare/v4.0.11...v4.0.12)

* Auto update or manual updated will be aborted: remote DB has new DB version or Post-Processor or ShowUpdater are running
* RSS feeds now can use global proxy (if enabled)
* Show invalid date in UI when indexer has invalidar data
* Don't add episode to backlog paused shows when setting status to Wanted
* Post-Processor: ignores hidden folders inside folders
* Post-Processor: ignore folders that are not empty
* Show message instead of error when trying to update a show that is already being update
* Added Kaerizaki-Fansub regex
* Fixed log rotation in windows ("cannot access the file because it is being used by another process")
* New TorrentDay URL
* Added WebSafe filter to log viewer.
* Show the name of Syncfiles in log when Postpone PP halts because of them
* Better unrar message error
* Fix submit issue not reading all log files
* Disable daemon mode in MAC/OSX
* Fix ASCII decode errors when downloading subtitles
* Change tvrage error to warning
* IPT: forcing search in eponly mode (sponly not available)
* TorrentDay: Improved logging
* Improved Deluged
* PP: fix already processed episodes when downloading the same release.
* Fix various providers issue in webui
* Subliminal: reverted commit for path in unicode
* Fix mede8er xml declarations
* Show "No update need" notification even if auto_update is True
* Added WebSafe filter to log viewer.
* Added limit title length when Submitting log
* Send LOCALE when submitting issue

### 4.0.11 (2014-03-08)
[full changelog](https://github.com/SiCKRAGETV/SickRage/compare/v4.0.10...v4.0.11)

* Use Scene Exceptions in Post Processing
* Fix some PP issues related to message "Problem(s) during Processing"
* Fix github issue when didn't return list of branches
* Manage backlog now only show WANTED. Don't show snatched anymore
* Fix error while showing invalid dates from indexer
* Fix unable to add torrent rss when nzb search is disable
* Fix metadata errors when info is missing from indexer
* Fix git password not encrypted
* Fix for Pushbullet update notification
* Fix to delete ALL associated files while replacing old episodes (PP)
* Faster PP copy method
* Added field for custom title tag in torrent rss provider
* New TRAKT features and fixes
* Viewlog page can read the logs from all the logfiles (you can search in all your log files using UI)
* If you missed this feature: you can change the number of logs in settings and size per file)
* WARNING: Windows users: please set number of logs to 0 (zero) to avoid errors. Known issue.

### 4.0.10 (2014-03-03)
[full changelog](https://github.com/SiCKRAGETV/SickRage/compare/v4.0.9...v4.0.10)

* Add "Use failed downloads" to search settings
* Add a missing urllib3.disbale_warning()
* Add a warning when gh object is set to None
* Add normalized locale code.
* Add option to delete RAR contents when Process_method != Move
* Add Provider AR
* Add RARBG provider
* Add SD search to RARBG provider
* Added a specific regex for horriblesubs
* Added apikey to censoredformatter log
* Added auto backup when updating
* Added Date field in email body
* Added failed.db and cache.db to backup
* Added missing network logos
* Added several network logos
* Added sponly to season pack search
* Added support for Plex Media Center updates with Auth Token
* Added sync file extensions to Post Processing Config page
* AniDB: Catch exception when generating white and blacklist
* AniDB: Fix generating exception on timeout in auth
* AniDB: Fix generating exception on timeout in PP
* AniDB: Show error in ui when unable to retreive Fansub Groups when
* BTN: Fix searching in season mode for episode
* Change the language dropdown in editShow.tmpl
* Check actual branch before switch
* Check for UnicodeDecodeError in Cheetah's Filter
* Check if we are on windows before query Windows version.
* Disable urllib3 InsecureRequestWarning
* Don't remove logs folder when git reset is enabled in UI
* Don't use system.encoding for Cheetah's Filter
* Fix .gitignore
* Fix add newznab provider
* Fix backup issue with invalid restore folder
* Fix changing episode scene number not updating the show's episode cache.
* Fix color in displayShow when manually searching
* Fix compiling error
* Fix downconverting path from unicode to str
* Fix list_associated_files and DeleteRAR contents
* Fix low quality snatch not showing in backlog overview
* Fix missing en_US alias in certain system.
* Fix msg created witout MIMEext
* Fix pyUnrar2 on bad archive
* Fix rarbg provider searchstring encoding
* Fix restart timeout 
* Fix set date/time to local tz when local is choosen
* Fix Show Lookups on Indexer
* Fix time display for fuzzy dates with trim zero and 24 hour time style
* Fix typo in emailnotify.py
* Fix viewlog.tmpl
* Fixes shows with double quotes
* Handles multi-page results and improved login for Freshon
* HBO and Starz logos where a little stretched. Replaced them.
* Hide submit errors button if no git user/pass and auto submit
* Improved logging to detect CloudFlare blocking
* Improved rTorrent support
* IPT: force eponly search since as it isn't supported by the provider.
* Kodi fix
* Limit number of pages for RSS search
* New Feature - Log search and log filter by SR thread
* OldPirateBay Replaced url tv/latest
* Opensubtitle - show only error not traceback
* Prettier file sizes in DisplayShow
* Provider SCC: Catch exception on getURL
* Redone restart.js
* Remove blue color from progress bar
* Remove part of the condition to enable utf8 on Windows
* Remove traceback from generic.py
* Remove trademark from filename
* Removed old TMF network logo. (channel stopped 2011)
* Removed 'page' parameter
* Removed some comment
* Renamed network logo of se´ries+ to series+
* Replace os.rmdir to shutil.rmtree
* Replace the language selection in add show
* Replaced adult swim network logo with colored version.
* Replaced white network logos with colored versions.
* Restored back previous Comedy Central logos.
* Reworked the backup/restore to properly handle the cache directory
* SCC: Fix season search only in sponly
* Set condition for tntvillage parameters
* Skip anidb query if previously failed
* Subliminal: Fix ogg subtitles track with und language
* Subtitles: Path is always unicode
* Suppressed torrent list not found error msg
* Suppressing subliminal logs on windows
* T411: Change addresse from t411.me to t411.io
* Trakt: Catch error when trying to delete library.
* Update config.js to compareDB on update
* Update default trakt timeout
* Update T411 to its new domain name
* Update traktchecker - remove traceback
* Update traktchecker - remove traceback
* Update webserve.py to add delete_failed
* Update webserve.py to compareDB on checkout
* Updated OldPirateBay file list parsing
* Updated Requests to 2.5.1
* Use hostname rather than IP
* Use sbdatetime instead of self
* UTF-8 encode url that is used in urllib.quote_plus(url) 
* Windows UTF-8 console via cp65001

### 0.x.x (2014-11-11 xx:xx:xx UTC)

* Add Bootstrap for UI features
* Change UI to resize fluidly on different display sizes, fixes the issue where top menu items would disappear on smaller screens
* Add date formats "dd/mm/yy", "dd/mm/yyyy", "day, dd/mm/yy" and "day, dd/mm/yyyy"
* Remove imdb watchlist feature from General Configuration/"Misc" tab as it wasn't ready for prime time
* Change rename tab General Configuration/"Web Interface" to "Interface"
* Add "User Interface" section to the General Configuration/"Interface" tab
* Change combine "Date and Time" and "Theme" tab content to "User Interface" section
* Add field in Advanced setting for a custom remote name used to populate branch versions
* Change theme name "original" to "light"
* Change text wording on all UI options under General Configuration
* Change reduce over use of capitals on all General Configuration tabs
* Change streamline UI layout, mark-up and some CSS styling on General Configuration tabs
* Fix imdb and three other images rejected by IExplorer because they were corrupt. Turns out that they were .ico files renamed to either .gif or .png instead of being properly converted
* Change cleanup Subtitles Search settings text, correct quotations, use spaces for code lines, tabs for html
* Add save sorting options automatically on Show List/Layout Poster
* Change clarify description for backlog searches option on provider settings page
* Fix sort mode "Next Episode" on Show List/Layout:Poster with show statuses that are Paused, Ended, and Continuing as they were random
* Fix sort of tvrage show statuses "New" and "Returning" on Show List/Layout:Simple by changing status column text to "Continuing"
* Add dark spinner to "Add New Show" (searching indexers), "Add existing shows" (Loading Folders), Coming Eps and all config pages (when saving)
* Change Config/Notifications test buttons to stop and highlight input fields that lack required values
* Change Test Plex Media Server to Test Plex Client as it only tests the client and not the server
* Change style config_notifications to match new config_general styling
* Change style config_providers to match new config_general styling
* Change move Providers Priorities qtip options to a new Search Providers/Provider Options tab
* Remove superfish-1.4.8.js and supersubs-0.2b.js as they are no longer required with new UI
* Change overhaul Config Search Settings in line with General Configuration
* Fix error when a show folder is deleted outside of SickRage
* Change combine the delete button function into the remove button on the display show page
* Change other small UI tweaks
* Fix keyerrors on backlog overview preventing the page to load
* Fix exception raised when converting 12pm to 24hr format and handle 12am when setting file modify time (e.g. used during PP)
* Fix proxy_indexers setting not loading from config file
* Add subtitle information to the cmd show and cmd shows api output
* Remove http login requirement for API when an API key is provided
* Change API now uses Timezone setting at General Config/Interface/User Interface at relevant endpoints
* Fix changing root dirs on the mass edit page
* Add use trash (or Recycle Bin) for selected actions on General Config/Misc/Send to trash
* Add handling for when deleting a show and the show folder no longer exists
* Fix Coming Episodes/Layout Calender/View Paused and tweak its UI text
* Made all init scripts executable
* Fix invalid responses when using sickbeard.searchtvdb api command
* Fixes unicode issues during searches on newznab providers when rid mapping occur
* Fix white screen of death when trying to add a show that is already in library on Add Show/Add Trending Show page
* Add show sorting options to Add Show/Add Trending Show page
* Add handler for when Trakt returns no results for Add Show/Add Trending Show page
* Fix image links when anchor child images are not found at Trakt on Add Show/Add Trending Show page
* Add image to be used when Trakt posters are void on Add Show/Add Trending Show page
* Fix growl registration not sending sickrage an update notification registration
* Add an anonymous redirect builder for external links
* Update kodi link to Kodi at Config Notifications
* Fix missing url for kickasstorrents in config_providers
* Fix post processing when using tvrage indexer and mediabrowser metadata generation
* Change reporting failed network_timezones.txt updates from an error to a warning
* Fix missing header and "on <missing text>" when network is none and Layout "Poster" with Sort By "Network" on coming episodes page.
* Change how the "local/network" setting is handled to address some issues

[develop changelog]
* Change improve display of progress bars in the Downloads columns of the show list page
* Change improve display of progress bars under the images in Layout Poster of the show list page
* Fix default top navbar background white-out behaviour on browsers that don't support gradients
* Change improve top navbar gradient use for greater cross browser compatibility (e.g. Safari)
* Fix dark theme divider between Season numbers on display show page
* Fix main background and border colour of logs on log page
* Fix "Subtitle Language" drop down font colour when entering text on the Subtitles Search settings
* Add confirmation dialogs back in that were missed due to new UI changes
* Fix the home page from failing to load if a show status contains nothing
* Fix and repositioned show_message on display show to use bootstrap styling
* Remove commented out html from display show accidently left in during UI changes
* Fix display issue of season tables in displayShow view / Display Specials
* Change to suppress reporting of Tornado exception error 1
* Fix progress sort direction for poster layout view on home page
* Fix invalid use of str() in the Send2Trash library for platforms other
* Fix dropdown confirm dialogs for restart and shutdown
* Fix parsing utf8 data from tvdb and tvrage
* Fix display show status and subtitle searches to use new column class names
* Fix API response header for JSON content type and the return of JSONP data
* Update PNotify to version [2.0.1]
* Change the notification popups to always show the close button.
* Fix issue where popups did not show if multiple tabs are used. Popups now queue and display when a tab is brought into focus.
* Fix missing HTML in notifications resulting in incorrect formatting.

### 0.2.1 (2014-10-22 06:41:00 UTC)

[full changelog](https://github.com/SiCKRAGETV/SickRage/compare/release_0.2.0...release_0.2.1)

* Fix HDtorrents provider screen scraping


### 0.2.0 (2014-10-21 12:36:50 UTC)

[full changelog](https://github.com/SiCKRAGETV/SickRage/compare/release_0.1.0...release_0.2.0)

* Fix for failed episodes not counted in total
* Fix for custom newznab providers with leading integer in name
* Add checkbox to control proxying of indexers
* Fix crash on general settings page when git output is None
* Add subcentre subtitle provider
* Add return code from hardlinking error to log
* Fix ABD regex for certain filenames
* Change miscellaneous UI fixes
* Update Tornado webserver to 4.1dev1 and add the certifi lib dependency
* Fix trending shows page from loading full size poster images
* Add "Archive on first match" to Manage, Mass Update, Edit Selected page
* Fix searching IPTorrentsProvider
* Remove travisci python 2.5 build testing


### 0.1.0 (2014-10-16 12:35:15 UTC)

* Initial release
