<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
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
        errors = sickbeard.classes.WarningViewer.errors
        title = _('WARNING logs')
    else:
        errors = sickbeard.classes.ErrorViewer.errors
        title = _('ERROR logs')
%>
<h1 class="header">${title}</h1>
<div class="align-left">
<pre>
% if errors:
% for curError in sorted(errors, key=lambda error: error.time, reverse=True)[:500]:
${curError.time} ${curError.message}
% endfor
% else:
${_('There are no events to display.')}
% endif
</pre>
</div>
</%block>
