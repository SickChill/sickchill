<%inherit file="/layouts/main.mako"/>
<%block name="content">
    <%
        import sickchill
        username = ("SickChillUI|?", sickchill.GIT_USERNAME)[bool(sickchill.GIT_USERNAME)]
    %>
    <iframe id="extFrame" src="https://kiwiirc.com/client/irc.freenode.net/?nick=${username}&theme=basic#sickchill" width="100%" height="500" frameBorder="0" style="border: 1px black solid;"></iframe>
</%block>
