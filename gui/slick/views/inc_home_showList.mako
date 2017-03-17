<%!
    import sickbeard
    import calendar
    from sickbeard import sbdatetime
    from sickbeard import network_timezones
    from sickrage.helper.common import pretty_file_size
    import os
    import re
    from six.moves import urllib

    ## Need to initialize these for gettext, they are done dynamically in the ui
    _('Continuing')
    _('Ended')
%>
<%page args="curListType, myShowList"/>
<%namespace file="/inc_defs.mako" import="renderQualityPill"/>

% if sickbeard.HOME_LAYOUT == 'poster':
    <div id="${('container', 'container-anime')[curListType == 'Anime']}" class="show-grid clearfix">
        <div class="posterview">
            % for curLoadingShow in sickbeard.showQueueScheduler.action.loadingShowList:
                <%
                    if curLoadingShow.show in sickbeard.showList:
                        continue

                    if curLoadingShow.show:
                        loading_show_name = curLoadingShow.show.name
                        loading_show_sort_name = curLoadingShow.show.sort_name
                        loading_show_id = curLoadingShow.show.indexerid
                        loading_show_network = curLoadingShow.show.network
                        loading_show_quality = curLoadingShow.show.quality
                    else:
                        loading_show_name = curLoadingShow.show_name.rsplit(os.sep)[-1]
                        loading_show_sort_name = curLoadingShow.show_name
                        if not sickbeard.SORT_ARTICLE:
                            loading_show_sort_name = re.sub(r'(?:The|A|An)\s', '', loading_show_sort_name, flags=re.I)

                        loading_show_id = urllib.parse.quote_plus(curLoadingShow.show_name)
                        loading_show_network = _('Loading')
                        loading_show_quality = 0
                %>
                <div class="show-container" data-name="${loading_show_sort_name}" data-date="1" data-network="0" data-progress="0">
                    <div class="show-image">
                        <img alt="" title="${loading_show_name}" class="show-image" style="border-bottom: 1px solid #111;" src="" data-src="${srRoot}/showPoster/?show=${loading_show_id}&amp;which=poster_thumb" />
                    </div>
                    <div class="progressbar hidden-print" style="position:relative;" data-show-id="${loading_show_id}" data-progress-percentage="0"></div>
                    <div class="show-title">${_('Loading')} (${loading_show_name})</div>
                    <div class="show-date">&nbsp;</div>
                    <div class="show-details">
                        <table class="show-details" width="100%" cellspacing="1" border="0" cellpadding="0">
                            <tr>
                                <td class="show-table">
                                    <span class="show-dlstats" title="${'Loading'}">${'Loading'}</span>
                                </td>
                                <td class="show-table">
                                    <span title="${loading_show_network}"><img class="show-network-image" src="" data-src="${srRoot}/showPoster/?show=${loading_show_id}&amp;which=network" alt="${loading_show_network}" title="${loading_show_network}" /></span>
                                </td>
                                <td class="show-table">
                                    ${renderQualityPill(loading_show_quality, showTitle=True, overrideClass="show-quality")}
                                </td>
                            </tr>
                        </table>
                    </div>
                </div>
            % endfor

            <% myShowList.sort(lambda x, y: x.sort_name < y.sort_name) %>
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
                        if display_status != 'Ended' and curShow.paused:
                            data_date = '5000000500.0'
                        elif display_status == 'Continuing':
                            data_date = '5000000000.0'
                        elif display_status == 'Ended':
                            data_date = '5000000100.0'
                %>
                <div class="show-container" id="show${curShow.indexerid}" data-name="${curShow.sort_name}" data-date="${data_date}" data-network="${curShow.network}" data-progress="${progressbar_percent}">
                    <div class="show-image">
                        <a href="${srRoot}/home/displayShow?show=${curShow.indexerid}"><img alt="" class="show-image" src="" data-src="${srRoot}/showPoster/?show=${curShow.indexerid}&amp;which=poster_thumb" /></a>
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
                                if display_status != 'Ended' and curShow.paused:
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
                                    % if curShow.network:
                                        <span title="${curShow.network}"><img class="show-network-image" src="" data-src="${srRoot}/showPoster/?show=${curShow.indexerid}&amp;which=network" alt="${curShow.network}" title="${curShow.network}" /></span>
                                    % else:
                                        <span title="${_('No Network')}"><img class="show-network-image" src="" data-src="${srRoot}/images/network/nonetwork.png" alt="No Network" title="No Network" /></span>
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
            <tbody>
                % if sickbeard.showQueueScheduler.action.loadingShowList:
                    % for curLoadingShow in sickbeard.showQueueScheduler.action.loadingShowList:
                        <%
                            if curLoadingShow.show in sickbeard.showList:
                                continue

                            if curLoadingShow.show:
                                loading_show_name = curLoadingShow.show.name
                                loading_show_id = curLoadingShow.show.indexerid
                            else:
                                loading_show_name = curLoadingShow.show_name.rsplit(os.sep)[-1]
                                loading_show_id = urllib.parse.quote_plus(curLoadingShow.show_name)
                        %>
                        <tr>
                            <td align="center">(${_('loading')})</td><td align="center"></td>
                            % if sickbeard.HOME_LAYOUT == 'small':
                                <td class="tvShow">
                                    <div class="imgsmallposter ${sickbeard.HOME_LAYOUT}">
                                        % if curLoadingShow.show:
                                            <a href="${srRoot}/home/displayShow?show=${loading_show_id}" title="${loading_show_name}">
                                        % else:
                                            <span title="${loading_show_name}">
                                        % endif
                                        <img src="" data-src="${srRoot}/showPoster/?show=${loading_show_id}&amp;which=poster_thumb" class="${sickbeard.HOME_LAYOUT}" alt="${loading_show_id}"/>
                                        % if curLoadingShow.show:
                                            </a>
                                            <a href="${srRoot}/home/displayShow?show=${loading_show_id}" style="vertical-align: middle;">${loading_show_name}</a>
                                        % else:
                                            </span>
                                            <span style="vertical-align: middle;">${_('Loading...')} (${loading_show_name})</span>
                                        % endif
                                    </div>
                                </td>
                            % elif sickbeard.HOME_LAYOUT == 'banner':
                                <td>
                                    <span style="display: none;">${_('Loading...')} (${loading_show_name})</span>
                                    <div class="imgbanner ${sickbeard.HOME_LAYOUT}">
                                        % if curLoadingShow.show:
                                            <a href="${srRoot}/home/displayShow?show=${loading_show_id}">
                                        % endif
                                        <img src="" data-src="${srRoot}/showPoster/?show=${loading_show_id}&amp;which=banner" class="${sickbeard.HOME_LAYOUT}" alt="${loading_show_id}" title="${loading_show_name}"/>
                                        % if curLoadingShow.show:
                                            </a>
                                        % endif
                                    </div>
                                </td>
                            % elif sickbeard.HOME_LAYOUT == 'simple':
                                <td class="tvShow">
                                    % if curLoadingShow.show:
                                        <a href="${srRoot}/home/displayShow?show=${loading_show_id}">${loading_show_name}</a>
                                    % else:
                                        <span title="">${_('Loading...')} (${loading_show_name})</span>
                                    % endif
                                </td>
                            % endif
                            <td></td>
                            <td></td>
                            <td></td>
                            <td></td>
                            <td></td>
                            <td></td>
                        </tr>
                    % endfor
                % endif

                <% myShowList.sort(lambda x, y: x.sort_name < y.sort_name) %>
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
                                        <img src="" data-src="${srRoot}/showPoster/?show=${curShow.indexerid}&amp;which=poster_thumb" class="${sickbeard.HOME_LAYOUT}" alt="${curShow.indexerid}"/>
                                    </a>
                                    <a href="${srRoot}/home/displayShow?show=${curShow.indexerid}" style="vertical-align: middle;">${curShow.name}</a>
                                </div>
                            </td>
                        % elif sickbeard.HOME_LAYOUT == 'banner':
                            <td>
                                <span style="display: none;">${curShow.name}</span>
                                <div class="imgbanner ${sickbeard.HOME_LAYOUT}">
                                    <a href="${srRoot}/home/displayShow?show=${curShow.indexerid}">
                                        <img src="" data-src="${srRoot}/showPoster/?show=${curShow.indexerid}&amp;which=banner" class="${sickbeard.HOME_LAYOUT}" alt="${curShow.indexerid}" title="${curShow.name}"/>
                                    </a>
                                </div>
                            </td>
                        % elif sickbeard.HOME_LAYOUT == 'simple':
                            <td class="tvShow"><a href="${srRoot}/home/displayShow?show=${curShow.indexerid}">${curShow.name}</a></td>
                        % endif

                        % if sickbeard.HOME_LAYOUT != 'simple':
                            <td align="center">
                                % if curShow.network:
                                    <span title="${curShow.network}" class="hidden-print"><img id="network" width="54" height="27" src="" data-src="${srRoot}/showPoster/?show=${curShow.indexerid}&amp;which=network" alt="${curShow.network}" title="${curShow.network}" /></span>
                                    <span class="visible-print-inline">${curShow.network}</span>
                                % else:
                                    <span title="No Network" class="hidden-print"><img id="network" width="54" height="27" src="" data-src="${srRoot}/images/network/nonetwork.png" alt="No Network" title="No Network" /></span>
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
                            <span class="displayshow-icon-${("disable", "enable")[not bool(curShow.paused)]}" title="${('No', 'Yes')[not bool(curShow.paused)]}"></span>
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
