<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    from sickbeard import db
    from sickbeard.helpers import anon_url
    import sys
    import platform
%>

<%block name="content">
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif

<div id="config-content">
<table class="infoTable" cellspacing="1" border="0" cellpadding="0" width="100%">
    <tr><td class="infoTableHeader" style="vertical-align: top;"><i class="icon16-config-sickrage"></i> SickRage Info:</td>
        <td class="infoTableCell">
        Branch: <a href="${anon_url('https://github.com/SickRage/SickRage/tree/%s' % sickbeard.BRANCH)}">${sickbeard.BRANCH}</a><br>
        Commit: <a href="${anon_url('https://github.com/SickRage/SickRage/commit/%s' % sickbeard.CUR_COMMIT_HASH)}">${sickbeard.CUR_COMMIT_HASH}</a><br>
        % if sr_version:
        Version: <a href="${anon_url('https://github.com/SickRage/SickRage/releases/tag/%s' % sr_version)}">${sr_version}</a>
        % endif
        </td>
    </tr>
    <tr><td class="infoTableHeader"><i class="icon16-config-python"></i> Python Version:</td><td class="infoTableCell">${sys.version[:120]}</td></tr>
    <tr><td class="infoTableHeader"><i class="icon16-config-ssl"></i> SSL Version:</td><td class="infoTableCell">${ssl_version}</td></tr>
    <tr><td class="infoTableHeader"><i class="icon16-config-os"></i> OS:</td><td class="infoTableCell">${platform.platform()}</td></tr>
    <tr><td class="infoTableHeader" style="vertical-align: top;"><i class="icon16-config-locale"></i> Locale:</td><td class="infoTableCell">${'.'.join([str(loc) for loc in sr_locale])}</td></tr>
    <tr><td>&nbsp;</td><td>&nbsp;</td></tr>
    <tr class="infoTableSeperator"><td>&nbsp;</td><td>&nbsp;</td></tr>
    <tr><td class="infoTableHeader"><i class="icon16-config-user"></i> User:</td><td class="infoTableCell">${sr_user}</td></tr>
    <tr><td class="infoTableHeader"><i class="icon16-config-dir"></i> Program Folder:</td><td class="infoTableCell">${sickbeard.PROG_DIR}</td></tr>
    <tr><td class="infoTableHeader"><i class="icon16-config-config"></i> Config File:</td><td class="infoTableCell">${sickbeard.CONFIG_FILE}</td></tr>
    <tr><td class="infoTableHeader"><i class="icon16-config-db"></i> Database File:</td><td class="infoTableCell">${db.dbFilename()}</td></tr>
    <tr><td class="infoTableHeader"><i class="icon16-config-cache"></i> Cache Folder:</td><td class="infoTableCell">${sickbeard.CACHE_DIR}</td></tr>
    <tr><td class="infoTableHeader"><i class="icon16-config-log"></i> Log Folder:</td><td class="infoTableCell">${sickbeard.LOG_DIR}</td></tr>
    % if sickbeard.MY_ARGS:
    <tr><td class="infoTableHeader"><i class="icon16-config-arguments"></i> Arguments:</td><td class="infoTableCell">${sickbeard.MY_ARGS}</td></tr>
    % endif
    % if sickbeard.WEB_ROOT:
    <tr><td class="infoTableHeader"><i class="icon16-config-folder"></i> Web Root:</td><td class="infoTableCell">${sickbeard.WEB_ROOT}</td></tr>
    % endif
    <tr><td>&nbsp;</td><td>&nbsp;</td></tr>
    <tr class="infoTableSeperator"><td>&nbsp;</td><td>&nbsp;</td></tr>
    <tr><td class="infoTableHeader"><i class="icon16-config-web"></i> Website:</td><td class="infoTableCell"><a href="${anon_url('http://sickrage.github.io/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">http://sickrage.github.io/</a></td></tr>
    <tr><td class="infoTableHeader"><i class="icon16-config-wiki"></i> Wiki:</td><td class="infoTableCell"><a href="${anon_url('https://github.com/SickRage/SickRage/wiki')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">https://github.com/SickRage/SickRage/wiki</a></td></tr>
    <tr><td class="infoTableHeader"><i class="icon16-config-github"></i> Source:</td><td class="infoTableCell"><a href="${anon_url('https://github.com/SickRage/SickRage/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">https://github.com/SickRage/SickRage/</a></td></tr>
    <tr><td class="infoTableHeader"><i class="icon16-config-mirc"></i> IRC Chat:</td><td class="infoTableCell"><a href="irc://irc.freenode.net/#sickrage-issues" rel="noreferrer"><i>#sickrage-issues</i> on <i>irc.freenode.net</i></a></td></tr>
</table>
</div>
</%block>
