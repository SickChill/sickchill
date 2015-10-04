<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    import calendar
    from sickbeard.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickbeard.common import Quality, qualityPresets, qualityPresetStrings
    from sickbeard import db, sbdatetime, network_timezones
    import datetime
    import re

    myDB = db.DBConnection()
    today = str(datetime.date.today().toordinal())
    layout = sickbeard.HOME_LAYOUT

    status_quality  = '(' + ','.join([str(x) for x in Quality.SNATCHED + Quality.SNATCHED_PROPER]) + ')'
    status_download = '(' + ','.join([str(x) for x in Quality.DOWNLOADED + Quality.ARCHIVED]) + ')'

    sql_statement  = 'SELECT showid, '

    sql_statement += '(SELECT COUNT(*) FROM tv_episodes WHERE showid=tv_eps.showid AND season > 0 AND episode > 0 AND airdate > 1 AND status IN ' + status_quality + ') AS ep_snatched, '
    sql_statement += '(SELECT COUNT(*) FROM tv_episodes WHERE showid=tv_eps.showid AND season > 0 AND episode > 0 AND airdate > 1 AND status IN ' + status_download + ') AS ep_downloaded, '
    sql_statement += '(SELECT COUNT(*) FROM tv_episodes WHERE showid=tv_eps.showid AND season > 0 AND episode > 0 AND airdate > 1 '
    sql_statement += ' AND ((airdate <= ' + today + ' AND (status = ' + str(SKIPPED) + ' OR status = ' + str(WANTED) + ' OR status = ' + str(FAILED) + ')) '
    sql_statement += ' OR (status IN ' + status_quality + ') OR (status IN ' + status_download + '))) AS ep_total, '

    sql_statement += ' (SELECT airdate FROM tv_episodes WHERE showid=tv_eps.showid AND airdate >= ' + today + ' AND (status = ' + str(UNAIRED) + ' OR status = ' + str(WANTED) + ') ORDER BY airdate ASC LIMIT 1) AS ep_airs_next, '
    sql_statement += ' (SELECT airdate FROM tv_episodes WHERE showid=tv_eps.showid AND airdate > 1 AND status <> ' + str(UNAIRED) + ' ORDER BY airdate DESC LIMIT 1) AS ep_airs_prev '
    sql_statement += ' FROM tv_episodes tv_eps GROUP BY showid'

    sql_result = myDB.select(sql_statement)

    show_stat = {}
    max_download_count = 1000

    for cur_result in sql_result:
        show_stat[cur_result['showid']] = cur_result
        if cur_result['ep_total'] > max_download_count:
            max_download_count = cur_result['ep_total']

    max_download_count = max_download_count * 100
%>
<%block name="metas">
<meta data-var="max_download_count" data-content="${max_download_count}">
</%block>
<%block name="scripts">
<script type="text/javascript" src="${srRoot}/js/new/home.js?${sbPID}"></script>
</%block>
<%block name="content">
<%namespace file="/inc_defs.mako" import="renderQualityPill"/>
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif

<div id="HomeLayout" class="pull-right hidden-print" style="margin-top: -40px;">
    % if layout != 'poster':
        <button id="popover" type="button" class="btn btn-inline">Select Columns <b class="caret"></b></button>
    % endif
    <span> Layout:
        <select name="layout" class="form-control form-control-inline input-sm" onchange="location = this.options[this.selectedIndex].value;">
            <option value="${srRoot}/setHomeLayout/?layout=poster" ${('', 'selected="selected"')[layout == 'poster']}>Poster</option>
            <option value="${srRoot}/setHomeLayout/?layout=small" ${('', 'selected="selected"')[layout == 'small']}>Small Poster</option>
            <option value="${srRoot}/setHomeLayout/?layout=banner" ${('', 'selected="selected"')[layout == 'banner']}>Banner</option>
            <option value="${srRoot}/setHomeLayout/?layout=simple" ${('', 'selected="selected"')[layout == 'simple']}>Simple</option>
        </select>
        % if layout != 'poster':
        Search:
            <input class="search form-control form-control-inline input-sm input200" type="search" data-column="2" placeholder="Search Show Name">
            <button type="button" class="resetsorting btn btn-inline">Reset Search</button>
        % endif
    </span>

    % if layout == 'poster':
    &nbsp;
    <span> Sort By:
        <select id="postersort" class="form-control form-control-inline input-sm">
            <option value="name" data-sort="${srRoot}/setPosterSortBy/?sort=name" ${('', 'selected="selected"')[sickbeard.POSTER_SORTBY == 'name']}>Name</option>
            <option value="date" data-sort="${srRoot}/setPosterSortBy/?sort=date" ${('', 'selected="selected"')[sickbeard.POSTER_SORTBY == 'date']}>Next Episode</option>
            <option value="network" data-sort="${srRoot}/setPosterSortBy/?sort=network" ${('', 'selected="selected"')[sickbeard.POSTER_SORTBY == 'network']}>Network</option>
            <option value="progress" data-sort="${srRoot}/setPosterSortBy/?sort=progress" ${('', 'selected="selected"')[sickbeard.POSTER_SORTBY == 'progress']}>Progress</option>
        </select>
    </span>
    &nbsp;
    <span> Sort Order:
        <select id="postersortdirection" class="form-control form-control-inline input-sm">
            <option value="true" data-sort="${srRoot}/setPosterSortDir/?direction=1" ${('', 'selected="selected"')[sickbeard.POSTER_SORTDIR == 1]}>Asc</option>
            <option value="false" data-sort="${srRoot}/setPosterSortDir/?direction=0" ${('', 'selected="selected"')[sickbeard.POSTER_SORTDIR == 0]}>Desc</option>
        </select>
    </span>
    &nbsp;

    % endif
