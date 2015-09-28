<%inherit file="/layouts/main.mako"/>
<%block name="scripts">
<%
    try:
        curSBHost = sbHost
        curSBHttpPort = sbHttpPort
        curSBHttpsEnabled = sbHttpsEnabled
        curSBHandleReverseProxy = sbHandleReverseProxy
        themeSpinner = sbThemeName
    except NameMapper.NotFound:
        curSBHost = "localhost"
        curSBHttpPort = sickbeard.WEB_PORT
        curSBHttpsEnabled = "False"
        curSBHandleReverseProxy = "False"
        themeSpinner = sickbeard.THEME_NAME
%>
<script type="text/javascript" charset="utf-8">
srRoot = "${srRoot}";
sbHttpPort = "${curSBHttpPort}";
sbHttpsEnabled = "${curSBHttpsEnabled}";
sbHandleReverseProxy = "${curSBHandleReverseProxy}";
sbHost = "${curSBHost}";
sbDefaultPage = "${sbDefaultPage}";
</script>
<script type="text/javascript" src="${srRoot}/js/lib/jquery-1.11.2.min.js?${sbPID}"></script>
<script type="text/javascript" src="${srRoot}/js/restart.js?${sbPID}&amp;${sbDefaultPage}"></script>
</%block>
<%block name="css">
<style>
.upgrade-notification {
    display: none;
}
</style>
</%block>
<%block name="content">
<%
    try:
        curSBHost = sbHost
        curSBHttpPort = sbHttpPort
        curSBHttpsEnabled = sbHttpsEnabled
        curSBHandleReverseProxy = sbHandleReverseProxy
        themeSpinner = sbThemeName
    except NameMapper.NotFound:
        curSBHost = "localhost"
        curSBHttpPort = sickbeard.WEB_PORT
        curSBHttpsEnabled = "False"
        curSBHandleReverseProxy = "False"
        themeSpinner = sickbeard.THEME_NAME
%>
<% themeSpinner = ('', '-dark')['dark' == themeSpinner] %>
<h2>Performing Restart</h2>
<br />
<div id="shut_down_message">
Waiting for SickRage to shut down:
<img src="${srRoot}/images/loading16${themeSpinner}.gif" height="16" width="16" id="shut_down_loading" />
<img src="${srRoot}/images/yes16.png" height="16" width="16" id="shut_down_success" style="display: none;" />
</div>

<div id="restart_message" style="display: none;">
Waiting for SickRage to start again:
<img src="${srRoot}/images/loading16${themeSpinner}.gif" height="16" width="16" id="restart_loading" />
<img src="${srRoot}/images/yes16.png" height="16" width="16" id="restart_success" style="display: none;" />
<img src="${srRoot}/images/no16.png" height="16" width="16" id="restart_failure" style="display: none;" />
</div>

<div id="refresh_message" style="display: none;">
Loading the default page:
<img src="${srRoot}/images/loading16${themeSpinner}.gif" height="16" width="16" id="refresh_loading" />
</div>

<div id="restart_fail_message" style="display: none;">
Error: The restart has timed out, perhaps something prevented SickRage from starting again?
</div>
</%block>
