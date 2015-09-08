<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    import calendar
    from sickbeard.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickbeard.common import Quality, qualityPresets, qualityPresetStrings
    from sickbeard import db, sbdatetime, network_timezones
    import datetime
    import re
%>
<%block name="scripts">
<script type="text/javascript" src="${sbRoot}/js/testRename.js"></script>
</%block>
<%block name="content">
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif

<input type="hidden" id="showID" value="${show.indexerid}" />

<h3>Preview of the proposed name changes</h3>
<blockquote>
% if int(show.air_by_date) == 1 and sickbeard.NAMING_CUSTOM_ABD:
    ${sickbeard.NAMING_ABD_PATTERN}
% elif int(show.sports) == 1 and sickbeard.NAMING_CUSTOM_SPORTS:
    ${sickbeard.NAMING_SPORTS_PATTERN}
% else:
    ${sickbeard.NAMING_PATTERN}
% endif
</blockquote>

<% curSeason = -1 %>
<% odd = False%>

<table id="SelectAllTable" class="sickbeardTable" cellspacing="1" border="0" cellpadding="0">
    <thead>
        <tr class="seasonheader" id="season-all">
            <td colspan="4">
                <h2>All Seasons</h2>
            </td>
        </tr>
        <tr class="seasoncols" id="selectall">
            <th class="col-checkbox"><input type="checkbox" class="seriesCheck" id="SelectAll" /></th>
            <th align="left" valign="top" class="nowrap">Select All</th>
            <th width="100%" class="col-name" style="visibility:hidden;"></th>
        </tr>
    </thead>
</table>

<br/>
<input type="submit" value="Rename Selected" class="btn btn-success"> <a href="/home/displayShow?show=${show.indexerid}" class="btn btn-danger">Cancel Rename</a>

<table id="testRenameTable" class="sickbeardTable" cellspacing="1" border="0" cellpadding="0">

% for cur_ep_obj in ep_obj_list:
<%
    curLoc = cur_ep_obj.location[len(cur_ep_obj.show.location)+1:]
    curExt = curLoc.split('.')[-1]
    newLoc = cur_ep_obj.proper_path() + '.' + curExt
%>
% if int(cur_ep_obj.season) != curSeason:
    <thead>
        <tr class="seasonheader" id="season-${cur_ep_obj.season}">
            <td colspan="4">
                 <br/>
                <h2>${('Season '+str(cur_ep_obj.season), 'Specials')[int(cur_ep_obj.season) == 0]}</h2>
            </td>
        </tr>
        <tr class="seasoncols" id="season-${cur_ep_obj.season}-cols">
            <th class="col-checkbox"><input type="checkbox" class="seasonCheck" id="${cur_ep_obj.season}" /></th>
            <th class="nowrap">Episode</th>
            <th class="col-name">Old Location</th>
            <th class="col-name">New Location</th>
        </tr>
    </thead>
<% curSeason = int(cur_ep_obj.season) %>
% endif
    <tbody>
<%
odd = not odd
epStr = str(cur_ep_obj.season) + "x" + str(cur_ep_obj.episode)
epList = sorted([cur_ep_obj.episode] + [x.episode for x in cur_ep_obj.relatedEps])
if len(epList) > 1:
    epList = [min(epList), max(epList)]
%>
        <tr class="season-${curSeason} ${('wanted', 'good')[curLoc == newLoc]} seasonstyle">
            <td class="col-checkbox">
            % if curLoc != newLoc:
                <input type="checkbox" class="epCheck" id="${str(cur_ep_obj.season) + 'x' + str(cur_ep_obj.episode)}" name="${str(cur_ep_obj.season) + "x" + str(cur_ep_obj.episode)}" />
            % endif
            </td>
            <td align="center" valign="top" class="nowrap">${"-".join(map(str, epList))}</td>
            <td width="50%" class="col-name">${curLoc}</td>
            <td width="50%" class="col-name">${newLoc}</td>
        </tr>
    </tbody>

% endfor
</table><br />
<input type="submit" value="Rename Selected" class="btn btn-success"> <a href="/home/displayShow?show=${show.indexerid}" class="btn btn-danger">Cancel Rename</a>
</%block>
