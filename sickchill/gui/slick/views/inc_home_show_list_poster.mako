<%!
    from sickchill import settings
    import calendar
    from sickchill.oldbeard import sbdatetime, network_timezones
    from sickchill.helper.common import pretty_file_size
    import os
    import re
%>
<%page args="curListType, myShowList"/>
<%namespace file="/inc_defs.mako" import="renderQualityPill"/>

<div id="${('container', 'container-anime')[curListType == 'Anime']}" class="show-grid clearfix">
    <div class="posterview">
        % for curLoadingShow in settings.showQueueScheduler.action.loading_show_list:
            <% loading_show = curLoadingShow.info %>
            <div class="show-container" data-name="${loading_show.sort_name}"
                 data-date="1" data-network="0" data-progress="0" data-progress-total="0" data-status="Loading">
                <div class="show-image">
                    <img alt="" title="${loading_show.name}" class="show-image" style="border-bottom: 1px solid #111;" src="${static_url("images/poster.png")}"
                         data-src="${static_url(loading_show.show_image_url('poster_thumb'))}" />
                </div>
                <div class="show-information">
                    <div class="progressbar hidden-print" style="position:relative;" data-show-id="${loading_show.id}" data-progress-percentage="0"></div>
                    <div class="show-title">${_('Loading')} (${loading_show.name})</div>
                    <div class="show-date">&nbsp;</div>
                    <div class="show-details">
                        <table class="show-details" width="100%" cellspacing="1" border="0" cellpadding="0">
                            <tr>
                                <td class="show-table">
                                    <span class="show-dlstats" title="${'Loading'}">${'Loading'}</span>
                                </td>
                                <td class="show-table">
                                    <span title="${loading_show.network}">
                                        <img class="show-network-image" src="${static_url("images/network/nonetwork.png")}"
                                             data-src="${static_url(loading_show.network_image_url)}"
                                             alt="${loading_show.network}" title="${loading_show.network}" />
                                    </span>
                                </td>
                                <td class="show-table">
                                    ${renderQualityPill(loading_show.quality, showTitle=True, overrideClass="show-quality")}
                                </td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
        % endfor
        % for curShow in myShowList:
            <%
                if settings.showQueueScheduler.action.is_in_remove_queue(curShow) or settings.showQueueScheduler.action.is_being_removed(curShow):
                    continue

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

                if curShow.paused:
                    display_status = _(display_status) + ' ' + _('Paused')

                cur_airs_next = None
                cur_airs_prev = None
                if curShow.indexerid in show_stat:
                    cur_airs_next = show_stat[curShow.indexerid]['ep_airs_next']
                    cur_airs_prev = show_stat[curShow.indexerid]['ep_airs_prev']

                    cur_snatched = show_stat[curShow.indexerid]['ep_snatched'] or 0
                    cur_downloaded = show_stat[curShow.indexerid]['ep_downloaded'] or 0
                    cur_total = show_stat[curShow.indexerid]['ep_total'] or 0

                download_stat = str(cur_downloaded)
                download_stat_tip = _('Downloaded') + ": " + str(cur_downloaded)

                if cur_snatched:
                    download_stat += "+" + str(cur_snatched)
                    download_stat_tip += "&#013;" + _('Snatched') + ": " + str(cur_snatched)

                download_stat += " / " + str(cur_total)
                download_stat_tip += "&#013;" + _('Total') + ": " + str(cur_total)

                nom = cur_downloaded
                if cur_total:
                    progressbar_percent = nom * 100 / float(cur_total)
                else:
                    progressbar_percent = 100.0
                    download_stat_tip = _('Unaired')

                if cur_airs_next:
                    data_date = calendar.timegm(sbdatetime.sbdatetime.convert_to_setting(network_timezones.parse_date_time(cur_airs_next, curShow.airs, curShow.network)).timetuple())
##                 elif cur_airs_prev:
##                     data_date = calendar.timegm(sbdatetime.sbdatetime.convert_to_setting(network_timezones.parse_date_time(cur_airs_prev, curShow.airs, curShow.network)).timetuple())
                elif display_status:
                    if display_status.startswith('Continuing'):
                        data_date = '5000000000.0'
                    elif display_status.startswith('Upcoming'):
                        data_date = '5000000050.0'
                    elif display_status.startswith('Ended'):
                        data_date = '5000000100.0'
                    elif curShow.paused:
                        data_date = '5000000500.0'
                else:
                    data_date = '6000000000.0'
            %>
            <div class="show-container" id="show${curShow.indexerid}" data-name="${curShow.sort_name}" data-date="${data_date}" data-network="${curShow.network}"
                 data-progress="${int(progressbar_percent)}" data-progress-total="${cur_total}" data-status="${curShow.status}">
                <div class="show-image">
                    <a href="${scRoot}/home/displayShow?show=${curShow.indexerid}">
                        <img alt="" class="show-image" src="${static_url("images/poster.png")}" data-src="${static_url(curShow.show_image_url('poster_thumb'))}" />
                    </a>
                </div>

                <div class="show-information">
                    <div class="progressbar hidden-print" style="position:relative;" data-show-id="${curShow.indexerid}"
                         data-progress-percentage="${int(progressbar_percent)}" data-progress-total="${cur_total}"></div>

                    <div class="show-title">
                        ${curShow.name}
                    </div>

                    <div class="show-date">
                        % if cur_airs_next or cur_airs_prev:
                        <%
                            ldatetime = sbdatetime.sbdatetime.convert_to_setting(network_timezones.parse_date_time(cur_airs_next or cur_airs_prev, curShow.airs, curShow.network))
                            try:
                                out = str(sbdatetime.sbdatetime.sbfdate(ldatetime))
                            except (ValueError, OSError):
                                out = _('Invalid date')
                                pass
                        %>
                        ${_(display_status)} ${out}
                        % else:
                            ${_(display_status)}
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
                                        <span title="${curShow.network}">
                                            <img class="show-network-image" src="${static_url('images/network/nonetwork.png')}"
                                                 data-src="${static_url(curShow.network_image_url)}" alt="${curShow.network}" title="${curShow.network}" />
                                        </span>
                                    % else:
                                        <span title="${_('No Network')}"><img class="show-network-image" src="${static_url('images/network/nonetwork.png')}" data-src="${static_url('images/network/nonetwork.png')}" alt="No Network" title="No Network" /></span>
                                    % endif
                                </td>
                                <td class="show-table">
                                    ${renderQualityPill(curShow.quality, showTitle=True, overrideClass="show-quality")}
                                </td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
        % endfor
    </div>
</div>
