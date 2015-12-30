<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    from sickbeard import db
    from sickbeard.helpers import anon_url
    from sickbeard.versionChecker import CheckVersion
    import sys
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
    <tr><td class="infoTableHeader" style="vertical-align: top;">Version:</td><td class="infoTableCell">
% if sickbeard.VERSION_NOTIFY:
        Branch: <a href="${anon_url('https://github.com/SickRage/SickRage/tree/%s' % sickbeard.BRANCH)}">${sickbeard.BRANCH}</a><br>
        Commit: <a href="${anon_url('https://github.com/SickRage/SickRage/commit/%s' % sickbeard.CUR_COMMIT_HASH)}">${sickbeard.CUR_COMMIT_HASH}</a><br>
        <%
        updater = CheckVersion().updater
        %>

        % if updater is not None:
            <%
            updater.need_update()
            %>

            Version: <a href="${anon_url('https://github.com/SickRage/SickRage/releases/tag/%s' % updater.get_cur_version())}">${updater.get_cur_version()}</a>
        % endif
        <!-- &ndash; build.date //-->
% else:
        You don't have version checking turned on. Please turn on "Check for Update" in Config > General.<br>
% endif
    </td></tr>

<%
    sr_user = None
    try:
        import os, pwd
        sr_user = pwd.getpwuid(os.getuid()).pw_name
    except ImportError:
        import getpass
        sr_user = getpass.getuser()
%>
% if sr_user:
    <tr><td class="infoTableHeader">User:</td><td class="infoTableCell">${sr_user}</td></tr>
% endif

% try:
    <% import locale %>
    <% sr_locale = locale.getdefaultlocale() %>
    <tr><td class="infoTableHeader" style="vertical-align: top;">Locale:</td><td class="infoTableCell">
        Language: ${sr_locale[0]}<br>
        Encoding: ${sr_locale[1]}
    </td></tr>
% except:
    ""
% endtry

    <tr><td class="infoTableHeader">Configuration File:</td><td class="infoTableCell">${sickbeard.CONFIG_FILE}</td></tr>
    <tr><td class="infoTableHeader">Database:</td><td class="infoTableCell">${db.dbFilename()}</td></tr>
    <tr><td class="infoTableHeader">Cache Directory:</td><td class="infoTableCell">${sickbeard.CACHE_DIR}</td></tr>
    <tr><td class="infoTableHeader">Log Directory:</td><td class="infoTableCell">${sickbeard.LOG_DIR}</td></tr>
    <tr><td class="infoTableHeader">Arguments:</td><td class="infoTableCell">${sickbeard.MY_ARGS}</td></tr>
% if sickbeard.WEB_ROOT:
    <tr><td class="infoTableHeader">Web Root:</td><td class="infoTableCell">${sickbeard.WEB_ROOT}</td></tr>
% endif
    <tr><td class="infoTableHeader">Python Version:</td><td class="infoTableCell">${sys.version[:120]}</td></tr>
    <tr class="infoTableSeperator"><td class="infoTableHeader"><i class="icon16-sb"></i> Website:</td><td class="infoTableCell"><a href="${anon_url('http://sickrage.github.io/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">http://sickrage.github.io/</a></td></tr>
    <tr><td class="infoTableHeader"><i class="icon16-WiKi"></i> Wiki:</td><td class="infoTableCell"><a href="${anon_url('https://github.com/SickRage/sickrage-issues/wiki')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">https://github.com/SickRage/sickrage-issues/wiki</a></td></tr>
    <tr><td class="infoTableHeader"><i class="icon16-github"></i> Source:</td><td class="infoTableCell"><a href="${anon_url('https://github.com/SickRage/SickRage/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">https://github.com/SickRage/SickRage/</a></td></tr>
    <tr><td class="infoTableHeader"><i class="icon16-mirc"></i> IRChat:</td><td class="infoTableCell"><a href="irc://irc.freenode.net/#sickrage-issues" rel="noreferrer"><i>#sickrage-issues</i> on <i>irc.freenode.net</i></a></td></tr>
</table>
</div>
</%block>
