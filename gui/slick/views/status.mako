<%inherit file="/layouts/main.mako"/>
<%!
    import collections
    import six
    import sickbeard
    from sickbeard import helpers
    from sickbeard.show_queue import ShowQueueActions
    from sickchill.helper.common import dateTimeFormat
%>
<%block name="content">
    <%
        schedulerList = collections.OrderedDict(sorted(six.iteritems({
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
    })))
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
                <table id="schedulerStatusTable" class="tablesorter" width="100%">
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
                        % for schedulerName, scheduler in six.iteritems(schedulerList):
                            ${scheduler_row(schedulerName, scheduler)}
                        % endfor
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    % if len(sickbeard.showQueueScheduler.action):
    <br/>
    <div class="row">
        <div class="col-md-12">
            <h2 class="header">${_('Show Queue')}</h2>
            <div class="horizontal-scroll">
                <table id="queueStatusTable" class="tablesorter" width="100%">
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
                        % if sickbeard.showQueueScheduler.action.currentItem is not None:
                            ${show_queue_row(sickbeard.showQueueScheduler.action.currentItem)}
                        % endif
                        % for item in sickbeard.showQueueScheduler.action.queue:
                            ${show_queue_row(item)}
                        % endfor
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    % endif
    % if len(sickbeard.postProcessorTaskScheduler.action):
    <br/>
    <div class="row">
        <div class="col-md-12">
            <h2 class="header">${_('Post Processing Queue')}</h2>
            <div class="horizontal-scroll">
                <table id="queueStatusTable" class="tablesorter" width="100%">
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
                        % if sickbeard.postProcessorTaskScheduler.action.currentItem is not None:
                            ${post_processor_task_row(sickbeard.postProcessorTaskScheduler.action.currentItem)}
                        % endif
                        % for item in sickbeard.postProcessorTaskScheduler.action.queue:
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
                <table id="DFStatusTable" class="tablesorter" width="50%">
                    <thead>
                        <tr>
                            <th>${_('Type')}</th>
                            <th>${_('Location')}</th>
                            <th>${_('Free space')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        % if sickbeard.TV_DOWNLOAD_DIR:
                            <tr>
                                <td>${_('TV Download Directory')}</td>
                                <td>${sickbeard.TV_DOWNLOAD_DIR}</td>
                                % if tvdirFree is not False:
                                    <td align="middle">${tvdirFree}</td>
                                % else:
                                    <td align="middle"><i>${_('Missing')}</i></td>
                                % endif
                            </tr>
                        % endif
                    <tr>
                        <td rowspan=${len(rootDir)}>${_('Media Root Directories')}</td>
                        % for cur_dir in rootDir:
                            <td>${cur_dir}</td>
                        % if rootDir[cur_dir] is not False:
                            <td align="middle">${rootDir[cur_dir]}</td>
                        % else:
                            <td align="middle"><i>${_('Missing')}</i></td>
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
    <% service = getattr(sickbeard, scheduler) %>

    <tr>
        <td>${schedulerName}</td>
        % if service.isAlive():
            <td style="background-color:green">${service.isAlive()}</td>
        % else:
            <td style="background-color:red">${service.isAlive()}</td>
        % endif
        % if scheduler == 'backlogSearchScheduler':
            <% searchQueue = getattr(sickbeard, 'searchQueueScheduler') %>
            <% BLSpaused = searchQueue.action.is_backlog_paused() %>
            <% BLSinProgress = searchQueue.action.is_backlog_in_progress() %>

            <% del searchQueue %>
            % if BLSpaused:
                <td>${_('Paused')}</td>
            % else:
                <td>${service.enable}</td>
            % endif
            % if BLSinProgress:
                <td>${_('True')}</td>
            % else:
                % try:
                    <td>${service.action.amActive}</td>
                % except Exception:
                    <td>${_('N/A')}</td>
                % endtry
            % endif
        % else:
            <td>${service.enable}</td>
             % try:
                <td>${service.action.amActive}</td>
            % except Exception:
                <td>${_('N/A')}</td>
            % endtry
        % endif
        % if service.start_time:
            <td align="right">${service.start_time}</td>
        % else:
            <td align="right"></td>
        % endif
        <% cycleTime = (service.cycleTime.microseconds + (service.cycleTime.seconds + service.cycleTime.days * 24 * 3600) * 10**6) / 10**6 %>
        <td align="right"
            data-seconds="${cycleTime}">${helpers.pretty_time_delta(cycleTime)}</td>
        % if service.enable:
            <% timeLeft = (service.timeLeft().microseconds + (service.timeLeft().seconds + service.timeLeft().days * 24 * 3600) * 10**6) / 10**6 %>
            <td align="right"
                data-seconds="${timeLeft}">${helpers.pretty_time_delta(timeLeft)}</td>
        % else:
            <td></td>
        % endif
        <td>${service.lastRun.strftime(dateTimeFormat)}</td>
        <td>${service.silent}</td>
    </tr>

    <% del service %>
</%def>

<%def name="show_queue_row(item)">
    <tr>
        % try:
            <td>${item.show.indexerid}</td>
        % except Exception:
            <td></td>
        % endtry
        % try:
            <td>${item.show.name}</td>
        % except Exception:
            % if item.action_id == ShowQueueActions.ADD:
                <td>${item.showDir}</td>
            % else:
                <td></td>
            % endif
        % endtry
        <td>${item.inProgress}</td>
        % if item.priority == 10:
            <td>${_('LOW')}</td>
        % elif item.priority == 20:
            <td>${_('NORMAL')}</td>
        % elif item.priority == 30:
            <td>${_('HIGH')}</td>
        % else:
            <td>${item.priority}</td>
        % endif
        <td>${item.added.strftime(dateTimeFormat)}</td>
        <td>${ShowQueueActions.names[item.action_id]}</td>
    </tr>
</%def>

<%def name="post_processor_task_row(item)">
    <tr>
        <td>${item.added.strftime(dateTimeFormat)}</td>
        <td>${item.mode}</td>
        <td>${item.directory}</td>
        <td>${item.filename}</td>
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
        <td>${item.inProgress}</td>
    </tr>
</%def>
