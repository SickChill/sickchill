<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    from sickbeard import db
    from sickbeard.helpers import anon_url
    import sys
%>

<%block name="content">
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif

<div id="config-content">
<table class="infoTable" cellspacing="1" border="0" cellpadding="0" width="145%">
    % if sr_version:
    <tr><td class="infoTableHeader" style="vertical-align: top;"><i class="icon16new-sickrage"></i> SickRage Version:</td>
        <td class="infoTableCell">
        Branch: <a href="${anon_url('https://github.com/SickRage/SickRage/tree/%s' % sickbeard.BRANCH)}">${sickbeard.BRANCH}</a><br>
        Commit: <a href="${anon_url('https://github.com/SickRage/SickRage/commit/%s' % sickbeard.CUR_COMMIT_HASH)}">${sickbeard.CUR_COMMIT_HASH}</a><br>
        Version: <a href="${anon_url('https://github.com/SickRage/SickRage/releases/tag/%s' % sr_version)}">${sr_version}</a>
        </td>
    </tr>
    % endif
    <tr><td class="infoTableHeader"><i class="icon16new-python"></i> Python Version:</td><td class="infoTableCell">${sys.version[:120]}</td></tr>
    <tr><td class="infoTableHeader"><i class="icon16new-ssl"></i> SSL Version:</td><td class="infoTableCell">${ssl_version}</td></tr>
    <tr><td class="infoTableHeader" style="vertical-align: top;"><i class="icon16new-locale"></i> Locale:</td><td class="infoTableCell">${'.'.join([str(loc) for loc in sr_locale])}</td></tr>
    <tr><td>&nbsp;</td><td>&nbsp;</td></tr>
    <tr class="infoTableSeperator"><td>&nbsp;</td><td>&nbsp;</td></tr>
    <tr><td class="infoTableHeader"><i class="icon16new-user"></i> User:</td><td class="infoTableCell">${sr_user}</td></tr>
    <tr><td class="infoTableHeader"><i class="icon16new-dir"></i> Program Path:</td><td class="infoTableCell">${sickbeard.PROG_DIR}</td></tr>
    <tr><td class="infoTableHeader"><i class="icon16new-config"></i> Config File:</td><td class="infoTableCell">${sickbeard.CONFIG_FILE}</td></tr>
    <tr><td class="infoTableHeader"><i class="icon16new-db"></i> Database:</td><td class="infoTableCell">${db.dbFilename()}</td></tr>
    <tr><td class="infoTableHeader"><i class="icon16new-cache"></i> Cache Directory:</td><td class="infoTableCell">${sickbeard.CACHE_DIR}</td></tr>
    <tr><td class="infoTableHeader"><i class="icon16new-log"></i> Log Directory:</td><td class="infoTableCell">${sickbeard.LOG_DIR}</td></tr>
    % if sickbeard.MY_ARGS:
    <tr><td class="infoTableHeader"><i class="icon16new-arguments"></i> Arguments:</td><td class="infoTableCell">${sickbeard.MY_ARGS}</td></tr>
    % endif
    % if sickbeard.WEB_ROOT:
    <tr><td class="infoTableHeader"><i class="icon16new-folder"></i> Web Root:</td><td class="infoTableCell">${sickbeard.WEB_ROOT}</td></tr>
    % endif
    <tr><td>&nbsp;</td><td>&nbsp;</td></tr>
    <tr class="infoTableSeperator"><td>&nbsp;</td><td>&nbsp;</td></tr>
    <tr><td class="infoTableHeader"><i class="icon16-web"></i> Website:</td><td class="infoTableCell"><a href="${anon_url('http://sickrage.github.io/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">http://sickrage.github.io/</a></td></tr>
    <tr><td class="infoTableHeader"><i class="icon16-sickrage"></i> Wiki:</td><td class="infoTableCell"><a href="${anon_url('https://github.com/SickRage/sickrage-issues/wiki')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">https://github.com/SickRage/sickrage-issues/wiki</a></td></tr>
    <tr><td class="infoTableHeader"><i class="icon16-github"></i> Source:</td><td class="infoTableCell"><a href="${anon_url('https://github.com/SickRage/SickRage/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">https://github.com/SickRage/SickRage/</a></td></tr>
    <tr><td class="infoTableHeader"><i class="icon16-mirc"></i> IRC Chat:</td><td class="infoTableCell"><a href="irc://irc.freenode.net/#sickrage-issues" rel="noreferrer"><i>#sickrage-issues</i> on <i>irc.freenode.net</i></a></td></tr>
</table>
</div>
</%block>
