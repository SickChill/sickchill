<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    import datetime
    from sickbeard.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickbeard.common import Overview, Quality, qualityPresets, qualityPresetStrings
    from sickbeard import sbdatetime, network_timezones
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

<% totalWanted = 0 %>
<% totalQual = 0 %>

% for curShow in sickbeard.showList:
    <% totalWanted = totalWanted + showCounts[curShow.indexerid][Overview.WANTED] %>
    <% totalQual = totalQual + showCounts[curShow.indexerid][Overview.QUAL] %>
% endfor

<div class="h2footer pull-right">
    <span class="listing-key wanted">Wanted: <b>${totalWanted}</b></span>
    <span class="listing-key qual">Low Quality: <b>${totalQual}</b></span>
</div><br>

<div class="float-left">
Jump to Show
    <select id="pickShow" class="form-control form-control-inline input-sm">
    % for curShow in sorted(sickbeard.showList, key=lambda x: x.name):
        % if showCounts[curShow.indexerid][Overview.QUAL] + showCounts[curShow.indexerid][Overview.WANTED] != 0:
        <option value="${curShow.indexerid}">${curShow.name}</option>
        % endif
    % endfor
    </select>
</div>

<table class="sickbeardTable" cellspacing="0" border="0" cellpadding="0">
% for curShow in sorted(sickbeard.showList, key=lambda x: x.name):

    % if showCounts[curShow.indexerid][Overview.QUAL] + showCounts[curShow.indexerid][Overview.WANTED] == 0:
        <% continue %>
    % endif
    <tr class="seasonheader" id="show-${curShow.indexerid}">
        <td colspan="3" class="align-left">
            <br><h2><a href="${srRoot}/home/displayShow?show=${curShow.indexerid}">${curShow.name}</a></h2>
            <div class="pull-right">
                <span class="listing-key wanted">Wanted: <b>${showCounts[curShow.indexerid][Overview.WANTED]}</b></span>
                <span class="listing-key qual">Low Quality: <b>${showCounts[curShow.indexerid][Overview.QUAL]}</b></span>
                <a class="btn btn-inline forceBacklog" href="${srRoot}/manage/backlogShow?indexer_id=${curShow.indexerid}"><i class="icon-play-circle icon-white"></i> Force Backlog</a>
            </div>
        </td>
    </tr>

    <tr class="seasoncols"><th>Episode</th><th>Name</th><th class="nowrap">Airdate</th></tr>

    % for curResult in showSQLResults[curShow.indexerid]:
        <% whichStr = str(curResult['season']) + 'x' + str(curResult['episode']) %>
        % try:
            <% overview = showCats[curShow.indexerid][whichStr] %>
        % except Exception:
            <% continue %>
        % endtry

        % if overview not in (Overview.QUAL, Overview.WANTED):
            <% continue %>
        % endif

        <tr class="seasonstyle ${Overview.overviewStrings[showCats[curShow.indexerid][whichStr]]}">
            <td class="tableleft" align="center">${whichStr}</td>
            <td class="tableright" align="center" class="nowrap">
                ${curResult["name"]}
            </td>
            <td>
            <% airDate = sbdatetime.sbdatetime.convert_to_setting(network_timezones.parse_date_time(curResult['airdate'], curShow.airs, curShow.network)) %>
            % if int(curResult['airdate']) != 1:
                <time datetime="${airDate.isoformat('T')}" class="date">${sbdatetime.sbdatetime.sbfdatetime(airDate)}</time>
            % else:
                Never
            % endif
            </td>
        </tr>
    % endfor
% endfor

</table>
</div>
</%block>
