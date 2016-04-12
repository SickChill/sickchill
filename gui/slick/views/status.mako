<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    from sickbeard import helpers
    from sickbeard.show_queue import ShowQueueActions
    from sickrage.helper.common import dateTimeFormat
%>
<%block name="content">
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif

<%
    schedulerList = {
        _('Daily Search'): 'daily_search_scheduler',
        _('Backlog'): 'backlog_search_scheduler',
        _('Show Update'): 'show_update_scheduler',
        _('Version Check'): 'version_check_scheduler',
        _('Show Queue'): 'show_queue_scheduler',
        _('Search Queue'): 'search_queue_scheduler',
        _('Proper Finder'): 'proper_search_scheduler',
        _('Post Process'): 'auto_post_processor_scheduler',
        _('Subtitles Finder'): 'subtitle_search_scheduler',
        _('Trakt Checker'): 'trakt_checker_scheduler',
    }
%>
<div id="config-content">
    <h2 class="header">${_('Scheduler')}</h2>
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
            % for schedulerName, scheduler in schedulerList.iteritems():
               <% service = getattr(sickbeard, scheduler) %>
           <tr>
               <td>${schedulerName}</td>
               % if service.is_alive():
               <td style="background-color:green">${service.is_alive()}</td>
               % else:
               <td style="background-color:red">${service.is_alive()}</td>
               % endif
               % if scheduler == 'backlog_search_scheduler':
                   <% searchQueue = getattr(sickbeard, 'search_queue_scheduler') %>
                   <% BLSpaused = searchQueue.action.is_backlog_paused() %>
                   <% del searchQueue %>
                   % if BLSpaused:
               <td>${_('Paused')}</td>
                   % else:
               <td>${service.enable}</td>
                   % endif
               % else:
               <td>${service.enable}</td>
               % endif
               % if scheduler == 'backlog_search_scheduler':
                   <% searchQueue = getattr(sickbeard, 'search_queue_scheduler') %>
                   <% BLSinProgress = searchQueue.action.is_backlog_in_progress() %>
                   <% del searchQueue %>
                   % if BLSinProgress:
               <td>${_('True')}</td>
                   % else:
                       % try:
                       <% am_active = service.action.am_active %>
               <td>${am_active}</td>
                       % except Exception:
               <td>${_('N/A')}</td>
                       % endtry
                   % endif
               % else:
                   % try:
                   <% am_active = service.action.am_active %>
               <td>${am_active}</td>
                   % except Exception:
               <td>${_('N/A')}</td>
                   % endtry
               % endif
               % if service.start_time:
               <td align="right">${service.start_time}</td>
               % else:
               <td align="right"></td>
               % endif
               <% cycle_time = (service.cycle_time.microseconds + (service.cycle_time.seconds + service.cycle_time.days * 24 * 3600) * 10**6) / 10**6 %>
               <td align="right" data-seconds="${cycle_time}">${helpers.pretty_time_delta(cycle_time)}</td>
               % if service.enable:
                   <% timeLeft = (service.timeLeft().microseconds + (service.timeLeft().seconds + service.timeLeft().days * 24 * 3600) * 10**6) / 10**6 %>
               <td align="right" data-seconds="${timeLeft}">${helpers.pretty_time_delta(timeLeft)}</td>
               % else:
               <td></td>
               % endif
               <td>${service.lastRun.strftime(dateTimeFormat)}</td>
               <td>${service.silent}</td>
           </tr>
           <% del service %>
           % endfor
       </tbody>
    </table>
    <h2 class="header">${_('Show Queue')}</h2>
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
            % if sickbeard.show_queue_scheduler.action.currentItem is not None:
                <tr>
                    % try:
                        <% showindexerid = sickbeard.show_queue_scheduler.action.currentItem.show.indexerid %>
                        <td>${showindexerid}</td>
                    % except Exception:
                        <td></td>
                    % endtry
                    % try:
                        <% showname = sickbeard.show_queue_scheduler.action.currentItem.show.name %>
                        <td>${showname}</td>
                    % except Exception:
                        % if sickbeard.show_queue_scheduler.action.currentItem.action_id == ShowQueueActions.ADD:
                            <td>${sickbeard.show_queue_scheduler.action.currentItem.showDir}</td>
                        % else:
                            <td></td>
                        % endif
                    % endtry
                    <td>${sickbeard.show_queue_scheduler.action.currentItem.inProgress}</td>
                    % if sickbeard.show_queue_scheduler.action.currentItem.priority == 10:
                        <td>${_('LOW')}</td>
                    % elif sickbeard.show_queue_scheduler.action.currentItem.priority == 20:
                        <td>${_('NORMAL')}</td>
                    % elif sickbeard.show_queue_scheduler.action.currentItem.priority == 30:
                        <td>${_('HIGH')}</td>
                    % else:
                        <td>sickbeard.show_queue_scheduler.action.currentItem.priority</td>
                    % endif
                    <td>${sickbeard.show_queue_scheduler.action.currentItem.added.strftime(dateTimeFormat)}</td>
                    <td>${ShowQueueActions.names[sickbeard.show_queue_scheduler.action.currentItem.action_id]}</td>
                </tr>
            % endif
            % for item in sickbeard.show_queue_scheduler.action.queue:
                <tr>
                    % try:
                        <% showindexerid = item.show.indexerid %>
                        <td>${showindexerid}</td>
                    % except Exception:
                        <td></td>
                    % endtry
                    % try:
                        <% showname = item.show.name %>
                        <td>${showname}</td>
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
            % endfor
        </tbody>
    </table>
    <h2 class="header">${_('Disk Space')}</h2>
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
</%block>
