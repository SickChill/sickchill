<%!
    import sickbeard
%>

<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8">
        <meta name="robots" content="noindex, nofollow">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width">

        <!-- These values come from css/dark.css and css/light.css -->
        % if sickbeard.THEME_NAME == "dark":
        <meta name="theme-color" content="#15528F">
        % elif sickbeard.THEME_NAME == "light":
        <meta name="theme-color" content="#333333">
        % endif

        <title>SickRage - BRANCH:[${sickbeard.BRANCH}] - ${title}</title>

        <!--[if lt IE 9]>
            <script src="https://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js"></script>
            <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
        <![endif]-->

        <link rel="shortcut icon" href="${sbRoot}/images/ico/favicon.ico">
        <link rel="icon" sizes="16x16 32x32 64x64" href="${sbRoot}/images/ico/favicon.ico">
        <link rel="icon" type="image/png" sizes="196x196" href="${sbRoot}/images/ico/favicon-196.png">
        <link rel="icon" type="image/png" sizes="160x160" href="${sbRoot}/images/ico/favicon-160.png">
        <link rel="icon" type="image/png" sizes="96x96" href="${sbRoot}/images/ico/favicon-96.png">
        <link rel="icon" type="image/png" sizes="64x64" href="${sbRoot}/images/ico/favicon-64.png">
        <link rel="icon" type="image/png" sizes="32x32" href="${sbRoot}/images/ico/favicon-32.png">
        <link rel="icon" type="image/png" sizes="16x16" href="${sbRoot}/images/ico/favicon-16.png">
        <link rel="apple-touch-icon" sizes="152x152" href="${sbRoot}/images/ico/favicon-152.png">
        <link rel="apple-touch-icon" sizes="144x144" href="${sbRoot}/images/ico/favicon-144.png">
        <link rel="apple-touch-icon" sizes="120x120" href="${sbRoot}/images/ico/favicon-120.png">
        <link rel="apple-touch-icon" sizes="114x114" href="${sbRoot}/images/ico/favicon-114.png">
        <link rel="apple-touch-icon" sizes="76x76" href="${sbRoot}/images/ico/favicon-76.png">
        <link rel="apple-touch-icon" sizes="72x72" href="${sbRoot}/images/ico/favicon-72.png">
        <link rel="apple-touch-icon" href="${sbRoot}/images/ico/favicon-57.png">
        <meta name="msapplication-TileColor" content="#FFFFFF">
        <meta name="msapplication-TileImage" content="${sbRoot}/images/ico/favicon-144.png">
        <meta name="msapplication-config" content="${sbRoot}/css/browserconfig.xml">

        <link rel="stylesheet" type="text/css" href="${sbRoot}/css/lib/bootstrap.css?${sbPID}"/>
        <link rel="stylesheet" type="text/css" href="${sbRoot}/css/browser.css?${sbPID}" />
        <link rel="stylesheet" type="text/css" href="${sbRoot}/css/lib/jquery-ui-1.10.4.custom.css?${sbPID}" />
        <link rel="stylesheet" type="text/css" href="${sbRoot}/css/lib/jquery.qtip-2.2.1.min.css?${sbPID}"/>
        <link rel="stylesheet" type="text/css" href="${sbRoot}/css/style.css?${sbPID}"/>
        <link rel="stylesheet" type="text/css" href="${sbRoot}/css/${sickbeard.THEME_NAME}.css?${sbPID}" />
        % if sbLogin:
        <link rel="stylesheet" type="text/css" href="${sbRoot}/css/lib/pnotify.custom.min.css?${sbPID}" />
        <link rel="stylesheet" type="text/css" href="${sbRoot}/css/country-flags.css?${sbPID}"/>
        % endif

        <script type="text/javascript" src="${sbRoot}/js/lib/jquery-1.11.2.min.js?${sbPID}"></script>
        <script type="text/javascript" src="${sbRoot}/js/lib/bootstrap.min.js?${sbPID}"></script>
        <script type="text/javascript" src="${sbRoot}/js/lib/bootstrap-hover-dropdown.min.js?${sbPID}"></script>
        <script type="text/javascript" src="${sbRoot}/js/lib/jquery-ui-1.10.4.custom.min.js?${sbPID}"></script>
        % if sbLogin:
        <script type="text/javascript" src="${sbRoot}/js/lib/jquery.cookie.js?${sbPID}"></script>
        <script type="text/javascript" src="${sbRoot}/js/lib/jquery.cookiejar.js?${sbPID}"></script>
        <script type="text/javascript" src="${sbRoot}/js/lib/jquery.json-2.2.min.js?${sbPID}"></script>
        <script type="text/javascript" src="${sbRoot}/js/lib/jquery.selectboxes.min.js?${sbPID}"></script>
        <script type="text/javascript" src="${sbRoot}/js/lib/jquery.tablesorter-2.17.7.min.js?${sbPID}"></script>
        <script type="text/javascript" src="${sbRoot}/js/lib/jquery.tablesorter.widgets-2.17.7.min.js?${sbPID}"></script>
        <script type="text/javascript" src="${sbRoot}/js/lib/jquery.tablesorter.widget-columnSelector-2.17.7.js?${sbPID}"></script>
        <script type="text/javascript" src="${sbRoot}/js/lib/jquery.qtip-2.2.1.min.js?${sbPID}"></script>
        <script type="text/javascript" src="${sbRoot}/js/lib/pnotify.custom.min.js"></script>
        <script type="text/javascript" src="${sbRoot}/js/lib/jquery.form-3.35.js?${sbPID}"></script>
        <script type="text/javascript" src="${sbRoot}/js/lib/jquery.ui.touch-punch-0.2.2.min.js?${sbPID}"></script>
        <script type="text/javascript" src="${sbRoot}/js/lib/isotope.pkgd.min.js?${sbPID}"></script>
        <script type="text/javascript" src="${sbRoot}/js/lib/jquery.confirm.js?${sbPID}"></script>
        <script type="text/javascript" src="${sbRoot}/js/script.js?${sbPID}"></script>


        % if sickbeard.FUZZY_DATING:
        <script type="text/javascript" src="${sbRoot}/js/moment/moment.min.js?${sbPID}"></script>
        <script type="text/javascript" src="${sbRoot}/js/fuzzyMoment.js?${sbPID}"></script>
        % endif
        <script type="text/javascript" charset="utf-8">
            sbRoot = '${sbRoot}'; // needed for browser.js & ajaxNotifications.js
            //HTML for scrolltopcontrol, which is auto wrapped in DIV w/ ID="topcontrol"
            top_image_html = '<img src="${sbRoot}/images/top.gif" width="31" height="11" alt="Jump to top" />';
            themeSpinner = '${('', '-dark')[sickbeard.THEME_NAME == 'dark']}';
            anonURL = '${sickbeard.ANON_REDIRECT}'
        </script>
        <script type="text/javascript" src="${sbRoot}/js/lib/jquery.scrolltopcontrol-1.1.js"></script>
        <script type="text/javascript" src="${sbRoot}/js/browser.js"></script>
        <script type="text/javascript" src="${sbRoot}/js/ajaxNotifications.js"></script>
        <script type="text/javascript">
            function initActions() {
                $("#SubMenu a[href*='/home/restart/']").addClass('restart').html('<span class="submenu-icon-restart"></span> Restart');
                $("#SubMenu a[href*='/home/shutdown/']").addClass('shutdown').html('<span class="submenu-icon-shutdown"></span> Shutdown');
                $("#SubMenu a[href*='/home/logout/']").html('<span class="ui-icon ui-icon-power"></span> Logout');
                $("#SubMenu a:contains('Edit')").html('<span class="ui-icon ui-icon-pencil"></span> Edit');
                $("#SubMenu a:contains('Remove')").addClass('remove').html('<span class="ui-icon ui-icon-trash"></span> Remove');
                $("#SubMenu a:contains('Clear History')").addClass('clearhistory').html('<span class="ui-icon ui-icon-trash"></span> Clear History');
                $("#SubMenu a:contains('Trim History')").addClass('trimhistory').html('<span class="ui-icon ui-icon-trash"></span> Trim History');
                $("#SubMenu a[href$='/errorlogs/clearerrors/']").html('<span class="ui-icon ui-icon-trash"></span> Clear Errors');
                $("#SubMenu a[href$='/errorlogs/submit_errors/']").html('<span class="ui-icon ui-icon-arrowreturnthick-1-n"></span> Submit Errors');
                $("#SubMenu a:contains('Re-scan')").html('<span class="ui-icon ui-icon-refresh"></span> Re-scan');
                $("#SubMenu a:contains('Backlog Overview')").html('<span class="ui-icon ui-icon-refresh"></span> Backlog Overview');
                $("#SubMenu a[href$='/home/updatePLEX/']").html('<span class="ui-icon ui-icon-refresh"></span> Update PLEX');
                $("#SubMenu a:contains('Force')").html('<span class="ui-icon ui-icon-transfer-e-w"></span> Force Full Update');
                $("#SubMenu a:contains('Rename')").html('<span class="ui-icon ui-icon-tag"></span> Preview Rename');
                $("#SubMenu a[href$='/config/subtitles/']").html('<span class="ui-icon ui-icon-comment"></span> Search Subtitles');
                $("#SubMenu a[href*='/home/subtitleShow']").html('<span class="ui-icon ui-icon-comment"></span> Download Subtitles');
                $("#SubMenu a:contains('Anime')").html('<span class="submenu-icon-anime"></span> Anime');
                $("#SubMenu a:contains('Settings')").html('<span class="ui-icon ui-icon-search"></span> Search Settings');
                $("#SubMenu a:contains('Provider')").html('<span class="ui-icon ui-icon-search"></span> Search Providers');
                $("#SubMenu a:contains('Backup/Restore')").html('<span class="ui-icon ui-icon-gear"></span> Backup/Restore');
                $("#SubMenu a:contains('General')").html('<span class="ui-icon ui-icon-gear"></span> General');
                $("#SubMenu a:contains('Episode Status')").html('<span class="ui-icon ui-icon-transferthick-e-w"></span> Episode Status Management');
                $("#SubMenu a:contains('Missed Subtitle')").html('<span class="ui-icon ui-icon-transferthick-e-w"></span> Missed Subtitles');
                $("#SubMenu a[href$='/home/addShows/']").html('<span class="ui-icon ui-icon-video"></span> Add Show');
                $("#SubMenu a:contains('Processing')").html('<span class="ui-icon ui-icon-folder-open"></span> Post-Processing');
                $("#SubMenu a:contains('Manage Searches')").html('<span class="ui-icon ui-icon-search"></span> Manage Searches');
                $("#SubMenu a:contains('Manage Torrents')").html('<span class="submenu-icon-bittorrent"></span> Manage Torrents');
                $("#SubMenu a[href$='/manage/failedDownloads/']").html('<span class="submenu-icon-failed-download"></span> Failed Downloads');
                $("#SubMenu a:contains('Notification')").html('<span class="ui-icon ui-icon-note"></span> Notifications');
                $("#SubMenu a:contains('Update show in KODI')").html('<span class="submenu-icon-kodi"></span> Update show in KODI');
                $("#SubMenu a[href$='/home/updateKODI/']").html('<span class="submenu-icon-kodi"></span> Update KODI');
                $("#SubMenu a:contains('Update show in Emby')").html('<span class="ui-icon ui-icon-refresh"></span> Update show in Emby');
                $("#SubMenu a[href$='/home/updateEMBY/']").html('<span class="ui-icon ui-icon-refresh"></span> Update Emby');
                $("#SubMenu a:contains('Pause')").html('<span class="ui-icon ui-icon-pause"></span> Pause');
                $("#SubMenu a:contains('Resume')").html('<span class="ui-icon ui-icon-play"></span> Resume');

                $('#SubMenu a span').addClass('pull-left');

            };

            $(document).ready(function() {
                initActions();

                $('.dropdown-toggle').dropdownHover();
            });
        </script>
    <script type="text/javascript" src="${sbRoot}/js/confirmations.js?${sbPID}"></script>
    % endif
    </head>

    <body>
        <nav class="navbar navbar-default navbar-fixed-top" role="navigation">
            <div class="container-fluid">
                <div class="navbar-header">
                    <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#bs-example-navbar-collapse-1">
                        <span class="sr-only">Toggle navigation</span>
                        <span class="icon-bar"></span>
                        <span class="icon-bar"></span>
                        <span class="icon-bar"></span>
                    </button>
                    <a class="navbar-brand" href="${sbRoot}/home/" title="SickRage"><img alt="SickRage" src="${sbRoot}/images/sickrage.png" style="height: 50px;" class="img-responsive pull-left" /></a>
                </div>

            % if sbLogin:
                <div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
                    <ul class="nav navbar-nav navbar-right">
                        <li id="NAVnews" ${('', 'class="active"')[topmenu == 'news']}>
                            <a href="${sbRoot}/news/">News</a>
                        </li>
                        <li id="NAVirc" ${('', 'class="active"')[topmenu == 'irc']}>
                            <a href="${sbRoot}/IRC/">IRC</a>
                        </li>
                        <li id="NAVhome" ${('', 'class="active"')[topmenu == 'home']}>
                            <a href="${sbRoot}/home/">Shows</a>
                        </li>

                        <li id="NAVcomingEpisodes" ${('', 'class="active"')[topmenu == 'comingEpisodes']}>
                            <a href="${sbRoot}/comingEpisodes/">Coming Episodes</a>
                        </li>

                        <li id="NAVhistory" ${('', 'class="active"')[topmenu == 'history']}>
                            <a href="${sbRoot}/history/">History</a>
                        </li>

                        <li id="NAVmanage" class="dropdown ${('', 'active')[topmenu == 'manage']}">
                            <a href="${sbRoot}/manage/" class="dropdown-toggle" data-toggle="dropdown">Manage <b class="caret"></b></a>
                            <ul class="dropdown-menu">
                                <li><a href="${sbRoot}/manage/"><i class="menu-icon-manage"></i>&nbsp;Mass Update</a></li>
                                <li><a href="${sbRoot}/manage/backlogOverview/"><i class="menu-icon-backlog-view"></i>&nbsp;Backlog Overview</a></li>
                                <li><a href="${sbRoot}/manage/manageSearches/"><i class="menu-icon-manage-searches"></i>&nbsp;Manage Searches</a></li>
                                <li><a href="${sbRoot}/manage/episodeStatuses/"><i class="menu-icon-backlog"></i>&nbsp;Episode Status Management</a></li>
                            % if sickbeard.USE_PLEX and sickbeard.PLEX_SERVER_HOST != "":
                                <li><a href="${sbRoot}/home/updatePLEX/"><i class="menu-icon-backlog-view"></i>&nbsp;Update PLEX</a></li>
                            % endif
                            % if sickbeard.USE_KODI and sickbeard.KODI_HOST != "":
                                <li><a href="${sbRoot}/home/updateKODI/"><i class="menu-icon-kodi"></i>&nbsp;Update KODI</a></li>
                            % endif
                            % if sickbeard.USE_EMBY and sickbeard.EMBY_HOST != "" and sickbeard.EMBY_APIKEY != "":
                                <li><a href="${sbRoot}/home/updateEMBY/"><i class="menu-icon-backlog-view"></i>&nbsp;Update Emby</a></li>
                            % endif
                            % if sickbeard.USE_TORRENTS and sickbeard.TORRENT_METHOD != 'blackhole' and (sickbeard.ENABLE_HTTPS and sickbeard.TORRENT_HOST[:5] == 'https' or not sickbeard.ENABLE_HTTPS and sickbeard.TORRENT_HOST[:5] == 'http:'):
                                <li><a href="${sbRoot}/manage/manageTorrents/"><i class="menu-icon-bittorrent"></i>&nbsp;Manage Torrents</a></li>
                            % endif
                            % if sickbeard.USE_FAILED_DOWNLOADS:
                                <li><a href="${sbRoot}/manage/failedDownloads/"><i class="menu-icon-failed-download"></i>&nbsp;Failed Downloads</a></li>
                            % endif
                            % if sickbeard.USE_SUBTITLES:
                                <li><a href="${sbRoot}/manage/subtitleMissed/"><i class="menu-icon-backlog"></i>&nbsp;Missed Subtitle Management</a></li>
                            % endif
                            </ul>
                        </li>

                        <li id="NAVerrorlogs" class="dropdown" ${('', 'class="active"')[topmenu == 'errorlogs']}>
                            <a href="${sbRoot}/errorlogs/" class="dropdown-toggle" data-toggle="dropdown">${logPageTitle} <b class="caret"></b></a>
                            <ul class="dropdown-menu">
                                <li><a href="${sbRoot}/errorlogs/"><i class="menu-icon-viewlog-errors"></i>&nbsp;View Log (Errors)</a></li>
                                <li><a href="${sbRoot}/errorlogs/viewlog/"><i class="menu-icon-viewlog"></i>&nbsp;View Log</a></li>
                            </ul>
                        </li>

                        <li id="NAVconfig" class="dropdown" ${('', 'class="active"')[topmenu == 'config']}>
                            <a href="${sbRoot}/config/" class="dropdown-toggle" data-toggle="dropdown"><img src="${sbRoot}/images/menu/system18.png" class="navbaricon hidden-xs" /><b class="caret hidden-xs"></b><span class="visible-xs">Config <b class="caret"></b></span></a>
                            <ul class="dropdown-menu">
                                <li><a href="${sbRoot}/config/"><i class="menu-icon-help"></i>&nbsp;Help &amp; Info</a></li>
                                <li><a href="${sbRoot}/config/general/"><i class="menu-icon-config"></i>&nbsp;General</a></li>
                                <li><a href="${sbRoot}/config/backuprestore/"><i class="menu-icon-config"></i>&nbsp;Backup &amp; Restore</a></li>
                                <li><a href="${sbRoot}/config/search/"><i class="menu-icon-config"></i>&nbsp;Search Settings</a></li>
                                <li><a href="${sbRoot}/config/providers/"><i class="menu-icon-config"></i>&nbsp;Search Providers</a></li>
                                <li><a href="${sbRoot}/config/subtitles/"><i class="menu-icon-config"></i>&nbsp;Subtitles Settings</a></li>
                                <li><a href="${sbRoot}/config/postProcessing/"><i class="menu-icon-config"></i>&nbsp;Post Processing</a></li>
                                <li><a href="${sbRoot}/config/notifications/"><i class="menu-icon-config"></i>&nbsp;Notifications</a></li>
                                <li><a href="${sbRoot}/config/anime/"><i class="menu-icon-config"></i>&nbsp;Anime</a></li>
                            </ul>
                        </li>

                        <li class="dropdown">
                            <a href="#" class="dropdown-toggle" data-toggle="dropdown"><img src="${sbRoot}/images/menu/system18-2.png" class="navbaricon hidden-xs" /><b class="caret hidden-xs"></b><span class="visible-xs">System <b class="caret"></b></span></a>
                            <ul class="dropdown-menu">
                                <li><a href="${sbRoot}/home/updateCheck?pid=${sbPID}"><i class="menu-icon-update"></i>&nbsp;Check For Updates</a></li>
                                <li><a href="${sbRoot}/changes"><i class="menu-icon-help"></i>&nbsp;Changelog</a></li>
                                <li><a href="${sbRoot}/home/restart/?pid=${sbPID}" class="confirm restart"><i class="menu-icon-restart"></i>&nbsp;Restart</a></li>
                                <li><a href="${sbRoot}/home/shutdown/?pid=${sbPID}" class="confirm shutdown"><i class="menu-icon-shutdown"></i>&nbsp;Shutdown</a></li>
                                <li><a href="${sbRoot}/logout" class="confirm logout"><i class="menu-icon-shutdown"></i>&nbsp;Logout</a></li>
                                <li><a href="${sbRoot}/home/status/"><i class="menu-icon-help"></i>&nbsp;Server Status</a></li>
                            </ul>
                        </li>
                        <li id="donate"><a href="https://github.com/SiCKRAGETV/SickRage/wiki/Donations" rel="noreferrer" onclick="window.open('${sickbeard.ANON_REDIRECT}' + this.href); return false;"><img src="${sbRoot}/images/donate.jpg" alt="[donate]" class="navbaricon hidden-xs" /></a></li>
                    </ul>
            % endif
                </div><!-- /.navbar-collapse -->
            </div><!-- /.container-fluid -->
        </nav>

        % if not submenu is UNDEFINED:
        <div id="SubMenu">
        <span>
        <% first = True %>
        % for menuItem in submenu:
            % if 'requires' not in menuItem or menuItem['requires']:
                  % if type(menuItem['path']) == dict:
                      ${("</span><span>", "")[bool(first)]}<b>${menuItem['title']}</b>
                      <%
                          first = False
                          inner_first = True
                      %>
                      % for cur_link in menuItem['path']:
                          ${("&middot; ", "")[bool(inner_first)]}<a class="inner" href="${sbRoot}/${menuItem['path'][cur_link]}">${cur_link}</a>
                          <% inner_first = False %>
                      % endfor
                  % else:
                      <a href="${sbRoot}/${menuItem['path']}" class="btn${('', ' confirm')['confirm' in menuItem]}">${menuItem['title']}</a>
                      <% first = False %>
                  % endif
            % endif
        % endfor
        </span>
        </div>
        % endif

        % if sickbeard.BRANCH and sickbeard.BRANCH != 'master' and not sickbeard.DEVELOPER and sbLogin:
        <div class="alert alert-danger upgrade-notification" role="alert">
            <span>You're using the ${sickbeard.BRANCH} branch. Please use 'master' unless specifically asked</span>
        </div>
        % endif

        % if sickbeard.NEWEST_VERSION_STRING and sbLogin:
        <div class="alert alert-success upgrade-notification" role="alert">
            <span>${sickbeard.NEWEST_VERSION_STRING}</span>
        </div>
        % endif

<div id="contentWrapper">
    <div id="content">
