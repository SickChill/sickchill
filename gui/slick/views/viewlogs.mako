<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    from sickbeard import classes
    from sickbeard.logger import reverseNames
%>
<%block name="scripts">
<script type="text/javascript" src="${srRoot}/js/new/viewlogs.js"></script>
</%block>
<%block name="content">
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif

<div class="h2footer pull-right">Minimum logging level to display: <select name="minLevel" id="minLevel" class="form-control form-control-inline input-sm">
<% levels = reverseNames.keys() %>
<% levels.sort(lambda x,y: cmp(reverseNames[x], reverseNames[y])) %>
% for level in levels:
    % if not sickbeard.DEBUG and (level == 'DEBUG' or level == 'DB'):
       <% continue %>
    % endif
<option value="${reverseNames[level]}" ${('', 'selected="selected"')[minLevel == reverseNames[level]]}>${level.title()}</option>
% endfor
</select>

Filter log by: <select name="logFilter" id="logFilter" class="form-control form-control-inline input-sm">
% for logNameFilter in sorted(logNameFilters):
    <option value="${logNameFilter}" ${('', 'selected="selected"')[logFilter == logNameFilter]}>${logNameFilters[logNameFilter]}</option>
% endfor
</select>
Search log by:
<input type="text" name="logSearch" placeholder="clear to reset" id="logSearch" value="${('', logSearch)[bool(logSearch)]}" class="form-control form-control-inline input-sm" />
</div>
<br />
<div class="align-left"><pre>
${logLines}
</pre>
</div>
<br />
</%block>
