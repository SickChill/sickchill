<%!
    import sickbeard
    import datetime
    from sickbeard import db, network_timezones
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
    srRoot = sickbeard.WEB_ROOT
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
        <meta name="msapplication-TileImage" content="${srRoot}/images/ico/favicon-144.png">
        <meta name="msapplication-config" content="${srRoot}/css/browserconfig.xml">


        <meta data-var="srRoot" data-content="${srRoot}">
        <meta data-var="themeSpinner" data-content="${('', '-dark')[sickbeard.THEME_NAME == 'dark']}">
        <meta data-var="anonURL" data-content="${sickbeard.ANON_REDIRECT}">

        <meta data-var="sickbeard.ANIME_SPLIT_HOME" data-content="${sickbeard.ANIME_SPLIT_HOME}">
        <meta data-var="sickbeard.COMING_EPS_LAYOUT" data-content="${sickbeard.COMING_EPS_LAYOUT}">
        <meta data-var="sickbeard.COMING_EPS_SORT" data-content="${sickbeard.COMING_EPS_SORT}">
        <meta data-var="sickbeard.DATE_PRESET" data-content="${sickbeard.DATE_PRESET}">
        <meta data-var="sickbeard.FILTER_ROW" data-content="${sickbeard.FILTER_ROW}">
        <meta data-var="sickbeard.FUZZY_DATING" data-content="${sickbeard.FUZZY_DATING}">
        <meta data-var="sickbeard.HISTORY_LAYOUT" data-content="${sickbeard.HISTORY_LAYOUT}">
        <meta data-var="sickbeard.HOME_LAYOUT" data-content="${sickbeard.HOME_LAYOUT}">
        <meta data-var="sickbeard.POSTER_SORTBY" data-content="${sickbeard.POSTER_SORTBY}">
        <meta data-var="sickbeard.POSTER_SORTDIR" data-content="${sickbeard.POSTER_SORTDIR}">
        <meta data-var="sickbeard.ROOT_DIRS" data-content="${sickbeard.ROOT_DIRS}">
        <meta data-var="sickbeard.SORT_ARTICLE" data-content="${sickbeard.SORT_ARTICLE}">
        <meta data-var="sickbeard.TIME_PRESET" data-content="${sickbeard.TIME_PRESET}">
        <meta data-var="sickbeard.TRIM_ZERO" data-content="${sickbeard.TRIM_ZERO}">
        <%block name="metas" />

        <link rel="shortcut icon" href="${srRoot}/images/ico/favicon.ico">
        <link rel="icon" sizes="16x16 32x32 64x64" href="${srRoot}/images/ico/favicon.ico">
        <link rel="icon" type="image/png" sizes="196x196" href="${srRoot}/images/ico/favicon-196.png">
        <link rel="icon" type="image/png" sizes="160x160" href="${srRoot}/images/ico/favicon-160.png">
        <link rel="icon" type="image/png" sizes="96x96" href="${srRoot}/images/ico/favicon-96.png">
        <link rel="icon" type="image/png" sizes="64x64" href="${srRoot}/images/ico/favicon-64.png">
        <link rel="icon" type="image/png" sizes="32x32" href="${srRoot}/images/ico/favicon-32.png">
        <link rel="icon" type="image/png" sizes="16x16" href="${srRoot}/images/ico/favicon-16.png">
        <link rel="apple-touch-icon" sizes="152x152" href="${srRoot}/images/ico/favicon-152.png">
        <link rel="apple-touch-icon" sizes="144x144" href="${srRoot}/images/ico/favicon-144.png">
        <link rel="apple-touch-icon" sizes="120x120" href="${srRoot}/images/ico/favicon-120.png">
        <link rel="apple-touch-icon" sizes="114x114" href="${srRoot}/images/ico/favicon-114.png">
        <link rel="apple-touch-icon" sizes="76x76" href="${srRoot}/images/ico/favicon-76.png">
        <link rel="apple-touch-icon" sizes="72x72" href="${srRoot}/images/ico/favicon-72.png">
        <link rel="apple-touch-icon" href="${srRoot}/images/ico/favicon-57.png">

        <link rel="stylesheet" type="text/css" href="${srRoot}/css/lib/bootstrap.min.css?${sbPID}"/>
        <link rel="stylesheet" type="text/css" href="${srRoot}/css/browser.css?${sbPID}" />
        <link rel="stylesheet" type="text/css" href="${srRoot}/css/lib/jquery-ui-1.10.4.custom.min.css?${sbPID}" />
        <link rel="stylesheet" type="text/css" href="${srRoot}/css/lib/jquery.qtip-2.2.1.min.css?${sbPID}"/>
        <link rel="stylesheet" type="text/css" href="${srRoot}/css/style.css?${sbPID}"/>
        <link rel="stylesheet" type="text/css" href="${srRoot}/css/${sickbeard.THEME_NAME}.css?${sbPID}" />
        <link rel="stylesheet" type="text/css" href="${srRoot}/css/print.css?${sbPID}" />
        % if sbLogin:
        <link rel="stylesheet" type="text/css" href="${srRoot}/css/lib/pnotify.custom.min.css?${sbPID}" />
        <link rel="stylesheet" type="text/css" href="${srRoot}/css/country-flags.css?${sbPID}"/>
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
                    <a class="navbar-brand" href="${srRoot}/home/" title="SickRage"><img alt="SickRage" src="${srRoot}/images/sickrage.png" style="height: 50px;" class="img-responsive pull-left" /></a>
                </div>

            % if sbLogin:
                <div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
                    <ul class="nav navbar-nav navbar-right">
                        <li id="NAVhome" class="navbar-split dropdown${('', ' active')[topmenu == 'home']}">
                            <a href="${srRoot}/home/" class="dropdown-toggle">Shows</a>
                            <a href="#" class="dropdown-toggle" data-toggle="dropdown"><b class="caret"></b></a>
                            <ul class="dropdown-menu">
                                <li><a href="${srRoot}/home/"><i class="menu-icon-home"></i>&nbsp;Show List</a></li>
                                <li><a href="${srRoot}/home/addShows/"><i class="menu-icon-addshow"></i>&nbsp;Add Shows</a></li>
                                <li><a href="${srRoot}/home/postprocess/"><i class="menu-icon-postprocess"></i>&nbsp;Manual Post-Processing</a></li>
                                % if sickbeard.SHOWS_RECENT:
                                    <li role="separator" class="divider"></li>
                                    % for recentShow in sickbeard.SHOWS_RECENT:
                                        <li><a href="${srRoot}/home/displayShow/?show=${recentShow['indexerid']}"><i class="menu-icon-addshow"></i>&nbsp;${recentShow['name']|trim,h}</a></li>
                                    % endfor
                                % endif
                            </ul>
                            <div style="clear:both;"></div>
                        </li>

                        <li id="NAVschedule"${('', ' class="active"')[topmenu == 'schedule']}>
                            <a href="${srRoot}/schedule/">Schedule</a>
                        </li>

                        <li id="NAVhistory"${('', ' class="active"')[topmenu == 'history']}>
                            <a href="${srRoot}/history/">History</a>
                        </li>

                        <li id="NAVmanage" class="navbar-split dropdown${('', ' active')[topmenu == 'manage']}">
                            <a href="${srRoot}/manage/episodeStatuses/" class="dropdown-toggle">Manage</a>
                            <a href="#" class="dropdown-toggle" data-toggle="dropdown"><b class="caret"></b></a>
                            <ul class="dropdown-menu">
                                <li><a href="${srRoot}/manage/"><i class="menu-icon-manage"></i>&nbsp;Mass Update</a></li>
                                <li><a href="${srRoot}/manage/backlogOverview/"><i class="menu-icon-backlog-view"></i>&nbsp;Backlog Overview</a></li>
                                <li><a href="${srRoot}/manage/manageSearches/"><i class="menu-icon-manage-searches"></i>&nbsp;Manage Searches</a></li>
                                <li><a href="${srRoot}/manage/episodeStatuses/"><i class="menu-icon-backlog"></i>&nbsp;Episode Status Management</a></li>
                            % if sickbeard.USE_PLEX and sickbeard.PLEX_SERVER_HOST != "":
                                <li><a href="${srRoot}/home/updatePLEX/"><i class="menu-icon-backlog-view"></i>&nbsp;Update PLEX</a></li>
                            % endif
                            % if sickbeard.USE_KODI and sickbeard.KODI_HOST != "":
                                <li><a href="${srRoot}/home/updateKODI/"><i class="menu-icon-kodi"></i>&nbsp;Update KODI</a></li>
                            % endif
                            % if sickbeard.USE_EMBY and sickbeard.EMBY_HOST != "" and sickbeard.EMBY_APIKEY != "":
                                <li><a href="${srRoot}/home/updateEMBY/"><i class="menu-icon-backlog-view"></i>&nbsp;Update Emby</a></li>
                            % endif
                            % if sickbeard.USE_TORRENTS and sickbeard.TORRENT_METHOD != 'blackhole' and (sickbeard.ENABLE_HTTPS and sickbeard.TORRENT_HOST[:5] == 'https' or not sickbeard.ENABLE_HTTPS and sickbeard.TORRENT_HOST[:5] == 'http:'):
                                <li><a href="${srRoot}/manage/manageTorrents/"><i class="menu-icon-bittorrent"></i>&nbsp;Manage Torrents</a></li>
                            % endif
                            % if sickbeard.USE_FAILED_DOWNLOADS:
                                <li><a href="${srRoot}/manage/failedDownloads/"><i class="menu-icon-failed-download"></i>&nbsp;Failed Downloads</a></li>
                            % endif
                            % if sickbeard.USE_SUBTITLES:
                                <li><a href="${srRoot}/manage/subtitleMissed/"><i class="menu-icon-backlog"></i>&nbsp;Missed Subtitle Management</a></li>
                            % endif
                            </ul>
                            <div style="clear:both;"></div>
                        </li>

                        <li id="NAVconfig" class="navbar-split dropdown${('', ' active')[topmenu == 'config']}">
                            <a href="${srRoot}/config/" class="dropdown-toggle"><span class="visible-xs">Config</span><img src="${srRoot}/images/menu/system18.png" class="navbaricon hidden-xs" /></a>
                            <a href="#" class="dropdown-toggle" data-toggle="dropdown"><b class="caret"></b></a>
                            <ul class="dropdown-menu">
                                <li><a href="${srRoot}/config/"><i class="menu-icon-help"></i>&nbsp;Help &amp; Info</a></li>
                                <li><a href="${srRoot}/config/general/"><i class="menu-icon-config"></i>&nbsp;General</a></li>
                                <li><a href="${srRoot}/config/backuprestore/"><i class="menu-icon-config"></i>&nbsp;Backup &amp; Restore</a></li>
                                <li><a href="${srRoot}/config/search/"><i class="menu-icon-config"></i>&nbsp;Search Settings</a></li>
                                <li><a href="${srRoot}/config/providers/"><i class="menu-icon-config"></i>&nbsp;Search Providers</a></li>
                                <li><a href="${srRoot}/config/subtitles/"><i class="menu-icon-config"></i>&nbsp;Subtitles Settings</a></li>
                                <li><a href="${srRoot}/config/postProcessing/"><i class="menu-icon-config"></i>&nbsp;Post Processing</a></li>
                                <li><a href="${srRoot}/config/notifications/"><i class="menu-icon-config"></i>&nbsp;Notifications</a></li>
                                <li><a href="${srRoot}/config/anime/"><i class="menu-icon-config"></i>&nbsp;Anime</a></li>
                            </ul>
                            <div style="clear:both;"></div>
                        </li>

                        <%
                            if sickbeard.NEWS_UNREAD:
                                newsBadge = ' <span class="badge">'+str(sickbeard.NEWS_UNREAD)+'</span>'
                            else:
                                newsBadge = ''

                            numCombined = numErrors + numWarnings + sickbeard.NEWS_UNREAD
                            if numCombined:
                                if numErrors:
                                    toolsBadgeClass = ' btn-danger'
                                elif numWarnings:
                                    toolsBadgeClass = ' btn-warning'
                                else:
                                    toolsBadgeClass = ''

                                toolsBadge = ' <span class="badge'+toolsBadgeClass+'">'+str(numCombined)+'</span>'
                            else:
                                toolsBadge = ''
                        %>
                        <li id="NAVsystem" class="navbar-split dropdown${('', ' active')[topmenu == 'system']}">
                            <a href="${srRoot}/home/status/" class="dropdown-toggle"><span class="visible-xs">Tools</span><img src="${srRoot}/images/menu/system18-2.png" class="navbaricon hidden-xs" />${toolsBadge}</a>
                            <a href="#" class="dropdown-toggle" data-toggle="dropdown"><b class="caret"></b></a>
                            <ul class="dropdown-menu">
                                <li><a href="${srRoot}/news/"><i class="menu-icon-help"></i>&nbsp;News${newsBadge}</a></li>
                                <li><a href="${srRoot}/IRC/"><i class="menu-icon-help"></i>&nbsp;IRC</a></li>
                                <li><a href="${srRoot}/changes/"><i class="menu-icon-help"></i>&nbsp;Changelog</a></li>
                                <li><a href="https://github.com/SiCKRAGETV/SickRage/wiki/Donations" rel="noreferrer" onclick="window.open('${sickbeard.ANON_REDIRECT}' + this.href); return false;"><i class="menu-icon-help"></i>&nbsp;Support SickRage</a></li>
                                <li role="separator" class="divider"></li>
                                %if numErrors:
                                    <li><a href="${srRoot}/errorlogs/"><i class="menu-icon-viewlog-errors"></i>&nbsp;View Errors <span class="badge btn-danger">${numErrors}</span></a></li>
                                %endif
                                %if numWarnings:
                                    <li><a href="${srRoot}/errorlogs/?level=${sickbeard.logger.WARNING}"><i class="menu-icon-viewlog-errors"></i>&nbsp;View Warnings <span class="badge btn-warning">${numWarnings}</span></a></li>
                                %endif
                                <li><a href="${srRoot}/errorlogs/viewlog/"><i class="menu-icon-viewlog"></i>&nbsp;View Log</a></li>
                                <li role="separator" class="divider"></li>
                                <li><a href="${srRoot}/home/updateCheck?pid=${sbPID}"><i class="menu-icon-update"></i>&nbsp;Check For Updates</a></li>
                                <li><a href="${srRoot}/home/restart/?pid=${sbPID}" class="confirm restart"><i class="menu-icon-restart"></i>&nbsp;Restart</a></li>
                                <li><a href="${srRoot}/home/shutdown/?pid=${sbPID}" class="confirm shutdown"><i class="menu-icon-shutdown"></i>&nbsp;Shutdown</a></li>
                                % if sbLogin != True:
                                    <li><a href="${srRoot}/logout" class="confirm logout"><i class="menu-icon-shutdown"></i>&nbsp;Logout</a></li>
                                % endif
                                <li role="separator" class="divider"></li>
                                <li><a href="${srRoot}/home/status/"><i class="menu-icon-help"></i>&nbsp;Server Status</a></li>
                            </ul>
                            <div style="clear:both;"></div>
                        </li>
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
                              ${("&middot; ", "")[bool(inner_first)]}<a class="inner" href="${srRoot}/${menuItem['path'][cur_link]}">${cur_link}</a>
                              <% inner_first = False %>
                          % endfor
                      % else:
                          <a href="${srRoot}/${menuItem['path']}" class="btn${('', (' confirm ' + menuItem.get('class', '')))['confirm' in menuItem]}">${('', '<span class="pull-left ' + icon_class + '"></span> ')[bool(icon_class)]}${menuItem['title']}</a>
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
                status_download = '(%s)' % ','.join([str(quality) for quality in Quality.DOWNLOADED + Quality.ARCHIVED])

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
                    localRoot = srRoot
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
                    Branch: <span class="footerhighlight">${sickbeard.BRANCH}</span> |
                    Now: <span class="footerhighlight">${datetime.datetime.now(network_timezones.sb_timezone)}</span>
                </div>
            </div>
        </footer>
        <script type="text/javascript" src="${srRoot}/js/_bower.min.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/lib/jquery.cookie.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/lib/jquery.cookiejar.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/lib/jquery.json-2.2.min.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/lib/jquery.selectboxes.min.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/lib/jquery.tablesorter-2.17.7.min.js?${sbPID}"></script><!-- Can't be added to bower -->
        <script type="text/javascript" src="${srRoot}/js/lib/jquery.tablesorter.widgets-2.17.7.min.js?${sbPID}"></script><!-- Can't be added to bower -->
        <script type="text/javascript" src="${srRoot}/js/lib/jquery.tablesorter.widget-columnSelector-2.17.7.js?${sbPID}"></script><!-- Can't be added to bower -->
        <script type="text/javascript" src="${srRoot}/js/lib/jquery.qtip-2.2.1.min.js?${sbPID}"></script><!-- Can't be added to bower -->
        <script type="text/javascript" src="${srRoot}/js/lib/jquery.ui.touch-punch-0.2.2.min.js?${sbPID}"></script><!-- Can't be added to bower -->
        <script type="text/javascript" src="${srRoot}/js/lib/isotope.pkgd.min.js?${sbPID}"></script><!-- Can't be added to bower -->
        <script type="text/javascript" src="${srRoot}/js/lib/jquery.confirm.js?${sbPID}"></script><!-- Can't be added to bower -->
        <script type="text/javascript" src="${srRoot}/js/lib/formwizard.js?${sbPID}"></script><!-- Can't be added to bower -->
        <script type="text/javascript" src="${srRoot}/js/lib/pnotify.custom.min.js?${sbPID}"></script><!-- Needs to be removed -->
        <script type="text/javascript" src="${srRoot}/js/new/parsers.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/new/meta.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/new/core.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/lib/jquery.scrolltopcontrol-1.1.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/browser.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/ajaxNotifications.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/confirmations.js?${sbPID}"></script>
    % endif
        <%block name="scripts" />
    </body>
</html>
