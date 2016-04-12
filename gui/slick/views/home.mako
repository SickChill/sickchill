<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    import calendar
    from sickbeard import sbdatetime
    from sickbeard import network_timezones
    from sickrage.helper.common import pretty_file_size
    import re

    ## Need to initialize these for gettext, they are done dynamically in the ui
    _('Continuing')
    _('Ended')
%>
<%block name="metas">
<meta data-var="max_download_count" data-content="${max_download_count}">
</%block>
<%block name="content">
<%namespace file="/inc_defs.mako" import="renderQualityPill"/>

<table style="width: 100%;" class="home-header">
    <tr>
        <td nowrap>
            % if not header is UNDEFINED:
                <h1 class="header" style="margin: 0;">${header}</h1>
            % else:
                <h1 class="title" style="margin: 0;">${title}</h1>
            % endif
        </td>

        <td align="right">
            <div>
                % if sickbeard.HOME_LAYOUT != 'poster':
                    <span class="show-option">
                        <button id="popover" type="button" class="btn btn-inline">${_('Select Columns')} <b class="caret"></b></button>
                    </span>

                    <span class="show-option">
                        <button type="button" class="resetsorting btn btn-inline">${_('Clear Filter(s)')}</button>
                    </span>
                % endif

                % if sickbeard.HOME_LAYOUT == 'poster':
                    <span class="show-option"> ${_('Poster Size')}:
                        <div style="width: 100px; display: inline-block; margin-left: 7px;" id="posterSizeSlider"></div>
                    </span>

                    <span class="show-option">
                        <input id="filterShowName" class="form-control form-control-inline input-sm input200" type="search" placeholder="${_('Filter Show Name')}">
                    </span>

                    <span class="show-option"> ${_('Sort By')}:
                        <select id="postersort" class="form-control form-control-inline input-sm">
                            <option value="name" data-sort="${srRoot}/setPosterSortBy/?sort=name" ${('', 'selected="selected"')[sickbeard.POSTER_SORTBY == 'name']}>${_('Name')}</option>
                            <option value="date" data-sort="${srRoot}/setPosterSortBy/?sort=date" ${('', 'selected="selected"')[sickbeard.POSTER_SORTBY == 'date']}>${_('Next Episode')}</option>
                            <option value="network" data-sort="${srRoot}/setPosterSortBy/?sort=network" ${('', 'selected="selected"')[sickbeard.POSTER_SORTBY == 'network']}>${_('Network')}</option>
                            <option value="progress" data-sort="${srRoot}/setPosterSortBy/?sort=progress" ${('', 'selected="selected"')[sickbeard.POSTER_SORTBY == 'progress']}>${_('Progress')}</option>
                        </select>
                    </span>

                    <span class="show-option"> ${_('Direction')}:
                        <select id="postersortdirection" class="form-control form-control-inline input-sm">
                            <option value="true" data-sort="${srRoot}/setPosterSortDir/?direction=1" ${('', 'selected="selected"')[sickbeard.POSTER_SORTDIR == 1]}>${_('Ascending')} </option>
                            <option value="false" data-sort="${srRoot}/setPosterSortDir/?direction=0" ${('', 'selected="selected"')[sickbeard.POSTER_SORTDIR == 0]}>${_('Descending')}</option>
                        </select>
                    </span>
                % endif

                <span class="show-option"> ${_('Layout')}:
                    <select name="layout" class="form-control form-control-inline input-sm" onchange="location = this.options[this.selectedIndex].value;">
                        <option value="${srRoot}/setHomeLayout/?layout=poster" ${('', 'selected="selected"')[sickbeard.HOME_LAYOUT == 'poster']}>${_('Poster')}</option>
                        <option value="${srRoot}/setHomeLayout/?layout=small" ${('', 'selected="selected"')[sickbeard.HOME_LAYOUT == 'small']}>${_('Small Poster')}</option>
                        <option value="${srRoot}/setHomeLayout/?layout=banner" ${('', 'selected="selected"')[sickbeard.HOME_LAYOUT == 'banner']}>${_('Banner')}</option>
                        <option value="${srRoot}/setHomeLayout/?layout=simple" ${('', 'selected="selected"')[sickbeard.HOME_LAYOUT == 'simple']}>${_('Simple')}</option>
                    </select>
                </span>
            </div>
        </td>
    </tr>
</table>
% if sickbeard.HOME_LAYOUT == 'poster':
    <div class="loading-spinner"></div>
% endif

