<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    import datetime
    from sickbeard.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickbeard.common import Quality, qualityPresets, statusStrings, qualityPresetStrings, cpu_presets
%>
<%block name="scripts">
<script type="text/javascript" src="${srRoot}/js/plotTooltip.js?${sbPID}"></script>
</%block>
<%block name="content">
<div id="content800">
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif

<div id="summary2" class="align-left">
<h3>Backlog Search:</h3>
<a class="btn" href="${srRoot}/manage/manageSearches/forceBacklog"><i class="icon-exclamation-sign"></i> Force</a>
<a class="btn" href="${srRoot}/manage/manageSearches/pauseBacklog?paused=${('1', '0')[bool(backlogPaused)]}"><i class="icon-${('paused', 'play')[bool(backlogPaused)]}"></i> ${('pause', 'Unpause')[bool(backlogPaused)]}</a>
% if not backlogRunning:
    Not in progress<br>
% else:
    ${('', 'Paused:')[bool(backlogPaused)]}
    Currently running<br>
% endif
<br>

<h3>Daily Search:</h3>
<a class="btn" href="${srRoot}/manage/manageSearches/forceSearch"><i class="icon-exclamation-sign"></i> Force</a>
${('Not in progress', 'In Progress')[dailySearchStatus]}<br>
<br>

<h3>Find Propers Search:</h3>
<a class="btn ${('disabled', '')[bool(sickbeard.DOWNLOAD_PROPERS)]}" href="${srRoot}/manage/manageSearches/forceFindPropers"><i class="icon-exclamation-sign"></i> Force</a>
% if not sickbeard.DOWNLOAD_PROPERS:
    Propers search disabled <br>
% elif not findPropersStatus:
    Not in progress<br>
% else:
    In Progress<br>
% endif
<br>

<h3>Search Queue:</h3>
Backlog: <i>${queueLength['backlog']} pending items</i></br>
Daily: <i>${queueLength['daily']} pending items</i></br>
Manual: <i>${queueLength['manual']} pending items</i></br>
Failed: <i>${queueLength['failed']} pending items</i></br>
</div>
</div>
</%block>