</div>

% for curShowlist in showlists:
    <% curListType = curShowlist[0] %>
    <% myShowList = list(curShowlist[1]) %>
    % if curListType == "Anime":
        <h1 class="header">Anime List</h1>
    % endif
% if layout == 'poster':
<div id="${('container', 'container-anime')[curListType == 'Anime' and layout == 'poster']}" class="clearfix">
<div class="posterview">
% for curLoadingShow in sickbeard.showQueueScheduler.action.loadingShowList:
    % if curLoadingShow.show == None:
        <div class="show" data-name="0" data-date="010101" data-network="0" data-progress="101">
            <img alt="" title="${curLoadingShow.show_name}" class="show-image" style="border-bottom: 1px solid #111;" src="${srRoot}/images/poster.png" />
            <div class="show-details">
                <div class="show-add">Loading... (${curLoadingShow.show_name})</div>
            </div>
        </div>

    % endif
% endfor

<% myShowList.sort(lambda x, y: cmp(x.name, y.name)) %>
% for curShow in myShowList:

<%
    cur_airs_next = ''
    cur_snatched = 0
    cur_downloaded = 0
    cur_total = 0
    download_stat_tip = ''
    display_status = curShow.status

    if None is not display_status:
        if re.search(r'(?i)(?:new|returning)\s*series', curShow.status):
            display_status = 'Continuing'
        elif re.search(r'(?i)(?:nded)', curShow.status):
            display_status = 'Ended'

    if curShow.indexerid in show_stat:
        cur_airs_next = show_stat[curShow.indexerid]['ep_airs_next']

        cur_snatched = show_stat[curShow.indexerid]['ep_snatched']
        if not cur_snatched:
            cur_snatched = 0

        cur_downloaded = show_stat[curShow.indexerid]['ep_downloaded']
        if not cur_downloaded:
            cur_downloaded = 0

        cur_total = show_stat[curShow.indexerid]['ep_total']
        if not cur_total:
            cur_total = 0

    if cur_total != 0:
        download_stat = str(cur_downloaded)
        download_stat_tip = "Downloaded: " + str(cur_downloaded)
        if cur_snatched > 0:
            download_stat = download_stat
            download_stat_tip = download_stat_tip + "&#013;" + "Snatched: " + str(cur_snatched)

        download_stat = download_stat + " / " + str(cur_total)
        download_stat_tip = download_stat_tip + "&#013;" + "Total: " + str(cur_total)
    else:
        download_stat = '?'
        download_stat_tip = "no data"

    nom = cur_downloaded
    den = cur_total
    if den == 0:
        den = 1

    progressbar_percent = nom * 100 / den

    data_date = '6000000000.0'
    if cur_airs_next:
        data_date = calendar.timegm(sbdatetime.sbdatetime.convert_to_setting(network_timezones.parse_date_time(cur_airs_next, curShow.airs, curShow.network)).timetuple())
    elif None is not display_status:
        if 'nded' not in display_status and 1 == int(curShow.paused):
            data_date = '5000000500.0'
        elif 'ontinu' in display_status:
            data_date = '5000000000.0'
        elif 'nded' in display_status:
            data_date = '5000000100.0'
%>
    <div class="show" id="show${curShow.indexerid}" data-name="${curShow.name}" data-date="${data_date}" data-network="${curShow.network}" data-progress="${progressbar_percent}">
        <div class="show-image">
            <a href="${srRoot}/home/displayShow?show=${curShow.indexerid}"><img alt="" class="show-image" src="${srRoot}/showPoster/?show=${curShow.indexerid}&amp;which=poster_thumb" /></a>
        </div>

        <div class="progressbar hidden-print" style="position:relative;" data-show-id="${curShow.indexerid}" data-progress-percentage="${progressbar_percent}"></div>

        <div class="show-title">
            ${curShow.name}
        </div>

        <div class="show-date">
