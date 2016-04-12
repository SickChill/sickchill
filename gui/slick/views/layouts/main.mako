<%!
    import re
    import datetime
    import sickbeard
    from sickrage.helper.common import pretty_file_size
    from sickrage.show.Show import Show
    from time import time

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
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0">

        <!-- These values come from css/dark.css and css/light.css -->
        % if sickbeard.THEME_NAME == "dark":
        <meta name="theme-color" content="#15528F">
        % elif sickbeard.THEME_NAME == "light":
        <meta name="theme-color" content="#333333">
        % endif

        <title>SickRage - ${title}</title>

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

        <link rel="stylesheet" type="text/css" href="${srRoot}/css/vender.min.css?${sbPID}"/>
        <link rel="stylesheet" type="text/css" href="${srRoot}/css/browser.css?${sbPID}" />
        <link rel="stylesheet" type="text/css" href="${srRoot}/css/lib/jquery-ui-1.10.4.custom.min.css?${sbPID}" />
        <link rel="stylesheet" type="text/css" href="${srRoot}/css/lib/jquery.qtip-2.2.1.min.css?${sbPID}"/>
        <link rel="stylesheet" type="text/css" href="${srRoot}/css/style.css?${sbPID}"/>
        <link rel="stylesheet" type="text/css" href="${srRoot}/css/${sickbeard.THEME_NAME}.css?${sbPID}" />
        <link rel="stylesheet" type="text/css" href="${srRoot}/css/print.css?${sbPID}" />
        % if srLogin:
        <link rel="stylesheet" type="text/css" href="${srRoot}/css/country-flags.css?${sbPID}"/>
        % endif
        <%block name="css" />
    </head>
    <body data-controller="${controller}" data-action="${action}">
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

            % if srLogin:
                <div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
                    <ul class="nav navbar-nav navbar-right">
                        <li id="NAVhome" class="navbar-split dropdown${('', ' active')[topmenu == 'home']}">
                            <a href="${srRoot}/home/" class="dropdown-toggle" aria-haspopup="true" data-toggle="dropdown" data-hover="dropdown"><span>${_('Shows')}</span>
                            <b class="caret"></b>
                            </a>
                            <ul class="dropdown-menu">
                                <li><a href="${srRoot}/home/"><i class="menu-icon-home"></i>&nbsp;${_('Show List')}</a></li>
                                <li><a href="${srRoot}/addShows/"><i class="menu-icon-addshow"></i>&nbsp;${_('Add Shows')}</a></li>
                                <li><a href="${srRoot}/home/postprocess/"><i class="menu-icon-postprocess"></i>&nbsp;${_('Manual Post-Processing')}</a></li>
                                % if sickbeard.SHOWS_RECENT:
                                    <li role="separator" class="divider"></li>
                                    % for recent_show in sickbeard.SHOWS_RECENT:
                                        <li><a href="${srRoot}/home/displayShow?show=${recent_show['indexerid']}"><i class="menu-icon-addshow"></i>&nbsp;${recent_show['name']|trim,h}</a></li>
                                    % endfor
                                % endif
                            </ul>
                            <div style="clear:both;"></div>
                        </li>

                        <li id="NAVschedule"${('', ' class="active"')[topmenu == 'schedule']}>
                            <a href="${srRoot}/schedule/">${_('Schedule')}</a>
                        </li>

                        <li id="NAVhistory"${('', ' class="active"')[topmenu == 'history']}>
                            <a href="${srRoot}/history/">${_('History')}</a>
                        </li>

                        <li id="NAVmanage" class="navbar-split dropdown${('', ' active')[topmenu == 'manage']}">
                            <a href="${srRoot}/manage/episodeStatuses/" class="dropdown-toggle" aria-haspopup="true" data-toggle="dropdown" data-hover="dropdown"><span>${_('Manage')}</span>
                            <b class="caret"></b>
                            </a>
                            <ul class="dropdown-menu">
                                <li><a href="${srRoot}/manage/"><i class="menu-icon-manage"></i>&nbsp;${_('Mass Update')}</a></li>
                                <li><a href="${srRoot}/manage/backlogOverview/"><i class="menu-icon-backlog-view"></i>&nbsp;${_('Backlog Overview')}</a></li>
                                <li><a href="${srRoot}/manage/manageSearches/"><i class="menu-icon-manage-searches"></i>&nbsp;${_('Manage Searches')}</a></li>
                                <li><a href="${srRoot}/manage/episodeStatuses/"><i class="menu-icon-manage2"></i>&nbsp;${_('Episode Status Management')}</a></li>
                            % if sickbeard.USE_PLEX_SERVER and sickbeard.PLEX_SERVER_HOST != "":
                                <li><a href="${srRoot}/home/updatePLEX/"><i class="menu-icon-plex"></i>&nbsp;${_('Update PLEX')}</a></li>
                            % endif
                            % if sickbeard.USE_KODI and sickbeard.KODI_HOST != "":
                                <li><a href="${srRoot}/home/updateKODI/"><i class="menu-icon-kodi"></i>&nbsp;${_('Update KODI')}</a></li>
                            % endif
                            % if sickbeard.USE_EMBY and sickbeard.EMBY_HOST != "" and sickbeard.EMBY_APIKEY != "":
                                <li><a href="${srRoot}/home/updateEMBY/"><i class="menu-icon-emby"></i>&nbsp;${_('Update Emby')}</a></li>
                            % endif
                            % if sickbeard.USE_TORRENTS and sickbeard.TORRENT_METHOD != 'blackhole' and (sickbeard.ENABLE_HTTPS and sickbeard.TORRENT_HOST[:5] == 'https' or not sickbeard.ENABLE_HTTPS and sickbeard.TORRENT_HOST[:5] == 'http:'):
                                <li><a href="${srRoot}/manage/manageTorrents/"><i class="menu-icon-bittorrent"></i>&nbsp;${_('Manage Torrents')}</a></li>
                            % endif
                            % if sickbeard.USE_FAILED_DOWNLOADS:
                                <li><a href="${srRoot}/manage/failedDownloads/"><i class="menu-icon-failed-download"></i>&nbsp;${_('Failed Downloads')}</a></li>
                            % endif
                            % if sickbeard.USE_SUBTITLES:
                                <li><a href="${srRoot}/manage/subtitleMissed/"><i class="menu-icon-backlog"></i>&nbsp;${_('Missed Subtitle Management')}</a></li>
                            % endif
                            </ul>
                            <div style="clear:both;"></div>
                        </li>

                        <li id="NAVconfig" class="navbar-split dropdown${('', ' active')[topmenu == 'config']}">
                            <a href="${srRoot}/config/" class="dropdown-toggle" aria-haspopup="true" data-toggle="dropdown" data-hover="dropdown"><span class="visible-xs-inline">Config</span><img src="${srRoot}/images/menu/system18.png" class="navbaricon hidden-xs" />
                            <b class="caret"></b>
                            </a>
                            <ul class="dropdown-menu">
                                <li><a href="${srRoot}/config/"><i class="menu-icon-help"></i>&nbsp;${_('Help &amp; Info')}</a></li>
                                <li><a href="${srRoot}/config/general/"><i class="menu-icon-config"></i>&nbsp;${_('General')}</a></li>
                                <li><a href="${srRoot}/config/backuprestore/"><i class="menu-icon-backup"></i>&nbsp;${_('Backup &amp; Restore')}</a></li>
                                <li><a href="${srRoot}/config/search/"><i class="menu-icon-manage-searches"></i>&nbsp;${_('Search Settings')}</a></li>
                                <li><a href="${srRoot}/config/providers/"><i class="menu-icon-provider"></i>&nbsp;${_('Search Providers')}</a></li>
                                <li><a href="${srRoot}/config/subtitles/"><i class="menu-icon-backlog"></i>&nbsp;${_('Subtitles Settings')}</a></li>
                                <li><a href="${srRoot}/config/postProcessing/"><i class="menu-icon-postprocess"></i>&nbsp;${_('Post Processing')}</a></li>
                                <li><a href="${srRoot}/config/notifications/"><i class="menu-icon-notification"></i>&nbsp;${_('Notifications')}</a></li>
                                <li><a href="${srRoot}/config/anime/"><i class="menu-icon-anime"></i>&nbsp;${_('Anime')}</a></li>
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
                            <a href="${srRoot}/home/status/" class="dropdown-toggle" aria-haspopup="true" data-toggle="dropdown" data-hover="dropdown"><span class="visible-xs-inline">${_('Tools')}</span><img src="${srRoot}/images/menu/system18-2.png" class="navbaricon hidden-xs" />${toolsBadge}
                            <b class="caret"></b>
                            </a>
                            <ul class="dropdown-menu">
                                <li><a href="${srRoot}/news/"><i class="menu-icon-news"></i>&nbsp;${_('News')}${newsBadge}</a></li>
                                <li><a href="${srRoot}/IRC/"><i class="menu-icon-irc"></i>&nbsp;${_('IRC')}</a></li>
                                <li><a href="${srRoot}/changes/"><i class="menu-icon-changelog"></i>&nbsp;${_('Changelog')}</a></li>
                                <li><a href="https://github.com/SickRage/SickRage/wiki/Donations" rel="noreferrer" onclick="window.open('${sickbeard.ANON_REDIRECT}' + this.href); return false;"><i class="menu-icon-support"></i>&nbsp;${_('Support SickRage')}</a></li>
                                <li role="separator" class="divider"></li>
                                %if numErrors:
                                    <li><a href="${srRoot}/errorlogs/"><i class="menu-icon-error"></i>&nbsp;${_('View Errors')} <span class="badge btn-danger">${numErrors}</span></a></li>
                                %endif
                                %if numWarnings:
                                    <li><a href="${srRoot}/errorlogs/?level=${sickbeard.logger.WARNING}"><i class="menu-icon-viewlog-errors"></i>&nbsp;${_('View Warnings')} <span class="badge btn-warning">${numWarnings}</span></a></li>
                                %endif
                                <li><a href="${srRoot}/errorlogs/viewlog/"><i class="menu-icon-viewlog"></i>&nbsp;${_('View Log')}</a></li>
                                <li role="separator" class="divider"></li>
                                <li><a href="${srRoot}/home/updateCheck?pid=${sbPID}"><i class="menu-icon-update"></i>&nbsp;${_('Check For Updates')}</a></li>
                                <li><a href="${srRoot}/home/restart/?pid=${sbPID}" class="confirm restart"><i class="menu-icon-restart"></i>&nbsp;${_('Restart')}</a></li>
                                <li><a href="${srRoot}/home/shutdown/?pid=${sbPID}" class="confirm shutdown"><i class="menu-icon-shutdown"></i>&nbsp;${_('Shutdown')}</a></li>
                                % if srLogin is not True:
                                    <li><a href="${srRoot}/logout" class="confirm logout"><i class="menu-icon-shutdown"></i>&nbsp;${_('Logout')}</a></li>
                                % endif
                                <li role="separator" class="divider"></li>
                                <li><a href="${srRoot}/home/status/"><i class="menu-icon-info"></i>&nbsp;${_('Server Status')}</a></li>
                            </ul>
                            <div style="clear:both;"></div>
                        </li>
                    </ul>
            % endif
                </div><!-- /.navbar-collapse -->
            </div><!-- /.container-fluid -->
        </nav>
        % if submenu:
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
                          <a href="${srRoot}/${menuItem['path']}" class="btn${('', ' confirm ' + menuItem.get('class', ''))['confirm' in menuItem]}">${('', '<span class="pull-left ' + icon_class + '"></span> ')[bool(icon_class)]}${menuItem['title']}</a>
                          <% first = False %>
                      % endif
                % endif
            % endfor
            </span>
        </div>
        % endif
        % if sickbeard.BRANCH and sickbeard.BRANCH != 'master' and not sickbeard.DEVELOPER and srLogin:
        <div class="alert alert-danger upgrade-notification hidden-print" role="alert">
            <span>${_('You\'re using the {branch} branch. Please use \'master\' unless specifically asked').format(branch=sickbeard.BRANCH)}</span>
        </div>
        % endif

        % if sickbeard.NEWEST_VERSION_STRING and srLogin:
        <div class="alert alert-success upgrade-notification hidden-print" role="alert">
            <span>${sickbeard.NEWEST_VERSION_STRING}</span>
        </div>
        % endif

        <div id="contentWrapper">
            <div id="content">
                <%block name="content" />
            </div> <!-- /content -->
        </div> <!-- /contentWrapper -->
    % if srLogin:
        <footer>
            <div class="footer clearfix">
            <%
                stats = Show.overall_stats()
                ep_downloaded = stats['episodes']['downloaded']
                ep_snatched = stats['episodes']['snatched']
                ep_total = stats['episodes']['total']
                ep_percentage = '' if ep_total == 0 else '(<span class="footerhighlight">%s%%</span>)' % re.sub(r'(\d+)(\.\d)\d+', r'\1\2', str((float(ep_downloaded)/float(ep_total))*100))
            %>
                <span class="footerhighlight">${stats['shows']['total']}</span> ${_('Shows')} (<span class="footerhighlight">${stats['shows']['active']}</span> ${_('Active')})
                | <span class="footerhighlight">${ep_downloaded}</span>

                % if ep_snatched:
                <span class="footerhighlight"><a href="${srRoot}/manage/episodeStatuses?whichStatus=2" title="${_('View overview of snatched episodes')}">+${ep_snatched}</a></span> ${_('Snatched')}
                % endif

                &nbsp;/&nbsp;<span class="footerhighlight">${ep_total}</span> ${_('Episodes Downloaded')} ${ep_percentage}
                | ${_('Daily Search')}: <span class="footerhighlight">${str(sickbeard.daily_search_scheduler.timeLeft()).split('.')[0]}</span>
                | ${_('Backlog Search')}: <span class="footerhighlight">${str(sickbeard.backlog_search_scheduler.timeLeft()).split('.')[0]}</span>

                <div>
                    % if has_resource_module:
                    ${_('Memory used')}: <span class="footerhighlight">${pretty_file_size(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)}</span> |
                    % endif
                    ${_('Load time')}: <span class="footerhighlight">${"%.4f" % (time() - sbStartTime)}s</span> / Mako: <span class="footerhighlight">${"%.4f" % (time() - makoStartTime)}s</span> |
                    ${_('Branch')}: <span class="footerhighlight">${sickbeard.BRANCH}</span> |
                    ${_('Now')}: <span class="footerhighlight">${datetime.datetime.now().strftime(sickbeard.DATE_PRESET+" "+sickbeard.TIME_PRESET)}</span>
                </div>
            </div>
        </footer>
        <script type="text/javascript" src="${srRoot}/js/vender.min.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/lib/jquery.cookiejar.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/lib/jquery.form.min.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/lib/jquery.json-2.2.min.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/lib/jquery.selectboxes.min.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/lib/formwizard.js?${sbPID}"></script><!-- Can't be added to bower -->
        <script type="text/javascript" src="${srRoot}/js/parsers.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/rootDirs.js?${sbPID}"></script>
        % if sickbeard.DEVELOPER:
        <script type="text/javascript" src="${srRoot}/js/core.js?${sbPID}"></script>
        % else:
        <script type="text/javascript" src="${srRoot}/js/core.min.js?${sbPID}"></script>
        % endif
        <script type="text/javascript" src="${srRoot}/js/lib/jquery.scrolltopcontrol-1.1.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/browser.js?${sbPID}"></script>
        <script type="text/javascript" src="${srRoot}/js/ajaxNotifications.js?${sbPID}"></script>
    % endif
        <%block name="scripts" />
    </body>
</html>
