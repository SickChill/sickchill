<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    import os.path
    import datetime
    import re
    import time

    from sickbeard import providers
    from sickbeard import sbdatetime
    from sickbeard.providers import generic

    from sickbeard.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED, DOWNLOADED, SUBTITLED
    from sickbeard.common import Quality, statusStrings, Overview

    from sickrage.show.History import History
%>
<%block name="scripts">
<script type="text/javascript" src="${srRoot}/js/new/history.js"></script>
</%block>
<%block name="content">
<%namespace file="/inc_defs.mako" import="renderQualityPill"/>
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif
<div class="h2footer pull-right"><b>Limit:</b>
    <select name="history_limit" id="history_limit" class="form-control form-control-inline input-sm">
        <option value="10" ${('', 'selected="selected"')[limit == 10]}>10</option>
        <option value="25" ${('', 'selected="selected"')[limit == 25]}>25</option>
        <option value="50" ${('', 'selected="selected"')[limit == 50]}>50</option>
        <option value="100" ${('', 'selected="selected"')[limit == 100]}>100</option>
        <option value="250" ${('', 'selected="selected"')[limit == 250]}>250</option>
        <option value="500" ${('', 'selected="selected"')[limit == 500]}>500</option>
        <option value="750" ${('', 'selected="selected"')[limit == 750]}>750</option>
        <option value="1000" ${('', 'selected="selected"')[limit == 1000]}>1000</option>
        <option value="0"   ${('', 'selected="selected"')[limit == 0  ]}>All</option>
    </select>

    <span> Layout:
        <select name="HistoryLayout" class="form-control form-control-inline input-sm" onchange="location = this.options[this.selectedIndex].value;">
            <option value="${srRoot}/setHistoryLayout/?layout=compact"  ${('', 'selected="selected"')[sickbeard.HISTORY_LAYOUT == 'compact']}>Compact</option>
            <option value="${srRoot}/setHistoryLayout/?layout=detailed" ${('', 'selected="selected"')[sickbeard.HISTORY_LAYOUT == 'detailed']}>Detailed</option>
        </select>
    </span>
</div>
<br>

% if sickbeard.HISTORY_LAYOUT == "detailed":
    <table id="historyTable" class="sickbeardTable tablesorter" cellspacing="1" border="0" cellpadding="0">
        <thead>
            <tr>
                <th class="nowrap">Time</th>
                <th>Episode</th>
                <th>Action</th>
                <th>Provider</th>
                <th>Quality</th>
            </tr>
        </thead>

        <tfoot>
            <tr>
                <th class="nowrap" colspan="5">&nbsp;</th>
            </tr>
        </tfoot>

        <tbody>
        % for hItem in historyResults:
            <% curStatus, curQuality = Quality.splitCompositeStatus(int(hItem["action"])) %>
            <tr>
                <td align="center">
                    <% airDate = sbdatetime.sbdatetime.sbfdatetime(datetime.datetime.strptime(str(hItem["date"]), History.date_format), show_seconds=True) %>
                    <% isoDate = datetime.datetime.strptime(str(hItem["date"]), History.date_format).isoformat('T') %>
                    <time datetime="${isoDate}" class="date">${airDate}</time>
                </td>
                <td class="tvShow" width="35%"><a href="${srRoot}/home/displayShow?show=${hItem["show_id"]}#S${hItem["season"]}E${hItem["episode"]}">${hItem["show_name"]} - ${"S%02i" % int(hItem["season"])}${"E%02i" % int(hItem["episode"])} ${('', '<span class="quality Proper">Proper</span>')["proper" in hItem["resource"].lower() or "repack" in hItem["resource"].lower()]}</a></td>
                <td align="center" ${('', 'class="subtitles_column"')[curStatus == SUBTITLED]}>
                % if curStatus == SUBTITLED:
                    <img width="16" height="11" style="vertical-align:middle;" src="${srRoot}/images/subtitles/flags/${hItem['resource']}.png" onError="this.onerror=null;this.src='${srRoot}/images/flags/unknown.png';">
                % endif
                    <span style="cursor: help; vertical-align:middle;" title="${os.path.basename(hItem['resource'])}">${statusStrings[curStatus]}</span>
                </td>
                <td align="center">
                % if curStatus in [DOWNLOADED, ARCHIVED]:
                    % if hItem["provider"] != "-1":
                        <span style="vertical-align:middle;"><i>${hItem["provider"]}</i></span>
                    % endif
                % else:
                    % if hItem["provider"] > 0:
                        % if curStatus in [SNATCHED, FAILED]:
                            <% provider = providers.getProviderClass(generic.GenericProvider.makeID(hItem["provider"])) %>
                            % if provider != None:
                                <img src="${srRoot}/images/providers/${provider.imageName()}" width="16" height="16" style="vertical-align:middle;" /> <span style="vertical-align:middle;">${provider.name}</span>
                            % else:
                                <img src="${srRoot}/images/providers/missing.png" width="16" height="16" style="vertical-align:middle;" title="missing provider"/> <span style="vertical-align:middle;">Missing Provider</span>
                            % endif
                        % else:
                                <img src="${srRoot}/images/subtitles/${hItem['provider']}.png" width="16" height="16" style="vertical-align:middle;" /> <span style="vertical-align:middle;">${hItem["provider"].capitalize()}</span>
                        % endif
                    % endif
                % endif
                </td>
                <span style="display: none;">${curQuality}</span>
                <td align="center">${renderQualityPill(curQuality)}</td>
            </tr>
        % endfor
        </tbody>
    </table>