% if cur_airs_next:
    <% ldatetime = sbdatetime.sbdatetime.convert_to_setting(network_timezones.parse_date_time(cur_airs_next, curShow.airs, curShow.network)) %>
    <%
        try:
            out = str(sbdatetime.sbdatetime.sbfdate(ldatetime))
        except ValueError:
            out = 'Invalid date'
            pass
    %>
        ${out}
% else:
    <%
    output_html = '?'
    display_status = curShow.status
    if None is not display_status:
        if 'nded' not in display_status and 1 == int(curShow.paused):
          output_html = 'Paused'
        elif display_status:
            output_html = display_status
    %>
    ${output_html}
% endif
        </div>

        <table width="100%" cellspacing="1" border="0" cellpadding="0">
            <tr>
                <td class="show-table">
                    <span class="show-dlstats" title="${download_stat_tip}">${download_stat}</span>
                </td>

                <td class="show-table">
                    % if layout != 'simple':
                        % if curShow.network:
                            <span title="${curShow.network}"><img class="show-network-image" src="${srRoot}/showPoster/?show=${curShow.indexerid}&amp;which=network" alt="${curShow.network}" title="${curShow.network}" /></span>
                        % else:
                            <span title="No Network"><img class="show-network-image" src="${srRoot}/images/network/nonetwork.png" alt="No Network" title="No Network" /></span>
                        % endif
                    % else:
                        <span title="${curShow.network}">${curShow.network}</span>
                    % endif
                </td>

                <td class="show-table">
                    ${renderQualityPill(curShow.quality, showTitle=True, overrideClass="show-quality")}
                </td>
            </tr>
        </table>

    </div>

% endfor
</div>
</div>

% else:

<table id="showListTable${curListType}" class="tablesorter" cellspacing="1" border="0" cellpadding="0">

    <thead>
        <tr>
            <th class="nowrap">Next Ep</th>
            <th class="nowrap">Prev Ep</th>
            <th>Show</th>
            <th>Network</th>
            <th>Quality</th>
            <th>Downloads</th>
            ## <th>Size</th>
            <th>Active</th>
            <th>Status</th>
        </tr>
    </thead>

    <tfoot class="hidden-print">
        <tr>
            <th rowspan="1" colspan="1" align="center"><a href="${srRoot}/home/addShows/">Add ${('Show', 'Anime')[curListType == 'Anime']}</a></th>
            <th>&nbsp;</th>
            <th>&nbsp;</th>
            <th>&nbsp;</th>
            <th>&nbsp;</th>
            <th>&nbsp;</th>
            ## <th>&nbsp;</th> // This is needed for size
            <th>&nbsp;</th>
            <th>&nbsp;</th>
        </tr>
    </tfoot>


% if sickbeard.showQueueScheduler.action.loadingShowList:
    <tbody class="tablesorter-infoOnly">
% for curLoadingShow in sickbeard.showQueueScheduler.action.loadingShowList:

    % if curLoadingShow.show != None and curLoadingShow.show in sickbeard.showList:
         <% continue %>
    % endif
  <tr>
    <td align="center">(loading)</td>
    <td></td>
    <td>
    % if curLoadingShow.show == None:
    <span title="">Loading... (${curLoadingShow.show_name})</span>
    % else:
    <a href="displayShow?show=${curLoadingShow.show.indexerid}">${curLoadingShow.show.name}</a>
    % endif
    </td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
  </tr>
% endfor
    </tbody>
% endif

    <tbody>

<% myShowList.sort(lambda x, y: cmp(x.name, y.name)) %>
% for curShow in myShowList:
<%
    cur_airs_next = ''
    cur_airs_prev = ''
    cur_snatched = 0
    cur_downloaded = 0
    cur_total = 0
    download_stat_tip = ''

    if curShow.indexerid in show_stat:
        cur_airs_next = show_stat[curShow.indexerid]['ep_airs_next']
        cur_airs_prev = show_stat[curShow.indexerid]['ep_airs_prev']

        cur_snatched = show_stat[curShow.indexerid]['ep_snatched']
        if not cur_snatched:
            cur_snatched = 0

        cur_downloaded = show_stat[curShow.indexerid]['ep_downloaded']
        if not cur_downloaded:
            cur_downloaded = 0

        cur_total = show_stat[curShow.indexerid]['ep_total']
        if not cur_total:
            cur_total = 0

    if cur_total != 0:
        download_stat = str(cur_downloaded)
        download_stat_tip = "Downloaded: " + str(cur_downloaded)
        if cur_snatched > 0:
            download_stat = download_stat + "+" + str(cur_snatched)
            download_stat_tip = download_stat_tip + "&#013;" + "Snatched: " + str(cur_snatched)

        download_stat = download_stat + " / " + str(cur_total)
        download_stat_tip = download_stat_tip + "&#013;" + "Total: " + str(cur_total)
    else:
        download_stat = '?'
        download_stat_tip = "no data"

    nom = cur_downloaded
    den = cur_total
    if den == 0:
        den = 1

    progressbar_percent = nom * 100 / den
