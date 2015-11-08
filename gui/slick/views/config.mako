<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    from sickbeard import db
    from sickbeard.helpers import anon_url
    import sys, os
%>
<%block name="content">
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif

##cpu_usage = ${psutil.cpu_percent()}
##ram = ${psutil.phymem_usage()}
##ram_total = ${ram.total / 2**20}
##ram_used = ${ram.used / 2**20}
##ram_free = ${ram.free / 2**20}
##ram_percent_used = ${ram.percent}
##disk = ${psutil.disk_usage('/')}
##disk_total = ${disk.total / 2**30}
##disk_used = ${disk.used / 2**30}
##disk_free = ${disk.free / 2**30}
##disk_percent_used = ${disk.percent}
<div id="config-content">
<table class="infoTable" cellspacing="1" border="0" cellpadding="0" width="100%">
    <tr><td class="infoTableHeader">SR Version: </td><td class="infoTableCell">
% if sickbeard.VERSION_NOTIFY:
        BRANCH: (${sickbeard.BRANCH}) / COMMIT: (${sickbeard.CUR_COMMIT_HASH}) <!-- &ndash; build.date //--><br>
% else:
        You don't have version checking turned on. Please turn on "Check for Update" in Config > General.<br>
% endif
    </td></tr>

<%
    sr_user = None
    try:
        import pwd
        sr_user = pwd.getpwuid(os.getuid()).pw_name
    except ImportError:
        import getpass
        sr_user = getpass.getuser()
%>
% if sr_user:
    <tr><td class="infoTableHeader">SR User:</td><td class="infoTableCell">${sr_user}</td></tr>
% endif

% try:
    <% import locale %>
    <% sr_locale = locale.getdefaultlocale() %>
    <tr><td class="infoTableHeader">SR Locale:</td><td class="infoTableCell">${sr_locale}</td></tr>
% except:
    ""
% endtry

    <tr><td class="infoTableHeader">SR Config:</td><td class="infoTableCell">${sickbeard.CONFIG_FILE}</td></tr>
    <tr><td class="infoTableHeader">SR Database:</td><td class="infoTableCell">${db.dbFilename()}</td></tr>
    <tr><td class="infoTableHeader">SR Cache Dir:</td><td class="infoTableCell">${sickbeard.CACHE_DIR}</td></tr>
    <tr><td class="infoTableHeader">SR Log Dir:</td><td class="infoTableCell">${sickbeard.LOG_DIR}</td></tr>
    <tr><td class="infoTableHeader">SR Arguments:</td><td class="infoTableCell">${sickbeard.MY_ARGS}</td></tr>
% if sickbeard.WEB_ROOT:
    <tr><td class="infoTableHeader">SR Web Root:</td><td class="infoTableCell">${sickbeard.WEB_ROOT}</td></tr>
% endif
    <tr><td class="infoTableHeader">Python Version:</td><td class="infoTableCell">${sys.version[:120]}</td></tr>
    <tr class="infoTableSeperator"><td class="infoTableHeader"><i class="icon16-sb"></i> Homepage</td><td class="infoTableCell"><a href="${anon_url('http://www.sickrage.tv/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">http://www.sickrage.tv/</a></td></tr>
    <tr><td class="infoTableHeader"><i class="icon16-WiKi"></i> WiKi</td><td class="infoTableCell"><a href="${anon_url('https://github.com/SiCKRAGETV/sickrage-issues/wiki')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">https://github.com/SiCKRAGETV/sickrage-issues/wiki</a></td></tr>
    <tr><td class="infoTableHeader"><i class="icon16-web"></i> Forums</td><td class="infoTableCell"><a href="${anon_url('http://sickrage.tv/forums/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">http://sickrage.tv/forums/</a></td></tr>
    <tr><td class="infoTableHeader"><i class="icon16-github"></i> Source</td><td class="infoTableCell"><a href="${anon_url('https://github.com/SiCKRAGETV/SickRage/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">https://github.com/SiCKRAGETV/SickRage/</a></td></tr>
    <tr><td class="infoTableHeader"><i class="icon16-mirc"></i> IRChat</td><td class="infoTableCell"><a href="irc://irc.freenode.net/#sickrage" rel="noreferrer"><i>#sickrage</i> on <i>irc.freenode.net</i></a></td></tr>
</table>
</div>
</%block>
