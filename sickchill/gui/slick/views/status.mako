<%inherit file="/layouts/main.mako"/>
<%!
    import timeago
    from datetime import datetime

    from sickchill import settings
    from sickchill.oldbeard import helpers
    from sickchill.oldbeard.show_queue import ShowQueueActions
%>
<%block name="content">
    <%
        schedulerList = dict(sorted({
            _('Daily Search'): 'dailySearchScheduler',
            _('Backlog'): 'backlogSearchScheduler',
            _('Show Update'): 'showUpdateScheduler',
            _('Version Check'): 'versionCheckScheduler',
            _('Show Queue'): 'showQueueScheduler',
            _('Search Queue'): 'searchQueueScheduler',
            _('Proper Finder'): 'properFinderScheduler',
            _('Post Process - Auto'): 'autoPostProcessorScheduler',
            _('Post Process'): 'postProcessorTaskScheduler',
            _('Subtitles Finder'): 'subtitlesFinderScheduler',
            _('Trakt Checker'): 'traktCheckerScheduler',
        }.items(), key=lambda item: item[0]))
    %>
    <div class="row">
        <div class="col-md-12">
            % if not header is UNDEFINED:
                <h1 class="header">${header}</h1>
            % else:
                <h1 class="title">${title}</h1>
            % endif
        </div>
    </div>
    <br/>
    <div class="row">
        <div class="col-md-12">

            <h2 class="header">${_('Scheduler')}</h2>
            <div class="horizontal-scroll">
                <table id="schedulerStatusTable" class="tablesorter">
                    <thead>
                        <tr>
                            <th>${_('Scheduler')}</th>
                            <th>${_('Alive')}</th>
                            <th>${_('Enable')}</th>
                            <th>${_('Active')}</th>
                            <th>${_('Start Time')}</th>
                            <th>${_('Cycle Time')}</th>
                            <th>${_('Next Run')}</th>
                            <th>${_('Last Run')}</th>
                            <th>${_('Silent')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        % for schedulerName, scheduler in schedulerList.items():
                            ${scheduler_row(schedulerName, scheduler)}
                        % endfor
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    % if settings.showQueueScheduler.action:
    <br/>
    <div class="row">
        <div class="col-md-12">
            <h2 class="header">${_('Show Queue')}</h2>
            <div class="horizontal-scroll">
                <table id="queueStatusTable" class="tablesorter">
                    <thead>
                        <tr>
                            <th>${_('Show id')}</th>
                            <th>${_('Show name')}</th>
                            <th>${_('In Progress')}</th>
                            <th>${_('Priority')}</th>
                            <th>${_('Added')}</th>
                            <th>${_('Queue type')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        % if settings.showQueueScheduler.action.currentItem is not None:
                            ${show_queue_row(settings.showQueueScheduler.action.currentItem)}
                        % endif
                        % for item in settings.showQueueScheduler.action.queue:
                            ${show_queue_row(item)}
                        % endfor
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    % endif
    % if settings.postProcessorTaskScheduler.action:
    <br/>
    <div class="row">
        <div class="col-md-12">
            <h2 class="header">${_('Post Processing Queue')}</h2>
            <div class="horizontal-scroll">
                <table id="queueStatusTable" class="tablesorter">
                    <thead>
                        <tr>
                            <th>${_('Added')}</th>
                            <th>${_('Mode')}</th>
                            <th>${_('Path')}</th>
                            <th>${_('Release Name')}</th>
                            <th>${_('Method')}</th>
                            <th>${_('Priority')}</th>
                            <th>${_('Delete')}</th>
                            <th>${_('Mark Failures')}</th>
                            <th>${_('Force')}</th>
                            <th>${_('In Progress')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        % if settings.postProcessorTaskScheduler.action.currentItem is not None:
                            ${post_processor_task_row(settings.postProcessorTaskScheduler.action.currentItem)}
                        % endif
                        % for item in settings.postProcessorTaskScheduler.action.queue:
                            ${post_processor_task_row(item)}
                        % endfor
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    % endif
    <br/>
    <div class="row">
        <div class="col-md-12">
            <h2 class="header">${_('Disk Space')}</h2>
            <div class="horizontal-scroll">
                <table id="DFStatusTable" class="tablesorter">
                    <thead>
                        <tr>
                            <th>${_('Type')}</th>
                            <th>${_('Location')}</th>
                            <th>${_('Free space')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        % if settings.TV_DOWNLOAD_DIR:
                            <tr>
                                <td>${_('TV Download Directory')}</td>
                                <td>${settings.TV_DOWNLOAD_DIR}</td>
                                % if tvdirFree is not False:
                                    <td>${tvdirFree}</td>
                                % else:
                                    <td><i>${_('Missing')}</i></td>
                                % endif
                            </tr>
                        % endif
                    <tr>
                        <td rowspan=${len(rootDir)}>${_('Media Root Directories')}</td>
                        % for cur_dir in rootDir:
                            <td>${cur_dir}</td>
                        % if rootDir[cur_dir] is not False:
                            <td>${rootDir[cur_dir]}</td>
                        % else:
                            <td><i>${_('Missing')}</i></td>
                        % endif
                        </tr>
                        % endfor
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</%block>

<%def name="scheduler_row(schedulerName, scheduler)">
    <% service = getattr(settings, scheduler) %>

    <tr class="text-center">
        <td class="text-left">${schedulerName}</td>
        <td class="${("false", "true")[service.is_alive()]}">${service.is_alive()}</td>
        <%
            try:
                enabled = service.enable
            except Exception:
                enabled = False

            try:
                active = service.action.amActive
            except Exception:
                active = False
        %>
        % if scheduler == 'backlogSearchScheduler':
            <% searchQueue = getattr(settings, 'searchQueueScheduler') %>
            % if searchQueue.action.is_backlog_paused():
                <td class="false">${_('Paused')}</td>
            % else:
                <td class="${("false", "true")[enabled]}">${enabled}</td>
            % endif
            % if searchQueue.action.is_backlog_in_progress():
                <td class="true">${_('True')}</td>
            % else:
                <td class="${("false", "true")[active]}">${active}</td>
            % endif
        % else:
            <td class="${("false", "true")[enabled]}">${enabled}</td>
            <td class="${("false", "true")[active]}">${active}</td>
        % endif
        % if service.start_time:
            <td>${service.start_time}</td>
        % else:
            <td></td>
        % endif
        <% cycleTime = (service.cycleTime.microseconds + (service.cycleTime.seconds + service.cycleTime.days * 24 * 3600) * 10**6) / 10**6 %>
        <td data-seconds="${cycleTime}">${helpers.pretty_time_delta(cycleTime)}</td>
        % if service.enable:
            <td>${timeago.format(datetime.now() + service.timeLeft())}</td>
        % else:
            <td></td>
        % endif
        <td>${timeago.format(service.lastRun)}</td>
        <td class="${("false", "true")[service.silent]}">${service.silent}</td>
    </tr>

    <% del service %>
</%def>

<%def name="show_queue_row(item)">
    <tr class="text-center">
        <%
            try:
                indexerid = item.show.indexerid
            except Exception:
                indexerid = ''
        %>
        <td>${indexerid}</td>
        % try:
            <td class="text-left">${item.show.name}</td>
        % except Exception:
            % if item.action_id == ShowQueueActions.ADD:
                <td class="text-left">${item.showDir}</td>
            % else:
                <td></td>
            % endif
        % endtry
        <td class="${("false", "true")[item.inProgress]}">${item.inProgress}</td>
        % if item.priority == 10:
            <td>${_('LOW')}</td>
        % elif item.priority == 20:
            <td>${_('NORMAL')}</td>
        % elif item.priority == 30:
            <td>${_('HIGH')}</td>
        % else:
            <td>${item.priority}</td>
        % endif
        <td>${timeago.format(item.added)}</td>
        <td>${ShowQueueActions.names[item.action_id]}</td>
    </tr>
</%def>

<%def name="post_processor_task_row(item)">
    <tr class="text-center">
        <td>${timeago.format(item.added)}</td>
        <td>${item.mode}</td>
        <td class="text-left">${item.directory}</td>
        <td class="text-left">${item.filename}</td>
        <td>${item.method}</td>
        % if item.priority == 10:
            <td>${_('LOW')}</td>
        % elif item.priority == 20:
            <td>${_('NORMAL')}</td>
        % elif item.priority == 30:
            <td>${_('HIGH')}</td>
        % else:
            <td>item.priority</td>
        % endif
        <td>${item.delete}</td>
        <td>${item.failed}</td>
        <td>${item.force}</td>
        <td class="${("false", "true")[item.inProgress]}">${item.inProgress}</td>
    </tr>
</%def>
