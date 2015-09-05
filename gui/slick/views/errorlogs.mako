<%include file="/inc_top.mako"/>
<%!
    import sickbeard
    from sickbeard import classes
    from sickbeard.logger import reverseNames
%>
<h1 class="header">${title}</h1>
<div class="align-left"><pre>
% if classes.ErrorViewer.errors:
    % for curError in sorted(classes.ErrorViewer.errors, key=lambda error: error.time, reverse=True)[:500]:
        ${curError.time} ${curError.message}
    % endfor
% endif
</pre>
</div>

<script type="text/javascript" charset="utf-8">
window.setInterval( "location.reload(true)", 600000); // Refresh every 10 minutes
</script>

<%include file="/inc_bottom.mako"/>
