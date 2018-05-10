<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    from sickbeard import db
    from sickbeard.helpers import anon_url
    import sys
    import platform
%>

<%block name="content">
    <div class="row">
        <div class="col-md-12">
            % if not header is UNDEFINED:
                <h1 class="header">${header}</h1>
            % else:
                <h1 class="title">${title}</h1>
            % endif
        </div>
    </div>
    <div class="row">
        <div class="col-md-12">
            <div class="row">
                <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                    <i class="icon16-config-sickrage"></i>&nbsp;&nbsp;SickRage Info:
                </div>
                <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                    <div class="row">
                        <div class="col-md-12">
                            Branch:
                            <a href="${anon_url('https://github.com/SickRage/SickRage/tree/%s' % sickbeard.BRANCH)}">
                                ${sickbeard.BRANCH}
                            </a>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            Commit:
                            <a href="${anon_url('https://github.com/SickRage/SickRage/commit/%s' % sickbeard.CUR_COMMIT_HASH)}">
                                ${sickbeard.CUR_COMMIT_HASH}
                            </a>
                        </div>
                    </div>
                    % if sr_version:
                        <div class="row">
                            <div class="col-md-12">
                                Version:
                                <a href="${anon_url('https://github.com/SickRage/SickRage/releases/tag/%s' % sr_version)}">
                                    ${sr_version}
                                </a>
                            </div>
                        </div>
                    % endif
                    <div class="row">
                        <div class="col-md-12">
                            Database Version: ${'{}.{}'.format(*db.DBConnection().version)}
                        </div>
                    </div>
                </div>
            </div>
            <br/>
            <div class="row">
                <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                    <i class="icon16-config-python"></i>&nbsp;&nbsp;${_('Python Version')}:
                </div>
                <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                    ${sys.version[:120]}
                </div>
            </div>
            <br/>
            <div class="row">
                <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                    <i class="icon16-config-ssl"></i>&nbsp;&nbsp;${_('SSL Version')}:
                </div>
                <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                    ${ssl_version}
                </div>
            </div>
            <br/>
            <div class="row">
                <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                    <i class="icon16-config-os"></i>&nbsp;&nbsp;${_('OS')}:
                </div>
                <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                    ${platform.platform()}
                </div>
            </div>
            <br/>
            <div class="row">
                <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                    <i class="icon16-config-locale"></i>&nbsp;&nbsp;${_('Locale')}:
                </div>
                <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                    ${'.'.join([str(loc) for loc in sr_locale])}
                </div>
            </div>
            <br/>
            <div class="config-group-divider"></div>
            <br/>
            <div class="row">
                <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                    <i class="icon16-config-user"></i>&nbsp;&nbsp;${_('User')}:
                </div>
                <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                    ${sr_user}
                </div>
            </div>
            <br/>
            <div class="row">
                <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                    <i class="icon16-config-dir"></i>&nbsp;&nbsp;${_('Program Folder')}:
                </div>
                <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                    ${sickbeard.PROG_DIR}
                </div>
            </div>
            <br/>
            <div class="row">
                <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                    <i class="icon16-config-config"></i>&nbsp;&nbsp;${_('Config File')}:
                </div>
                <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                    ${sickbeard.CONFIG_FILE}
                </div>
            </div>
            <br/>
            <div class="row">
                <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                    <i class="icon16-config-db"></i>&nbsp;&nbsp;${_('Database File')}:
                </div>
                <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                    ${db.db_full_path()}
                </div>
            </div>
            <br/>
            <div class="row">
                <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                    <i class="icon16-config-cache"></i>&nbsp;&nbsp;${_('Cache Folder')}:
                </div>
                <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                    ${sickbeard.CACHE_DIR}
                </div>
            </div>
            <br/>
            <div class="row">
                <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                    <i class="icon16-config-log"></i>&nbsp;&nbsp;${_('Log Folder')}:
                </div>
                <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                    ${sickbeard.LOG_DIR}
                </div>
            </div>
            <br/>
            % if sickbeard.MY_ARGS:
                <div class="row">
                    <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                        <i class="icon16-config-arguments"></i>&nbsp;&nbsp;${_('Arguments')}:
                    </div>
                    <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                        ${sickbeard.MY_ARGS}
                    </div>
                </div>
                <br/>
            % endif
            % if sickbeard.WEB_ROOT:
                <div class="row">
                    <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                        <i class="icon16-config-folder"></i>&nbsp;&nbsp;${_('Web Root')}:
                    </div>
                    <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                        ${sickbeard.WEB_ROOT}
                    </div>
                </div>
                <br/>
            % endif
            <div class="config-group-divider"></div>
            <br/>
            <div class="row">
                <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                    <i class="icon16-config-web"></i>&nbsp;&nbsp;${_('Website')}:
                </div>
                <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                    <a href="${anon_url('http://sickrage.github.io/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">
                        http://sickrage.github.io/
                    </a>
                </div>
            </div>
            <br/>
            <div class="row">
                <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                    <i class="icon16-config-wiki"></i>&nbsp;&nbsp;${_('Wiki')}:
                </div>
                <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                    <a href="${anon_url('https://github.com/SickRage/SickRage/wiki')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">
                        https://github.com/SickRage/SickRage/wiki
                    </a>
                </div>
            </div>
            <br/>
            <div class="row">
                <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                    <i class="icon16-config-github"></i>&nbsp;&nbsp;${_('Source')}:
                </div>
                <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                    <a href="${anon_url('https://github.com/SickRage/SickRage/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">
                        https://github.com/SickRage/SickRage/
                    </a>
                </div>
            </div>
            <br/>
            <div class="row">
                <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                    <i class="icon16-config-mirc"></i>&nbsp;&nbsp;${_('IRC Chat')}:
                </div>
                <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                    <a href="irc://irc.freenode.net/#sickrage-issues" rel="noreferrer">
                        <i>#sickrage-issues</i> on <i>irc.freenode.net</i>
                    </a>
                </div>
            </div>
        </div>
    </div>
</%block>
