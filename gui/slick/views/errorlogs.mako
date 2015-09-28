<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    from sickbeard import classes
    from sickbeard.logger import reverseNames
%>
<%block name="scripts">
<script type="text/javascript" src="${srRoot}/js/new/errorlogs.js"></script>
</%block>
<%block name="content">
<h1 class="header">${title}</h1>
<div class="align-left"><pre>
% if classes.ErrorViewer.errors:
    % for curError in sorted(classes.ErrorViewer.errors, key=lambda error: error.time, reverse=True)[:500]:
        ${curError.time} ${curError.message}
    % endfor
% endif
</pre>
</div>
</%block>
