<%inherit file="/layouts/config.mako"/>
<%!
    import sickbeard
    import re
    from sickbeard.helpers import anon_url
%>

<%block name="tabs">
    <li><a href="#htpcnas">${_('Home Theater / NAS')}</a></li>
    <li><a href="#devices">${_('Devices')}</a></li>
    <li><a href="#social">${_('Social')}</a></li>
</%block>

<%block name="pages">
    <form id="configForm" action="saveNotifications" method="post">

        <!-- /HTPC / NAS //-->
        <div id="htpcnas">

            <!-- /kodi component-group //-->
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-kodi" title="KODI"></span>
                        <h3><a href="${anon_url('http://kodi.tv/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">KODI</a></h3>
                        <p>${_('A free and open source cross-platform media center and home entertainment system software with a 10-foot user interface designed for the living-room TV.')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                    <fieldset class="component-group-list">
                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Enable')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" class="enabler" name="use_kodi" id="use_kodi" ${('', 'checked="checked"')[bool(sickbeard.USE_KODI)]}/>
                                <label for="use_kodi">${_('send KODI commands?')}</label>
                            </div>
                        </div>

                        <!-- content_use_kodi //-->
                        <div id="content_use_kodi">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Always on')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="kodi_always_on" id="kodi_always_on" ${('', 'checked="checked"')[bool(sickbeard.KODI_ALWAYS_ON)]}/>
                                    <label for="kodi_always_on">${_('log errors when unreachable?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on snatch')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="kodi_notify_onsnatch" id="kodi_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.KODI_NOTIFY_ONSNATCH)]}/>
                                    <label for="kodi_notify_onsnatch">${_('send a notification when a download starts?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="kodi_notify_ondownload" id="kodi_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.KODI_NOTIFY_ONDOWNLOAD)]}/>
                                    <label for="kodi_notify_ondownload">${_('send a notification when a download finishes?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on subtitle download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="kodi_notify_onsubtitledownload" id="kodi_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.KODI_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                    <label for="kodi_notify_onsubtitledownload">${_('send a notification when subtitles are downloaded?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Update library')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="kodi_update_library" id="kodi_update_library" ${('', 'checked="checked"')[bool(sickbeard.KODI_UPDATE_LIBRARY)]}/>
                                    <label for="kodi_update_library">${_('update KODI library when a download finishes?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Full library update')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="kodi_update_full" id="kodi_update_full" ${('', 'checked="checked"')[bool(sickbeard.KODI_UPDATE_FULL)]}/>
                                    <label for="kodi_update_full">${_('perform a full library update if update per-show fails?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Only update first host')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="kodi_update_onlyfirst" id="kodi_update_onlyfirst" ${('', 'checked="checked"')[bool(sickbeard.KODI_UPDATE_ONLYFIRST)]}/>
                                    <label for="kodi_update_onlyfirst">${_('only send library updates to the first active host?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('KODI IP:Port')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="kodi_host" id="kodi_host" value="${sickbeard.KODI_HOST}" class="form-control input-sm input350" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="kodi_host" class="component-desc">${_('host running KODI (eg. 192.168.1.100:8080)')}</label>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label>${_('(multiple host strings must be separated by commas)')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Username')}</span>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="kodi_username" id="kodi_username" value="${sickbeard.KODI_USERNAME}" class="form-control input-sm input250" autocapitalize="off" autocomplete="no" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="kodi_username">${_('username for your KODI server (blank for none)')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Password')}</span>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="password" name="kodi_password" id="kodi_password" value="${sickbeard.KODI_PASSWORD}" class="form-control input-sm input250" autocomplete="no" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="kodi_password">${_('password for your KODI server (blank for none)')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <div class="testNotification" id="testKODI-result">${_('Click below to test.')}</div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-12">
                                    <input  class="btn" type="button" value="Test KODI" id="testKODI" />
                                    <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                </div>
                            </div>
                        </div>

                    </fieldset>
                </div>
            </div>

            <div class="config-group-divider"></div>

            <!-- /plex media server component-group -->
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-plex" title="Plex Media Server"></span>
                        <h3><a href="${anon_url('http://www.plexapp.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Plex Media Server</a></h3>
                        <p>${_('Experience your media on a visually stunning, easy to use interface on your Mac connected to your TV. Your media library has never looked this good!')}</p>
                        <p class="plexinfo hide">${_('For sending notifications to Plex Home Theater (PHT) clients, use the KODI notifier with port <b>3005</b>.')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                    <fieldset class="component-group-list">

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Enable')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" class="enabler" name="use_plex_server" id="use_plex_server" ${('', 'checked="checked"')[bool(sickbeard.USE_PLEX_SERVER)]}/>
                                <label for="use_plex_server">${_('send Plex Media Server library updates?')}</label>
                            </div>
                        </div>

                        <div id="content_use_plex_server">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Plex Media Server Auth Token')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="plex_server_token" id="plex_server_token" value="${sickbeard.PLEX_SERVER_TOKEN}" class="form-control input-sm input350" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="plex_server_token">${_('auth token used by Plex')}</label>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <span class="component-desc">(<a href="${anon_url('https://support.plex.tv/hc/en-us/articles/204059436-Finding-your-account-token-X-Plex-Token')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">
                                                <u>Finding your account token</u></a>)
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Username')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="plex_server_username" id="plex_server_username" value="${sickbeard.PLEX_SERVER_USERNAME}" class="form-control input-sm input250" autocapitalize="off" autocomplete="no" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="plex_server_username">${_('blank = no authentication')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Password')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="password" name="plex_server_password" id="plex_server_password" value="${'*' * len(sickbeard.PLEX_SERVER_PASSWORD)}" class="form-control input-sm input250" autocomplete="no" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="plex_server_password">${_('blank = no authentication')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Update Library')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" class="enabler" name="plex_update_library" id="plex_update_library" ${('', 'checked="checked"')[bool(sickbeard.PLEX_UPDATE_LIBRARY)]}/>
                                    <label for="plex_update_library">${_('update Plex Media Server library when a download finishes')}</label>
                                </div>
                            </div>

                            <div id="content_plex_update_library">

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Plex Media Server IP:Port')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" name="plex_server_host" id="plex_server_host" value="${re.sub(r'\b,\b', ', ', sickbeard.PLEX_SERVER_HOST)}" class="form-control input-sm input350" autocapitalize="off" />
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="plex_server_host">${_('one or more hosts running Plex Media Server<br/>(eg. 192.168.1.1:32400, 192.168.1.2:32400)')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('HTTPS')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="plex_server_https" id="plex_server_https" ${('', 'checked="checked"')[bool(sickbeard.PLEX_SERVER_HTTPS)]}/>
                                        <label for="plex_server_https">${_('use https for plex media server requests?')}</label>
                                    </div>
                                </div>

                                <div class="row">
                                    <div class="col-md-12">
                                        <div class="testNotification" id="testPMS-result">${_('Click below to test Plex Media Server(s)')}</div>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <input class="btn" type="button" value="${_('Test Plex Media Server')}" id="testPMS" />
                                        <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                    </div>
                                </div>

                            </div>
                        </div><!-- /content_use_plex_server -->
                    </fieldset>
                </div>
            </div>

            <div class="config-group-divider"></div>

            <!-- /Plex Home Theater component-group -->
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-plexth" title="${_('Plex Home Theater')}"></span>
                        <h3><a href="${anon_url('http://www.plexapp.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Plex Home Theater</a></h3>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                    <fieldset class="component-group-list">

                         <div class="field-pair row">
                             <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                 <label class="component-title">${_('Enable')}</label>
                             </div>
                             <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                 <input type="checkbox" class="enabler" name="use_plex_client" id="use_plex_client" ${('', 'checked="checked"')[bool(sickbeard.USE_PLEX_CLIENT)]}/>
                                 <label for="use_plex_client">${_('send Plex Home Theater notifications?')}</label>
                             </div>
                        </div>

                        <div id="content_use_plex_client">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on snatch')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="plex_notify_onsnatch" id="plex_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.PLEX_NOTIFY_ONSNATCH)]}/>
                                    <label for="plex_notify_onsnatch">${_('send a notification when a download starts?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="plex_notify_ondownload" id="plex_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.PLEX_NOTIFY_ONDOWNLOAD)]}/>
                                    <label for="plex_notify_ondownload">${_('send a notification when a download finishes?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on subtitle download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="plex_notify_onsubtitledownload" id="plex_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                    <label for="plex_notify_onsubtitledownload">${_('send a notification when subtitles are downloaded?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Plex Home Theater IP:Port')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="plex_client_host" id="plex_client_host" value="${sickbeard.PLEX_CLIENT_HOST}" class="form-control input-sm input350" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="plex_client_host">${_('one or more hosts running Plex Home Theater<br>(eg. 192.168.1.100:3000, 192.168.1.101:3000)')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Username')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="plex_client_username" id="plex_client_username" value="${sickbeard.PLEX_CLIENT_USERNAME}" class="form-control input-sm input250" autocapitalize="off" autocomplete="no" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="plex_client_username">${_('blank = no authentication')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Password')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="password" name="plex_client_password" id="plex_client_password" value="${'*' * len(sickbeard.PLEX_CLIENT_PASSWORD)}" class="form-control input-sm input250" autocomplete="no" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="plex_client_password">${_('blank = no authentication')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <div class="testNotification" id="testPHT-result">${_('Click below to test Plex Home Theater(s)')}</div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-12">
                                    <input class="btn" type="button" value="${_('Test Plex Home Theater')}" id="testPHT" />
                                    <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-12">
                                    <label><b>${_('note')}:</b>&nbsp;${_('some Plex Home Theaters <b class="boldest">do not</b> support notifications e.g. Plexapp for Samsung TVs')}</label>
                                </div>
                            </div>

                        </div><!-- /content_use_plex_client -->
                    </fieldset>
                </div>

            </div>

            <div class="config-group-divider"></div>

            <!-- /emby component-group //-->
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-emby" title="${_('Emby')}"></span>
                        <h3><a href="${anon_url('http://emby.media/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Emby</a></h3>
                        <p>${_('A home media server built using other popular open source technologies.')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                    <fieldset class="component-group-list">

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Enable')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" class="enabler" name="use_emby" id="use_emby" ${('', 'checked="checked"')[bool(sickbeard.USE_EMBY)]} />
                                <label for="use_emby">${_('send update commands to Emby?')}</label>
                            </div>
                        </div>

                        <div id="content_use_emby">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Emby IP:Port')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="emby_host" id="emby_host" value="${sickbeard.EMBY_HOST}" class="form-control input-sm input250" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="emby_host">${_('host running Emby (eg. 192.168.1.100:8096)')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Emby API Key')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="text" name="emby_apikey" id="emby_apikey" value="${sickbeard.EMBY_APIKEY}" class="form-control input-sm input250" autocapitalize="off" />
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <div class="testNotification" id="testEMBY-result">${_('Click below to test.')}</div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-12">
                                    <input  class="btn" type="button" value="Test Emby" id="testEMBY" />
                                    <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                </div>
                            </div>
                        </div>
                    </fieldset>
                </div>
            </div>

            <div class="config-group-divider"></div>

            <!-- /nmj component-group //-->
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-nmj" title="${_('Networked Media Jukebox')}"></span>
                        <h3><a href="${anon_url('http://www.popcornhour.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">NMJ</a></h3>
                        <p>${_('The Networked Media Jukebox, or NMJ, is the official media jukebox interface made available for the Popcorn Hour 200-series.')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                    <fieldset class="component-group-list">

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Enable')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" class="enabler" name="use_nmj" id="use_nmj" ${('', 'checked="checked"')[bool(sickbeard.USE_NMJ)]}/>
                                <label for="use_nmj">${_('send update commands to NMJ?')}</label>
                            </div>
                        </div>

                        <div id="content_use_nmj">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Popcorn IP address')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="nmj_host" id="nmj_host" value="${sickbeard.NMJ_HOST}" class="form-control input-sm input250" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="nmj_host">${_('IP address of Popcorn 200-series (eg. 192.168.1.100)')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Get settings')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input class="btn btn-inline" type="button" value="${_('Get Settings')}" id="settingsNMJ" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="settingsNMJ">${_('the Popcorn Hour device must be powered on and NMJ running.')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('NMJ database')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="nmj_database" id="nmj_database" value="${sickbeard.NMJ_DATABASE}" class="form-control input-sm input250" ${(' readonly="readonly"', '')[sickbeard.NMJ_DATABASE is True]} autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="nmj_database">${_('automatically filled via the \'Get Settings\' button.')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('NMJ mount url')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="nmj_mount" id="nmj_mount" value="${sickbeard.NMJ_MOUNT}" class="form-control input-sm input250" ${(' readonly="readonly"', '')[sickbeard.NMJ_MOUNT is True]} autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="nmj_mount">${_('automatically filled via the \'Get Settings\' button.')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <div class="testNotification" id="testNMJ-result">${_('Click below to test.')}</div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-12">
                                    <input class="btn" type="button" value="Test NMJ" id="testNMJ" />
                                    <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                </div>
                            </div>

                        </div>

                    </fieldset>
                </div>
            </div>

            <div class="config-group-divider"></div>

            <!-- /nmjv2 component-group //-->
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-nmj" title="${_('Networked Media Jukebox v2')}"></span>
                        <h3><a href="${anon_url('http://www.popcornhour.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">NMJv2</a></h3>
                        <p>${_('The Networked Media Jukebox, or NMJv2, is the official media jukebox interface made available for the Popcorn Hour 300 & 400-series.')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                    <fieldset class="component-group-list">

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Enable')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" class="enabler" name="use_nmjv2" id="use_nmjv2" ${('', 'checked="checked"')[bool(sickbeard.USE_NMJv2)]}/>
                                <label for="use_nmjv2">${_('send update commands to NMJv2?')}</label>
                            </div>
                        </div>

                        <div id="content_use_nmjv2">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Popcorn IP address')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="nmjv2_host" id="nmjv2_host" value="${sickbeard.NMJv2_HOST}" class="form-control input-sm input250" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="nmjv2_host">${_('IP address of Popcorn 300/400-series (eg. 192.168.1.100)')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Database location')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="radio" NAME="nmjv2_dbloc" VALUE="local" id="NMJV2_DBLOC_A" ${('', 'checked="checked"')[sickbeard.NMJv2_DBLOC == 'local']}/>
                                            <label for="NMJV2_DBLOC_A">PCH Local Media</label>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="radio" NAME="nmjv2_dbloc" VALUE="network" id="NMJV2_DBLOC_B" ${('', 'checked="checked"')[sickbeard.NMJv2_DBLOC == 'network']}/>
                                            <label for="NMJV2_DBLOC_B">PCH Network Media</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Database instance')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <select id="NMJv2db_instance" class="form-control input-sm input350">
                                                <option value="0">#1 </option>
                                                <option value="1">#2 </option>
                                                <option value="2">#3 </option>
                                                <option value="3">#4 </option>
                                                <option value="4">#5 </option>
                                                <option value="5">#6 </option>
                                                <option value="6">#7 </option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="NMJv2db_instance">${_('adjust this value if the wrong database is selected.')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Find database')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="button" class="btn btn-inline" value="${_('Find Database')}" id="settingsNMJv2" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="settingsNMJv2">${_('the Popcorn Hour device must be powered on.')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('NMJv2 database')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="nmjv2_database" id="nmjv2_database" value="${sickbeard.NMJv2_DATABASE}" class="form-control input-sm input250" ${(' readonly="readonly"', '')[sickbeard.NMJv2_DATABASE is True]} autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="nmjv2_database">${_('automatically filled via the \'Find Database\' buttons.')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <div class="testNotification" id="testNMJv2-result">Click below to test.</div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-12">
                                    <input class="btn" type="button" value="Test NMJv2" id="testNMJv2" />
                                    <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                </div>
                            </div>

                        </div>

                    </fieldset>
                </div>
            </div>

            <div class="config-group-divider"></div>

            <!-- /synoindex component-group //-->
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-syno1" title="${_('Synology')}"></span>
                        <h3><a href="${anon_url('http://synology.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Synology</a></h3>
                        <p>${_('The Synology DiskStation NAS.')}</p>
                        <p>${_('Synology Indexer is the daemon running on the Synology NAS to build its media database.')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">

                    <fieldset class="component-group-list">
                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Enable')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="row">
                                    <div class="col-md-12">
                                        <input type="checkbox" class="enabler" name="use_synoindex" id="use_synoindex" ${('', 'checked="checked"')[bool(sickbeard.USE_SYNOINDEX)]}/>
                                        <label for="use_synoindex">${_('send Synology notifications?')}</label>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <label><b>${_('note')}:</b>&nbsp;${_('requires SickRage to be running on your Synology NAS.')}</label>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div id="content_use_synoindex">
                            <div class="row">
                                <div class="col-md-12">
                                    <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                </div>
                            </div>
                        </div>

                    </fieldset>
                </div>
            </div>

            <div class="config-group-divider"></div>

            <!-- /synology notifier component-group //-->
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-syno2" title="${_('Synology Indexer')}"></span>
                        <h3><a href="${anon_url('http://synology.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Synology Notifier</a></h3>
                        <p>${_('Synology Notifier is the notification system of Synology DSM')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                    <fieldset class="component-group-list">

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Enable')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="row">
                                    <div class="col-md-12">
                                        <input type="checkbox" class="enabler" name="use_synologynotifier" id="use_synologynotifier" ${('', 'checked="checked"')[bool(sickbeard.USE_SYNOLOGYNOTIFIER)]}/>
                                        <label for="use_synologynotifier">${_('send notifications to the Synology Notifier?')}</label>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <label><b>${_('note')}:</b>&nbsp;${_('requires SickRage to be running on your Synology NAS.')}</label>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div id="content_use_synologynotifier">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on snatch')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="synologynotifier_notify_onsnatch" id="synologynotifier_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH)]}/>
                                    <label for="synologynotifier_notify_onsnatch">${_('send a notification when a download starts?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="synologynotifier_notify_ondownload" id="synologynotifier_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD)]}/>
                                    <label for="synologynotifier_notify_ondownload">${_('send a notification when a download finishes?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on subtitle download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="synologynotifier_notify_onsubtitledownload" id="synologynotifier_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                    <label for="synologynotifier_notify_onsubtitledownload">${_('send a notification when subtitles are downloaded?')}</label>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                </div>
                            </div>
                        </div>
                    </fieldset>
                </div>
            </div>

            <div class="config-group-divider"></div>

            <!-- /pyTivo component-group //-->
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-pytivo" title="${_('pyTivo')}"></span>
                        <h3><a href="${anon_url('http://pytivo.sourceforge.net/wiki/index.php/PyTivo')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">pyTivo</a></h3>
                        <p>${_('pyTivo is both an HMO and GoBack server. This notifier will load the completed downloads to your Tivo.')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                    <fieldset class="component-group-list">

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Enable')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="row">
                                    <div class="col-md-12">
                                        <input type="checkbox" class="enabler" name="use_pytivo" id="use_pytivo" ${('', 'checked="checked"')[bool(sickbeard.USE_PYTIVO)]}/>
                                        <label for="use_pytivo">${_('send notifications to pyTivo?')}</label>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <label><b>${_('note')}:</b>&nbsp;${_('requires the downloaded files to be accessible by pyTivo.')}</label>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div id="content_use_pytivo">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('pyTivo IP:Port')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="pytivo_host" id="pytivo_host" value="${sickbeard.PYTIVO_HOST}" class="form-control input-sm input250" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="pytivo_host">${_('host running pyTivo (eg. 192.168.1.1:9032)')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('pyTivo share name')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="pytivo_share_name" id="pytivo_share_name" value="${sickbeard.PYTIVO_SHARE_NAME}" class="form-control input-sm input250" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="pytivo_share_name">${_('value used in pyTivo Web Configuration to name the share.')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                             <div class="field-pair row">
                                 <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                     <label class="component-title">${_('Tivo name')}</label>
                                 </div>
                                 <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                     <div class="row">
                                         <div class="col-md-12">
                                             <input type="text" name="pytivo_tivo_name" id="pytivo_tivo_name" value="${sickbeard.PYTIVO_TIVO_NAME}" class="form-control input-sm input250" autocapitalize="off" />
                                         </div>
                                     </div>
                                     <div class="row">
                                         <div class="col-md-12">
                                             <label for="pytivo_tivo_name">${_('(Messages &amp; Settings > Account &amp; System Information > System Information > DVR name)')}</label>
                                         </div>
                                     </div>
                                 </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                </div>
                            </div>
                        </div>

                    </fieldset>
                </div>
            </div>

        </div>

        <!-- /Devices //-->
        <div id="devices">

            <!-- /growl component-group //-->
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-growl" title="${_('Growl')}"></span>
                        <h3><a href="${anon_url('http://growl.info/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Growl</a></h3>
                        <p>${_('A cross-platform unobtrusive global notification system.')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                    <fieldset class="component-group-list">
                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Enable')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" class="enabler" name="use_growl" id="use_growl" ${('', 'checked="checked"')[bool(sickbeard.USE_GROWL)]}/>
                                <label for="use_growl">${_('send Growl notifications?')}</label>
                            </div>
                        </div>

                        <div id="content_use_growl">
                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on snatch')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="growl_notify_onsnatch" id="growl_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.GROWL_NOTIFY_ONSNATCH)]}/>
                                    <label for="growl_notify_onsnatch">${_('send a notification when a download starts?')}</label>
                                </div>
                            </div>
                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="growl_notify_ondownload" id="growl_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.GROWL_NOTIFY_ONDOWNLOAD)]}/>
                                    <label for="growl_notify_ondownload">${_('send a notification when a download finishes?')}</label>
                                </div>
                            </div>
                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on subtitle download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="growl_notify_onsubtitledownload" id="growl_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.GROWL_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                    <label for="growl_notify_ondownload">${_('send a notification when subtitles are downloaded?')}</label>
                                </div>
                            </div>
                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Growl IP:Port')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="growl_host" id="growl_host" value="${sickbeard.GROWL_HOST}" class="form-control input-sm input250" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="growl_host">${_('host running Growl (eg. 192.168.1.100:23053)')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Password')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="password" name="growl_password" id="growl_password" value="${sickbeard.GROWL_PASSWORD}" class="form-control input-sm input250" autocomplete="no" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="growl_password">${_('may leave blank if SickRage is on the same host.')}</label>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label>${_('otherwise Growl <b>requires</b> a password to be used.')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <div class="testNotification" id="testGrowl-result">${_('Click below to register and test Growl, this is required for Growl notifications to work.')}</div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-12">
                                    <input  class="btn" type="button" value="${_('Register Growl')}" id="testGrowl" />
                                    <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                </div>
                            </div>

                        </div>

                    </fieldset>
                </div>
            </div>

            <div class="config-group-divider"></div>

            <!-- /prowl component-group //-->
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-prowl" title="${_('Prowl')}"></span>
                        <h3><a href="${anon_url('http://www.prowlapp.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Prowl</a></h3>
                        <p>${_('A Growl client for iOS.')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">

                    <fieldset class="component-group-list">

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Enable')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" class="enabler" name="use_prowl" id="use_prowl" ${('', 'checked="checked"')[bool(sickbeard.USE_PROWL)]}/>
                                <label for="use_prowl">${_('send Prowl notifications?')}</label>
                            </div>
                        </div>

                        <div id="content_use_prowl">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on snatch')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="prowl_notify_onsnatch" id="prowl_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.PROWL_NOTIFY_ONSNATCH)]}/>
                                    <label for="prowl_notify_onsnatch">${_('send a notification when a download starts?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="prowl_notify_ondownload" id="prowl_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.PROWL_NOTIFY_ONDOWNLOAD)]}/>
                                    <label for="prowl_notify_ondownload">${_('send a notification when a download finishes?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on subtitle download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="prowl_notify_onsubtitledownload" id="prowl_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                    <label for="prowl_notify_onsubtitledownload">${_('send a notification when subtitles are downloaded?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Prowl Message Title')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="text" name="prowl_message_title" id="prowl_message_title" value="${sickbeard.PROWL_MESSAGE_TITLE}" class="form-control input-sm input250" autocapitalize="off" />
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Global Prowl API key(s)')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="prowl_api" id="prowl_api" value="${sickbeard.PROWL_API}" class="form-control input-sm input250" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="prowl_api">${_('''Prowl API(s) listed here, separated by commas if applicable, will<br> receive notifications for <b>all</b> shows. Your Prowl API key is available at:''')}
                                                <a href="${anon_url('https://www.prowlapp.com/api_settings.php')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">
                                                         https://www.prowlapp.com/api_settings.php
                                                </a><br>
                                                ${_('(this field may be blank except when testing.)')}
                                            </label>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Show notification list')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <select name="prowl_show" id="prowl_show" class="form-control input-sm input350">
                                                <option value="-1">${_('-- Select a Show --')}</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="prowl_show_list" id="prowl_show_list" class="form-control input-sm input350" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="prowl_show_list">
                                                ${_('''Configure per-show notifications here by entering Prowl API key(s), separated by commas, '
                                                'after selecting a show in the drop-down box.   Be sure to activate the 'Save for this show' '
                                                'button below after each entry.''')}
                                            </label>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input id="prowl_show_save" class="btn" type="button" value="${_('Save for this show')}" />
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Prowl priority')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <select id="prowl_priority" name="prowl_priority" class="form-control input-sm input250">
                                                <option value="-2" ${('', 'selected="selected"')[sickbeard.PROWL_PRIORITY == '-2']}>${_('Very Low')}</option>
                                                <option value="-1" ${('', 'selected="selected"')[sickbeard.PROWL_PRIORITY == '-1']}>${_('Moderate')}</option>
                                                <option value="0" ${('', 'selected="selected"')[sickbeard.PROWL_PRIORITY == '0']}>${_('Normal')}</option>
                                                <option value="1" ${('', 'selected="selected"')[sickbeard.PROWL_PRIORITY == '1']}>${_('High')}</option>
                                                <option value="2" ${('', 'selected="selected"')[sickbeard.PROWL_PRIORITY == '2']}>${_('Emergency')}</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="prowl_priority">${_('priority of Prowl messages from SickRage.')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="testNotification" id="testProwl-result">${_('Click below to test.')}</div>
                            <input  class="btn" type="button" value="Test Prowl" id="testProwl" />
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                        </div><!-- /content_use_prowl //-->

                    </fieldset>
                </div>
            </div>

            <div class="config-group-divider"></div>

            <!-- /libnotify component-group //-->
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-libnotify" title="${_('Libnotify')}"></span>
                        <h3><a href="${anon_url('http://library.gnome.org/devel/libnotify/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Libnotify</a></h3>
                        <p>${_('The standard desktop notification API for Linux/*nix systems.  This notifier will only function if the pynotify module is installed (Ubuntu/Debian package <a href="apt:python-notify">python-notify</a>).')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">

                    <fieldset class="component-group-list">

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Enable')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" class="enabler" name="use_libnotify" id="use_libnotify" ${('', 'checked="checked"')[bool(sickbeard.USE_LIBNOTIFY)]}/>
                                <label for="use_libnotify">${_('send Libnotify notifications?')}</label>
                            </div>
                        </div>

                        <div id="content_use_libnotify">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on snatch')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="libnotify_notify_onsnatch" id="libnotify_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.LIBNOTIFY_NOTIFY_ONSNATCH)]}/>
                                    <label for="libnotify_notify_onsnatch">${_('send a notification when a download starts?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="libnotify_notify_ondownload" id="libnotify_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.LIBNOTIFY_NOTIFY_ONDOWNLOAD)]}/>
                                    <label for="libnotify_notify_ondownload">${_('send a notification when a download finishes?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on subtitle download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="libnotify_notify_onsubtitledownload" id="libnotify_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                    <label for="libnotify_notify_onsubtitledownload">${_('send a notification when subtitles are downloaded?')}</label>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <div class="testNotification" id="testLibnotify-result">${_('Click below to test.')}</div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-12">
                                    <input  class="btn" type="button" value="Test Libnotify" id="testLibnotify" />
                                    <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                </div>
                            </div>

                        </div>

                    </fieldset>
                </div>
            </div>

            <div class="config-group-divider"></div>

            <!-- /pushover component-group //-->
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-pushover" title="${_('Pushover')}"></span>
                        <h3><a href="${anon_url('https://pushover.net/apps/clone/sickrage')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Pushover</a></h3>
                        <p>${_('Pushover makes it easy to send real-time notifications to your Android and iOS devices.')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">

                    <fieldset class="component-group-list">

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Enable')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" class="enabler" name="use_pushover" id="use_pushover" ${('', 'checked="checked"')[bool(sickbeard.USE_PUSHOVER)]}/>
                                <label for="use_pushover">${_('send Pushover notifications?')}</label>
                            </div>
                        </div>

                        <div id="content_use_pushover">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on snatch')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="pushover_notify_onsnatch" id="pushover_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.PUSHOVER_NOTIFY_ONSNATCH)]}/>
                                    <label for="pushover_notify_onsnatch">${_('send a notification when a download starts?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="pushover_notify_ondownload" id="pushover_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.PUSHOVER_NOTIFY_ONDOWNLOAD)]}/>
                                    <label for="pushover_notify_ondownload">${_('send a notification when a download finishes?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on subtitle download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="pushover_notify_onsubtitledownload" id="pushover_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                    <label for="pushover_notify_onsubtitledownload">${_('send a notification when subtitles are downloaded?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Pushover key')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="pushover_userkey" id="pushover_userkey" value="${sickbeard.PUSHOVER_USERKEY}" class="form-control input-sm input250" autocapitalize="off" autocomplete="no" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="pushover_userkey">${_('user key of your Pushover account')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Pushover API key')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="pushover_apikey" id="pushover_apikey" value="${sickbeard.PUSHOVER_APIKEY}" class="form-control input-sm input250" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="pushover_apikey"><a href="${anon_url('https://pushover.net/apps/clone/sickrage')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;"><b>click here</b></a> to create a Pushover API key</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Pushover devices')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="pushover_device" id="pushover_device" value="${sickbeard.PUSHOVER_DEVICE}" class="form-control input-sm input250" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="pushover_device">${_('comma separated list of pushover devices you want to send notifications to')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Pushover notification sound')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <select id="pushover_sound" name="pushover_sound" class="form-control input-sm input250">
                                                <option value="pushover" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'pushover']}>${_('Pushover')}</option>
                                                <option value="bike" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'bike']}>${_('Bike')}</option>
                                                <option value="bugle" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'bugle']}>${_('Bugle')}</option>
                                                <option value="cashregister" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'cashregister']}>${_('Cash Register')}</option>
                                                <option value="classical" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'classical']}>${_('Classical')}</option>
                                                <option value="cosmic" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'cosmic']}>${_('Cosmic')}</option>
                                                <option value="falling" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'falling']}>${_('Falling')}</option>
                                                <option value="gamelan" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'gamelan']}>${_('Gamelan')}</option>
                                                <option value="incoming" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'incoming']}> ${_('Incoming')}</option>
                                                <option value="intermission" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'intermission']}>${_('Intermission')}</option>
                                                <option value="magic" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'magic']}>${_('Magic')}</option>
                                                <option value="mechanical" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'mechanical']}>${_('Mechanical')}</option>
                                                <option value="pianobar" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'pianobar']}>${_('Piano Bar')}</option>
                                                <option value="siren" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'siren']}>${_('Siren')}</option>
                                                <option value="spacealarm" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'spacealarm']}>${_('Space Alarm')}</option>
                                                <option value="tugboat" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'tugboat']}>${_('Tug Boat')}</option>
                                                <option value="alien" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'alien']}>${_('Alien Alarm (long)')}</option>
                                                <option value="climb" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'climb']}>${_('Climb (long)')}</option>
                                                <option value="persistent" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'persistent']}>${_('Persistent (long)')}</option>
                                                <option value="echo" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'echo']}>${_('Pushover Echo (long)')}</option>
                                                <option value="updown" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'updown']}>${_('Up Down (long)')}</option>
                                                <option value="none" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'none']}>${_('None (silent)')}</option>
                                                <option value="default" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'default']}>${_('Device specific')}</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label class="component-desc">${_('choose notification sound to use')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Pushover priority')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <select id="pushover_priority" name="pushover_priority" class="form-control input-sm input250">
                                            <option value="-2" ${('', 'selected="selected"')[sickbeard.PUSHOVER_PRIORITY == '-2']}>${_('Very Low')}</option>
                                            <option value="-1" ${('', 'selected="selected"')[sickbeard.PUSHOVER_PRIORITY == '-1']}>${_('Moderate')}</option>
                                            <option value="0" ${('', 'selected="selected"')[sickbeard.PUSHOVER_PRIORITY == '0']}>${_('Normal')}</option>
                                            <option value="1" ${('', 'selected="selected"')[sickbeard.PUSHOVER_PRIORITY == '1']}>${_('High')}</option>
                                            <option value="2" ${('', 'selected="selected"')[sickbeard.PUSHOVER_PRIORITY == '2']}>${_('Emergency')}</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label class="component-desc">${_('Choose priority to use')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <div class="testNotification" id="testPushover-result">${_('Click below to test.')}</div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-12">
                                    <input  class="btn" type="button" value="Test Pushover" id="testPushover" />
                                    <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                </div>
                            </div>

                        </div>

                    </fieldset>
                </div>
            </div>

            <div class="config-group-divider"></div>

            <!-- /boxcar2 component-group //-->
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-boxcar2" title="${_('Boxcar 2')}"></span>
                        <h3><a href="${anon_url('https://new.boxcar.io/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Boxcar 2</a></h3>
                        <p>${_('Read your messages where and when you want them!')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">

                    <fieldset class="component-group-list">

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Enable')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" class="enabler" name="use_boxcar2" id="use_boxcar2" ${('', 'checked="checked"')[bool(sickbeard.USE_BOXCAR2)]}/>
                                <label for="use_boxcar2">${_('send Boxcar notifications?')}</label>
                            </div>
                        </div>

                        <div id="content_use_boxcar2">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on snatch')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="boxcar2_notify_onsnatch" id="boxcar2_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.BOXCAR2_NOTIFY_ONSNATCH)]}/>
                                    <label for="boxcar2_notify_onsnatch">${_('send a notification when a download starts?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="boxcar2_notify_ondownload" id="boxcar2_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.BOXCAR2_NOTIFY_ONDOWNLOAD)]}/>
                                    <label for="boxcar2_notify_ondownload">${_('send a notification when a download finishes?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on subtitle download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="boxcar2_notify_onsubtitledownload" id="boxcar2_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                    <label for="boxcar2_notify_onsubtitledownload">${_('send a notification when subtitles are downloaded?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Boxcar2 access token')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="boxcar2_accesstoken" id="boxcar2_accesstoken" value="${sickbeard.BOXCAR2_ACCESSTOKEN}" class="form-control input-sm input250" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="boxcar2_accesstoken">${_('access token for your Boxcar account.')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <div class="testNotification" id="testBoxcar2-result">${_('Click below to test.')}</div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-12">
                                    <input  class="btn" type="button" value="Test Boxcar" id="testBoxcar2" />
                                    <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                </div>
                            </div>

                        </div>

                    </fieldset>
                </div>
            </div>

            <div class="config-group-divider"></div>

            <!-- /nma component-group //-->
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-nma" alt="" title="${_('NMA')}"></span>
                        <h3><a href="${anon_url('http://www.notifymyandroid.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">${_('Notify My Android')}</a></h3>
                        <p>${_('Notify My Android is a Prowl-like Android App and API that offers an easy way to send notifications from your application directly to your Android device.')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">

                    <fieldset class="component-group-list">

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Enable')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" class="enabler" name="use_nma" id="use_nma" ${('', 'checked="checked"')[bool(sickbeard.USE_NMA)]}/>
                                <label for="use_nma">${_('send NMA notifications?')}</label>
                            </div>
                        </div>

                        <div id="content_use_nma">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on snatch')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="nma_notify_onsnatch" id="nma_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.NMA_NOTIFY_ONSNATCH)]}/>
                                    <label for="nma_notify_onsnatch">${_('send a notification when a download starts?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="nma_notify_ondownload" id="nma_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.NMA_NOTIFY_ONDOWNLOAD)]}/>
                                    <label for="nma_notify_ondownload">${_('send a notification when a download finishes?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on subtitle download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="nma_notify_onsubtitledownload" id="nma_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.NMA_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                    <label for="nma_notify_onsubtitledownload">${_('send a notification when subtitles are downloaded?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('NMA API key')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="nma_api" id="nma_api" value="${sickbeard.NMA_API}" class="form-control input-sm input350" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="nma_api">${_('(multiple keys must be separated by commas, up to a maximum of 5)')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('NMA priority')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <select id="nma_priority" name="nma_priority" class="form-control input-sm input350">
                                                <option value="-2" ${('', 'selected="selected"')[sickbeard.NMA_PRIORITY == '-2']}>${_('Very Low')}</option>
                                                <option value="-1" ${('', 'selected="selected"')[sickbeard.NMA_PRIORITY == '-1']}>${_('Moderate')}</option>
                                                <option value="0" ${('', 'selected="selected"')[sickbeard.NMA_PRIORITY == '0']}>${_('Normal')}</option>
                                                <option value="1" ${('', 'selected="selected"')[sickbeard.NMA_PRIORITY == '1']}>${_('High')}</option>
                                                <option value="2" ${('', 'selected="selected"')[sickbeard.NMA_PRIORITY == '2']}>${_('Emergency')}</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="nma_priority">${_('priority of NMA messages from SickRage.')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <div class="testNotification" id="testNMA-result">${_('Click below to test.')}</div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-12">
                                    <input  class="btn" type="button" value="Test NMA" id="testNMA" />
                                    <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                </div>
                            </div>

                        </div>

                    </fieldset>
                </div>
            </div>

            <div class="config-group-divider"></div>

            <!-- /pushalot component-group //-->
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-pushalot" title="${_('Pushalot')}"></span>
                        <h3><a href="${anon_url('https://pushalot.com')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Pushalot</a></h3>
                        <p>${_('Pushalot is a platform for receiving custom push notifications to connected devices running Windows Phone or Windows 8.')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">

                    <fieldset class="component-group-list">

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Enable')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" class="enabler" name="use_pushalot" id="use_pushalot" ${('', 'checked="checked"')[bool(sickbeard.USE_PUSHALOT)]}/>
                                <label for="use_pushalot">${_('send Pushalot notifications ?')}</label>
                            </div>
                        </div>

                        <div id="content_use_pushalot">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on snatch')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="pushalot_notify_onsnatch" id="pushalot_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.PUSHALOT_NOTIFY_ONSNATCH)]}/>
                                    <label for="pushalot_notify_onsnatch">${_('send a notification when a download starts?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="pushalot_notify_ondownload" id="pushalot_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.PUSHALOT_NOTIFY_ONDOWNLOAD)]}/>
                                    <label for="pushalot_notify_ondownload">${_('send a notification when a download finishes?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on subtitle download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="pushalot_notify_onsubtitledownload" id="pushalot_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                    <label for="pushalot_notify_onsubtitledownload">${_('send a notification when subtitles are downloaded?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Pushalot authorization token')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="pushalot_authorizationtoken" id="pushalot_authorizationtoken" value="${sickbeard.PUSHALOT_AUTHORIZATIONTOKEN}" class="form-control input-sm input350" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="pushalot_authorizationtoken">${_('authorization token of your Pushalot account.')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <div class="testNotification" id="testPushalot-result">${_('Click below to test.')}</div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-12">
                                    <input type="button" class="btn" value="Test Pushalot" id="testPushalot" />
                                    <input type="submit" class="btn config_submitter" value="${_('Save Changes')}" />
                                </div>
                            </div>

                        </div>

                    </fieldset>
                </div>
            </div>

            <div class="config-group-divider"></div>

            <!-- /pushbullet component-group //-->
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-pushbullet" title="${_('Pushbullet')}"></span>
                        <h3><a href="${anon_url('https://www.pushbullet.com')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Pushbullet</a></h3>
                        <p>${_('Pushbullet is a platform for receiving custom push notifications to connected devices running Android/iOS and desktop browsers such as Chrome, Firefox or Opera.')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">

                    <fieldset class="component-group-list">

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Enable')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" class="enabler" name="use_pushbullet" id="use_pushbullet" ${('', 'checked="checked"')[bool(sickbeard.USE_PUSHBULLET)]}/>
                                <label for="use_pushbullet">${_('send Pushbullet notifications?')}</label>
                            </div>
                        </div>

                        <div id="content_use_pushbullet">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on snatch')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="pushbullet_notify_onsnatch" id="pushbullet_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.PUSHBULLET_NOTIFY_ONSNATCH)]}/>
                                    <label for="pushbullet_notify_onsnatch">${_('send a notification when a download starts?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="pushbullet_notify_ondownload" id="pushbullet_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.PUSHBULLET_NOTIFY_ONDOWNLOAD)]}/>
                                    <label for="pushbullet_notify_ondownload">${_('send a notification when a download finishes?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on subtitle download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="pushbullet_notify_onsubtitledownload" id="pushbullet_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                    <label for="pushbullet_notify_onsubtitledownload">${_('send a notification when subtitles are downloaded?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Pushbullet API key')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="pushbullet_api" id="pushbullet_api" value="${sickbeard.PUSHBULLET_API}" class="form-control input-sm input350" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="pushbullet_api">${_('API key of your Pushbullet account')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Pushbullet devices')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <select name="pushbullet_device_list" id="pushbullet_device_list" class="form-control input-sm input250" title="Pushbullet device list"></select>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="hidden" id="pushbullet_device" value="${sickbeard.PUSHBULLET_DEVICE}">
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="button" class="btn btn-inline" value="${_('Update device list')}" id="getPushbulletDevices" />
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Pushbullet channels')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <select name="pushbullet_channel_list" id="pushbullet_channel_list" class="form-control input-sm input250" title="Pushbullet channel list"></select>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="hidden" id="pushbullet_channel" value="${sickbeard.PUSHBULLET_CHANNEL}">
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <div class="testNotification" id="testPushbullet-result">${_('Click below to test.')}</div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-12">
                                    <input type="button" class="btn" value="Test Pushbullet" id="testPushbullet" />
                                    <input type="submit" class="btn config_submitter" value="${_('Save Changes')}" />
                                </div>
                            </div>

                        </div>

                    </fieldset>
                </div>
            </div>

            <div class="config-group-divider"></div>

            <!-- /freemobile component-group //-->
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-freemobile" title="${_('Free Mobile')}"></span>
                        <h3><a href="${anon_url('http://mobile.free.fr/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Free Mobile</a></h3>
                        <p>${_('Free Mobile is a famous French cellular network provider.<br> It provides to their customer a free SMS API.')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">

                    <fieldset class="component-group-list">

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Enable')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" class="enabler" name="use_freemobile" id="use_freemobile" ${('', 'checked="checked"')[bool(sickbeard.USE_FREEMOBILE)]}/>
                                <label for="use_freemobile">${_('send SMS notifications?')}</label>
                            </div>
                        </div>

                        <div id="content_use_freemobile">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on snatch')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="freemobile_notify_onsnatch" id="freemobile_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.FREEMOBILE_NOTIFY_ONSNATCH)]}/>
                                    <label for="freemobile_notify_onsnatch">${_('send a SMS when a download starts?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="freemobile_notify_ondownload" id="freemobile_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.FREEMOBILE_NOTIFY_ONDOWNLOAD)]}/>
                                    <label for="freemobile_notify_ondownload">${_('send a SMS when a download finishes?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on subtitle download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="freemobile_notify_onsubtitledownload" id="freemobile_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                    <label for="freemobile_notify_onsubtitledownload">${_('send a SMS when subtitles are downloaded?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Free Mobile customer ID')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="freemobile_id" id="freemobile_id" value="${sickbeard.FREEMOBILE_ID}" class="form-control input-sm input250" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <span class="component-desc">${_('it\'s your Free Mobile customer ID (8 digits)')}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Free Mobile API key')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="freemobile_apikey" id="freemobile_apikey" value="${sickbeard.FREEMOBILE_APIKEY}" class="form-control input-sm input250" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="freemobile_apikey">${_('find your API key in your customer portal.')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <div class="testNotification" id="testFreeMobile-result">${_('Click below to test your settings.')}</div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-12">
                                    <input  class="btn" type="button" value="Test SMS" id="testFreeMobile" />
                                    <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                </div>
                            </div>

                        </div>

                    </fieldset>
                </div>
            </div>

            <div class="config-group-divider"></div>

            <!-- /telegram component-group //-->
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-telegram" title="${_('Telegram')}"></span>
                        <h3><a href="${anon_url('https://telegram.org/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">${_('Telegram')}</a></h3>
                        <p>${_('Telegram is a cloud-based instant messaging service.')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">

                    <fieldset class="component-group-list">

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Enable')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" class="enabler" name="use_telegram" id="use_telegram" ${('', 'checked="checked"')[bool(sickbeard.USE_TELEGRAM)]}/>
                                <label for="use_telegram">${_('send Telegram notifications?')}</label>
                            </div>
                        </div>

                        <div id="content_use_telegram">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on snatch')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="telegram_notify_onsnatch" id="telegram_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.TELEGRAM_NOTIFY_ONSNATCH)]}/>
                                    <label for="telegram_notify_onsnatch">${_('send a message when a download starts?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="telegram_notify_ondownload" id="telegram_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.TELEGRAM_NOTIFY_ONDOWNLOAD)]}/>
                                    <label for="telegram_notify_ondownload">${_('send a message when a download finishes?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on subtitle download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="telegram_notify_onsubtitledownload" id="telegram_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.TELEGRAM_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                    <label for="telegram_notify_onsubtitledownload">${_('send a message when subtitles are downloaded?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('User/group ID')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="telegram_id" id="telegram_id" value="${sickbeard.TELEGRAM_ID}" class="form-control input-sm input250" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="telegram_id">${_('contact @myidbot on Telegram to get an ID')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Bot API token')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="telegram_apikey" id="telegram_apikey" value="${sickbeard.TELEGRAM_APIKEY}" class="form-control input-sm input250" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="telegram_apikey">${_('contact @BotFather on Telegram to set up one')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <div class="testNotification" id="testTelegram-result">${_('Click below to test your settings.')}</div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-12">
                                    <input  class="btn" type="button" value="Test Telegram" id="testTelegram" />
                                    <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                </div>
                            </div>

                        </div>

                    </fieldset>
                </div>
            </div>

            <div class="config-group-divider"></div>

            <!-- /join component-group //-->
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-join" title="${_('Join')}"></span>
                        <h3><a href="${anon_url('http://joaoapps.com/join/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">${_('Join')}</a></h3>
                        <p>${_('Join all of your devices together!')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">

                    <fieldset class="component-group-list">

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Enable')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" class="enabler" name="use_join" id="use_join" ${('', 'checked="checked"')[bool(sickbeard.USE_JOIN)]}/>
                                <label for="use_join">${_('send Join notifications?')}</label>
                            </div>
                        </div>

                        <div id="content_use_join">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on snatch')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="join_notify_onsnatch" id="telegram_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.JOIN_NOTIFY_ONSNATCH)]}/>
                                    <label for="join_notify_onsnatch">${_('send a message when a download starts?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="join_notify_ondownload" id="join_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.JOIN_NOTIFY_ONDOWNLOAD)]}/>
                                    <label for="join_notify_ondownload">${_('send a message when a download finishes?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on subtitle download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="join_notify_onsubtitledownload" id="join_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.JOIN_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                    <label for="join_notify_onsubtitledownload">${_('send a message when subtitles are downloaded?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Device ID')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="join_id" id="join_id" value="${sickbeard.JOIN_ID}" class="form-control input-sm input250" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="join_id">${_('per device specific id')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">

                                    <div class="testNotification" id="testJoin-result">${_('Click below to test your settings.')}</div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-12">
                                    <input  class="btn" type="button" value="Test Join" id="testJoin" />
                                    <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                </div>
                            </div>

                        </div>

                    </fieldset>
                </div>
            </div>

            <div class="config-group-divider"></div>

            <!-- /twilio component-group //-->
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-twilio" title="${_('Twilio')}"></span>
                        <h3><a href="${anon_url('http://www.twilio.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Twilio</a></h3>
                        <p>${_('Twilio is a webservice API that allows you to communicate directly with a mobile number. This notifier will send a text directly to your mobile device.')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                    <fieldset class="component-group-list">

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Enable')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="row">
                                    <div class="col-md-12">
                                        <input type="checkbox" class="enabler" name="use_twilio" id="use_twilio" ${('', 'checked="checked"')[bool(sickbeard.USE_TWILIO)]}/>
                                        <label for="use_twilio">${_('should SickRage text your mobile device?')}</label>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div id="content_use_twilio">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on snatch')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="twilio_notify_onsnatch" id="twilio_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.TWILIO_NOTIFY_ONSNATCH)]}/>
                                    <label for="twilio_notify_onsnatch">${_('send a notification when a download starts?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="twilio_notify_ondownload" id="twilio_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.TWILIO_NOTIFY_ONDOWNLOAD)]}/>
                                    <label for="twilio_notify_ondownload">${_('send a notification when a download finishes?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on subtitle download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="twilio_notify_onsubtitledownload" id="twilio_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.TWILIO_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                    <label for="twilio_notify_onsubtitledownload">${_('send a notification when subtitles are downloaded?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Twilio Account SID')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="twilio_account_sid" id="twilio_account_sid" value="${sickbeard.TWILIO_ACCOUNT_SID}" class="form-control input-sm input300" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="twilio_account_sid">${_('account SID of your Twilio account.')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Twilio Auth Token')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="twilio_auth_token" id="twilio_auth_token" value="${sickbeard.TWILIO_AUTH_TOKEN}" class="form-control input-sm input300" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="twilio_auth_token">${_('account SID of your Twilio account.')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Twilio Phone SID')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="twilio_phone_sid" id="twilio_phone_sid" value="${sickbeard.TWILIO_PHONE_SID}" class="form-control input-sm input300" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="twilio_phone_sid">${_('phone SID that you would like to send the sms from')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Your phone number')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="twilio_to_number" id="twilio_to_number" value="${sickbeard.TWILIO_TO_NUMBER}" class="form-control input-sm input200" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="twilio_to_number">${_('phone number that will receive the sms. Please use the format +1-###-###-####')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <div class="testNotification" id="testTwilio-result">${_('Click below to test.')}</div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <input  class="btn" type="button" value="Test Twilio" id="testTwilio" />
                                    <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                </div>
                            </div>
                        </div>

                    </fieldset>
                </div>
            </div>
        </div>

        <!-- /Social //-->
        <div id="social">

            <!-- /twitter component-group //-->
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-twitter" title="${_('Twitter')}"></span>
                        <h3><a href="${anon_url('http://www.twitter.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Twitter</a></h3>
                        <p>${_('A social networking and microblogging service, enabling its users to send and read other users\' messages called tweets.')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                    <fieldset class="component-group-list">

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Enable')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="row">
                                    <div class="col-md-12">
                                        <input type="checkbox" class="enabler" name="use_twitter" id="use_twitter" ${('', 'checked="checked"')[bool(sickbeard.USE_TWITTER)]}/>
                                        <label for="use_twitter">${_('should SickRage post tweets on Twitter?')}</label>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <label><b>${_('note')}:</b>&nbsp;${_('you may want to use a secondary account.')}</label>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div id="content_use_twitter">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on snatch')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="twitter_notify_onsnatch" id="twitter_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.TWITTER_NOTIFY_ONSNATCH)]}/>
                                    <label for="twitter_notify_onsnatch">${_('send a notification when a download starts?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="twitter_notify_ondownload" id="twitter_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.TWITTER_NOTIFY_ONDOWNLOAD)]}/>
                                    <label for="twitter_notify_ondownload">${_('send a notification when a download finishes?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on subtitle download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="twitter_notify_onsubtitledownload" id="twitter_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                    <label for="twitter_notify_onsubtitledownload">${_('send a notification when subtitles are downloaded?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('send direct message')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="twitter_usedm" id="twitter_usedm" ${('', 'checked="checked"')[bool(sickbeard.TWITTER_USEDM)]}/>
                                    <label for="twitter_usedm">${_('send a notification via Direct Message, not via status update')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('send DM to')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="twitter_dmto" id="twitter_dmto" value="${sickbeard.TWITTER_DMTO}" class="form-control input-sm input250" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="twitter_dmto">${_('Twitter account to send Direct Messages to (must follow you)')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Step One')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input class="btn" type="button" value="${_('Request Authorization')}" id="twitterStep1" />
                                    <label style="font-size: 11px;">${_('Click the "Request Authorization" button.<br> This will open a new page containing an auth key.<br> <b>note:</b> if nothing happens check your popup blocker.')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Step Two')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <span style="font-size: 11px;">${_('Enter the key Twitter gave you below, and click "Verify Key".')}</span>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" id="twitter_key" value="" class="form-control input-sm input350" autocapitalize="off" />
                                            <input class="btn btn-inline" type="button" value="Verify Key" id="twitterStep2" />
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <div class="testNotification" id="testTwitter-result">${_('Click below to test.')}</div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <input  class="btn" type="button" value="Test Twitter" id="testTwitter" />
                                    <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                </div>
                            </div>
                        </div>

                    </fieldset>
                </div>
            </div>

            <div class="config-group-divider"></div>

            <!-- /trakt component-group //-->
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-trakt" title="${_('Trakt')}"></span>
                        <h3><a href="${anon_url('http://trakt.tv/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Trakt</a></h3>
                        <p>${_('Trakt helps keep a record of what TV shows and movies you are watching. Based on your favorites, Trakt recommends additional shows and movies you\'ll enjoy!')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                    <fieldset class="component-group-list">

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Enable')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" class="enabler" name="use_trakt" id="use_trakt" ${('', 'checked="checked"')[bool(sickbeard.USE_TRAKT)]}/>
                                <label for="use_trakt">${_('send Trakt.tv notifications?')}</label>
                            </div>
                        </div>

                        <div id="content_use_trakt">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Username')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="trakt_username" id="trakt_username" value="${sickbeard.TRAKT_USERNAME}" class="form-control input-sm input250" autocapitalize="off" autocomplete="no" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="trakt_username">${_('username of your Trakt account.')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Trakt PIN')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="hidden" id="trakt_pin_url" value="${sickbeard.TRAKT_PIN_URL}">
                                            <input type="button" class="btn ${('', 'hide')[bool(sickbeard.TRAKT_ACCESS_TOKEN)]}" value="${_('Get Trakt PIN')}" id="TraktGetPin" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="trakt_pin" id="trakt_pin" value="" class="form-control input-sm input250" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="trakt_pin">${_('PIN code to authorize SickRage to access Trakt on your behalf.')}</label>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="button" class="btn hide" value="Authorize SickRage" id="authTrakt" />
                                        </div>
                                    </div>
                                </div>
                            </div>


                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('API Timeout')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="number" min="10" step="1" name="trakt_timeout" id="trakt_timeout" value="${sickbeard.TRAKT_TIMEOUT}" class="form-control input-sm input75" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="trakt_timeout">${_('seconds to wait for Trakt API to respond. (Use 0 to wait forever)')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Default indexer')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <select id="trakt_default_indexer" name="trakt_default_indexer" class="form-control input-sm input250" title="trakt_default_indexer">
                                        % for indexer in sickbeard.indexerApi().indexers:
                                            <option value="${indexer}" ${('', 'selected="selected"')[sickbeard.TRAKT_DEFAULT_INDEXER == indexer]}>${sickbeard.indexerApi().indexers[indexer]}</option>
                                        % endfor
                                    </select>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Sync libraries')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" class="enabler" name="trakt_sync" id="trakt_sync" ${('', 'checked="checked"')[bool(sickbeard.TRAKT_SYNC)]}/>
                                    <label for="trakt_sync">${_('sync your SickRage show library with your trakt show library.')}</label>
                                </div>
                            </div>

                            <div id="content_trakt_sync">

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Remove Episodes From Collection')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="trakt_sync_remove" id="trakt_sync_remove" ${('', 'checked="checked"')[bool(sickbeard.TRAKT_SYNC_REMOVE)]}/>
                                        <label for="trakt_sync_remove">${_('remove an episode from your Trakt Collection if it is not in your SickRage Library.')}</label>
                                    </div>
                                </div>

                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Sync watchlist')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="checkbox" class="enabler" name="trakt_sync_watchlist" id="trakt_sync_watchlist" ${('', 'checked="checked"')[bool(sickbeard.TRAKT_SYNC_WATCHLIST)]}/>
                                            <label for="trakt_sync_watchlist">${_('sync your SickRage show watchlist with your trakt show watchlist (either Show and Episode).')}</label>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label>${_('episode will be added on watch list when wanted or snatched and will be removed when downloaded ')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div id="content_trakt_sync_watchlist">

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Watchlist add method')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <select id="trakt_method_add" name="trakt_method_add" class="form-control input-sm input250">
                                                    <option value="0" ${('', 'selected="selected"')[sickbeard.TRAKT_METHOD_ADD == 0]}>${_('Skip All')}</option>
                                                    <option value="1" ${('', 'selected="selected"')[sickbeard.TRAKT_METHOD_ADD == 1]}>${_('Download Pilot Only')}</option>
                                                    <option value="2" ${('', 'selected="selected"')[sickbeard.TRAKT_METHOD_ADD == 2]}>${_('Get whole show')}</option>
                                                </select>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="trakt_method_add">${_('method in which to download episodes for new shows.')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Remove episode')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="trakt_remove_watchlist" id="trakt_remove_watchlist" ${('', 'checked="checked"')[bool(sickbeard.TRAKT_REMOVE_WATCHLIST)]}/>
                                        <label for="trakt_remove_watchlist">${_('remove an episode from your watchlist after it is downloaded.')}</label>
                                    </div>
                                </div>

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Remove series')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="trakt_remove_serieslist" id="trakt_remove_serieslist" ${('', 'checked="checked"')[bool(sickbeard.TRAKT_REMOVE_SERIESLIST)]}/>
                                        <label for="trakt_remove_serieslist">${_('remove the whole series from your watchlist after any download.')}</label>
                                    </div>
                                </div>

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Remove watched show')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="trakt_remove_show_from_sickrage" id="trakt_remove_show_from_sickrage" ${('', 'checked="checked"')[bool(sickbeard.TRAKT_REMOVE_SHOW_FROM_SICKRAGE)]}/>
                                        <label for="trakt_remove_show_from_sickrage">${_('remove the show from sickrage if it\'s ended and completely watched')}</label>
                                    </div>
                                </div>

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Start paused')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="trakt_start_paused" id="trakt_start_paused" ${('', 'checked="checked"')[bool(sickbeard.TRAKT_START_PAUSED)]}/>
                                        <label for="trakt_start_paused">${_('shows grabbed from your trakt watchlist start paused.')}</label>
                                    </div>
                                </div>

                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Trakt blackList name')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="trakt_blacklist_name" id="trakt_blacklist_name" value="${sickbeard.TRAKT_BLACKLIST_NAME}" class="form-control input-sm input250" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="trakt_blacklist_name">${_('name (slug) of list on Trakt for blacklisting show on \'Add Trending Show\' & \'Add Recommended Shows\' pages')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <div class="testNotification" id="testTrakt-result">${_('Click below to test.')}</div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <input type="button" class="btn" value="Test Trakt" id="testTrakt" />
                                    <input type="submit" class="btn config_submitter" value="${_('Save Changes')}" />
                                </div>
                            </div>
                        </div>
                    </fieldset>
                </div>
            </div>

            <div class="config-group-divider"></div>

            <!-- /email component-group //-->
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-email" title="${_('Email')}"></span>
                        <h3><a href="${anon_url('http://en.wikipedia.org/wiki/Comparison_of_webmail_providers')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Email</a></h3>
                        <p>${_('Allows configuration of email notifications on a per show basis.')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                    <fieldset class="component-group-list">
                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Enable')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <input type="checkbox" class="enabler" name="use_email" id="use_email" ${('', 'checked="checked"')[bool(sickbeard.USE_EMAIL)]}/>
                                <label for="use_email">${_('send email notifications?')}</label>
                            </div>
                        </div>

                        <div id="content_use_email">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on snatch')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="email_notify_onsnatch" id="email_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.EMAIL_NOTIFY_ONSNATCH)]}/>
                                    <label for="email_notify_ondownload">${_('send a notification when a download starts?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="email_notify_ondownload" id="email_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.EMAIL_NOTIFY_ONDOWNLOAD)]}/>
                                    <label for="email_notify_ondownload">${_('send a notification when a download finishes?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on subtitle download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="email_notify_onsubtitledownload" id="email_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                    <label for="email_notify_onsubtitledownload">${_('send a notification when subtitles are downloaded?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('SMTP host')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="email_host" id="email_host" value="${sickbeard.EMAIL_HOST}" class="form-control input-sm input250" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="email_host">${_('hostname of your SMTP email server.')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('SMTP port')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="number" min="1" step="1" name="email_port" id="email_port" value="${sickbeard.EMAIL_PORT}" class="form-control input-sm input75" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="email_port">${_('port number used to connect to your SMTP host.')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('SMTP from')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="email_from" id="email_from" value="${sickbeard.EMAIL_FROM}" class="form-control input-sm input250" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="email_from">${_('sender email address, some hosts require a real address.')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Use TLS')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="email_tls" id="email_tls" ${('', 'checked="checked"')[bool(sickbeard.EMAIL_TLS)]}/>
                                    <label for="email_tls">${_('check to use TLS encryption.')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('SMTP user')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="email_user" id="email_user" value="${sickbeard.EMAIL_USER}" class="form-control input-sm input250" autocapitalize="off" autocomplete="no" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="email_user">${_('(optional) your SMTP server username.')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('SMTP password')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="password" name="email_password" id="email_password" value="${sickbeard.EMAIL_PASSWORD}" class="form-control input-sm input250" autocomplete="no" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="email_password">${_('(optional) your SMTP server password.')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Global email list')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="email_list" id="email_list" value="${sickbeard.EMAIL_LIST}" class="form-control input-sm input350" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="email_list">${_('email addresses listed here, separated by commas if applicable, will<br> receive notifications for <b>all</b> shows.')}<br>${_('(This field may be blank except when testing.)')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Email Subject')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="email_subject" id="email_subject" value="${sickbeard.EMAIL_SUBJECT}" class="form-control input-sm input350" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="email_subject">
                                                ${_('use a custom subject for some privacy protection?')}<br>
                                                ${_('(leave blank for the default SickRage subject)')}
                                            </label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Show notification list')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <select name="email_show" id="email_show" class="form-control input-sm input350" title="Email show">
                                                <option value="-1">${_('-- Select a Show --')}</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="email_show_list" id="email_show_list" class="form-control input-sm input350" autocapitalize="off" />
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="email_show_list">
                                                ${_('configure per-show notifications here by entering email address(es), separated by commas,')}
                                                ${_('after selecting a show in the drop-down box.  Be sure to activate the \'Save for this show\'')}
                                                ${_('button below after each entry.')}
                                            </label>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input id="email_show_save" class="btn" type="button" value="${_('Save for this show')}"/>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <div class="testNotification" id="testEmail-result">${_('Click below to test.')}</div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <input class="btn" type="button" value="Test Email" id="testEmail" />
                                    <input class="btn config_submitter" type="submit" value="${_('Save Changes')}" />
                                </div>
                            </div>

                        </div>
                    </fieldset>
                </div>
            </div>

            <div class="config-group-divider"></div>

            <!-- /slack component-group //-->
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-slack" title="${_('Slack')}"></span>
                        <h3><a href="${anon_url('http://www.slack.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Slack</a></h3>
                        <p>${_('Slack brings all your communication together in one place. It\'s real-time messaging, archiving and search for modern teams.')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                    <fieldset class="component-group-list">

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Enable')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="row">
                                    <div class="col-md-12">
                                        <input type="checkbox" class="enabler" name="use_slack" id="use_slack" ${('', 'checked="checked"')[bool(sickbeard.USE_SLACK)]}/>
                                        <label for="use_slack">${_('should SickRage post messages on Slack?')}</label>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div id="content_use_slack">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on snatch')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="slack_notify_snatch" id="slack_notify_snatch" ${('', 'checked="checked"')[bool(sickbeard.SLACK_NOTIFY_SNATCH)]}/>
                                    <label for="slack_notify_snatch">${_('send a notification when a download starts?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="slack_notify_download" id="slack_notify_download" ${('', 'checked="checked"')[bool(sickbeard.SLACK_NOTIFY_DOWNLOAD)]}/>
                                    <label for="slack_notify_download">${_('send a notification when a download finishes?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Slack Incoming Webhook')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="text" name="slack_webhook" id="slack_webhook" value="${sickbeard.SLACK_WEBHOOK}" class="form-control input-sm input350" autocapitalize="off" />
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <div class="testNotification" id="testSlack-result">${_('Click below to test.')}</div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <input  class="btn" type="button" value="Test Slack" id="testSlack" />
                                    <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                </div>
                            </div>
                        </div>

                    </fieldset>
                </div>
            </div>

            <div class="config-group-divider"></div>

            <!-- /Discord component-group //-->
            <div class="row">
                <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-discord" title="${_('Discord')}"></span>
                        <h3><a href="${anon_url('https://discordapp.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Discord</a></h3>
                        <p>${_('All-in-one voice and text chat for gammers that\'s free, secure, and works on both your desktop and phone.')}</p>
                    </div>
                </div>
                <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                    <fieldset class="component-group-list">

                        <div class="field-pair row">
                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                <label class="component-title">${_('Enable')}</label>
                            </div>
                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                <div class="row">
                                    <div class="col-md-12">
                                        <input type="checkbox" class="enabler" name="use_discord" id="use_discord" ${('', 'checked="checked"')[bool(sickbeard.USE_DISCORD)]}/>
                                        <label for="use_discord">${_('Should SickRage post messages on Discord?')}</label>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div id="content_use_discord">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on snatch')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="discord_notify_snatch" id="discord_notify_snatch" ${('', 'checked="checked"')[bool(sickbeard.DISCORD_NOTIFY_SNATCH)]}/>
                                    <label for="discord_notify_snatch">${_('send a notification when a download starts?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Notify on download')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="discord_notify_download" id="discord_notify_download" ${('', 'checked="checked"')[bool(sickbeard.DISCORD_NOTIFY_DOWNLOAD)]}/>
                                    <label for="discord_notify_download">${_('send a notification when a download finishes?')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Discord Incoming Webhook')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                  <div class="row">
                                    <div class="col-md-12">
                                      <input type="text" name="discord_webhook" id="discord_webhook" value="${sickbeard.DISCORD_WEBHOOK}" class="form-control input-sm input350" autocapitalize="off" />
                                    </div>
                                    <div class="col-md-12">
                                      <label for="discord_webhook">${_('Create webhook under channel settings.')}</label>
                                    </div>
                                  </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Discord Bot Name')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                  <div class="row">
                                    <div class="col-md-12">
                                      <input type="text" name="discord_name" id="discord_name" value="${sickbeard.DISCORD_NAME}" class="form-control input-sm input350" autocapitalize="off" />
                                    </div>
                                    <div class="col-md-12">
                                      <label for="discord_name">${_('Blank will use webhook default Name.')}</label>
                                    </div>
                                  </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Discord Avatar URL')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                  <div class="row">
                                    <div class="col-md-12">
                                      <input type="text" name="discord_avatar_url" id="discord_avatar_url" value="${sickbeard.DISCORD_AVATAR_URL}" class="form-control input-sm input350" autocapitalize="off" />
                                    </div>
                                    <div class="col-md-12">
                                      <label for="discord_avatar_url">${_('Blank will use webhook default Avatar.')}</label>
                                    </div>
                                  </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Discord TTS')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="discord_tts" id="discord_tts" ${('', 'checked="checked"')[bool(sickbeard.DISCORD_TTS)]}/>
                                    <label for="discord_tts">${_('Send notifications using text-to-speech')}</label>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <div class="testNotification" id="testDiscord-result">${_('Click below to test.')}</div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-12">
                                    <input  class="btn" type="button" value="Test Discord" id="testDiscord" />
                                    <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                </div>
                            </div>
                        </div>

                    </fieldset>
                </div>
            </div>

            <!-- end component groups -->
        </div>

    </form>
</%block>
