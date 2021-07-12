<%inherit file="/layouts/main.mako"/>
<%!
    from sickchill import settings
    from sickchill.oldbeard import db
    from sickchill.oldbeard.helpers import anon_url
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
                    <i class="icon16-config-sickchill"></i>&nbsp;&nbsp;SickChill Info:
                </div>
                <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                    <div class="row">
                        <div class="col-md-12">
                            % if settings.BRANCH == 'pip':
                                ${_('Install')}:
                                <a href="${anon_url('https://pypi.org/project/sickchill/')}">
                                    pip
                                </a>
                            % else:
                                ${_('Branch')}:
                                <a href="${anon_url('https://github.com/SickChill/SickChill/tree/%s' % settings.BRANCH)}">
                                    ${settings.BRANCH}
                                </a>
                            % endif
                        </div>
                    </div>
                    % if settings.BRANCH != 'pip':
                    <div class="row">
                        <div class="col-md-12">
                            ${_('Commit')}:
                            <a href="${anon_url('https://github.com/SickChill/SickChill/commit/%s' % settings.CUR_COMMIT_HASH)}">
                                ${settings.CUR_COMMIT_HASH}
                            </a>
                        </div>
                    </div>
                    % endif
                    % if sc_version:
                        <div class="row">
                            <div class="col-md-12">
                                Version:
                                <a href="${anon_url('https://github.com/SickChill/SickChill/releases/tag/%s' % sc_version)}">
                                    ${sc_version}
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
                    ${'.'.join([str(loc) for loc in sc_locale])}
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
                    ${sc_user}
                </div>
            </div>
            <br/>
            <div class="row">
                <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                    <i class="icon16-config-dir"></i>&nbsp;&nbsp;${_('Program Folder')}:
                </div>
                <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                    ${settings.PROG_DIR}
                </div>
            </div>
            <br/>
            <div class="row">
                <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                    <i class="icon16-config-config"></i>&nbsp;&nbsp;${_('Config File')}:
                </div>
                <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                    ${settings.CONFIG_FILE}
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
                    ${settings.CACHE_DIR}
                </div>
            </div>
            <br/>
            <div class="row">
                <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                    <i class="icon16-config-log"></i>&nbsp;&nbsp;${_('Log Folder')}:
                </div>
                <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                    ${settings.LOG_DIR}
                </div>
            </div>
            <br/>
            <div class="row">
                <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                    <i class="icon16-config-python"></i>&nbsp;&nbsp;${_('Executable')}:
                </div>
                <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                    ${sys.executable}
                </div>
            </div>
            <br/>
            <div class="row">
                <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                    <i class="icon16-config-arguments"></i>&nbsp;&nbsp;${_('Main Script')}:
                </div>
                <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                    ${settings.MY_FULLNAME}
                </div>
            </div>
            <br/>
            % if settings.MY_ARGS:
                <div class="row">
                    <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                        <i class="icon16-config-arguments"></i>&nbsp;&nbsp;${_('Arguments')}:
                    </div>
                    <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                        ${" ".join(settings.MY_ARGS)}
                    </div>
                </div>
                <br/>
            % endif
            % if settings.WEB_ROOT:
                <div class="row">
                    <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                        <i class="icon16-config-folder"></i>&nbsp;&nbsp;${_('Web Root')}:
                    </div>
                    <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                        ${settings.WEB_ROOT}
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
                    <a href="${anon_url('https://sickchill.github.io/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">
                        https://sickchill.github.io/
                    </a>
                </div>
            </div>
            <br/>
            <div class="row">
                <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                    <i class="icon16-config-wiki"></i>&nbsp;&nbsp;${_('Wiki')}:
                </div>
                <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                    <a href="${anon_url('https://github.com/SickChill/SickChill/wiki')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">
                        https://github.com/SickChill/SickChill/wiki
                    </a>
                </div>
            </div>
            <br/>
            <div class="row">
                <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                    <i class="icon16-config-github"></i>&nbsp;&nbsp;${_('Source')}:
                </div>
                <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                    <a href="${anon_url('https://github.com/SickChill/SickChill/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">
                        https://github.com/SickChill/SickChill/
                    </a>
                </div>
            </div>
            <br/>
            <div class="row">
                <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                    <i class="icon16-config-mirc"></i>&nbsp;&nbsp;${_('IRC Chat')}:
                </div>
                <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                    <a href="irc://irc.freenode.net/#sickchill" rel="noreferrer">
                        <i>#sickchill</i> on <i>irc.freenode.net</i>
                    </a>
                </div>
            </div>
            <br/>
            <div class="row">
                <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                    <i class="fa fa-fw fa-discord" style="color: #6B8ADB"></i>${_('Discord')}:
                </div>
                <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                    <a href="https://discord.gg/U8WPBdf" rel="noreferrer">
                        https://discord.gg/U8WPBdf
                    </a>
                </div>
            </div>
            <br/>
            <div class="row">
                <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                    <i class="fa fa-fw fa-slack" style="color: #3A0B36"></i>${_('Slack')}:
                </div>
                <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                    <a href="https://sickchill.slack.com" rel="noreferrer">
                        Workspace
                    </a>
                    <a href="https://join.slack.com/t/sickchill/shared_invite/zt-60hql14k-u7eJ3Dbl91Cb2LZgtqKpUw" rel="noreferrer">
                        (Invite)
                    </a>
                </div>
            </div>
            <br/>
            <div class="row">
                <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                    <i class="fa fa-fw fa-telegram" style="color: #38789A"></i>${_('Telegram')}:
                </div>
                <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                    <a href="https://t.me/sickchill" rel="noreferrer">
                        https://t.me/sickchill
                    </a>
                </div>
            </div>
        </div>
    </div>
</%block>
