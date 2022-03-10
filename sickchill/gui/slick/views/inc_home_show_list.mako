<%!
    from sickchill import settings
    import calendar
    from sickchill.oldbeard import sbdatetime, network_timezones
    from sickchill.helper.common import pretty_file_size
    import os
    import re

    ## Need to initialize these for gettext, they are done dynamically in the ui
    _('Continuing')
    _('Ended')
%>
<%page args="curListType, myShowList"/>
<%namespace file="/inc_defs.mako" import="renderQualityPill"/>

% if settings.HOME_LAYOUT == 'poster':
    <%include file="/inc_home_show_list_poster.mako" args="curListType=curListType, myShowList=myShowList"/>
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
                    <th rowspan="1" colspan="1" align="center"><a href="${static_url("addShows/", include_version=False)}">${_('Add')} ${(_('Show'), _('Anime'))[curListType == 'Anime']}</a></th>
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
                % for curLoadingShow in settings.showQueueScheduler.action.loading_show_list:
                    <% loading_show = curLoadingShow.info %>
                    <tr>
                        <td align="center">(${_('loading')})</td>
                        <td align="center"></td>
                        % if settings.HOME_LAYOUT == 'small':
                            <td class="tvShow">
                                <div class="imgsmallposter ${settings.HOME_LAYOUT}">
                                    % if curLoadingShow.show:
                                        <a href="${scRoot}/home/displayShow?show=${loading_show.id}" title="${loading_show.name}">
                                            <img src="${static_url("images/poster.png")}" data-src="${static_url(loading_show.show_image_url('poster_thumb'))}"
                                                 class="${settings.HOME_LAYOUT}" alt="${loading_show.name}"/>
                                        </a>
                                        <a href="${scRoot}/home/displayShow?show=${loading_show.id}" style="vertical-align: middle;">${loading_show.name}</a>
                                    % else:
                                        <span title="${loading_show.name}">
                                        <img src="${static_url("images/poster.png")}" data-src="${static_url(loading_show.show_image_url('poster_thumb'))}"
                                             class="${settings.HOME_LAYOUT}" alt="${loading_show.name}"/>
                                        </span>
                                        <span style="vertical-align: middle;">${_('Loading...')} (${loading_show.name})</span>
                                    % endif
                                </div>
                            </td>
                        % elif settings.HOME_LAYOUT == 'banner':
                            <td>
                                <span style="display: none;">${_('Loading...')} (${loading_show.name})</span>
                                <div class="imgbanner ${settings.HOME_LAYOUT}">
                                    % if curLoadingShow.show:
                                        <a href="${scRoot}/home/displayShow?show=${loading_show.id}">
                                    % endif
                                    <img src="${static_url("images/banner.png")}" data-src="${static_url(loading_show.show_image_url('banner'))}"
                                         class="${settings.HOME_LAYOUT}" alt="${loading_show.name}" title="${loading_show.name}"/>
                                    % if curLoadingShow.show:
                                        </a>
                                    % endif
                                </div>
                            </td>
                        % elif settings.HOME_LAYOUT == 'simple':
                            <td class="tvShow">
                                % if curLoadingShow.show:
                                    <a href="${scRoot}/home/displayShow?show=${loading_show.id}">${loading_show.name}</a>
                                % else:
                                    <span title="">${_('Loading...')} (${loading_show.name})</span>
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
                % for curShow in myShowList:
                    <%
                        if settings.showQueueScheduler.action.is_in_remove_queue(curShow) or settings.showQueueScheduler.action.is_being_removed(curShow):
                            continue

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
                            progressbar_percent = nom * 100 / float(cur_total)
                        else:
                            progressbar_percent = 100.0
                            download_stat_tip = _('Unaired')
                    %>
                    <tr>
                        % if cur_airs_next:
                            <% airDate = sbdatetime.sbdatetime.convert_to_setting(network_timezones.parse_date_time(cur_airs_next, curShow.airs, curShow.network)) %>
                            % try:
                                <td align="center" class="nowrap">
                                    <time datetime="${airDate.isoformat('T')}" class="date">${sbdatetime.sbdatetime.sbfdate(airDate)}</time>
                                </td>
                            % except (ValueError, OSError):
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
                            % except (ValueError, OSError):
                                <td align="center" class="nowrap"></td>
                            % endtry
                        % else:
                            <td align="center" class="nowrap"></td>
                        % endif

                        % if settings.HOME_LAYOUT == 'small':
                            <td class="tvShow">
                                <div class="imgsmallposter ${settings.HOME_LAYOUT}">
                                    <a href="${scRoot}/home/displayShow?show=${curShow.indexerid}" title="${curShow.name}">
                                        <img src="${static_url("images/poster.png")}" data-src="${static_url(curShow.show_image_url('poster_thumb'))}"
                                             class="${settings.HOME_LAYOUT}" alt="${curShow.indexerid}"/>
                                    </a>
                                    <a href="${scRoot}/home/displayShow?show=${curShow.indexerid}" style="vertical-align: middle;">${curShow.name}</a>
                                </div>
                            </td>
                        % elif settings.HOME_LAYOUT == 'banner':
                            <td>
                                <span style="display: none;">${curShow.name}</span>
                                <div class="imgbanner ${settings.HOME_LAYOUT}">
                                    <a href="${scRoot}/home/displayShow?show=${curShow.indexerid}">
                                        <img src="${static_url("images/banner.png")}" data-src="${static_url(curShow.show_image_url('banner'))}"
                                             class="${settings.HOME_LAYOUT}" alt="${curShow.indexerid}" title="${curShow.name}"/>
                                    </a>
                                </div>
                            </td>
                        % elif settings.HOME_LAYOUT == 'simple':
                            <td class="tvShow"><a href="${scRoot}/home/displayShow?show=${curShow.indexerid}">${curShow.name}</a></td>
                        % endif

                        % if settings.HOME_LAYOUT != 'simple':
                            <td align="center">
                                % if curShow.network:
                                    <span title="${curShow.network}" class="hidden-print">
                                        <img id="network" width="54" height="27" src="${static_url('images/network/nonetwork.png')}"
                                             data-src="${static_url(curShow.network_image_url)}"
                                             alt="${curShow.network}" title="${curShow.network}" />
                                    </span>
                                    <span class="visible-print-inline">${curShow.network}</span>
                                % else:
                                    <span title="No Network" class="hidden-print">
                                        <img id="network" width="54" height="27" src="${static_url('images/network/nonetwork.png')}"
                                             data-src="${static_url('images/network/nonetwork.png')}" alt="No Network" title="No Network" />
                                    </span>
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
                            <div class="progressbar hidden-print" style="position:relative;" data-show-id="${curShow.indexerid}"
                                 data-progress-text="${download_stat}"
                                 data-progress-tip="${download_stat_tip}"
                                 data-progress-percentage="${int(progressbar_percent)}"
                                 data-progress-total="${cur_total}"
                            ></div>
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
