<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
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
<h3>${_('Backlog Search')}:</h3>
<a class="btn" href="${srRoot}/manage/manageSearches/forceBacklog"><i class="icon-exclamation-sign"></i> ${_('Force')}</a>
<a class="btn" href="${srRoot}/manage/manageSearches/pauseBacklog?paused=${('1', '0')[bool(backlogPaused)]}"><i class="icon-${('paused', 'play')[bool(backlogPaused)]}"></i> ${('pause', 'Unpause')[bool(backlogPaused)]}</a>
% if not backlogRunning:
    ${_('Not in progress')}<br>
% else:
    ${('', 'Paused:')[bool(backlogPaused)]}
    ${_('Currently running')}<br>
% endif
<br>

<h3>${_('Daily Search')}:</h3>
<a class="btn" href="${srRoot}/manage/manageSearches/forceSearch"><i class="icon-exclamation-sign"></i> ${_('Force')}</a>
${_('Not in progress')}', '${_('In Progress')}')[dailySearchStatus]}<br>
<br>

<h3>${_('Find Propers Search')}:</h3>
<a class="btn ${('disabled', '')[bool(sickbeard.DOWNLOAD_PROPERS)]}" href="${srRoot}/manage/manageSearches/forceFindPropers"><i class="icon-exclamation-sign"></i> ${_('Force')}</a>
% if not sickbeard.DOWNLOAD_PROPERS:
    ${_('Propers search disabled')}<br>
% elif not findPropersStatus:
    ${_('Not in progress')}<br>
% else:
    ${_('In Progress')}<br>
% endif
<br>

<h3>${_('Subtitle Search')}:</h3>
<a class="btn ${('disabled', '')[bool(sickbeard.USE_SUBTITLES)]}" href="${srRoot}/manage/manageSearches/forceSubtitlesFinder"><i class="icon-exclamation-sign"></i> ${_('Force')}</a>
% if not sickbeard.USE_SUBTITLES:
    ${_('Subtitle search disabled')} <br>
% elif not subtitlesFinderStatus:
    ${_('Not in progress')}<br>
% else:
    ${_('In Progress')}<br>
% endif
<br>

<h3>${_('Search Queue')}:</h3>
${_('Backlog')}: <i>${queueLength['backlog']} ${_('pending items')}</i><br>
${_('Daily')}: <i>${queueLength['daily']} ${_('pending items')}</i><br>
${_('Manual')}: <i>${queueLength['manual']} ${_('pending items')}</i><br>
${_('Failed')}: <i>${queueLength['failed']} ${_('pending items')}</i><br>
</div>
</div>
</%block>
