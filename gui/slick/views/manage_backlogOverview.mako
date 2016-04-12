<%inherit file="/layouts/main.mako"/>
<%!
    import datetime
    import sickbeard
    from sickbeard import sbdatetime, network_timezones
    from sickbeard.common import WANTED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, Overview, Quality
    from sickrage.helper.common import episode_num
%>
<%block name="scripts">
<script type="text/javascript">
</script>
</%block>
<%block name="content">
<div id="content960">

% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif

<%
    showQualSnatched = lambda x: Quality.splitQuality(x.quality)[1]

    totalWanted = totalQual = totalQualSnatched = 0
    backLogShows = sorted([x for x in sickbeard.show_list if show_counts[x.indexerid][Overview.QUAL] + show_counts[x.indexerid][Overview.WANTED] + (0, show_counts[x.indexerid][Overview.SNATCHED])[len(showQualSnatched(x)) > 0]], key=lambda x: x.name)
    for cur_show in backLogShows:
        totalWanted += show_counts[cur_show.indexerid][Overview.WANTED]
        totalQual += show_counts[cur_show.indexerid][Overview.QUAL]
        if showQualSnatched(cur_show):
            totalQualSnatched += show_counts[x.indexerid][Overview.SNATCHED]
%>

<div class="h2footer pull-right">
    % if totalWanted > 0:
    <span class="listing-key wanted">${_('Wanted')}: <b>${totalWanted}</b></span>
    % endif

    % if totalQualSnatched > 0:
    <span class="listing-key snatched">${_('Snatched (Allowed)')}: <b>${totalQualSnatched}</b></span>
    % endif

    % if totalQual > 0:
    <span class="listing-key qual">${_('Allowed')}: <b>${totalQual}</b></span>
    % endif
</div><br>

<div class="float-left">
Jump to Show:
    <select id="pickShow" class="form-control form-control-inline input-sm">
    % for cur_show in backLogShows:
        <option value="${cur_show.indexerid}">${cur_show.name}</option>
    % endfor
    </select>
</div>

<table class="sickbeardTable" cellspacing="0" border="0" cellpadding="0">
% for cur_show in backLogShows:
    % if not showQualSnatched(cur_show) and not show_counts[cur_show.indexerid][Overview.WANTED] + show_counts[cur_show.indexerid][Overview.QUAL]:
        <% continue %>
    % endif
    <tr class="seasonheader" id="show-${cur_show.indexerid}">
        <td colspan="3" class="align-left" style="position: relative;">
            <h2 style="display: inline-block;"><a href="${srRoot}/home/displayShow?show=${cur_show.indexerid}">${cur_show.name}</a></h2>
            <div style="position: absolute; bottom: 10px; right: 0;">
                % if show_counts[cur_show.indexerid][Overview.WANTED] > 0:
                <span class="listing-key wanted">${_('Wanted')}: <b>${show_counts[cur_show.indexerid][Overview.WANTED]}</b></span>
                % endif

                % if showQualSnatched(cur_show) and show_counts[cur_show.indexerid][Overview.SNATCHED] > 0:
                    <span class="listing-key snatched">${_('Snatched (Allowed)')}: <b>${show_counts[cur_show.indexerid][Overview.SNATCHED]}</b></span>
                % endif

                % if show_counts[cur_show.indexerid][Overview.QUAL] > 0:
                <span class="listing-key qual">${_('Allowed')}: <b>${show_counts[cur_show.indexerid][Overview.QUAL]}</b></span>
                % endif

                <a class="btn btn-inline forceBacklog" href="${srRoot}/manage/backlogShow?indexer_id=${cur_show.indexerid}"><i class="icon-play-circle icon-white"></i> ${_('Force Backlog')}</a>
            </div>
        </td>
    </tr>

    <tr class="seasoncols"><th>${_('Episode')}</th><th>${_('Name')}</th><th class="nowrap">${_('Airdate')}</th></tr>

    % for cur_result in showSQLResults[cur_show.indexerid]:
        <%
            whichStr = episode_num(cur_result['season'], cur_result['episode']) or episode_num(cur_result['season'], cur_result['episode'], numbering='absolute')
            if whichStr not in showCats[cur_show.indexerid] or showCats[cur_show.indexerid][whichStr] not in (Overview.QUAL, Overview.WANTED, Overview.SNATCHED):
                continue

            if not showQualSnatched(cur_show) and showCats[cur_show.indexerid][whichStr] == Overview.SNATCHED:
                continue
        %>
        <tr class="seasonstyle ${Overview.overviewStrings[showCats[cur_show.indexerid][whichStr]]}">
            <td class="tableleft" align="center">${whichStr}</td>
            <td class="tableright" align="center" class="nowrap">
                ${cur_result["name"]}
            </td>
            <td>
                <% epResult = cur_result %>
                <% show = cur_show %>
                % if int(epResult['airdate']) != 1:
                    ## Lets do this exactly like ComingEpisodes and History
                    ## Avoid issues with dateutil's _isdst on Windows but still provide air dates
                    <% airDate = datetime.datetime.fromordinal(epResult['airdate']) %>
                    % if airDate.year >= 1970 or show.network:
                        <% airDate = sbdatetime.sbdatetime.convert_to_setting(network_timezones.parse_date_time(epResult['airdate'], show.airs, show.network)) %>
                    % endif
                    <time datetime="${airDate.isoformat('T')}" class="date">${sbdatetime.sbdatetime.sbfdatetime(airDate)}</time>
                % else:
                    Never
                % endif
            </td>
            </td>
        </tr>
    % endfor
% endfor
</table>
</div>
</%block>
