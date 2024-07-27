<%inherit file="/layouts/main.mako" />
<%!
    import datetime
    from sickchill import settings
    from sickchill.oldbeard import scdatetime, network_timezones
    from sickchill.oldbeard.common import WANTED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, Overview, Quality
    from sickchill.helper.common import episode_num
%>
<%block name="content">
    <div class="row">
        <div class="col-lg-8 col-md-7 col-sm-6 col-xs-12 pull-right">
            <div class="pull-right">
                % if total_wanted > 0:
                    <span class="listing-key wanted">${_('Wanted')}: <b>${total_wanted}</b></span>
                % endif

                % if total_qual_snatched > 0:
                    <span class="listing-key snatched">${_('Snatched (Allowed)')}: <b>${total_qual_snatched}</b></span>
                % endif

                % if total_qual > 0:
                    <span class="listing-key qual">${_('Allowed')}: <b>${total_qual}</b></span>
                % endif
            </div>
        </div>
        <div class="col-lg-4 col-md-5 col-sm-6 col-xs-12">
            % if not header is UNDEFINED:
                <h1 class="header">${header}</h1>
            % else:
                <h1 class="title">${title}</h1>
            % endif
        </div>
    </div>
    <div class="row">
        <div class="col-md-12">
            <label for="pickShow">${_('Jump to Show')}:</label>
            <select id="pickShow" class="form-control form-control-inline input-sm">
                % for cur_show in backlog_shows:
                    <option value="${cur_show.indexerid}">${cur_show.name}</option>
                % endfor
            </select>
        </div>
    </div>

    % for cur_show in backlog_shows:
        % if not show_qual_snatched(cur_show) and not show_counts[cur_show.indexerid][Overview.WANTED] + show_counts[cur_show.indexerid][Overview.QUAL]:
            <% continue %>
        % endif

        <div class="row">
            <div class="col-md-12">
                <div class="pull-right" style="margin-top: 30px;">
                    % if show_counts[cur_show.indexerid][Overview.WANTED] > 0:
                        <span class="listing-key wanted">${_('Wanted')}: <b>${show_counts[cur_show.indexerid][Overview.WANTED]}</b></span>
                    % endif

                    % if show_qual_snatched(cur_show) and show_counts[cur_show.indexerid][Overview.SNATCHED] > 0:
                        <span class="listing-key snatched">${_('Snatched (Allowed)')}: <b>${show_counts[cur_show.indexerid][Overview.SNATCHED]}</b></span>
                    % endif

                    % if show_counts[cur_show.indexerid][Overview.QUAL] > 0:
                        <span class="listing-key qual">${_('Allowed')}: <b>${show_counts[cur_show.indexerid][Overview.QUAL]}</b></span>
                    % endif

                    <a class="btn btn-inline forceBacklog" href="${scRoot}/manage/backlogShow?indexer_id=${cur_show.indexerid}"><i class="icon-play-circle icon-white"></i> ${_('Force Backlog')}</a>
                </div>

                <h2 style="display: inline-block;">
                    <a href="${scRoot}/home/displayShow?show=${cur_show.indexerid}">${cur_show.name}</a>
                </h2>
            </div>
        </div>
        <div class="row">
            <div class="col-md-12">
                <div class="horizontal-scroll">
                    <table class="sickchillTable">
                        <tr class="seasonheader" id="show-${cur_show.indexerid}">
                            <td colspan="3" class="align-left" style="position: relative;"></td>
                        </tr>
                        <tr class="seasoncols"><th>${_('Episode')}</th><th>${_('Name')}</th><th class="nowrap">${_('Airdate')}</th></tr>

                        % for cur_result in show_sql_results[cur_show.indexerid]:
                        <%
                            which_str = episode_num(cur_result['season'], cur_result['episode']) or episode_num(cur_result['season'], cur_result['episode'], numbering='absolute')
                            if which_str not in show_categories[cur_show.indexerid] or show_categories[cur_show.indexerid][which_str] not in (Overview.QUAL, Overview.WANTED, Overview.SNATCHED):
                                continue

                            if not show_qual_snatched(cur_show) and show_categories[cur_show.indexerid][which_str] == Overview.SNATCHED:
                                continue
                        %>
                            <tr class="seasonstyle ${Overview.overviewStrings[show_categories[cur_show.indexerid][which_str]]}">
                                <td class="tableleft text-center">${which_str}</td>
                                <td class="tableright text-center nowrap">
                                    ${cur_result["name"]}
                                </td>
                                <td>
                                % try:
                                    % if int(cur_result['airdate']) > 1:
                                        <% air_date = datetime.datetime.fromordinal(cur_result['airdate']) %>
                                        % if air_date > datetime.datetime.utcfromtimestamp(0) and cur_show.network:
                                            <% air_date = scdatetime.scdatetime.convert_to_setting(network_timezones.parse_date_time(cur_result['airdate'], cur_show.airs, cur_show.network)) %>
                                        % endif
                                        <time datetime="${air_date.isoformat('T')}" class="date">${scdatetime.scdatetime.scfdatetime(air_date)}</time>
                                    % else:
                                        Never
                                    % endif
                                % except:
                                    Unknown
                                % endtry
                                </td>
                            </tr>
                        % endfor
                    </table>
                </div>
            </div>
        </div>
    % endfor
</%block>
