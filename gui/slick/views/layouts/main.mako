<%!
    import sickbeard
    import datetime
    from sickbeard import db
    from sickbeard.common import Quality, SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickbeard.common import qualityPresets, qualityPresetStrings
    import calendar
    from time import time
    import re

    # resource module is unix only
    has_resource_module = True
    try:
        import resource
    except ImportError:
        has_resource_module = False
%>
<%
    sbRoot = sickbeard.WEB_ROOT
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
        <meta name="msapplication-TileColor" content="#FFFFFF">
        <meta name="msapplication-TileImage" content="${sbRoot}/images/ico/favicon-144.png">
        <meta name="msapplication-config" content="${sbRoot}/css/browserconfig.xml">

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

        <link rel="stylesheet" type="text/css" href="${sbRoot}/css/lib/bootstrap.min.css?${sbPID}"/>
        <link rel="stylesheet" type="text/css" href="${sbRoot}/css/browser.css?${sbPID}" />
        <link rel="stylesheet" type="text/css" href="${sbRoot}/css/lib/jquery-ui-1.10.4.custom.min.css?${sbPID}" />
        <link rel="stylesheet" type="text/css" href="${sbRoot}/css/lib/jquery.qtip-2.2.1.min.css?${sbPID}"/>
        <link rel="stylesheet" type="text/css" href="${sbRoot}/css/style.css?${sbPID}"/>
        <link rel="stylesheet" type="text/css" href="${sbRoot}/css/${sickbeard.THEME_NAME}.css?${sbPID}" />
        <link rel="stylesheet" type="text/css" href="${sbRoot}/css/print.css?${sbPID}" />
        % if sbLogin:
        <link rel="stylesheet" type="text/css" href="${sbRoot}/css/lib/pnotify.custom.min.css?${sbPID}" />
        <link rel="stylesheet" type="text/css" href="${sbRoot}/css/country-flags.css?${sbPID}"/>
        % endif
        <%block name="css" />
    </head>

    <body>
        <nav class="navbar navbar-default navbar-fixed-top hidden-print" role="navigation">
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
        <div id="SubMenu" class="hidden-print">
            <span>
            <% first = True %>
            % for menuItem in submenu:
                % if 'requires' not in menuItem or menuItem['requires']:
                    <% icon_class = '' if 'icon' not in menuItem else ' ' + menuItem['icon'] %>
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
                          <a href="${sbRoot}/${menuItem['path']}" class="btn${('', (' confirm ' + menuItem.get('class', '')))['confirm' in menuItem]}">${('', '<span class="pull-left ' + icon_class + '"></span> ')[bool(icon_class)]}${menuItem['title']}</a>
                          <% first = False %>
                      % endif
                % endif
            % endfor
            </span>
        </div>
        % endif

        % if sickbeard.BRANCH and sickbeard.BRANCH != 'master' and not sickbeard.DEVELOPER and sbLogin:
        <div class="alert alert-danger upgrade-notification hidden-print" role="alert">
            <span>You're using the ${sickbeard.BRANCH} branch. Please use 'master' unless specifically asked</span>
        </div>
        % endif

        % if sickbeard.NEWEST_VERSION_STRING and sbLogin:
        <div class="alert alert-success upgrade-notification hidden-print" role="alert">
            <span>${sickbeard.NEWEST_VERSION_STRING}</span>
        </div>
        % endif

        <div id="contentWrapper">
            <div id="content">
                <%block name="content" />
            </div> <!-- /content -->
        </div> <!-- /contentWrapper -->
    % if sbLogin:
        <footer>
            <div class="footer clearfix">
            <%
                myDB = db.DBConnection()
                today = str(datetime.date.today().toordinal())
                status_quality = '(%s)' % ','.join([str(quality) for quality in Quality.SNATCHED + Quality.SNATCHED_PROPER])
                status_download = '(%s)' % ','.join([str(quality) for quality in Quality.DOWNLOADED + [ARCHIVED]])

                sql_statement = 'SELECT ' \
                + '(SELECT COUNT(*) FROM tv_episodes WHERE season > 0 AND episode > 0 AND airdate > 1 AND status IN %s) AS ep_snatched, ' % status_quality \
                + '(SELECT COUNT(*) FROM tv_episodes WHERE season > 0 AND episode > 0 AND airdate > 1 AND status IN %s) AS ep_downloaded, ' % status_download \
                + '(SELECT COUNT(*) FROM tv_episodes WHERE season > 0 AND episode > 0 AND airdate > 1 AND ((airdate <= %s AND (status = %s OR status = %s)) ' % (today, str(SKIPPED), str(WANTED)) \
                + ' OR (status IN %s) OR (status IN %s))) AS ep_total FROM tv_episodes tv_eps LIMIT 1' % (status_quality, status_download)

                sql_result = myDB.select(sql_statement)

                shows_total = len(sickbeard.showList)
                shows_active = len([show for show in sickbeard.showList if show.paused == 0 and show.status == "Continuing"])

                if sql_result:
                    ep_snatched = sql_result[0]['ep_snatched']
                    ep_downloaded = sql_result[0]['ep_downloaded']
                    ep_total = sql_result[0]['ep_total']
                else:
                    ep_snatched = 0
                    ep_downloaded = 0
                    ep_total = 0

                ep_percentage = '' if ep_total == 0 else '(<span class="footerhighlight">%s%%</span>)' % re.sub(r'(\d+)(\.\d)\d+', r'\1\2', str((float(ep_downloaded)/float(ep_total))*100))

                try:
                    localRoot = sbRoot
                except NotFound:
                    localRoot = ''

                try:
                    localheader = header
                except NotFound:
                    localheader = ''
            %>
                <span class="footerhighlight">${shows_total}</span> Shows (<span class="footerhighlight">${shows_active}</span> Active)
                | <span class="footerhighlight">${ep_downloaded}</span>

                % if ep_snatched:
                <span class="footerhighlight"><a href="${localRoot}/manage/episodeStatuses?whichStatus=2" title="View overview of snatched episodes">+${ep_snatched}</a></span> Snatched
                % endif

                        &nbsp;/&nbsp;<span class="footerhighlight">${ep_total}</span> Episodes Downloaded ${ep_percentage}
                | Daily Search: <span class="footerhighlight">${str(sickbeard.dailySearchScheduler.timeLeft()).split('.')[0]}</span>
                | Backlog Search: <span class="footerhighlight">${str(sickbeard.backlogSearchScheduler.timeLeft()).split('.')[0]}</span>

                <div>
                    % if has_resource_module:
                    Memory used: <span class="footerhighlight">${sickbeard.helpers.pretty_filesize(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)}</span> |
                    % endif
                    Load time: <span class="footerhighlight">${"%.4f" % (time() - sbStartTime)}s</span> / Mako: <span class="footerhighlight">${"%.4f" % (time() - makoStartTime)}s</span> |
                    Branch: <span class="footerhighlight">${sickbeard.BRANCH}</span>
                </div>
            </div>
        </footer>
        <script type="text/javascript" src="${sbRoot}/js/lib/jquery-1.11.2.min.js?${sbPID}"></script>
        <script type="text/javascript" src="${sbRoot}/js/lib/bootstrap.min.js?${sbPID}"></script>
        <script type="text/javascript" src="${sbRoot}/js/lib/bootstrap-hover-dropdown.min.js?${sbPID}"></script>
        <script type="text/javascript" src="${sbRoot}/js/lib/jquery-ui-1.10.4.custom.min.js?${sbPID}"></script>
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
        <script type="text/javascript">
            sbRoot = '${sbRoot}'; // needed for browser.js & ajaxNotifications.js
            //HTML for scrolltopcontrol, which is auto wrapped in DIV w/ ID="topcontrol"
            top_image_html = '<img src="${sbRoot}/images/top.gif" width="31" height="11" alt="Jump to top" />';
            themeSpinner = '${('', '-dark')[sickbeard.THEME_NAME == 'dark']}';
            anonURL = '${sickbeard.ANON_REDIRECT}';
        </script>
        <script type="text/javascript" src="${sbRoot}/js/lib/jquery.scrolltopcontrol-1.1.js"></script>
        <script type="text/javascript" src="${sbRoot}/js/browser.js"></script>
        <script type="text/javascript" src="${sbRoot}/js/ajaxNotifications.js"></script>
        <script type="text/javascript" src="${sbRoot}/js/confirmations.js?${sbPID}"></script>
    % endif
        <script type="text/javascript">
            $(document).ready(function() {
                $('.dropdown-toggle').dropdownHover();
            });
        </script>
        <%block name="scripts" />
    </body>
</html>
