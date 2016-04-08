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
    backLogShows = sorted([x for x in sickbeard.showList if showCounts[x.indexerid][Overview.QUAL] + showCounts[x.indexerid][Overview.WANTED] + (0, showCounts[x.indexerid][Overview.SNATCHED])[len(showQualSnatched(x)) > 0]], key=lambda x: x.name)
    for curShow in backLogShows:
        totalWanted += showCounts[curShow.indexerid][Overview.WANTED]
        totalQual += showCounts[curShow.indexerid][Overview.QUAL]
        if showQualSnatched(curShow):
            totalQualSnatched += showCounts[x.indexerid][Overview.SNATCHED]
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
    % for curShow in backLogShows:
        <option value="${curShow.indexerid}">${curShow.name}</option>
    % endfor
    </select>
</div>

<table class="sickbeardTable" cellspacing="0" border="0" cellpadding="0">
% for curShow in backLogShows:
    % if not showQualSnatched(curShow) and not showCounts[curShow.indexerid][Overview.WANTED] + showCounts[curShow.indexerid][Overview.QUAL]:
        <% continue %>
    % endif
    <tr class="seasonheader" id="show-${curShow.indexerid}">
        <td colspan="3" class="align-left" style="position: relative;">
            <h2 style="display: inline-block;"><a href="${srRoot}/home/displayShow?show=${curShow.indexerid}">${curShow.name}</a></h2>
            <div style="position: absolute; bottom: 10px; right: 0;">
                % if showCounts[curShow.indexerid][Overview.WANTED] > 0:
                <span class="listing-key wanted">${_('Wanted')}: <b>${showCounts[curShow.indexerid][Overview.WANTED]}</b></span>
                % endif

                % if showQualSnatched(curShow) and showCounts[curShow.indexerid][Overview.SNATCHED] > 0:
                    <span class="listing-key snatched">${_('Snatched (Allowed)')}: <b>${showCounts[curShow.indexerid][Overview.SNATCHED]}</b></span>
                % endif

                % if showCounts[curShow.indexerid][Overview.QUAL] > 0:
                <span class="listing-key qual">${_('Allowed')}: <b>${showCounts[curShow.indexerid][Overview.QUAL]}</b></span>
                % endif

                <a class="btn btn-inline forceBacklog" href="${srRoot}/manage/backlogShow?indexer_id=${curShow.indexerid}"><i class="icon-play-circle icon-white"></i> ${_('Force Backlog')}</a>
            </div>
        </td>
    </tr>

    <tr class="seasoncols"><th>${_('Episode')}</th><th>${_('Name')}</th><th class="nowrap">${_('Airdate')}</th></tr>

    % for curResult in showSQLResults[curShow.indexerid]:
        <%
            whichStr = episode_num(curResult['season'], curResult['episode']) or episode_num(curResult['season'], curResult['episode'], numbering='absolute')
            if whichStr not in showCats[curShow.indexerid] or showCats[curShow.indexerid][whichStr] not in (Overview.QUAL, Overview.WANTED, Overview.SNATCHED):
                continue

            if not showQualSnatched(curShow) and showCats[curShow.indexerid][whichStr] == Overview.SNATCHED:
                continue
        %>
        <tr class="seasonstyle ${Overview.overviewStrings[showCats[curShow.indexerid][whichStr]]}">
            <td class="tableleft" align="center">${whichStr}</td>
            <td class="tableright" align="center" class="nowrap">
                ${curResult["name"]}
            </td>
            <td>
                <% epResult = curResult %>
                <% show = curShow %>
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