% for cur_showlist in showlists:
    <% cur_list_type = cur_showlist[0] %>
    <% my_show_list = list(cur_showlist[1]) %>
    % if cur_list_type == "Anime":
        <h1 class="header">${_('Anime List')}</h1>
        % if sickbeard.HOME_LAYOUT == 'poster':
            <div class="loading-spinner"></div>
    % endif
    % endif
% if sickbeard.HOME_LAYOUT == 'poster':
<div id="${('container', 'container-anime')[cur_list_type == 'Anime' and sickbeard.HOME_LAYOUT == 'poster']}" class="show-grid clearfix">
<div class="posterview">
% for cur_loading_show in sickbeard.show_queue_scheduler.action.loadingShowList:
    % if cur_loading_show.show is None:
        <div class="show-container" data-name="0" data-date="010101" data-network="0" data-progress="101">
            <img alt="" title="${cur_loading_show.show_name}" class="show-image" style="border-bottom: 1px solid #111;" src="data:image/png;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" data-src="${srRoot}/images/poster.png" />
            <div class="show-details">
                <div class="show-add">${_('Loading...')} (${cur_loading_show.show_name})</div>
            </div>
        </div>

    % endif
% endfor

<% my_show_list.sort(lambda x, y: cmp(x.name, y.name)) %>
% for cur_show in my_show_list:

<%
    cur_airs_next = ''
    cur_snatched = 0
    cur_downloaded = 0
    cur_total = 0
    download_stat_tip = ''
    display_status = cur_show.status

    if display_status:
        if re.search(r'(?i)(?:new|returning)\s*series', cur_show.status):
            display_status = 'Continuing'
        elif re.search(r'(?i)(?:nded)', cur_show.status):
            display_status = 'Ended'

    if cur_show.indexerid in show_stat:
        cur_airs_next = show_stat[cur_show.indexerid]['ep_airs_next']

        cur_snatched = show_stat[cur_show.indexerid]['ep_snatched']
        if not cur_snatched:
            cur_snatched = 0

        cur_downloaded = show_stat[cur_show.indexerid]['ep_downloaded']
        if not cur_downloaded:
            cur_downloaded = 0

        cur_total = show_stat[cur_show.indexerid]['ep_total']
        if not cur_total:
            cur_total = 0

    download_stat = str(cur_downloaded)
    download_stat_tip = _('Downloaded') + ": " + str(cur_downloaded)

    if cur_snatched:
        download_stat = download_stat + "+" + str(cur_snatched)
        download_stat_tip = download_stat_tip + "&#013;" + _('Snatched') + ": " + str(cur_snatched)

    download_stat = download_stat + " / " + str(cur_total)
    download_stat_tip = download_stat_tip + "&#013;" + _('Total') + ": " + str(cur_total)

    nom = cur_downloaded
    if cur_total:
        den = cur_total
    else:
        den = 1
        download_stat_tip = _('Unaired')

    progressbar_percent = nom * 100 / den

    data_date = '6000000000.0'
    if cur_airs_next:
        data_date = calendar.timegm(sbdatetime.sbdatetime.convert_to_setting(network_timezones.parse_date_time(cur_airs_next, cur_show.airs, cur_show.network)).timetuple())
    elif display_status:
        if display_status != 'Ended' and 1 == int(cur_show.paused):
            data_date = '5000000500.0'
        elif display_status == 'Continuing':
            data_date = '5000000000.0'
        elif display_status == 'Ended':
            data_date = '5000000100.0'
%>
    <div class="show-container" id="show${cur_show.indexerid}" data-name="${cur_show.name}" data-date="${data_date}" data-network="${cur_show.network}" data-progress="${progressbar_percent}">
        <div class="show-image">
            <a href="${srRoot}/home/displayShow?show=${cur_show.indexerid}"><img alt="" class="show-image" src="data:image/png;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" data-src="${srRoot}/showPoster/?show=${cur_show.indexerid}&amp;which=poster_thumb" /></a>
        </div>

        <div class="progressbar hidden-print" style="position:relative;" data-show-id="${cur_show.indexerid}" data-progress-percentage="${progressbar_percent}"></div>

        <div class="show-title">
            ${cur_show.name}
        </div>

        <div class="show-date">
% if cur_airs_next:
    <% ldatetime = sbdatetime.sbdatetime.convert_to_setting(network_timezones.parse_date_time(cur_airs_next, cur_show.airs, cur_show.network)) %>
    <%
        try:
            out = str(sbdatetime.sbdatetime.sbfdate(ldatetime))
        except ValueError:
            out = _('Invalid date')
            pass
    %>
        ${out}