% else:

    <table id="historyTable" class="sickbeardTable tablesorter" cellspacing="1" border="0" cellpadding="0">
        <thead>
            <tr>
                <th class="nowrap">Time</th>
                <th>Episode</th>
                <th>Snatched</th>
                <th>Downloaded</th>
                % if sickbeard.USE_SUBTITLES:
                <th>Subtitled</th>
                % endif
                <th>Quality</th>
            </tr>
        </thead>

        <tfoot>
            <tr>
                <th class="nowrap" colspan="6">&nbsp;</th>
            </tr>
        </tfoot>

        <tbody>
        % for hItem in compactResults:
            <tr>
                <td align="center">
                    <% airDate = sbdatetime.sbdatetime.sbfdatetime(datetime.datetime.strptime(str(hItem["actions"][0]["time"]), History.date_format), show_seconds=True) %>
                    <% isoDate = datetime.datetime.strptime(str(hItem["actions"][0]["time"]), History.date_format).isoformat('T') %>
                    <time datetime="${isoDate}" class="date">${airDate}</time>
                </td>
                <td class="tvShow" width="25%">
                    <span><a href="${srRoot}/home/displayShow?show=${hItem["show_id"]}#season-${hItem["season"]}">${hItem["show_name"]} - ${"S%02i" % int(hItem["season"])}${"E%02i" % int(hItem["episode"])}${('', ' <span class="quality Proper">Proper</span>')['proper' in hItem["resource"].lower() or 'repack' in hItem["resource"].lower()]}</a></span>
                </td>
                <td align="center" provider="${str(sorted(hItem["actions"])[0]["provider"])}">
                    % for action in sorted(hItem["actions"]):
                        <% curStatus, curQuality = Quality.splitCompositeStatus(int(action["action"])) %>
                        % if curStatus in [SNATCHED, FAILED]:
                            <% provider = providers.getProviderClass(generic.GenericProvider.makeID(action["provider"])) %>
                            % if provider != None:
                                <img src="${srRoot}/images/providers/${provider.imageName()}" width="16" height="16" style="vertical-align:middle;" alt="${provider.name}" style="cursor: help;" title="${provider.name}: ${os.path.basename(action["resource"])}"/>
                            % else:
                                <img src="${srRoot}/images/providers/missing.png" width="16" height="16" style="vertical-align:middle;" alt="missing provider" title="missing provider"/>
                            % endif
                        % endif
                    % endfor
                </td>
                <td align="center">
                    % for action in sorted(hItem["actions"]):
                        <% curStatus, curQuality = Quality.splitCompositeStatus(int(action["action"])) %>
                        % if curStatus in [DOWNLOADED, ARCHIVED]:
                            % if action["provider"] != "-1":
                                <span style="cursor: help;" title="${os.path.basename(action["resource"])}"><i>${action["provider"]}</i></span>
                            % else:
                                <span style="cursor: help;" title="${os.path.basename(action["resource"])}"></span>
                            % endif
                        % endif
                    % endfor
                </td>
                % if sickbeard.USE_SUBTITLES:
                <td align="center">
                    % for action in sorted(hItem["actions"]):
                        <% curStatus, curQuality = Quality.splitCompositeStatus(int(action["action"])) %>
                        % if curStatus == SUBTITLED:
                            <img src="${srRoot}/images/subtitles/${action['provider']}.png" width="16" height="16" style="vertical-align:middle;" alt="${action["provider"]}" title="${action["provider"].capitalize()}: ${os.path.basename(action["resource"])}"/>
                            <span style="vertical-align:middle;"> / </span>
                            <img width="16" height="11" style="vertical-align:middle;" src="${srRoot}/images/subtitles/flags/${action['resource']}.png" onError="this.onerror=null;this.src='${srRoot}/images/flags/unknown.png';" style="vertical-align: middle !important;">
                            &nbsp;
                        % endif
                    % endfor
                </td>
                % endif
                <td align="center" width="14%" quality="${curQuality}">${renderQualityPill(curQuality)}</td>
            </tr>
        % endfor
        </tbody>
    </table>

% endif
</%block>
