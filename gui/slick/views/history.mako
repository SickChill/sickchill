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

    layout = sickbeard.HISTORY_LAYOUT
    history_limit = sickbeard.HISTORY_LIMIT

    fuzzydate = 'airdate'
%>
<%block name="css">
<style type="text/css">
.sort_data {display:none;}
</style>
</%block>
<%block name="scripts">
<script type="text/javascript">
$.tablesorter.addParser({
    id: 'cDate',
    is: function(s) {
        return false;
    },
    format: function(s) {
        return s;
    },
    type: 'numeric'
});

$(document).ready(function(){
    $("#historyTable:has(tbody tr)").tablesorter({
        widgets: ['zebra', 'filter'],
        sortList: [[0,1]],
      textExtraction: {
        % if ( layout == 'detailed'):
            0: function(node) { return $(node).find("span").text().toLowerCase(); },
            4: function(node) { return $(node).find("span").text().toLowerCase(); }
        % else:
            0: function(node) { return $(node).find("span").text().toLowerCase(); },
            1: function(node) { return $(node).find("span").text().toLowerCase(); },
            2: function(node) { return $(node).attr("provider").toLowerCase(); },
            5: function(node) { return $(node).attr("quality").toLowerCase(); }
        % endif
      },
        headers: {
        % if ( layout == 'detailed'):
          0: { sorter: 'cDate' },
          4: { sorter: 'quality' }
        % else:
          0: { sorter: 'cDate' },
          4: { sorter: false },
          5: { sorter: 'quality' }
        % endif
      }

    });
    $('#history_limit').on('change', function() {
        var url = '${sbRoot}/history/?limit=' + $(this).val()
        window.location.href = url
    });

    % if sickbeard.FUZZY_DATING:
    fuzzyMoment({
        containerClass : '.${fuzzydate}',
        dateHasTime : true,
        dateFormat : '${sickbeard.DATE_PRESET}',
        timeFormat : '${sickbeard.TIME_PRESET_W_SECONDS}',
        trimZero : ${('false', 'true')[bool(sickbeard.TRIM_ZERO)]},
        dtGlue : ', ',
    });
    % endif

});
</script>
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
        <option value="100" ${('', 'selected="selected"')[limit == 100]}>100</option>
        <option value="250" ${('', 'selected="selected"')[limit == 250]}>250</option>
        <option value="500" ${('', 'selected="selected"')[limit == 500]}>500</option>
        <option value="0"   ${('', 'selected="selected"')[limit == 0  ]}>All</option>
    </select>

    <span> Layout:
        <select name="HistoryLayout" class="form-control form-control-inline input-sm" onchange="location = this.options[this.selectedIndex].value;">
            <option value="${sbRoot}/setHistoryLayout/?layout=compact"  ${('', 'selected="selected"')[sickbeard.HISTORY_LAYOUT == 'compact']}>Compact</option>
            <option value="${sbRoot}/setHistoryLayout/?layout=detailed" ${('', 'selected="selected"')[sickbeard.HISTORY_LAYOUT == 'detailed']}>Detailed</option>
        </select>
    </span>
</div>
<br>

% if layout == "detailed":
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
                <% curdatetime = datetime.datetime.strptime(str(hItem["date"]), History.date_format) %>
                <td align="center"><div class="${fuzzydate}">${sbdatetime.sbdatetime.sbfdatetime(curdatetime, show_seconds=True)}</div><span class="sort_data">${time.mktime(curdatetime.timetuple())}</span></td>
                <td class="tvShow" width="35%"><a href="${sbRoot}/home/displayShow?show=${hItem["show_id"]}#season-${hItem["season"]}">${hItem["show_name"]} - ${"S%02i" % int(hItem["season"])}${"E%02i" % int(hItem["episode"])} ${('', '<span class="quality Proper">Proper</span>')["proper" in hItem["resource"].lower() or "repack" in hItem["resource"].lower()]}</a></td>
                <td align="center" ${('', 'class="subtitles_column"')[curStatus == SUBTITLED]}>
                % if curStatus == SUBTITLED:
                    <img width="16" height="11" style="vertical-align:middle;" src="${sbRoot}/images/subtitles/flags/${hItem['resource']}.png" onError="this.onerror=null;this.src='${sbRoot}/images/flags/unknown.png';">
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
                                <img src="${sbRoot}/images/providers/${provider.imageName()}" width="16" height="16" style="vertical-align:middle;" /> <span style="vertical-align:middle;">${provider.name}</span>
                            % else:
                                <img src="${sbRoot}/images/providers/missing.png" width="16" height="16" style="vertical-align:middle;" title="missing provider"/> <span style="vertical-align:middle;">Missing Provider</span>
                            % endif
                        % else:
                                <img src="${sbRoot}/images/subtitles/${hItem['provider']}.png" width="16" height="16" style="vertical-align:middle;" /> <span style="vertical-align:middle;">${hItem["provider"].capitalize()}</span>
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
                <% curdatetime = datetime.datetime.strptime(str(hItem["actions"][0]["time"]), History.date_format) %>
                <td align="center"><div class="${fuzzydate}">${sbdatetime.sbdatetime.sbfdatetime(curdatetime, show_seconds=True)}</div><span class="sort_data">${time.mktime(curdatetime.timetuple())}</span></td>
                <td class="tvShow" width="25%">
                    <span><a href="${sbRoot}/home/displayShow?show=${hItem["show_id"]}#season-${hItem["season"]}">${hItem["show_name"]} - ${"S%02i" % int(hItem["season"])}${"E%02i" % int(hItem["episode"])}${('', ' <span class="quality Proper">Proper</span>')['proper' in hItem["resource"].lower() or 'repack' in hItem["resource"].lower()]}</a></span>
                </td>
                <td align="center" provider="${str(sorted(hItem["actions"])[0]["provider"])}">
                    % for action in sorted(hItem["actions"]):
                        <% curStatus, curQuality = Quality.splitCompositeStatus(int(action["action"])) %>
                        % if curStatus in [SNATCHED, FAILED]:
                            <% provider = providers.getProviderClass(generic.GenericProvider.makeID(action["provider"])) %>
                            % if provider != None:
                                <img src="${sbRoot}/images/providers/${provider.imageName()}" width="16" height="16" style="vertical-align:middle;" alt="${provider.name}" style="cursor: help;" title="${provider.name}: ${os.path.basename(action["resource"])}"/>
                            % else:
                                <img src="${sbRoot}/images/providers/missing.png" width="16" height="16" style="vertical-align:middle;" alt="missing provider" title="missing provider"/>
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
                            <img src="${sbRoot}/images/subtitles/${action['provider']}.png" width="16" height="16" style="vertical-align:middle;" alt="${action["provider"]}" title="${action["provider"].capitalize()}: ${os.path.basename(action["resource"])}"/>
                            <span style="vertical-align:middle;"> / </span>
                            <img width="16" height="11" style="vertical-align:middle;" src="${sbRoot}/images/subtitles/flags/${action['resource']}.png" onError="this.onerror=null;this.src='${sbRoot}/images/flags/unknown.png';" style="vertical-align: middle !important;">
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
