<%
    from sickbeard import classes
    global header="Logs &amp; Errors"
    title="Logs &amp; Errors"

    sbPath = ".."

    topmenu="errorlogs"
%>
<%include file="/inc_top.mako"/>

% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif
<div class="align-left"><pre>
% if classes.ErrorViewer.errors:
    % for curError in sorted(classes.ErrorViewer.errors, key=lambda error: error.time, reverse=True)[:500]:
        ${curError.time} ${curError.message}
    % endfor
% endif
</pre>
</div>

<script type="text/javascript" charset="utf-8">
<!--
window.setInterval( "location.reload(true)", 600000); // Refresh every 10 minutes
//-->
</script>

<%include file="/inc_bottom.mako"/>
