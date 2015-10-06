<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    from sickbeard import helpers
    from sickbeard.show_queue import ShowQueueActions
    from sickrage.helper.common import dateTimeFormat
%>
<%block name="scripts">
<script type="text/javascript" src="${srRoot}/js/new/status.js"></script>
</%block>
<%block name="content">
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif

<%
    schedulerList = {
        'Daily Search': 'dailySearchScheduler',
        'Backlog': 'backlogSearchScheduler',
        'Show Update': 'showUpdateScheduler',
        'Version Check': 'versionCheckScheduler',
        'Show Queue': 'showQueueScheduler',
        'Search Queue': 'searchQueueScheduler',
        'Proper Finder': 'properFinderScheduler',
        'Post Process': 'autoPostProcesserScheduler',
        'Subtitles Finder': 'subtitlesFinderScheduler',
        'Trakt Checker': 'traktCheckerScheduler',
    }
%>
<div id="config-content">
    <h2 class="header">Scheduler</h2>
    <table id="schedulerStatusTable" class="tablesorter" width="100%">
        <thead>
            <tr>
                <th>Scheduler</th>
                <th>Alive</th>
                <th>Enable</th>
                <th>Active</th>
                <th>Start Time</th>
                <th>Cycle Time</th>
                <th>Next Run</th>
                <th>Last Run</th>
                <th>Silent</th>
            </tr>
        </thead>
        <tbody>
            % for schedulerName, scheduler in schedulerList.iteritems():
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
                   <% del searchQueue %>
                   % if BLSpaused:
               <td>Paused</td>
                   % else:
               <td>${service.enable}</td>
                   % endif
               % else:
               <td>${service.enable}</td>
               % endif
               % if scheduler == 'backlogSearchScheduler':
                   <% searchQueue = getattr(sickbeard, 'searchQueueScheduler') %>
                   <% BLSinProgress = searchQueue.action.is_backlog_in_progress() %>
                   <% del searchQueue %>
                   % if BLSinProgress:
               <td>True</td>
                   % else:
                       % try:
                       <% amActive = service.action.amActive %>
               <td>${amActive}</td>
                       % except Exception:
               <td>N/A</td>
                       % endtry
                   % endif
               % else:
                   % try:
                   <% amActive = service.action.amActive %>
               <td>${amActive}</td>
                   % except Exception:
               <td>N/A</td>
                   % endtry
               % endif
               % if service.start_time:
               <td align="right">${service.start_time}</td>
               % else:
               <td align="right"></td>
               % endif
               <% cycleTime = (service.cycleTime.microseconds + (service.cycleTime.seconds + service.cycleTime.days * 24 * 3600) * 10**6) / 10**6 %>
               <td align="right">${helpers.pretty_time_delta(cycleTime)}</td>
               % if service.enable:
                   <% timeLeft = (service.timeLeft().microseconds + (service.timeLeft().seconds + service.timeLeft().days * 24 * 3600) * 10**6) / 10**6 %>
               <td align="right">${helpers.pretty_time_delta(timeLeft)}</td>
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
    <h2 class="header">Show Queue</h2>
    <table id="queueStatusTable" class="tablesorter" width="100%">
        <thead>
            <tr>
                <th>Show id</th>
                <th>Show name</th>
                <th>In Progress</th>
                <th>Priority</th>
                <th>Added</th>
                <th>Queue type</th>
            </tr>
        </thead>
        <tbody>
            % if sickbeard.showQueueScheduler.action.currentItem is not None:
                <tr>
                    % try:
                        <% showindexerid = sickbeard.showQueueScheduler.action.currentItem.show.indexerid %>
                        <td>${showindexerid}</td>
                    % except Exception:
                        <td></td>
                    % endtry
                    % try:
                        <% showname = sickbeard.showQueueScheduler.action.currentItem.show.name %>
                        <td>${showname}</td>
                    % except Exception:
                        % if sickbeard.showQueueScheduler.action.currentItem.action_id == ShowQueueActions.ADD:
                            <td>${sickbeard.showQueueScheduler.action.currentItem.showDir}</td>
                        % else:
                            <td></td>
                        % endif
                    % endtry
                    <td>${sickbeard.showQueueScheduler.action.currentItem.inProgress}</td>
                    % if sickbeard.showQueueScheduler.action.currentItem.priority == 10:
                        <td>LOW</td>
                    % elif sickbeard.showQueueScheduler.action.currentItem.priority == 20:
                        <td>NORMAL</td>
                    % elif sickbeard.showQueueScheduler.action.currentItem.priority == 30:
                        <td>HIGH</td>
                    % else:
                        <td>sickbeard.showQueueScheduler.action.currentItem.priority</td>
                    % endif
                    <td>${sickbeard.showQueueScheduler.action.currentItem.added.strftime(dateTimeFormat)}</td>
                    <td>${ShowQueueActions.names[sickbeard.showQueueScheduler.action.currentItem.action_id]}</td>
                </tr>
            % endif
            % for item in sickbeard.showQueueScheduler.action.queue:
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
                        <td>LOW</td>
                    % elif item.priority == 20:
                        <td>NORMAL</td>
                    % elif item.priority == 30:
                        <td>HIGH</td>
                    % else:
                        <td>${item.priority}</td>
                    % endif
                    <td>${item.added.strftime(dateTimeFormat)}</td>
                    <td>${ShowQueueActions.names[item.action_id]}</td>
                </tr>
            % endfor
        </tbody>
    </table>
    <h2 class="header">Disk Space</h2>
    <table id="DFStatusTable" class="tablesorter" width="50%">
        <thead>
            <tr>
                <th>Type</th>
                <th>Location</th>
                <th>Free space</th>
            </tr>
        </thead>
        <tbody>
            % if sickbeard.TV_DOWNLOAD_DIR:
            <tr>
                <td>TV Download Directory</td>
                <td>${sickbeard.TV_DOWNLOAD_DIR}</td>
                % if tvdirFree is not False:
                <td>${tvdirFree} MB</td>
                % else:
                <td><i>Missing</i></td>
                % endif
            </tr>
            % endif
            <tr>
                <td rowspan=${len(rootDir)}>Media Root Directories</td>
                % for cur_dir in rootDir:
                    <td>${cur_dir}</td>
                    % if rootDir[cur_dir] is not False:
                        <td>${rootDir[cur_dir]} MB</td>
                    % else:
                        <td><i>Missing</i></td>
                    % endif
            </tr>
            % endfor
        </tbody>
    </table>
</div>
</%block>
