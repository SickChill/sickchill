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
    <meta data-var="max_download_count" data-content="${max_download_count}"/>
</%block>

<%block name="content">
    <%namespace file="/inc_defs.mako" import="renderQualityPill"/>

    <div class="row">
        <div class="pull-right col-lg-9 col-md-9 col-sm-${'12' if(sickbeard.HOME_LAYOUT == 'poster') else '8'} col-xs-12">
            <span class="pull-right show-option"> ${_('Layout')}:
                <select name="layout" class="form-control form-control-inline input-sm" onchange="location = this.options[this.selectedIndex].value;" title="Layout">
                    <option value="${srRoot}/setHomeLayout/?layout=poster" ${('', 'selected="selected"')[sickbeard.HOME_LAYOUT == 'poster']}>${_('Poster')}</option>
                    <option value="${srRoot}/setHomeLayout/?layout=small" ${('', 'selected="selected"')[sickbeard.HOME_LAYOUT == 'small']}>${_('Small Poster')}</option>
                    <option value="${srRoot}/setHomeLayout/?layout=banner" ${('', 'selected="selected"')[sickbeard.HOME_LAYOUT == 'banner']}>${_('Banner')}</option>
                    <option value="${srRoot}/setHomeLayout/?layout=simple" ${('', 'selected="selected"')[sickbeard.HOME_LAYOUT == 'simple']}>${_('Simple')}</option>
                </select>
            </span>

            % if sickbeard.HOME_LAYOUT != 'poster':
                <span class="pull-right show-option">
                    <button type="button" class="resetsorting btn btn-inline">${_('Clear Filter(s)')}</button>
                </span>
                <span class="pull-right show-option">
                    <button id="popover" type="button" class="btn btn-inline">${_('Select Columns')} <b class="caret"></b></button>
                </span>
            % endif

            % if sickbeard.HOME_LAYOUT == 'poster':
                <span class="pull-right show-option"> ${_('Direction')}:
                    <select id="postersortdirection" class="form-control form-control-inline input-sm" title="Sort">
                        <option value="true" data-sort="${srRoot}/setPosterSortDir/?direction=1" ${('', 'selected="selected"')[sickbeard.POSTER_SORTDIR == 1]}>${_('Ascending')} </option>
                        <option value="false" data-sort="${srRoot}/setPosterSortDir/?direction=0" ${('', 'selected="selected"')[sickbeard.POSTER_SORTDIR == 0]}>${_('Descending')}</option>
                    </select>
                </span>

                <span class="pull-right show-option"> ${_('Sort By')}:
                    <select id="postersort" class="form-control form-control-inline input-sm" title="Poster Sort">
                        <option value="name" data-sort="${srRoot}/setPosterSortBy/?sort=name" ${('', 'selected="selected"')[sickbeard.POSTER_SORTBY == 'name']}>${_('Name')}</option>
                        <option value="date" data-sort="${srRoot}/setPosterSortBy/?sort=date" ${('', 'selected="selected"')[sickbeard.POSTER_SORTBY == 'date']}>${_('Next Episode')}</option>
                        <option value="network" data-sort="${srRoot}/setPosterSortBy/?sort=network" ${('', 'selected="selected"')[sickbeard.POSTER_SORTBY == 'network']}>${_('Network')}</option>
                        <option value="progress" data-sort="${srRoot}/setPosterSortBy/?sort=progress" ${('', 'selected="selected"')[sickbeard.POSTER_SORTBY == 'progress']}>${_('Progress')}</option>
                    </select>
                </span>

                <span class="pull-right show-option">
                    <input id="filterShowName" class="form-control form-control-inline input-sm input200" type="search" placeholder="${_('Filter Show Name')}">
                </span>

                <span class="pull-right show-option"> ${_('Poster Size')}:
                    <div style="width: 100px; display: inline-block; margin-left: 7px;" id="posterSizeSlider"></div>
                </span>
            % endif
        </div>

        <div class="col-lg-3 col-md-3 col-sm-${'12' if(sickbeard.HOME_LAYOUT == 'poster') else '4'} col-xs-12">
            % if not header is UNDEFINED:
                <h1 class="header">${header}</h1>
            % else:
                <h1 class="title">${title}</h1>
            % endif
        </div>
    </div>

    <div class="row home-container">
        <div class="col-md-12">
            % if sickbeard.HOME_LAYOUT == 'poster':
                <div class="loading-spinner"></div>
            % endif

            % for curShowlist in showlists:
                <div class="row">
                    <div class="col-md-12">
                        <% curListType = curShowlist[0] %>
                        <% myShowList = list(curShowlist[1]) %>
                        % if curListType == "Anime":
                            <br/>
                            <br/>
                            <div class="row">
                                <div class="col-md-12">
                                    <h1 class="header">${_('Anime List')}</h1>
                                    % if sickbeard.HOME_LAYOUT == 'poster':
                                        <div class="loading-spinner"></div>
                                    % endif
                                </div>
                            </div>
                        % endif

                        % if sickbeard.HOME_LAYOUT == 'poster':
                            <div id="${('container', 'container-anime')[curListType == 'Anime' and sickbeard.HOME_LAYOUT == 'poster']}" class="show-grid clearfix">
                                <div class="posterview">
                                    % for curLoadingShow in sickbeard.showQueueScheduler.action.loadingShowList:
                                        % if curLoadingShow.show is None:
                                            <div class="show-container" data-name="0" data-date="010101" data-network="0" data-progress="101">
                                                <img alt="" title="${curLoadingShow.show_name}" class="show-image" style="border-bottom: 1px solid #111;" src="data:image/png;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" data-src="${srRoot}/images/poster.png" />
                                                <div class="show-details">
                                                    <div class="show-add">${_('Loading...')} (${curLoadingShow.show_name})</div>
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

                                            if display_status:
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
                                                data_date = calendar.timegm(sbdatetime.sbdatetime.convert_to_setting(network_timezones.parse_date_time(cur_airs_next, curShow.airs, curShow.network)).timetuple())
                                            elif display_status:
                                                if display_status != 'Ended' and 1 == int(curShow.paused):
                                                    data_date = '5000000500.0'
                                                elif display_status == 'Continuing':
                                                    data_date = '5000000000.0'
                                                elif display_status == 'Ended':
                                                    data_date = '5000000100.0'
                                        %>
                                        <div class="show-container" id="show${curShow.indexerid}" data-name="${curShow.name}" data-date="${data_date}" data-network="${curShow.network}" data-progress="${progressbar_percent}">
                                            <div class="show-image">
                                                <a href="${srRoot}/home/displayShow?show=${curShow.indexerid}"><img alt="" class="show-image" src="data:image/png;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" data-src="${srRoot}/showPoster/?show=${curShow.indexerid}&amp;which=poster_thumb" /></a>
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
                                                        out = _('Invalid date')
                                                        pass
                                                %>
                                                ${out}
                                                % else:
                                                <%
                                                    output_html = '?'
                                                    display_status = curShow.status
                                                    if display_status:
                                                        if display_status != 'Ended' and 1 == int(curShow.paused):
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
                                                                % if curShow.network:
                                                                    <span title="${curShow.network}"><img class="show-network-image" src="data:image/png;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" data-src="${srRoot}/showPoster/?show=${curShow.indexerid}&amp;which=network" alt="${curShow.network}" title="${curShow.network}" /></span>
                                                                % else:
                                                                    <span title="${_('No Network')}"><img class="show-network-image" src="data:image/png;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" data-src="${srRoot}/images/network/nonetwork.png" alt="No Network" title="No Network" /></span>
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
                                        </div>
                                    % endfor
                                </div>
                            </div>
                        % else:
                            <div class="horizontal-scroll">
                                <table id="showListTable${curListType}" class="tablesorter" cellspacing="1" border="0" cellpadding="0">
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
                                            <th rowspan="1" colspan="1" align="center"><a href="${srRoot}/addShows/">${_('Add')} ${(_('Show'), _('Anime'))[curListType == 'Anime']}</a></th>
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
                                    % if sickbeard.showQueueScheduler.action.loadingShowList:
                                        <tbody class="tablesorter-infoOnly">
                                            % for curLoadingShow in sickbeard.showQueueScheduler.action.loadingShowList:
                                            % if curLoadingShow.show is not None and curLoadingShow.show in sickbeard.showList:
                                                <% continue %>
                                            % endif
                                                <tr>
                                                    <td align="center">(${_('loading')})</td>
                                                    <td></td>
                                                    <td>
                                                        % if curLoadingShow.show is None:
                                                            <span title="">${_('Loading...')} (${curLoadingShow.show_name})</span>
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
                                                show_size = 0
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

                                                    show_size = show_stat[curShow.indexerid]['show_size']

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

                                                % if sickbeard.HOME_LAYOUT == 'small':
                                                    <td class="tvShow">
                                                        <div class="imgsmallposter ${sickbeard.HOME_LAYOUT}">
                                                            <a href="${srRoot}/home/displayShow?show=${curShow.indexerid}" title="${curShow.name}">
                                                                <img src="data:image/png;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" data-src="${srRoot}/showPoster/?show=${curShow.indexerid}&amp;which=poster_thumb" class="${sickbeard.HOME_LAYOUT}" alt="${curShow.indexerid}"/>
                                                            </a>
                                                            <a href="${srRoot}/home/displayShow?show=${curShow.indexerid}" style="vertical-align: middle;">${curShow.name}</a>
                                                        </div>
                                                    </td>
                                                % elif sickbeard.HOME_LAYOUT == 'banner':
                                                    <td>
                                                        <span style="display: none;">${curShow.name}</span>
                                                        <div class="imgbanner ${sickbeard.HOME_LAYOUT}">
                                                            <a href="${srRoot}/home/displayShow?show=${curShow.indexerid}">
                                                                <img src="data:image/png;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" data-src="${srRoot}/showPoster/?show=${curShow.indexerid}&amp;which=banner" class="${sickbeard.HOME_LAYOUT}" alt="${curShow.indexerid}" title="${curShow.name}"/>
                                                            </a>
                                                        </div>
                                                    </td>
                                                % elif sickbeard.HOME_LAYOUT == 'simple':
                                                    <td class="tvShow"><a href="${srRoot}/home/displayShow?show=${curShow.indexerid}">${curShow.name}</a></td>
                                                % endif

                                                % if sickbeard.HOME_LAYOUT != 'simple':
                                                    <td align="center">
                                                        % if curShow.network:
                                                            <span title="${curShow.network}" class="hidden-print"><img id="network" width="54" height="27" src="data:image/png;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" data-src="${srRoot}/showPoster/?show=${curShow.indexerid}&amp;which=network" alt="${curShow.network}" title="${curShow.network}" /></span>
                                                            <span class="visible-print-inline">${curShow.network}</span>
                                                        % else:
                                                            <span title="No Network" class="hidden-print"><img id="network" width="54" height="27" src="data:image/png;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" data-src="${srRoot}/images/network/nonetwork.png" alt="No Network" title="No Network" /></span>
                                                            <span class="visible-print-inline">${_('No Network')}</span>
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

                                                <td align="center" data-show-size="${show_size}">${pretty_file_size(show_size)}</td>

                                                <td align="center">
                                                    <% paused = int(curShow.paused) == 0 and curShow.status == 'Continuing' %>
                                                    <img src="data:image/png;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" data-src="${srRoot}/images/${('no16.png', 'yes16.png')[bool(paused)]}" alt="${('No', 'Yes')[bool(paused)]}" width="16" height="16" />
                                                </td>

                                                <td align="center">
                                                    <%
                                                        display_status = curShow.status
                                                        if display_status:
                                                            if re.search(r'(?i)(?:new|returning)\s*series', curShow.status):
                                                                display_status = 'Continuing'
                                                            elif re.search('(?i)(?:nded)', curShow.status):
                                                                display_status = 'Ended'

                                                    %>
                                                    ${_(display_status)}
                                                </td>
                                            </tr>
                                        % endfor
                                    </tbody>
                                </table>
                            </div>
                        % endif
                    </div>
                </div>
            % endfor
        </div>
    </div>
</%block>