%>
    <tr>
    % if cur_airs_next:
        <% airDate = sbdatetime.sbdatetime.convert_to_setting(network_timezones.parse_date_time(cur_airs_next, curShow.airs, curShow.network)) %>
        % try:
            <td align="center" class="nowrap">
                <time datetime="${airDate.isoformat('T')}" class="date">${sbdatetime.sbdatetime.sbfdate(airDate)}</time>
            </td>
        % except ValueError:
            <td align="center" class="nowrap"></td>
        % endtry
    % else:
        <td align="center" class="nowrap"></td>
    % endif

    % if cur_airs_prev:
        <% airDate = sbdatetime.sbdatetime.convert_to_setting(network_timezones.parse_date_time(cur_airs_prev, curShow.airs, curShow.network)) %>
        % try:
            <td align="center" class="nowrap">
                <time datetime="${airDate.isoformat('T')}" class="date">${sbdatetime.sbdatetime.sbfdate(airDate)}</time>
            </td>
        % except ValueError:
            <td align="center" class="nowrap"></td>
        % endtry
    % else:
        <td align="center" class="nowrap"></td>
    % endif

    % if layout == 'small':
        <td class="tvShow">
            <div class="imgsmallposter ${layout}">
                <a href="${srRoot}/home/displayShow?show=${curShow.indexerid}" title="${curShow.name}">
                    <img src="${srRoot}/showPoster/?show=${curShow.indexerid}&amp;which=poster_thumb" class="${layout}" alt="${curShow.indexerid}"/>
                </a>
                <a href="${srRoot}/home/displayShow?show=${curShow.indexerid}" style="vertical-align: middle;">${curShow.name}</a>
            </div>
        </td>
    % elif layout == 'banner':
        <td>
            <span style="display: none;">${curShow.name}</span>
            <div class="imgbanner ${layout}">
                <a href="${srRoot}/home/displayShow?show=${curShow.indexerid}">
                <img src="${srRoot}/showPoster/?show=${curShow.indexerid}&amp;which=banner" class="${layout}" alt="${curShow.indexerid}" title="${curShow.name}"/>
            </div>
        </td>
    % elif layout == 'simple':
        <td class="tvShow"><a href="${srRoot}/home/displayShow?show=${curShow.indexerid}">${curShow.name}</a></td>
    % endif

    % if layout != 'simple':
        <td align="center">
        % if curShow.network:
            <span title="${curShow.network}" class="hidden-print"><img id="network" width="54" height="27" src="${srRoot}/showPoster/?show=${curShow.indexerid}&amp;which=network" alt="${curShow.network}" title="${curShow.network}" /></span>
            <span class="visible-print-inline">${curShow.network}</span>
        % else:
            <span title="No Network" class="hidden-print"><img id="network" width="54" height="27" src="${srRoot}/images/network/nonetwork.png" alt="No Network" title="No Network" /></span>
            <span class="visible-print-inline">No Network</span>
        % endif
        </td>
    % else:
        <td>
            <span title="${curShow.network}">${curShow.network}</span>
        </td>
    % endif

        <td align="center">${renderQualityPill(curShow.quality, showTitle=True)}</td>

        <td align="center">
            ## This first span is used for sorting and is never displayed to user
            <span style="display: none;">${download_stat}</span>
            <div class="progressbar hidden-print" style="position:relative;" data-show-id="${curShow.indexerid}" data-progress-percentage="${progressbar_percent}" data-progress-text="${download_stat}" data-progress-tip="${download_stat_tip}"></div>
            <span class="visible-print-inline">${download_stat}</span>
        </td>

        ## <% show_size = sickbeard.helpers.get_size(curShow._location) %>
        ## <td align="center" data-show-size="${show_size}">${sickbeard.helpers.pretty_filesize(show_size)}</td>

        <td align="center">
            <% paused = int(curShow.paused) == 0 and curShow.status == 'Continuing' %>
            <img src="${srRoot}/images/${('no16.png', 'yes16.png')[bool(paused)]}" alt="${('No', 'Yes')[bool(paused)]}" width="16" height="16" />
        </td>

        <td align="center">
        <%
            display_status = curShow.status
            if None is not display_status:
                if re.search('(?i)(?:new|returning)\s*series', curShow.status):
                    display_status = 'Continuing'
                elif re.search('(?i)(?:nded)', curShow.status):
                    display_status = 'Ended'
        %>
        ${display_status}
        </td>
    </tr>
% endfor
</tbody>
</table>

% endif
% endfor
</%block>
