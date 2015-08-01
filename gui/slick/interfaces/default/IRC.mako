<%include file="/inc_top.mako"/>
<%
from sickbeard import GIT_USERNAME
if GIT_USERNAME:
        username = GIT_USERNAME
else:
        username = "SickRageUI|?"
%>
<iframe id="extFrame" src="https://kiwiirc.com/client/irc.freenode.net/?nick=${username}&theme=basic#sickrage" width="100%" height="500" frameBorder="0" style="border: 1px black solid;"></iframe>
<%include file="/inc_bottom.mako"/>
