<%!
    import re
    import datetime
    from urllib.parse import urljoin
    from sickchill.oldbeard.filters import hide
    from sickchill.helper.common import pretty_file_size
    from sickchill.show.Show import Show
    from sickchill import settings, logger
    from time import time

    # resource module is unix only
    has_resource_module = True
    try:
        import resource
    except ImportError:
        has_resource_module = False
%>
<!DOCTYPE html>
<html lang="${settings.GUI_LANG}">
    <head>
        <meta name="robots" content="noindex, nofollow">
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0">

        <% themeColors = { "dark": "#15528F", "light": "#333333" } %>
        <!-- Android -->
        <meta name="theme-color" content="${themeColors[settings.THEME_NAME]}">

        <!-- Windows Phone -->
        <meta name="msapplication-navbutton-color" content="${themeColors[settings.THEME_NAME]}">
        <!-- iOS -->
        <meta name="apple-mobile-web-app-status-bar-style" content="${themeColors[settings.THEME_NAME]}">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="mobile-web-app-capable" content="yes">

        <title>SickChill - ${title}</title>

        <!--[if lt IE 9]>
            <script src="${static_url('js/html5shiv.min.js')}"></script>
            <script src="${static_url('js/respond.min.js')}"></script>
        <![endif]-->

        <meta name="msapplication-TileColor" content="#2b5797">
        <meta name="msapplication-TileImage" content="${static_url('images/ico/mstile-144x144.png')}">
        <meta name="msapplication-config" content="${static_url('images/ico/browserconfig.xml')}">

        <meta data-var="scRoot" data-content="${settings.WEB_ROOT}">
        <meta data-var="themeSpinner" data-content="${('', '-dark')[settings.THEME_NAME == 'dark']}">
        <meta data-var="anonURL" data-content="${settings.ANON_REDIRECT}">

        <meta data-var="settings.ANIME_SPLIT_HOME" data-content="${settings.ANIME_SPLIT_HOME}">
        <meta data-var="settings.ANIME_SPLIT_HOME_IN_TABS" data-content="${settings.ANIME_SPLIT_HOME_IN_TABS}">
        <meta data-var="settings.COMING_EPS_LAYOUT" data-content="${settings.COMING_EPS_LAYOUT}">
        <meta data-var="settings.COMING_EPS_SORT" data-content="${settings.COMING_EPS_SORT}">
        <meta data-var="settings.DATE_PRESET" data-content="${settings.DATE_PRESET}">
        <meta data-var="settings.FUZZY_DATING" data-content="${settings.FUZZY_DATING}">
        <meta data-var="settings.HISTORY_LAYOUT" data-content="${settings.HISTORY_LAYOUT}">
        <meta data-var="settings.USE_SUBTITLES" data-content="${settings.USE_SUBTITLES}">
        <meta data-var="settings.HOME_LAYOUT" data-content="${settings.HOME_LAYOUT}">
        <meta data-var="settings.POSTER_SORTBY" data-content="${settings.POSTER_SORTBY}">
        <meta data-var="settings.POSTER_SORTDIR" data-content="${settings.POSTER_SORTDIR}">
        <meta data-var="settings.ROOT_DIRS" data-content="${settings.ROOT_DIRS}">
        <meta data-var="settings.SORT_ARTICLE" data-content="${settings.SORT_ARTICLE}">
        <meta data-var="settings.TIME_PRESET" data-content="${settings.TIME_PRESET}">
        <meta data-var="settings.TRIM_ZERO" data-content="${settings.TRIM_ZERO}">
        <meta data-var="settings.SICKCHILL_BACKGROUND" data-content="${settings.SICKCHILL_BACKGROUND}">
        <meta data-var="settings.FANART_BACKGROUND" data-content="${settings.FANART_BACKGROUND}">
        <meta data-var="settings.FANART_BACKGROUND_OPACITY" data-content="${settings.FANART_BACKGROUND_OPACITY}">
        <meta data-var="settings.GUI_LANG" data-content="${settings.GUI_LANG}">
        <%block name="metas" />

        <link rel="shortcut icon" href="${static_url('images/ico/favicon.ico')}">

        <link rel="mask-icon" href="${static_url('images/ico/safari-pinned-tab.svg')}" color="#5bbad5">

        <link rel="apple-touch-icon" href="${static_url('images/ico/apple-touch-icon-57x57.png')}">
        <link rel="apple-touch-icon" sizes="180x180" href="${static_url('images/ico/apple-touch-icon.png')}">
        <link rel="apple-touch-icon" sizes="152x152" href="${static_url('images/ico/apple-touch-icon-152x152.png')}">
        <link rel="apple-touch-icon" sizes="144x144" href="${static_url('images/ico/apple-touch-icon-144x144.png')}">
        <link rel="apple-touch-icon" sizes="120x120" href="${static_url('images/ico/apple-touch-icon-120x120.png')}">
        <link rel="apple-touch-icon" sizes="114x114" href="${static_url('images/ico/apple-touch-icon-114x114.png')}">
        <link rel="apple-touch-icon" sizes="76x76" href="${static_url('images/ico/apple-touch-icon-76x76.png')}">
        <link rel="apple-touch-icon" sizes="72x72" href="${static_url('images/ico/apple-touch-icon-72x72.png')}">

        <link rel="icon" type="image/png" sizes="16x16" href="${static_url('images/ico/favicon-16x16.png')}">
        <link rel="icon" type="image/png" sizes="32x32" href="${static_url('images/ico/favicon-32x32.png')}">
        <link rel="icon" type="image/png" sizes="32x32" href="${static_url('images/ico/favicon-32x32.png')}">
        <link rel="icon" type="image/png" sizes="192x192" href="${static_url('images/ico/android-chrome-192x192.png')}">

        <link rel="manifest" href="${static_url('images/ico/site.webmanifest')}">


        <link rel="stylesheet" type="text/css" href="${static_url('css/vendor.min.css')}"/>
        <link rel="stylesheet" type="text/css" href="${static_url('css/browser.css')}" />
        <link rel="stylesheet" type="text/css" href="${static_url('css/font-awesome.min.css')}" />
        <link rel="stylesheet" type="text/css" href="${static_url('css/fork-awesome.min.css')}" />
        <link rel="stylesheet" type="text/css" href="${static_url('css/lib/jquery-ui-1.10.4.custom.min.css')}" />
        <link rel="stylesheet" type="text/css" href="${static_url('css/lib/jquery.qtip-2.2.1.min.css')}"/>
        <link rel="stylesheet" type="text/css" href="${static_url('css/style.css')}"/>
        <link rel="stylesheet" type="text/css" href="${static_url('css/print.css')}" />
        <link rel="stylesheet" type="text/css" href="${static_url('css/country-flags.css')}"/>
        <link rel="stylesheet" type="text/css" href="${static_url('css/jquery-ui-custom.css')}" />

        % if settings.THEME_NAME != "light":
            <link rel="stylesheet" type="text/css" href="${static_url(urljoin('css/', '.'.join((settings.THEME_NAME, 'css'))))}" />
        % endif

        <%block name="css" />

        % if settings.CUSTOM_CSS:
            ## TODO: check if this exists first
            <link rel="stylesheet" type="text/css" href="${static_url('ui/custom.css', include_version=False)}" />
        % endif
    </head>
    <body data-controller="${controller}" data-action="${action}">
        <nav class="navbar navbar-default navbar-fixed-top hidden-print">
            <div class="container-fluid">
                <%
                    numCombined = numErrors + numWarnings + settings.NEWS_UNREAD
                    if numCombined:
                        if numErrors:
                            toolsBadgeClass = ' btn-danger'
                        elif numWarnings:
                            toolsBadgeClass = ' btn-warning'
                        else:
                            toolsBadgeClass = ''
                %>
                <div class="navbar-header">
                    <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#collapsible-navbar">
                        % if numCombined:
                            <span class="floating-badge${ toolsBadgeClass }">${ str(numCombined) }</span>
                        % endif
                        <span class="sr-only">Toggle navigation</span>
                        <span class="icon-bar"></span>
                        <span class="icon-bar"></span>
                        <span class="icon-bar"></span>
                    </button>
                    <a class="navbar-brand" href="${static_url("home/", include_version=False)}" title="SickChill"><img alt="SickChill" src="${static_url('images/sickchill.png')}"
                                                                                         style="height: 50px;padding: 3px;"
                                                                                 class="img-responsive pull-left" /></a>
                </div>
                % if srLogin:
                    <div class="collapse navbar-collapse" id="collapsible-navbar">
                        <ul class="nav navbar-nav navbar-right">
                            <%block name="navbar" />
                            <li id="NAVhome" class="navbar-split dropdown${('', ' active')[topmenu == 'home']}">
                                <a href="${static_url("home/", include_version=False)}" class="dropdown-toggle" aria-haspopup="true" data-toggle="dropdown" data-hover="dropdown"><span>${_('Shows')}</span>
                                    <b class="caret"></b>
                                </a>
                                <ul class="dropdown-menu">
                                    <li><a href="${static_url("home/", include_version=False)}"><i class="fa fa-fw fa-home"></i>&nbsp;${_('Show List')}</a></li>
                                    <li><a href="${static_url("addShows/", include_version=False)}"><i class="fa fa-fw fa-television"></i>&nbsp;${_('Add Shows')}</a></li>
                                    <li><a href="${static_url("home/postprocess/", include_version=False)}"><i class="fa fa-fw fa-refresh"></i>&nbsp;${_('Manual Post-Processing')}</a></li>
                                    % if settings.SHOWS_RECENT:
                                        <li role="separator" class="divider"></li>
                                        % for recentShow in settings.SHOWS_RECENT:
                                            <li><a href="${static_url("home/displayShow?show={}".format(recentShow['indexerid']), include_version=False)}"><i class="fa fa-fw fa-television"></i>&nbsp;${recentShow['name']|trim,h}</a></li>
                                        % endfor
                                    % endif
                                </ul>
                                <div style="clear:both;"></div>
                            </li>
                            % if settings.DEVELOPER:
                            <li id="NAVmovies" class="navbar-split dropdown${('', ' active')[topmenu == 'movies']}">
                                <a href="${reverse_url("movies", "")}" class="dropdown-toggle" aria-haspopup="true" data-toggle="dropdown" data-hover="dropdown"><span>${_('Movies')}</span>
                                    <b class="caret"></b>
                                </a>
                                <ul class="dropdown-menu">
                                    <li><a href="${reverse_url("movies", "")}"><i class="fa fa-fw fa-home"></i>&nbsp;${_('Movie List')}</a></li>
                                    <li><a href="${reverse_url("movies-search", "search")}"><i class="fa fa-fw fa-television"></i>&nbsp;${_('Add Movies')}</a></li>
                                </ul>
                                <div style="clear:both;"></div>
                            </li>
                            % endif
                            <li id="NAVschedule"${('', ' class="active"')[topmenu == 'schedule']}>
                                <a href="${static_url("schedule/", include_version=False)}">${_('Schedule')}</a>
                            </li>

                            <li id="NAVhistory"${('', ' class="active"')[topmenu == 'history']}>
                                <a href="${static_url("history/", include_version=False)}">${_('History')}</a>
                            </li>

                            <li id="NAVmanage" class="navbar-split dropdown${('', ' active')[topmenu == 'manage']}">
                                <a href="${static_url("manage/episodeStatuses/", include_version=False)}" class="dropdown-toggle" aria-haspopup="true" data-toggle="dropdown" data-hover="dropdown"><span>${_('Manage')}</span>
                                    <b class="caret"></b>
                                </a>
                                <ul class="dropdown-menu">
                                    <li><a href="${static_url("manage/", include_version=False)}"><i class="fa fa-fw fa-pencil"></i>&nbsp;${_('Mass Update')}</a></li>
                                    <li><a href="${static_url("manage/backlogOverview/", include_version=False)}"><i class="fa fa-fw fa-binoculars"></i>&nbsp;${_('Backlog Overview')}</a></li>
                                    <li><a href="${static_url("manage/manageSearches/", include_version=False)}"><i class="fa fa-fw fa-search"></i>&nbsp;${_('Manage Searches')}</a></li>
                                    <li><a href="${static_url("manage/episodeStatuses/", include_version=False)}"><i class="fa fa-fw fa-gavel"></i>&nbsp;${_('Episode Status Management')}</a></li>
                                    % if settings.USE_PLEX_SERVER and settings.PLEX_SERVER_HOST != "":
                                        <li><a href="${static_url("home/updatePLEX/", include_version=False)}"><i class="menu-icon-plex"></i>&nbsp;${_('Update PLEX')}</a></li>
                                    % endif
                                    % if settings.USE_KODI and settings.KODI_HOST != "":
                                        <li><a href="${static_url("home/updateKODI/", include_version=False)}"><i class="menu-icon-kodi"></i>&nbsp;${_('Update KODI')}</a></li>
                                    % endif
                                    % if settings.USE_EMBY and settings.EMBY_HOST != "" and settings.EMBY_APIKEY != "":
                                        <li><a href="${static_url("home/updateEMBY/", include_version=False)}"><i class="menu-icon-emby"></i>&nbsp;${_('Update Emby')}</a></li>
                                    % endif
                                    % if manage_torrents_url:
                                        <li><a href="${manage_torrents_url}" target="_blank"><i class="fa fa-fw fa-download"></i>&nbsp;${_('Manage Torrents')}</a></li>
                                    % endif
                                    % if settings.USE_FAILED_DOWNLOADS:
                                        <li><a href="${static_url("manage/failedDownloads/", include_version=False)}"><i class="fa fa-fw fa-thumbs-o-down"></i>&nbsp;${_('Failed Downloads')}</a></li>
                                    % endif
                                    % if settings.USE_SUBTITLES:
                                        <li><a href="${static_url("manage/subtitleMissed/", include_version=False)}"><i class="fa fa-fw fa-language"></i>&nbsp;${_('Missed Subtitle Management')}</a></li>
                                    % endif
                                </ul>
                                <div style="clear:both;"></div>
                            </li>

                            <li id="NAVconfig" class="navbar-split dropdown${('', ' active')[topmenu == 'config']}">
                                <a href="${static_url("config/", include_version=False) }" class="dropdown-toggle" aria-haspopup="true"
                                   data-toggle="dropdown" data-hover="dropdown">
                                    <span class="visible-xs-inline">Config</span>
                                    <img src="${ static_url('images/menu/system18.png')}" alt="Config" class="navbaricon hidden-xs" />
                                    <b class="caret"></b>
                                </a>
                                <ul class="dropdown-menu">
                                    <li><a href="${static_url("config/", include_version=False)}"><i class="fa fa-fw fa-question"></i>&nbsp;${_('Help &amp; Info')}</a></li>
                                    <li><a href="${static_url("config/general/", include_version=False)}"><i class="fa fa-fw fa-cog"></i>&nbsp;${_('General')}</a></li>
                                    <li><a href="${static_url("config/backuprestore/", include_version=False)}"><i class="fa fa-fw fa-floppy-o"></i>&nbsp;${_('Backup &amp; Restore')}</a></li>
                                    <li><a href="${static_url("config/search/", include_version=False)}"><i class="fa fa-fw fa-search"></i>&nbsp;${_('Search Settings')}</a></li>
                                    <li><a href="${static_url("config/providers/", include_version=False)}"><i class="fa fa-fw fa-plug"></i>&nbsp;${_('Search Providers')}</a></li>
                                    <li><a href="${static_url("config/subtitles/", include_version=False)}"><i class="fa fa-fw fa-language"></i>&nbsp;${_('Subtitles Settings')}</a></li>
                                    <li><a href="${static_url("config/postProcessing/", include_version=False)}"><i class="fa fa-fw fa-refresh"></i>&nbsp;${_('Post Processing')}</a></li>
                                    <li><a href="${static_url("config/notifications/", include_version=False)}"><i class="fa fa-fw fa-bell-o"></i>&nbsp;${_('Notifications')}</a></li>
                                    <li><a href="${static_url("config/anime/", include_version=False)}"><i class="fa fa-fw fa-eye"></i>&nbsp;${_('Anime')}</a></li>
                                    <li role="separator" class="divider"></li>
                                    <li><a href="${static_url("apibuilder", include_version=False)}"><i class="fa fa-fw fa-info-circle"></i>&nbsp;${_('API Builder')}</a></li>
                                </ul>
                                <div style="clear:both;"></div>
                            </li>

                            <%
                                if settings.NEWS_UNREAD:
                                    newsBadge = ' <span class="badge">'+str(settings.NEWS_UNREAD)+'</span>'
                                else:
                                    newsBadge = ''

                                if numCombined:
                                    toolsBadge = ' <span class="badge'+toolsBadgeClass+'">'+str(numCombined)+'</span>'
                                else:
                                    toolsBadge = ''
                            %>
                            <li id="NAVsystem" class="navbar-split dropdown${('', ' active')[topmenu == 'system']}">
                                <a href="${static_url("home/status/", include_version=False) }" class="dropdown-toggle" aria-haspopup="true" data-toggle="dropdown" data-hover="dropdown">
                                    <span class="visible-xs-inline">${_('Tools')}</span>
                                    <img src="${ static_url('images/menu/system18-2.png')}" alt="Tools" class="navbaricon hidden-xs" />${toolsBadge}
                                    <b class="caret"></b>
                                </a>
                                <ul class="dropdown-menu">
                                    <li><a href="${static_url("news/", include_version=False)}"><i class="fa fa-fw fa-newspaper-o"></i>&nbsp;${_('News')}${newsBadge}</a></li>
                                    <li><a href="${static_url("IRC/", include_version=False)}"><i class="fa fa-fw fa-hashtag"></i>&nbsp;${_('IRC')}</a></li>
                                    <li><a href="https://discord.gg/U8WPBdf"><i class="fa fa-fw fa-discord-alt"></i>&nbsp;${_('Discord')}</a></li>
                                    <li><a href="https://sickchill.slack.com"><i class="fa fa-fw fa-slack"></i>&nbsp;${_('Slack')}</a></li>
                                    <li><a href="https://t.me/sickchill"><i class="fa fa-fw fa-telegram"></i>&nbsp;${_('Telegram')}</a></li>
                                    <li><a href="${static_url("changes/", include_version=False)}"><i class="fa fa-fw fa-globe"></i>&nbsp;${_('Changelog')}</a></li>
                                    <li><a href="https://github.com/SickChill/SickChill/wiki/Donations" rel="noreferrer" onclick="window.open('${settings.ANON_REDIRECT}' + this.href); return false;"><i class="fa fa-fw fa-life-ring"></i>&nbsp;${_('Support SickChill')}</a></li>
                                    <li role="separator" class="divider"></li>
                                    %if numErrors:
                                        <li><a href="${static_url("errorlogs/", include_version=False)}"><i class="fa fa-fw fa-exclamation-circle"></i>&nbsp;${_('View Errors')} <span class="badge btn-danger">${numErrors}</span></a></li>
                                    %endif
                                    %if numWarnings:
                                        <li>
                                          <a href="${static_url("errorlogs/?level={}".format(logger.WARNING), include_version=False)}">
                                            <i class="fa fa-fw fa-exclamation-triangle"></i>&nbsp;${_('View Warnings')} <span class="badge btn-warning">${numWarnings}</span>
                                          </a>
                                        </li>
                                    %endif
                                    <li><a href="${static_url("errorlogs/viewlog/", include_version=False)}"><i class="fa fa-fw fa-file-text-o"></i>&nbsp;${_('View Log')}</a></li>
                                    <li role="separator" class="divider"></li>
                                    <li><a href="${static_url("home/updateCheck?pid={}".format(sbPID), include_version=False)}"><i class="fa fa-fw fa-wrench"></i>&nbsp;${_('Check For Updates')}</a></li>
                                    <li><a href="${static_url("home/restart/?pid={}".format(sbPID), include_version=False)}" class="confirm restart"><i
                                        class="fa fa-fw fa-repeat"></i>&nbsp;${_('Restart')}</a></li>
                                    <li><a href="${static_url("home/shutdown/?pid={}".format(sbPID), include_version=False)}" class="confirm shutdown"><i
                                        class="fa fa-fw fa-power-off"></i>&nbsp;${_('Shutdown')}</a></li>
                                    % if srLogin:
                                        <li><a href="${static_url("logout", include_version=False)}" class="confirm logout"><i class="fa fa-fw fa-sign-out"></i>&nbsp;${_('Logout')}</a></li>
                                    % endif
                                    <li role="separator" class="divider"></li>
                                    <li><a href="${static_url("home/status/", include_version=False)}"><i class="fa fa-fw fa-info-circle"></i>&nbsp;${_('Server Status')}</a></li>
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
                                        ${("&middot;", "")[bool(inner_first)]}<a href="${static_url(menuItem['path'][cur_link], include_version=False)}" class="inner ${menuItem.get('class', '')}">${cur_link}</a>
                                        <% inner_first = False %>
                                    % endfor
                                % else:
                                    <a href="${static_url(menuItem['path'], include_version=False)}" class="btn ${('', ' confirm ')['confirm' in menuItem] + menuItem.get('class', '')}">
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
                    <div id="site-messages"></div>
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
                                    <span class="footerhighlight">
                                      <a href="${static_url("manage/episodeStatuses?whichStatus=2", include_version=False)}" title="${_('View overview of snatched episodes')}">
                                        +${ep_snatched}
                                      </a>
                                    </span>&nbsp;${_('Snatched')}
                                % endif
                                /&nbsp;<span class="footerhighlight">${ep_total}</span>&nbsp;${_('Episodes Downloaded')}&nbsp;${ep_percentage}
                            </span>&nbsp;|
                             <span class="footer-item">${_('Daily Search')}: <span class="footerhighlight">${str(settings.dailySearchScheduler.timeLeft()).split('.')[0]}</span></span>&nbsp;|
                             <span class="footer-item">${_('Backlog Search')}: <span class="footerhighlight">${str(settings.backlogSearchScheduler.timeLeft()).split('.')[0]}</span></span>
                        </div>

                        <div>
                            % if has_resource_module:
                                <span class="footer-item">${_('Memory used')}: <span class="footerhighlight">${pretty_file_size(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)}</span></span> |
                            % endif
                            <span class="footer-item">${_('Load time')}: <span class="footerhighlight">${"{:.4f}".format(time() - sbStartTime)}s</span></span> |
                            <span class="footer-item">Mako: <span class="footerhighlight">${"{:.4f}".format(time() - makoStartTime)}s</span></span> |
                            <span class="footer-item">${_('Branch')}: <span class="footerhighlight">${settings.BRANCH}</span></span> |
                            <span class="footer-item">${_('Now')}: <span class="footerhighlight">${datetime.datetime.now().strftime(settings.DATE_PRESET+" "+settings.TIME_PRESET)}</span></span>
                        </div>
                    </div>
                </div>
                <script type="text/javascript" src="${static_url('js/vendor.min.js')}"></script>
                <script type="text/javascript" src="${static_url('js/lib/jquery.form.min.js')}"></script>
                <script type="text/javascript" src="${static_url('js/lib/jquery.selectboxes.min.js')}"></script>
                <script type="text/javascript" src="${static_url('js/lib/formwizard.js')}"></script><!-- Can't be added to bower -->
                <script type="text/javascript" src="${static_url('js/parsers.js')}"></script>
                <script type="text/javascript" src="${static_url('js/rootDirs.js')}"></script>
                % if settings.DEVELOPER:
                    <script type="text/javascript" src="${static_url('js/core.js')}"></script>
                % else:
                    <script type="text/javascript" src="${static_url('js/core.min.js')}"></script>
                % endif
                <script type="text/javascript" src="${static_url('js/lib/jquery.scrolltopcontrol-1.1.js')}"></script>
                <script type="text/javascript" src="${static_url('js/browser.js')}" charset="utf-8"></script>
                <script type="text/javascript" src="${static_url('js/ajaxNotifications.js')}"></script>
            % endif
            <%block name="scripts" />
        </div>
    </body>
</html>
