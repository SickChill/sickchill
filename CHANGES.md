### 0.x.x (2014-11-05 xx:xx:xx UTC)

* Add Bootstrap for UI features
* Change UI to resize fluidly on different display sizes, fixes the issue where top menu items would disappear on smaller screens.
* Add date formats "dd/mm/yy", "dd/mm/yyyy", "day, dd/mm/yy" and "day, dd/mm/yyyy"
* Remove imdb watchlist feature from General Configuration/"Misc" tab as it wasn't ready for prime time
* Change to rename General Configuration/"Web Interface" tab as "Interface"
* Add a "User Interface" section to the General Configuration/"Interface" tab
* Change bring together "Date and Time" and "Theme" tab content to "User Interface" section
* Add field in Advanced setting for a custom remote name used to populate branch versions
* Change theme name "original" to "light"
* Improve text wording on all UI options under General Configuration
* Improve reduce over use of capitals on all General Configuration tabs
* Improve streamline UI layout, mark-up and some CSS styling on General Configuration tabs
* Fix imdb and three other images rejected by IExplorer because they were corrupt. Turns out that they were .ico files renamed to either .gif or .png instead of being properly converted
* Clean Subtitles Search settings text, correct quotations, use spaces for code lines, tabs for html
* Implement automatic saving of poster layout sorting options on show list
* Clarify description for backlog searches option on provider settings page
* Fix sort mode "next" with show statuses Paused, Ended, and Continuing as they were random under home/Layout "Poster"
* Fix sort of tvrage show statuses "New" and "Returning" by changing status column text to "Continuing" under home/Layout "Simple"
* Add dark spinner to "Add New Show" (searching indexers), "Add existing shows" (Loading Folders), Coming Eps and all config pages (when saving)
* Change notifier test buttons to not run if required field is missing
* Require fields will now highlight input box and add an icon if field is missing when test is pushed
* Change Test Plex Media Server to Test Plex Client as it only tests the client and not the server
* Style config_notifications to match new config_general styling
* Style config_providers to match new config_general styling
* Remove qtip from providers and moved those options to a tab
* Remove superfish-1.4.8.js and supersubs-0.2b.js as they no longer break provider sorting with qtip removed and is no longer required due to new UI
* Overhaul Config Search Settings in line with General Configuration
* Fix errors occurring when a show folder is deleted outside of SickRage
* Combined delete and remove buttons in to one on individual show pages
* Other small UI tweaks
* Fix keyerrors on backlog overview preventing the page to load
* Fix exception raised when converting 12pm to 24hr format and handle 12am when setting file modify time (e.g. used during PP)
* Fix proxy_indexers setting not loading from config file
* Add subtitle information to the cmd show and cmd shows api output
* Removed requirement for http login for API when an API key is provided
* Change API now uses Timezone setting at General Config/Interface/User Interface/ at relevant endpoints
* Fixes changing root dirs on the mass edit page
* Add the ability to use trash (or Recycle Bin) for selected actions on General Config/Misc/Send to trash
* Add handling for when deleting a show and the show folder no longer exists

[develop changelog]
* Improve display of progress bars in the Downloads columns of the show list page
* Improve display of progress bars under the images in Layout Poster of the show list page
* Fix default top navbar background white-out behaviour on browsers that don't support gradients
* Improve top navbar gradient use for greater cross browser compatibility (e.g. Safari)
* Fix dark theme divider between Season numbers on display show page
* Fix main background and border colour of logs on log page
* Fix "Subtitle Language" drop down font colour when entering text on the Subtitles Search settings
* Add confirmation dialogs back in that were missed due to new UI changes
* Fix the home page from failing to load if a show status contains nothing
* Fix and repositioned show_message on display show to use bootstrap styling
* Remove commented out html from display show accidently left in during UI changes
* Fix display issue of season tables in displayShow view / Display Specials
* Change to suppress reporting of Tornado exception error 1


### 0.2.1 (2014-10-22 06:41:00 UTC)

[full changelog](https://github.com/SickragePVR/SickRage/compare/release_0.2.0...release_0.2.1)

* Fix HDtorrents provider screen scraping


### 0.2.0 (2014-10-21 12:36:50 UTC)

[full changelog](https://github.com/SickragePVR/SickRage/compare/release_0.1.0...release_0.2.0)

* Fix for failed episodes not counted in total
* Fix for custom newznab providers with leading integer in name
* Add checkbox to control proxying of indexers
* Fix crash on general settings page when git output is None
* Add subcentre subtitle provider
* Add return code from hardlinking error to log
* Fix ABD regex for certain filenames
* Miscellaneous UI fixes
* Update Tornado webserver to 4.1dev1 and add the certifi lib dependency
* Fix trending shows page from loading full size poster images
* Add "Archive on first match" to Manage, Mass Update, Edit Selected page
* Fix searching IPTorrentsProvider
* Remove travisci python 2.5 build testing


### 0.1.0 (2014-10-16 12:35:15 UTC)

* Initial release