% else:
    <%
    output_html = '?'
    display_status = cur_show.status
    if display_status:
        if display_status != 'Ended' and 1 == int(cur_show.paused):
          output_html = 'Paused'
        elif display_status:
            output_html = display_status
    %>
    ${_(output_html)}
% endif
        </div>

        <div class="show-details">
            <table class="show-details" width="100%" cellspacing="1" border="0" cellpadding="0">
                <tr>
                    <td class="show-table">
                        <span class="show-dlstats" title="${download_stat_tip}">${download_stat}</span>
                    </td>

                    <td class="show-table">
                        % if sickbeard.HOME_LAYOUT != 'simple':
                            % if cur_show.network:
                                <span title="${cur_show.network}"><img class="show-network-image" src="data:image/png;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" data-src="${srRoot}/showPoster/?show=${cur_show.indexerid}&amp;which=network" alt="${cur_show.network}" title="${cur_show.network}" /></span>
                            % else:
                                <span title="${_('No Network')}"><img class="show-network-image" src="data:image/png;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" data-src="${srRoot}/images/network/nonetwork.png" alt="No Network" title="No Network" /></span>
                            % endif
                        % else:
                            <span title="${cur_show.network}">${cur_show.network}</span>
                        % endif
                    </td>

                    <td class="show-table">
                        ${renderQualityPill(cur_show.quality, showTitle=True, overrideClass="show-quality")}
                    </td>
                </tr>
            </table>
        </div>

    </div>

% endfor
</div>
</div>

% else:

<table id="showListTable${cur_list_type}" class="tablesorter" cellspacing="1" border="0" cellpadding="0">

    <thead>
        <tr>
            <th class="nowrap">${_('Next Ep')}</th>
            <th class="nowrap">${_('Prev Ep')}</th>
            <th>${_('Show')}</th>
            <th>${_('Network')}</th>
            <th>${_('Quality')}</th>
            <th>${_('Downloads')}</th>
            <th>${_('Size')}</th>
            <th>${_('Active')}</th>
            <th>${_('Status')}</th>
        </tr>
    </thead>

    <tfoot class="hidden-print">
        <tr>
            <th rowspan="1" colspan="1" align="center"><a href="${srRoot}/addShows/">${_('Add')} ${(_('Show'), _('Anime'))[cur_list_type == 'Anime']}</a></th>
            <th>&nbsp;</th>
            <th>&nbsp;</th>
            <th>&nbsp;</th>
            <th>&nbsp;</th>
            <th>&nbsp;</th>
            <th>&nbsp;</th>
            <th>&nbsp;</th>
            <th>&nbsp;</th>
        </tr>
    </tfoot>


% if sickbeard.show_queue_scheduler.action.loadingShowList:
    <tbody class="tablesorter-infoOnly">
% for cur_loading_show in sickbeard.show_queue_scheduler.action.loadingShowList:

    % if cur_loading_show.show is not None and cur_loading_show.show in sickbeard.showList:
         <% continue %>
    % endif
  <tr>
    <td align="center">(${_('loading')})</td>
    <td></td>
    <td>
    % if cur_loading_show.show is None:
    <span title="">${_('Loading...')} (${cur_loading_show.show_name})</span>
    % else:
    <a href="displayShow?show=${cur_loading_show.show.indexerid}">${cur_loading_show.show.name}</a>
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

<% my_show_list.sort(lambda x, y: cmp(x.name, y.name)) %>
% for cur_show in my_show_list:
<%
    cur_airs_next = ''
    cur_airs_prev = ''
    cur_snatched = 0
    cur_downloaded = 0
    cur_total = 0
    show_size = 0
    download_stat_tip = ''

    if cur_show.indexerid in show_stat:
        cur_airs_next = show_stat[cur_show.indexerid]['ep_airs_next']
        cur_airs_prev = show_stat[cur_show.indexerid]['ep_airs_prev']

        cur_snatched = show_stat[cur_show.indexerid]['ep_snatched']
        if not cur_snatched:
            cur_snatched = 0

        cur_downloaded = show_stat[cur_show.indexerid]['ep_downloaded']
        if not cur_downloaded:
            cur_downloaded = 0

        cur_total = show_stat[cur_show.indexerid]['ep_total']
        if not cur_total:
            cur_total = 0

        show_size = show_stat[cur_show.indexerid]['show_size']

    download_stat = str(cur_downloaded)
    download_stat_tip = _('Downloaded') + ": " + str(cur_downloaded)

    if cur_snatched:
        download_stat = download_stat + "+" + str(cur_snatched)
        download_stat_tip = download_stat_tip + "&#013;" + _('Snatched') + ": " + str(cur_snatched)

    download_stat = download_stat + " / " + str(cur_total)
    download_stat_tip = download_stat_tip + "&#013;" + _('Total') + ": " + str(cur_total)

    nom = cur_downloaded
    if cur_total:
        den = cur_total
    else:
        den = 1
        download_stat_tip = _('Unaired')

    progressbar_percent = nom * 100 / den
