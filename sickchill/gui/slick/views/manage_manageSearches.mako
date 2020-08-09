<%inherit file="/layouts/main.mako"/>
<%!
    from sickchill import settings
%>
<%block name="scripts">
<script type="text/javascript" src="${static_url('js/plotTooltip.js')}"></script>
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
            <a class="btn" href="${scRoot}/manage/manageSearches/forceBacklog"><i class="icon-exclamation-sign"></i> ${_('Force')}</a>
            <a class="btn" href="${scRoot}/manage/manageSearches/pauseBacklog?paused=${('1', '0')[backlogPaused]}"><i class="icon-${('paused', 'play')[backlogPaused]}"></i> ${('Pause', 'Unpause')[backlogPaused]}</a>
            ${((_('Not in progress'), _('In Progress'))[backlogRunning], _('Paused'))[backlogPaused]}
        </div>
    </div>
    <br>
    <div class="row">
        <div class="col-md-12">
            <h3>${_('Daily Search')}:</h3>
            <a class="btn" href="${scRoot}/manage/manageSearches/forceSearch"><i class="icon-exclamation-sign"></i> ${_('Force')}</a>
            ${(_('Not in progress'), _('In Progress'))[dailySearchStatus]}
        </div>
    </div>
    <br>
    <div class="row">
        <div class="col-md-12">
            <h3>${_('Find Propers Search')}:</h3>
            <a class="btn ${('disabled', '')[settings.DOWNLOAD_PROPERS]}" href="${scRoot}/manage/manageSearches/forceFindPropers"><i class="icon-exclamation-sign"></i> ${_('Force')}</a>
            ${(_('Not in progress'), _('In Progress'))[findPropersStatus] if settings.DOWNLOAD_PROPERS else _('Propers search disabled')}
        </div>
    </div>
    <br>
    <div class="row">
        <div class="col-md-12">
            <h3>${_('Subtitle Search')}:</h3>
            <a class="btn ${('disabled', '')[settings.USE_SUBTITLES]}" href="${scRoot}/manage/manageSearches/forceSubtitlesFinder"><i class="icon-exclamation-sign"></i> ${_('Force')}</a>
            ${(_('Not in progress'), _('In Progress'))[subtitlesFinderStatus] if settings.USE_SUBTITLES else _('Subtitle search disabled')}
        </div>
    </div>
    <br>
    <div class="row">
        <div class="col-md-12">
            <h3>${_('Auto Post Processor')}:</h3>
            <a class="btn ${('disabled', '')[settings.PROCESS_AUTOMATICALLY]}" href="${scRoot}/manage/manageSearches/forceAutoPostProcess">
                <i class="icon-exclamation-sign"></i> ${_('Force')}
            </a>
            ${(_('Not in progress'), _('In Progress'))[autoPostProcessorStatus] if settings.PROCESS_AUTOMATICALLY else _('Auto Post Processor disabled')}
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
    <br>
    <div class="row">
        <div class="col-md-12">
            <h3>${_('Post Processing Queue')}:</h3>
            <table>
                <tr>
                    <td>${_('Auto')}:</td>
                    <td><i>${processing_queue['auto']} ${_('pending items')}</i></td>
                </tr>
                <tr>
                    <td>${_('Manual')}:</td>
                    <td><i>${processing_queue['manual']} ${_('pending items')}</i></td>
                </tr>
            </table>
        </div>
    </div>
</%block>
