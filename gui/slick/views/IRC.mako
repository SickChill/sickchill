<%inherit file="/layouts/main.mako"/>
<%block name="content">
<%
import sickbeard
username = ("SickRageUI|?", sickbeard.GIT_USERNAME)[bool(sickbeard.GIT_USERNAME)]
%>
<div class="container-fluid">
	<iframe id="extFrame" src="https://kiwiirc.com/client/irc.freenode.net/?nick=${username}&theme=basic#sickrage-issues" width="100%" height="500" frameBorder="0" style="border: 1px black solid;"></iframe>
</div>
</%block>
