<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    from sickbeard import classes
%>
<%block name="css">
<style>
pre {
  overflow: auto;
  word-wrap: normal;
  white-space: pre;
}
</style>
</%block>
<%block name="content">
<%
    if logLevel == sickbeard.logger.WARNING:
        errors = classes.WarningViewer.errors
        title = 'WARNING logs'
    else:
        errors = classes.ErrorViewer.errors
        title = 'ERROR logs'
%>
<h1 class="header">${title}</h1>
<div class="align-left">
<pre>
% if errors:
% for curError in sorted(errors, key=lambda error: error.time, reverse=True)[:500]:
${curError.time} ${curError.message}
% endfor
% else:
There are no events to display.
% endif
</pre>
</div>
</%block>
