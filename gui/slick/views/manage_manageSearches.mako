<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
%>
<%block name="scripts">
<script type="text/javascript" src="${static_url('js/plotTooltip.js')}"></script>
</%block>
<%block name="content">
    <div class="row">
        <h1 class="header">${header}</h1>
    </div>
    <div class="row">
        <div class="col-xs-6 well well-sm">
            <div class="col-xs-12">
                <h3>${_('Backlog Search')}:
                  <a class="btn" href="${srRoot}/manage/manageSearches/forceBacklog">
                    <i class="icon-exclamation-sign"></i> ${_('Force')}</a>
                  <a class="btn" href="${srRoot}/manage/manageSearches/pauseBacklog?paused=${('1', '0')[backlogPaused]}">
                    <i class="icon-${('paused', 'play')[backlogPaused]}"></i> ${('Pause', 'Unpause')[backlogPaused]}
                  </a>
                </h3>
                ${((_('Not in progress'), _('In Progress'))[backlogRunning], _('Paused'))[backlogPaused]}
            </div>
            <div class="col-xs-12">
                <h3>${_('Daily Search')}:
                    <a class="btn" href="${srRoot}/manage/manageSearches/forceSearch">
                      <i class="icon-exclamation-sign"></i> ${_('Force')}</a>
                </h3>
                ${(_('Not in progress'), _('In Progress'))[dailySearchStatus]}
            </div>
            <div class="col-xs-12">
                <h3>${_('Find Propers Search')}:
                    <a class="btn ${('disabled', '')[sickbeard.DOWNLOAD_PROPERS]}" href="${srRoot}/manage/manageSearches/forceFindPropers">
                      <i class="icon-exclamation-sign"></i> ${_('Force')}
                    </a>
                </h3>
                ${(_('Not in progress'), _('In Progress'))[findPropersStatus] if sickbeard.DOWNLOAD_PROPERS else _('Propers search is disabled')}
            </div>
            <div class="col-xs-12">
                <h3>${_('Subtitle Search')}:
                    <a class="btn ${('disabled', '')[sickbeard.USE_SUBTITLES]}" href="${srRoot}/manage/manageSearches/forceSubtitlesFinder">
                      <i class="icon-exclamation-sign"></i> ${_('Force')}
                    </a>
                </h3>
                ${(_('Not in progress'), _('In Progress'))[subtitlesFinderStatus] if sickbeard.USE_SUBTITLES else _('Subtitle search is disabled')}
            </div>
            <div class="col-xs-12">
                <h3>${_('Auto Post Processor')}:
                    <a class="btn ${('disabled', '')[sickbeard.PROCESS_AUTOMATICALLY]}" href="${srRoot}/manage/manageSearches/forceAutoPostProcessor">
                      <i class="icon-exclamation-sign"></i> ${_('Force')}
                    </a>
                </h3>
                <p>
                    ${_('Auto Post Processor') + ': ' + (_('Not in progress'), _('In Progress'))[autoPostProcessorStatus] if sickbeard.PROCESS_AUTOMATICALLY else \
                      _('Auto Post Processor is disabled')}
                </p>
                <p>
                    ${_('Post Processor') + ': ' + (_('Not in progress'), _('In Progress'))[postProcessorStatus]}
                </p>
            </div>
        </div>
        <div class="col-xs-6">
            <ul class="list-group col-xs-6 col-xs-offset-3">
                <li class="list-group-item list-group-item-info">
                    ${_('Search Queue')}:
                </li>
                <li class="list-group-item">
                    <span class="badge">${queueLength['backlog']} ${_('pending items')}</span>
                    ${_('Backlog')}:
                </li>
                <li class="list-group-item">
                    <span class="badge">${queueLength['daily']} ${_('pending items')}</span>
                    ${_('Daily')}:
                </li>
                <li class="list-group-item">
                    <span class="badge">${queueLength['manual']} ${_('pending items')}</span>
                    ${_('Manual')}:
                </li>
                <li class="list-group-item">
                    <span class="badge">${queueLength['failed']} ${_('pending items')}</span>
                    ${_('Failed')}:
                </li>
            </ul>
        </div>
    </div>
</%block>