%>
    <tr>
    % if cur_airs_next:
        <% airDate = sbdatetime.sbdatetime.convert_to_setting(network_timezones.parse_date_time(cur_airs_next, cur_show.airs, cur_show.network)) %>
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
        <% airDate = sbdatetime.sbdatetime.convert_to_setting(network_timezones.parse_date_time(cur_airs_prev, cur_show.airs, cur_show.network)) %>
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

    % if sickbeard.HOME_LAYOUT == 'small':
        <td class="tvShow">
            <div class="imgsmallposter ${sickbeard.HOME_LAYOUT}">
                <a href="${srRoot}/home/displayShow?show=${cur_show.indexerid}" title="${cur_show.name}">
                    <img src="data:image/png;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" data-src="${srRoot}/showPoster/?show=${cur_show.indexerid}&amp;which=poster_thumb" class="${sickbeard.HOME_LAYOUT}" alt="${cur_show.indexerid}"/>
                </a>
                <a href="${srRoot}/home/displayShow?show=${cur_show.indexerid}" style="vertical-align: middle;">${cur_show.name}</a>
            </div>
        </td>
    % elif sickbeard.HOME_LAYOUT == 'banner':
        <td>
            <span style="display: none;">${cur_show.name}</span>
            <div class="imgbanner ${sickbeard.HOME_LAYOUT}">
                <a href="${srRoot}/home/displayShow?show=${cur_show.indexerid}">
                <img src="data:image/png;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" data-src="${srRoot}/showPoster/?show=${cur_show.indexerid}&amp;which=banner" class="${sickbeard.HOME_LAYOUT}" alt="${cur_show.indexerid}" title="${cur_show.name}"/>
            </div>
        </td>
    % elif sickbeard.HOME_LAYOUT == 'simple':
        <td class="tvShow"><a href="${srRoot}/home/displayShow?show=${cur_show.indexerid}">${cur_show.name}</a></td>
    % endif

    % if sickbeard.HOME_LAYOUT != 'simple':
        <td align="center">
        % if cur_show.network:
            <span title="${cur_show.network}" class="hidden-print"><img id="network" width="54" height="27" src="data:image/png;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" data-src="${srRoot}/showPoster/?show=${cur_show.indexerid}&amp;which=network" alt="${cur_show.network}" title="${cur_show.network}" /></span>
            <span class="visible-print-inline">${cur_show.network}</span>
        % else:
            <span title="No Network" class="hidden-print"><img id="network" width="54" height="27" src="data:image/png;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" data-src="${srRoot}/images/network/nonetwork.png" alt="No Network" title="No Network" /></span>
            <span class="visible-print-inline">${_('No Network')}</span>
        % endif
        </td>
    % else:
        <td>
            <span title="${cur_show.network}">${cur_show.network}</span>
        </td>
    % endif

        <td align="center">${renderQualityPill(cur_show.quality, showTitle=True)}</td>

        <td align="center">
            ## This first span is used for sorting and is never displayed to user
            <span style="display: none;">${download_stat}</span>
            <div class="progressbar hidden-print" style="position:relative;" data-show-id="${cur_show.indexerid}" data-progress-percentage="${progressbar_percent}" data-progress-text="${download_stat}" data-progress-tip="${download_stat_tip}"></div>
            <span class="visible-print-inline">${download_stat}</span>
        </td>

        <td align="center" data-show-size="${show_size}">${pretty_file_size(show_size)}</td>

        <td align="center">
            <% paused = int(cur_show.paused) == 0 and cur_show.status == 'Continuing' %>
            <img src="data:image/png;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" data-src="${srRoot}/images/${('no16.png', 'yes16.png')[bool(paused)]}" alt="${('No', 'Yes')[bool(paused)]}" width="16" height="16" />
        </td>

        <td align="center">
        <%
            display_status = cur_show.status
            if display_status:
                if re.search(r'(?i)(?:new|returning)\s*series', cur_show.status):
                    display_status = 'Continuing'
                elif re.search('(?i)(?:nded)', cur_show.status):
                    display_status = 'Ended'

        %>
        ${_(display_status)}
        </td>
    </tr>
% endfor
</tbody>
</table>

% endif
% endfor
</%block>
