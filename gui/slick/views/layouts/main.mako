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

    srRoot = sickbeard.WEB_ROOT
%>
<!DOCTYPE html>
<html lang="${sickbeard.GUI_LANG}">
    <head>
        <meta charset="utf-8">
        <meta name="robots" content="noindex, nofollow">
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0">

        <% themeColors = { "dark": "#15528F", "light": "#333333" } %>
        <!-- Android -->
        <meta name="theme-color" content="${themeColors[sickbeard.THEME_NAME]}">
        <!-- Windows Phone -->
        <meta name="msapplication-navbutton-color" content="${themeColors[sickbeard.THEME_NAME]}">
        <!-- iOS -->
        <meta name="apple-mobile-web-app-status-bar-style" content="${themeColors[sickbeard.THEME_NAME]}">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="mobile-web-app-capable" content="yes">

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
        <meta data-var="sickbeard.ANIME_SPLIT_HOME_IN_TABS" data-content="${sickbeard.ANIME_SPLIT_HOME_IN_TABS}">
        <meta data-var="sickbeard.COMING_EPS_LAYOUT" data-content="${sickbeard.COMING_EPS_LAYOUT}">
        <meta data-var="sickbeard.COMING_EPS_SORT" data-content="${sickbeard.COMING_EPS_SORT}">
        <meta data-var="sickbeard.DATE_PRESET" data-content="${sickbeard.DATE_PRESET}">
        <meta data-var="sickbeard.FUZZY_DATING" data-content="${sickbeard.FUZZY_DATING}">
        <meta data-var="sickbeard.HISTORY_LAYOUT" data-content="${sickbeard.HISTORY_LAYOUT}">
        <meta data-var="sickbeard.USE_SUBTITLES" data-content="${sickbeard.USE_SUBTITLES}">
        <meta data-var="sickbeard.HOME_LAYOUT" data-content="${sickbeard.HOME_LAYOUT}">
        <meta data-var="sickbeard.POSTER_SORTBY" data-content="${sickbeard.POSTER_SORTBY}">
        <meta data-var="sickbeard.POSTER_SORTDIR" data-content="${sickbeard.POSTER_SORTDIR}">
        <meta data-var="sickbeard.ROOT_DIRS" data-content="${sickbeard.ROOT_DIRS}">
        <meta data-var="sickbeard.SORT_ARTICLE" data-content="${sickbeard.SORT_ARTICLE}">
        <meta data-var="sickbeard.TIME_PRESET" data-content="${sickbeard.TIME_PRESET}">
        <meta data-var="sickbeard.TRIM_ZERO" data-content="${sickbeard.TRIM_ZERO}">
        <meta data-var="sickbeard.SICKRAGE_BACKGROUND" data-content="${sickbeard.SICKRAGE_BACKGROUND}">
        <meta data-var="sickbeard.FANART_BACKGROUND" data-content="${sickbeard.FANART_BACKGROUND}">
        <meta data-var="sickbeard.FANART_BACKGROUND_OPACITY" data-content="${sickbeard.FANART_BACKGROUND_OPACITY}">
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
        <link rel="stylesheet" type="text/css" href="${srRoot}/css/font-awesome.min.css?${sbPID}" />
        <link rel="stylesheet" type="text/css" href="${srRoot}/css/lib/jquery-ui-1.10.4.custom.min.css?${sbPID}" />
        <link rel="stylesheet" type="text/css" href="${srRoot}/css/lib/jquery.qtip-2.2.1.min.css?${sbPID}"/>
        <link rel="stylesheet" type="text/css" href="${srRoot}/css/style.css?${sbPID}"/>
        <link rel="stylesheet" type="text/css" href="${srRoot}/css/print.css?${sbPID}" />
        <link rel="stylesheet" type="text/css" href="${srRoot}/css/country-flags.css?${sbPID}"/>

        % if sickbeard.THEME_NAME != "light":
            <link rel="stylesheet" type="text/css" href="${srRoot}/css/${sickbeard.THEME_NAME}.css?${sbPID}" />
        % endif

        <%block name="css" />

        % if sickbeard.CUSTOM_CSS:
            <link rel="stylesheet" type="text/css" href="${srRoot}/ui/custom.css" />
        % endif
    </head>
    <body data-controller="${controller}" data-action="${action}">
        <nav class="navbar navbar-default navbar-fixed-top hidden-print" role="navigation">
            <div class="container-fluid">
                <div class="navbar-header">
                    <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#collapsible-navbar">
                        <span class="sr-only">Toggle navigation</span>
                        <span class="icon-bar"></span>
                        <span class="icon-bar"></span>
                        <span class="icon-bar"></span>
                    </button>
                    <a class="navbar-brand" href="${srRoot}/home/" title="SickRage"><img alt="SickRage" src="${srRoot}/images/sickrage.png" style="height: 50px;padding: 3px;" class="img-responsive pull-left" /></a>
                </div>
                % if srLogin:
                    <div class="collapse navbar-collapse" id="collapsible-navbar">
                        <ul class="nav navbar-nav navbar-right">
                            <li id="NAVhome" class="navbar-split dropdown${('', ' active')[topmenu == 'home']}">
                                <a href="${srRoot}/home/" class="dropdown-toggle" aria-haspopup="true" data-toggle="dropdown" data-hover="dropdown"><span>${_('Shows')}</span>
                                    <b class="caret"></b>
                                </a>
                                <ul class="dropdown-menu">
                                    <li><a href="${srRoot}/home/"><i class="fa fa-home"></i>&nbsp;${_('Show List')}</a></li>
                                    <li><a href="${srRoot}/addShows/"><i class="fa fa-television"></i>&nbsp;${_('Add Shows')}</a></li>
                                    <li><a href="${srRoot}/home/postprocess/"><i class="fa fa-refresh"></i>&nbsp;${_('Manual Post-Processing')}</a></li>
                                    % if sickbeard.SHOWS_RECENT:
                                        <li role="separator" class="divider"></li>
                                        % for recentShow in sickbeard.SHOWS_RECENT:
                                            <li><a href="${srRoot}/home/displayShow?show=${recentShow['indexerid']}"><i class="fa fa-television"></i>&nbsp;${recentShow['name']|trim,h}</a></li>
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
                                    <li><a href="${srRoot}/manage/"><i class="fa fa-pencil"></i>&nbsp;${_('Mass Update')}</a></li>
                                    <li><a href="${srRoot}/manage/backlogOverview/"><i class="fa fa-binoculars"></i>&nbsp;${_('Backlog Overview')}</a></li>
                                    <li><a href="${srRoot}/manage/manageSearches/"><i class="fa fa-search"></i>&nbsp;${_('Manage Searches')}</a></li>
                                    <li><a href="${srRoot}/manage/episodeStatuses/"><i class="fa fa-gavel"></i>&nbsp;${_('Episode Status Management')}</a></li>
                                    % if sickbeard.USE_PLEX_SERVER and sickbeard.PLEX_SERVER_HOST != "":
                                        <li><a href="${srRoot}/home/updatePLEX/"><i class="menu-icon-plex"></i>&nbsp;${_('Update PLEX')}</a></li>
                                    % endif
                                    % if sickbeard.USE_KODI and sickbeard.KODI_HOST != "":
                                        <li><a href="${srRoot}/home/updateKODI/"><i class="menu-icon-kodi"></i>&nbsp;${_('Update KODI')}</a></li>
                                    % endif
                                    % if sickbeard.USE_EMBY and sickbeard.EMBY_HOST != "" and sickbeard.EMBY_APIKEY != "":
                                        <li><a href="${srRoot}/home/updateEMBY/"><i class="menu-icon-emby"></i>&nbsp;${_('Update Emby')}</a></li>
                                    % endif
                                    % if manage_torrents_url:
                                        <li><a href="${manage_torrents_url}" target="_blank"><i class="fa fa-download"></i>&nbsp;${_('Manage Torrents')}</a></li>
                                    % endif
                                    % if sickbeard.USE_FAILED_DOWNLOADS:
                                        <li><a href="${srRoot}/manage/failedDownloads/"><i class="fa fa-thumbs-o-down"></i>&nbsp;${_('Failed Downloads')}</a></li>
                                    % endif
                                    % if sickbeard.USE_SUBTITLES:
                                        <li><a href="${srRoot}/manage/subtitleMissed/"><i class="fa fa-language"></i>&nbsp;${_('Missed Subtitle Management')}</a></li>
                                    % endif
                                </ul>
                                <div style="clear:both;"></div>
                            </li>

                            <li id="NAVconfig" class="navbar-split dropdown${('', ' active')[topmenu == 'config']}">
                                <a href="${srRoot}/config/" class="dropdown-toggle" aria-haspopup="true" data-toggle="dropdown" data-hover="dropdown"><span class="visible-xs-inline">Config</span><img src="${srRoot}/images/menu/system18.png" class="navbaricon hidden-xs" />
                                    <b class="caret"></b>
                                </a>
                                <ul class="dropdown-menu">
                                    <li><a href="${srRoot}/config/"><i class="fa fa-question"></i>&nbsp;${_('Help &amp; Info')}</a></li>
                                    <li><a href="${srRoot}/config/general/"><i class="fa fa-cog"></i>&nbsp;${_('General')}</a></li>
                                    <li><a href="${srRoot}/config/backuprestore/"><i class="fa fa-floppy-o"></i>&nbsp;${_('Backup &amp; Restore')}</a></li>
                                    <li><a href="${srRoot}/config/search/"><i class="fa fa-search"></i>&nbsp;${_('Search Settings')}</a></li>
                                    <li><a href="${srRoot}/config/providers/"><i class="fa fa-plug"></i>&nbsp;${_('Search Providers')}</a></li>
                                    <li><a href="${srRoot}/config/subtitles/"><i class="fa fa-language"></i>&nbsp;${_('Subtitles Settings')}</a></li>
                                    <li><a href="${srRoot}/config/postProcessing/"><i class="fa fa-refresh"></i>&nbsp;${_('Post Processing')}</a></li>
                                    <li><a href="${srRoot}/config/notifications/"><i class="fa fa-bell-o"></i>&nbsp;${_('Notifications')}</a></li>
                                    <li><a href="${srRoot}/config/anime/"><i class="fa fa-eye"></i>&nbsp;${_('Anime')}</a></li>
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
                                    <li><a href="${srRoot}/news/"><i class="fa fa-newspaper-o"></i>&nbsp;${_('News')}${newsBadge}</a></li>
                                    <li><a href="${srRoot}/IRC/"><i class="fa fa-hashtag"></i>&nbsp;${_('IRC')}</a></li>
                                    <li><a href="${srRoot}/changes/"><i class="fa fa-globe"></i>&nbsp;${_('Changelog')}</a></li>
                                    <li><a href="https://github.com/SickRage/SickRage/wiki/Donations" rel="noreferrer" onclick="window.open('${sickbeard.ANON_REDIRECT}' + this.href); return false;"><i class="fa fa-life-ring"></i>&nbsp;${_('Support SickRage')}</a></li>
                                    <li role="separator" class="divider"></li>
                                    %if numErrors:
                                        <li><a href="${srRoot}/errorlogs/"><i class="fa fa-exclamation-circle"></i>&nbsp;${_('View Errors')} <span class="badge btn-danger">${numErrors}</span></a></li>
                                    %endif
                                    %if numWarnings:
                                        <li><a href="${srRoot}/errorlogs/?level=${sickbeard.logger.WARNING}"><i class="fa fa-exclamation-triangle"></i>&nbsp;${_('View Warnings')} <span class="badge btn-warning">${numWarnings}</span></a></li>
                                    %endif
                                    <li><a href="${srRoot}/errorlogs/viewlog/"><i class="fa fa-file-text-o"></i>&nbsp;${_('View Log')}</a></li>
                                    <li role="separator" class="divider"></li>
                                    <li><a href="${srRoot}/home/updateCheck?pid=${sbPID}"><i class="fa fa-wrench"></i>&nbsp;${_('Check For Updates')}</a></li>
                                    <li><a href="${srRoot}/home/restart/?pid=${sbPID}" class="confirm restart"><i class="fa fa-repeat"></i>&nbsp;${_('Restart')}</a></li>
                                    <li><a href="${srRoot}/home/shutdown/?pid=${sbPID}" class="confirm shutdown"><i class="fa fa-power-off"></i>&nbsp;${_('Shutdown')}</a></li>
                                    % if srLogin:
                                        <li><a href="${srRoot}/logout" class="confirm logout"><i class="fa fa-sign-out"></i>&nbsp;${_('Logout')}</a></li>
                                    % endif
                                    <li role="separator" class="divider"></li>
                                    <li><a href="${srRoot}/home/status/"><i class="fa fa-info-circle"></i>&nbsp;${_('Server Status')}</a></li>
                                </ul>
                                <div style="clear:both;"></div>
                            </li>
                        </ul>
                    </div>
                % endif
            </div>
        </nav>
        <div class="container-fluid">
            <div id="sub-menu-container" class="row">
                % if submenu:
                    <div id="sub-menu" class="hidden-print">
                        <% first = True %>
                        % for menuItem in reversed(submenu):
                            % if menuItem.get('requires', 1):
                                % if isinstance(menuItem['path'], dict):
                                    ${("</span><span>", "")[bool(first)]}<b>${menuItem['title']}</b>
                                    <%
                                        first = False
                                        inner_first = True
                                    %>
                                    % for cur_link in menuItem['path']:
                                        ${("&middot;", "")[bool(inner_first)]}<a href="${srRoot}/${menuItem['path'][cur_link]}" class="inner ${menuItem.get('class', '')}">${cur_link}</a>
                                        <% inner_first = False %>
                                    % endfor
                                % else:
                                    <a href="${srRoot}/${menuItem['path']}" class="btn ${('', ' confirm ')['confirm' in menuItem] + menuItem.get('class', '')}">
                                        <i class='${menuItem.get('icon', '')}'></i> ${menuItem['title']}
                                    </a>
                                    <% first = False %>
                                % endif
                            % endif
                        % endfor
                    </div>
                % endif
                <div class="clearfix"></div>
                % if srLogin:
                    <div id="site-messages"/>
                % endif
            </div>
            <div class="row">
                <div class="col-lg-10 col-lg-offset-1 col-md-10 col-md-offset-1 col-sm-12 col-xs-12">
                    <%block name="content" />
                </div>
            </div>

            <div class="modal fade" id="site-notification-modal">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <button type="button" class="close" data-dismiss="modal" aria-hidden="true">x</button>
                            <h4 class="modal-title">Notice</h4>
                        </div>
                        <div class="modal-body"></div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-primary" data-dismiss="modal">Ok</button>
                        </div>
                    </div>
                </div>
            </div>

            % if srLogin:
                <div class="row">
                    <div class="footer clearfix col-lg-10 col-lg-offset-1 col-md-10 col-md-offset-1 col-sm-12 col-xs-12">
                        <%
                            stats = Show.overall_stats()
                            ep_downloaded = stats['episodes']['downloaded']
                            ep_snatched = stats['episodes']['snatched']
                            ep_total = stats['episodes']['total']
                            ep_percentage = '' if ep_total == 0 else '(<span class="footerhighlight">%s%%</span>)' % re.sub(r'(\d+)(\.\d)\d+', r'\1\2', str((float(ep_downloaded)/float(ep_total))*100))
                        %>
                        <div>
                            <span class="footer-item">
                                <span class="footerhighlight">${stats['shows']['total']}</span> ${_('Shows')} (<span class="footerhighlight">${stats['shows']['active']}</span> ${_('Active')})
                            </span>&nbsp;|
                            <span class="footer-item">
                                <span class="footerhighlight">${ep_downloaded}</span>
                                % if ep_snatched:
                                    <span class="footerhighlight"><a href="${srRoot}/manage/episodeStatuses?whichStatus=2" title="${_('View overview of snatched episodes')}">+${ep_snatched}</a></span> ${_('Snatched')}
                                % endif
                                /&nbsp;<span class="footerhighlight">${ep_total}</span>&nbsp;${_('Episodes Downloaded')}&nbsp;${ep_percentage}
                            </span>&nbsp;|
                             <span class="footer-item">${_('Daily Search')}: <span class="footerhighlight">${str(sickbeard.dailySearchScheduler.timeLeft()).split('.')[0]}</span></span>&nbsp;|
                             <span class="footer-item">${_('Backlog Search')}: <span class="footerhighlight">${str(sickbeard.backlogSearchScheduler.timeLeft()).split('.')[0]}</span></span>
                        </div>

                        <div>
                            % if has_resource_module:
                                <span class="footer-item">${_('Memory used')}: <span class="footerhighlight">${pretty_file_size(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)}</span></span> |
                            % endif
                            <span class="footer-item">${_('Load time')}: <span class="footerhighlight">${"%.4f" % (time() - sbStartTime)}s</span></span> |
                            <span class="footer-item">Mako: <span class="footerhighlight">${"%.4f" % (time() - makoStartTime)}s</span></span> |
                            <span class="footer-item">${_('Branch')}: <span class="footerhighlight">${sickbeard.BRANCH}</span></span> |
                            <span class="footer-item">${_('Now')}: <span class="footerhighlight">${datetime.datetime.now().strftime(sickbeard.DATE_PRESET+" "+sickbeard.TIME_PRESET)}</span></span>
                        </div>
                    </div>
                </div>
                <script type="text/javascript" src="${srRoot}/js/vender.min.js?${sbPID}"></script>
                <script type="text/javascript" src="${srRoot}/js/lib/jquery.form.min.js?${sbPID}"></script>
                <script type="text/javascript" src="${srRoot}/js/lib/jquery.selectboxes.min.js?${sbPID}"></script>
                <script type="text/javascript" src="${srRoot}/js/lib/formwizard.js?${sbPID}"></script><!-- Can't be added to bower -->
                <script type="text/javascript" src="${srRoot}/js/parsers.js?${sbPID}"></script>
                <script type="text/javascript" src="${srRoot}/js/rootDirs.js?${sbPID}"></script>
                <script type="text/javascript" src="${srRoot}/js/dist/bundle.js?${sbPID}"></script>
                <script type="text/javascript" src="${srRoot}/js/lib/jquery.scrolltopcontrol-1.1.js?${sbPID}"></script>
                <script type="text/javascript" src="${srRoot}/js/browser.js?${sbPID}" charset="utf-8"></script>
                <script type="text/javascript" src="${srRoot}/js/ajaxNotifications.js?${sbPID}"></script>
            % endif
            <%block name="scripts" />
        </div>
    </body>
</html>
