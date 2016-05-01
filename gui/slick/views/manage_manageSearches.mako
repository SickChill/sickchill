<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
%>
<%block name="scripts">
<script type="text/javascript" src="${srRoot}/js/plotTooltip.js?${sbPID}"></script>
</%block>
<%block name="content">
    <div class="row">
        <div class="col-md-12">
	        <h1 class="header">${header}</h1>
        </div>
    </div>
    <div class="row">
        <div class="col-md-12">
	        <h3>${_('Backlog Search')}:</h3>
	        <a class="btn" href="${srRoot}/manage/manageSearches/forceBacklog"><i class="icon-exclamation-sign"></i> ${_('Force')}</a>
	        <a class="btn" href="${srRoot}/manage/manageSearches/pauseBacklog?paused=${('1', '0')[backlogPaused]}"><i class="icon-${('paused', 'play')[backlogPaused]}"></i> ${('Pause', 'Unpause')[backlogPaused]}</a>
            ${((_('Not in progress'), _('In Progress'))[backlogRunning], _('Paused'))[backlogPaused]}
        </div>
    </div>
    <br>
    <div class="row">
	    <div class="col-md-12">
		    <h3>${_('Daily Search')}:</h3>
		    <a class="btn" href="${srRoot}/manage/manageSearches/forceSearch"><i class="icon-exclamation-sign"></i> ${_('Force')}</a>
            ${(_('Not in progress'), _('In Progress'))[dailySearchStatus]}
	    </div>
    </div>
    <br>
    <div class="row">
	    <div class="col-md-12">
		    <h3>${_('Find Propers Search')}:</h3>
		    <a class="btn ${('disabled', '')[sickbeard.DOWNLOAD_PROPERS]}" href="${srRoot}/manage/manageSearches/forceFindPropers"><i class="icon-exclamation-sign"></i> ${_('Force')}</a>
            ${(_('Not in progress'), _('In Progress'))[findPropersStatus] if sickbeard.DOWNLOAD_PROPERS else _('Propers search disabled')}
	    </div>
    </div>
    <br>
    <div class="row">
	    <div class="col-md-12">
		    <h3>${_('Subtitle Search')}:</h3>
		    <a class="btn ${('disabled', '')[sickbeard.USE_SUBTITLES]}" href="${srRoot}/manage/manageSearches/forceSubtitlesFinder"><i class="icon-exclamation-sign"></i> ${_('Force')}</a>
            ${(_('Not in progress'), _('In Progress'))[subtitlesFinderStatus] if sickbeard.USE_SUBTITLES else _('Subtitle search disabled')}
	    </div>
    </div>
    <br>
    <div class="row">
	    <div class="col-md-12">
		    <h3>${_('Search Queue')}:</h3>
            <table>
                <tr>
                    <td>${_('Backlog')}:</td>
                    <td><i>${queueLength['backlog']} ${_('pending items')}</i></td>
                </tr>
                <tr>
                    <td>${_('Daily')}:</td>
                    <td><i>${queueLength['daily']} ${_('pending items')}</i></td>
                </tr>
                <tr>
                    <td>${_('Manual')}:</td>
                    <td><i>${queueLength['manual']} ${_('pending items')}</i></td>
                </tr>
                <tr>
                    <td>${_('Failed')}:</td>
                    <td><i>${queueLength['failed']} ${_('pending items')}</i></td>
                </tr>
            </table>
	    </div>
    </div>
</%block>
