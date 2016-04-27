<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    import re
    from sickbeard.helpers import anon_url
%>
<%block name="content">
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif

<div id="config">
    <div id="config-content">
        <form id="configForm" action="saveNotifications" method="post">
            <div id="config-components">
                <ul>
                    <li><a href="#tabs-1">${_('Home Theater / NAS')}</a></li>
                    <li><a href="#tabs-2">${_('Devices')}</a></li>
                    <li><a href="#tabs-3">${_('Social')}</a></li>
                </ul>

                <div id="tabs-1">
                <div class="component-group">

                    <div class="component-group-desc">
                        <span class="icon-notifiers-kodi" title="KODI"></span>
                        <h3><a href="${anon_url('http://kodi.tv/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">KODI</a></h3>
                        <p>${_('A free and open source cross-platform media center and home entertainment system software with a 10-foot user interface designed for the living-room TV.')}</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label class="clearfix" for="use_kodi">
                                <span class="component-title">${_('Enable')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_kodi" id="use_kodi" ${('', 'checked="checked"')[bool(sickbeard.USE_KODI)]}/>
                                    <p>${_('Send KODI commands?')}<p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_kodi">
                            <div class="field-pair">
                                <label for="kodi_always_on">
                                    <span class="component-title">${_('Always on')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="kodi_always_on" id="kodi_always_on" ${('', 'checked="checked"')[bool(sickbeard.KODI_ALWAYS_ON)]}/>
                                        <p>${_('log errors when unreachable?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="kodi_notify_onsnatch">
                                    <span class="component-title">${_('Notify on snatch')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="kodi_notify_onsnatch" id="kodi_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.KODI_NOTIFY_ONSNATCH)]}/>
                                        <p>${_('send a notification when a download starts?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="kodi_notify_ondownload">
                                    <span class="component-title">${_('Notify on download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="kodi_notify_ondownload" id="kodi_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.KODI_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>${_('send a notification when a download finishes?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="kodi_notify_onsubtitledownload">
                                    <span class="component-title">${_('Notify on subtitle download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="kodi_notify_onsubtitledownload" id="kodi_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.KODI_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>${_('send a notification when subtitles are downloaded?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="kodi_update_library">
                                    <span class="component-title">${_('Update library')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="kodi_update_library" id="kodi_update_library" ${('', 'checked="checked"')[bool(sickbeard.KODI_UPDATE_LIBRARY)]}/>
                                        <p>${_('update KODI library when a download finishes?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="kodi_update_full">
                                    <span class="component-title">${_('Full library update')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="kodi_update_full" id="kodi_update_full" ${('', 'checked="checked"')[bool(sickbeard.KODI_UPDATE_FULL)]}/>
                                        <p>${_('perform a full library update if update per-show fails?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="kodi_update_onlyfirst">
                                    <span class="component-title">${_('Only update first host')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="kodi_update_onlyfirst" id="kodi_update_onlyfirst" ${('', 'checked="checked"')[bool(sickbeard.KODI_UPDATE_ONLYFIRST)]}/>
                                        <p>${_('only send library updates to the first active host?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="kodi_host">
                                    <span class="component-title">${_('KODI IP:Port')}</span>
                                    <input type="text" name="kodi_host" id="kodi_host" value="${sickbeard.KODI_HOST}" class="form-control input-sm input350" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('host running KODI (eg. 192.168.1.100:8080)')}</span>
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('(multiple host strings must be separated by commas)')}</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="kodi_username">
                                    <span class="component-title">${_('Username')}</span>
                                    <input type="text" name="kodi_username" id="kodi_username" value="${sickbeard.KODI_USERNAME}" class="form-control input-sm input250" autocapitalize="off" autocomplete="no" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('username for your KODI server (blank for none)')}</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="kodi_password">
                                    <span class="component-title">${_('Password')}</span>
                                    <input type="password" name="kodi_password" id="kodi_password" value="${sickbeard.KODI_PASSWORD}" class="form-control input-sm input250" autocomplete="no" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('password for your KODI server (blank for none)')}</span>
                                </label>
                            </div>
                            <div class="testNotification" id="testKODI-result">${_('Click below to test.')}</div>
                            <input  class="btn" type="button" value="Test KODI" id="testKODI" />
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                        </div><!-- /content_use_kodi //-->

                    </fieldset>

                </div><!-- /kodi component-group //-->

                <div class="component-group">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-plex" title="Plex Media Server"></span>
                        <h3><a href="${anon_url('http://www.plexapp.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Plex Media Server</a></h3>
                        <p>${_('Experience your media on a visually stunning, easy to use interface on your Mac connected to your TV. Your media library has never looked this good!')}</p>
                        <p class="plexinfo hide">${_('For sending notifications to Plex Home Theater (PHT) clients, use the KODI notifier with port <b>3005</b>.')}</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_plex_server">
                                <span class="component-title">${_('Enable')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_plex_server" id="use_plex_server" ${('', 'checked="checked"')[bool(sickbeard.USE_PLEX_SERVER)]}/>
                                    <p>${_('Send Plex Media Server library updates?')}</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_plex_server">
                            <div class="field-pair">
                                <label for="plex_server_token">
                                    <span class="component-title">${_('Plex Media Server Auth Token')}</span>
                                    <input type="text" name="plex_server_token" id="plex_server_token" value="${sickbeard.PLEX_SERVER_TOKEN}" class="form-control input-sm input250" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('Auth Token used by plex')}</span>
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">(<a href="${anon_url('https://support.plex.tv/hc/en-us/articles/204059436-Finding-your-account-token-X-Plex-Token')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;"><u>Finding your account token</u></a>)</span>
                                </label>
                            </div>
                            <div class="component-group" style="padding: 0; min-height: 130px">
                                <div class="field-pair">
                                    <label for="plex_server_username">
                                        <span class="component-title">${_('Username')}</span>
                                        <span class="component-desc">
                                            <input type="text" name="plex_server_username" id="plex_server_username" value="${sickbeard.PLEX_SERVER_USERNAME}" class="form-control input-sm input250" autocapitalize="off" autocomplete="no" />
                                            <p>${_('blank = no authentication')}</p>
                                        </span>
                                    </label>
                                </div>
                                <div class="field-pair">
                                    <label for="plex_server_password">
                                        <span class="component-title">${_('Password')}</span>
                                        <span class="component-desc">
                                            <input type="password" name="plex_server_password" id="plex_server_password" value="${'*' * len(sickbeard.PLEX_SERVER_PASSWORD)}" class="form-control input-sm input250" autocomplete="no" autocapitalize="off" />
                                            <p>${_('blank = no authentication')}</p>
                                        </span>
                                    </label>
                                </div>
                            </div>
                            <div class="component-group" style="padding: 0; min-height: 50px">
                                <div class="field-pair">
                                    <label for="plex_update_library">
                                        <span class="component-title">${_('Update Library')}</span>
                                        <span class="component-desc">
                                            <input type="checkbox" class="enabler" name="plex_update_library" id="plex_update_library" ${('', 'checked="checked"')[bool(sickbeard.PLEX_UPDATE_LIBRARY)]}/>
                                            <p>${_('update Plex Media Server library when a download finishes')}</p>
                                        </span>
                                    </label>
                                </div>
                                <div id="content_plex_update_library">
                                    <div class="field-pair">
                                        <label for="plex_server_host">
                                            <span class="component-title">${_('Plex Media Server IP:Port')}</span>
                                            <span class="component-desc">
                                                <input type="text" name="plex_server_host" id="plex_server_host" value="${re.sub(r'\b,\b', ', ', sickbeard.PLEX_SERVER_HOST)}" class="form-control input-sm input350" autocapitalize="off" />
                                                <div class="clear-left">
                                                    <p>${_('one or more hosts running Plex Media Server<br>(eg. 192.168.1.1:32400, 192.168.1.2:32400)')}</p>
                                                </div>
                                            </span>
                                        </label>
                                    </div>
                                    <div class="field-pair">
                                        <label for="plex_server_https">
                                            <span class="component-title">${_('HTTPS')}</span>
                                            <span class="component-desc">
                                                <input type="checkbox" name="plex_server_https" id="plex_server_https" ${('', 'checked="checked"')[bool(sickbeard.PLEX_SERVER_HTTPS)]}/>
                                                <p>${_('use https for plex media server requests?')}</p>
                                            </span>
                                        </label>
                                    </div>
                                    <div class="field-pair">
                                        <div class="testNotification" id="testPMS-result">${_('Click below to test Plex Media Server(s)')}</div>
                                        <input class="btn" type="button" value="${_('Test Plex Media Server')}" id="testPMS" />
                                        <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                        <div class="clear-left">&nbsp;</div>
                                    </div>
                                </div>
                            </div>
                        </div><!-- /content_use_plex_server -->
                    </fieldset>
                </div><!-- /plex media server component-group -->

                <div class="component-group">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-plexth" title="${_('Plex Home Theater')}"></span>
                        <h3><a href="${anon_url('http://www.plexapp.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Plex Home Theater</a></h3>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_plex_client">
                                <span class="component-title">${_('Enable')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_plex_client" id="use_plex_client" ${('', 'checked="checked"')[bool(sickbeard.USE_PLEX_CLIENT)]}/>
                                    <p>${_('Send Plex Home Theater notifications?')}</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_plex_client">
                            <div class="field-pair">
                                <label for="plex_notify_onsnatch">
                                    <span class="component-title">${_('Notify on snatch')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="plex_notify_onsnatch" id="plex_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.PLEX_NOTIFY_ONSNATCH)]}/>
                                        <p>${_('send a notification when a download starts?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="plex_notify_ondownload">
                                    <span class="component-title">${_('Notify on download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="plex_notify_ondownload" id="plex_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.PLEX_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>${_('send a notification when a download finishes?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="plex_notify_onsubtitledownload">
                                    <span class="component-title">${_('Notify on subtitle download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="plex_notify_onsubtitledownload" id="plex_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>${_('send a notification when subtitles are downloaded?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="plex_client_host">
                                    <span class="component-title">${_('Plex Home Theater IP:Port')}</span>
                                    <span class="component-desc">
                                        <input type="text" name="plex_client_host" id="plex_client_host" value="${sickbeard.PLEX_CLIENT_HOST}" class="form-control input-sm input350" autocapitalize="off" />
                                        <div class="clear-left">
                                            <p>${_('one or more hosts running Plex Home Theater<br>(eg. 192.168.1.100:3000, 192.168.1.101:3000)')}</p>
                                        </div>
                                    </span>
                                </label>
                            </div>
                            <div class="component-group" style="padding: 0; min-height: 130px">
                                <div class="field-pair">
                                    <label for="plex_server_username">
                                        <span class="component-title">${_('Username')}</span>
                                        <span class="component-desc">
                                            <input type="text" name="plex_client_username" id="plex_client_username" value="${sickbeard.PLEX_CLIENT_USERNAME}" class="form-control input-sm input250" autocapitalize="off" autocomplete="no" />
                                            <p>${_('blank = no authentication')}</p>
                                        </span>
                                    </label>
                                </div>
                                <div class="field-pair">
                                    <label for="plex_client_password">
                                        <span class="component-title">${_('Password')}</span>
                                        <span class="component-desc">
                                            <input type="password" name="plex_client_password" id="plex_client_password" value="${'*' * len(sickbeard.PLEX_CLIENT_PASSWORD)}" class="form-control input-sm input250" autocomplete="no" autocapitalize="off" />
                                            <p>${_('blank = no authentication')}</p>
                                        </span>
                                    </label>
                                </div>
                            </div>

                            <div class="field-pair">
                                <div class="testNotification" id="testPHT-result">${_('Click below to test Plex Home Theater(s)')}</div>
                                <input class="btn" type="button" value="${_('Test Plex Home Theater')}" id="testPHT" />
                                <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                <div class=clear-left><p>${_('Note: some Plex Home Theaters <b class="boldest">do not</b> support notifications e.g. Plexapp for Samsung TVs')}</p></div>
                            </div>
                        </div><!-- /content_use_plex_client -->
                    </fieldset>
                </div><!-- /Plex Home Theater component-group -->


                 <div class="component-group">
                     <div class="component-group-desc">
                        <span class="icon-notifiers-emby" alt="" title="${_('Emby')}"></span>
                        <h3><a href="${anon_url('http://emby.media/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Emby</a></h3>
                        <p>${_('A home media server built using other popular open source technologies.')}</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_emby">
                                <span class="component-title">${_('Enable')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_emby" id="use_emby" ${('', 'checked="checked"')[bool(sickbeard.USE_EMBY)]} />
                                    <p>${_('Send update commands to Emby?')}<p>
                                </span>
                            </label>
                        </div>
                        <div id="content_use_emby">
                            <div class="field-pair">
                                <label for="emby_host">
                                    <span class="component-title">${_('Emby IP:Port')}</span>
                                    <input type="text" name="emby_host" id="emby_host" value="${sickbeard.EMBY_HOST}" class="form-control input-sm input250" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('host running Emby (eg. 192.168.1.100:8096)')}</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="emby_apikey">
                                    <span class="component-title">${_('Emby API Key')}</span>
                                    <input type="text" name="emby_apikey" id="emby_apikey" value="${sickbeard.EMBY_APIKEY}" class="form-control input-sm input250" autocapitalize="off" />
                                </label>
                            </div>
                            <div class="testNotification" id="testEMBY-result">${_('Click below to test.')}</div>
                                <input  class="btn" type="button" value="Test Emby" id="testEMBY" />
                                <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                            </div>
                        <!-- /content_use_emby //-->
                    </fieldset>
                </div><!-- /emby component-group //-->


                <div class="component-group">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-nmj" alt="" title="${_('Networked Media Jukebox')}"></span>
                        <h3><a href="${anon_url('http://www.popcornhour.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">NMJ</a></h3>
                        <p>${_('The Networked Media Jukebox, or NMJ, is the official media jukebox interface made available for the Popcorn Hour 200-series.')}</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_nmj">
                                <span class="component-title">${_('Enable')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_nmj" id="use_nmj" ${('', 'checked="checked"')[bool(sickbeard.USE_NMJ)]}/>
                                    <p>${_('Send update commands to NMJ?')}</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_nmj">
                            <div class="field-pair">
                                <label for="nmj_host">
                                    <span class="component-title">${_('Popcorn IP address')}</span>
                                    <input type="text" name="nmj_host" id="nmj_host" value="${sickbeard.NMJ_HOST}" class="form-control input-sm input250" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('IP address of Popcorn 200-series (eg. 192.168.1.100)')}</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label>
                                    <span class="component-title">${_('Get settings')}</span>
                                    <input class="btn btn-inline" type="button" value="${_('Get Settings')}" id="settingsNMJ" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('the Popcorn Hour device must be powered on and NMJ running.')}</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="nmj_database">
                                    <span class="component-title">${_('NMJ database')}</span>
                                    <input type="text" name="nmj_database" id="nmj_database" value="${sickbeard.NMJ_DATABASE}" class="form-control input-sm input250" ${(' readonly="readonly"', '')[sickbeard.NMJ_DATABASE is True]} autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('automatically filled via the \'Get Settings\' button.')}</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="nmj_mount">
                                    <span class="component-title">${_('NMJ mount url')}</span>
                                    <input type="text" name="nmj_mount" id="nmj_mount" value="${sickbeard.NMJ_MOUNT}" class="form-control input-sm input250" ${(' readonly="readonly"', '')[sickbeard.NMJ_MOUNT is True]} autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('automatically filled via the \'Get Settings\' button.')}</span>
                                </label>
                            </div>
                            <div class="testNotification" id="testNMJ-result">${_('Click below to test.')}</div>
                            <input class="btn" type="button" value="Test NMJ" id="testNMJ" />
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                        </div><!-- /content_use_nmj //-->

                    </fieldset>
                </div><!-- /nmj component-group //-->

                <div class="component-group">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-nmj" alt="" title="${_('Networked Media Jukebox v2')}"></span>
                        <h3><a href="${anon_url('http://www.popcornhour.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">NMJv2</a></h3>
                        <p>${_('The Networked Media Jukebox, or NMJv2, is the official media jukebox interface made available for the Popcorn Hour 300 & 400-series.')}</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_nmjv2">
                                <span class="component-title">${_('Enable')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_nmjv2" id="use_nmjv2" ${('', 'checked="checked"')[bool(sickbeard.USE_NMJv2)]}/>
                                    <p>${_('Send update commands to NMJv2?')}</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_nmjv2">
                            <div class="field-pair">
                                <label for="nmjv2_host">
                                    <span class="component-title">${_('Popcorn IP address')}</span>
                                    <input type="text" name="nmjv2_host" id="nmjv2_host" value="${sickbeard.NMJv2_HOST}" class="form-control input-sm input250" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('IP address of Popcorn 300/400-series (eg. 192.168.1.100)')}</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <span class="component-title">${_('Database location')}</span>
                                <span class="component-desc">
                                    <label for="NMJV2_DBLOC_A" class="space-right">
                                        <input type="radio" NAME="nmjv2_dbloc" VALUE="local" id="NMJV2_DBLOC_A" ${('', 'checked="checked"')[sickbeard.NMJv2_DBLOC == 'local']}/>PCH Local Media
                                    </label>
                                    <label for="NMJV2_DBLOC_B">
                                        <input type="radio" NAME="nmjv2_dbloc" VALUE="network" id="NMJV2_DBLOC_B" ${('', 'checked="checked"')[sickbeard.NMJv2_DBLOC == 'network']}/>PCH Network Media
                                    </label>
                                </span>
                            </div>
                            <div class="field-pair">
                                <label for="NMJv2db_instance">
                                    <span class="component-title">${_('Database instance')}</span>
                                    <span class="component-desc">
                                    <select id="NMJv2db_instance" class="form-control input-sm">
                                        <option value="0">#1 </option>
                                        <option value="1">#2 </option>
                                        <option value="2">#3 </option>
                                        <option value="3">#4 </option>
                                        <option value="4">#5 </option>
                                        <option value="5">#6 </option>
                                        <option value="6">#7 </option>
                                    </select>
                                    </span>
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('adjust this value if the wrong database is selected.')}</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="settingsNMJv2">
                                    <span class="component-title">${_('Find database')}</span>
                                    <input type="button" class="btn btn-inline" value="${_('Find Database')}" id="settingsNMJv2" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('the Popcorn Hour device must be powered on.')}</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="nmjv2_database">
                                    <span class="component-title">${_('NMJv2 database')}</span>
                                    <input type="text" name="nmjv2_database" id="nmjv2_database" value="${sickbeard.NMJv2_DATABASE}" class="form-control input-sm input250" ${(' readonly="readonly"', '')[sickbeard.NMJv2_DATABASE is True]} autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('automatically filled via the \'Find Database\' buttons.')}</span>
                                </label>
                            </div>
                        <div class="testNotification" id="testNMJv2-result">Click below to test.</div>
                        <input class="btn" type="button" value="Test NMJv2" id="testNMJv2" />
                        <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                        </div><!-- /content_use_nmjv2 //-->

                    </fieldset>
                </div><!-- /nmjv2 component-group //-->


                <div class="component-group">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-syno1" alt="" title="${_('Synology')}"></span>
                        <h3><a href="${anon_url('http://synology.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Synology</a></h3>
                        <p>${_('The Synology DiskStation NAS.')}</p>
                        <p>${_('Synology Indexer is the daemon running on the Synology NAS to build its media database.')}</p>
                    </div>

                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_synoindex">
                                <span class="component-title">${_('Enable')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_synoindex" id="use_synoindex" ${('', 'checked="checked"')[bool(sickbeard.USE_SYNOINDEX)]}/>
                                    <p>${_('Send Synology notifications?')}</p>
                                </span>
                            </label>
                            <label>
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc"><b>${_('Note')}:</b> ${_('requires SickRage to be running on your Synology NAS.')}</span>
                            </label>
                        </div>

                        <div id="content_use_synoindex">
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                        </div><!-- /content_use_synoindex //-->

                    </fieldset>
                </div><!-- /synoindex component-group //-->


                <div class="component-group">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-syno2" alt="" title="${_('Synology Indexer')}"></span>
                        <h3><a href="${anon_url('http://synology.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Synology Notifier</a></h3>
                        <p>${_('Synology Notifier is the notification system of Synology DSM')}</p>
                    </div>

                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_synologynotifier">
                                <span class="component-title">${_('Enable')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_synologynotifier" id="use_synologynotifier" ${('', 'checked="checked"')[bool(sickbeard.USE_SYNOLOGYNOTIFIER)]}/>
                                    <p>${_('Send notifications to the Synology Notifier?')}</p>
                                </span>
                            </label>
                            <label>
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc"><b>${_('Note')}:</b> ${_('requires SickRage to be running on your Synology DSM.')}</span>
                            </label>
                           </div>
                        <div id="content_use_synologynotifier">
                            <div class="field-pair">
                                <label for="synologynotifier_notify_onsnatch">
                                    <span class="component-title">${_('Notify on snatch')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="synologynotifier_notify_onsnatch" id="synologynotifier_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH)]}/>
                                        <p>${_('send a notification when a download starts?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="synologynotifier_notify_ondownload">
                                    <span class="component-title">${_('Notify on download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="synologynotifier_notify_ondownload" id="synologynotifier_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>${_('send a notification when a download finishes?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="synologynotifier_notify_onsubtitledownload">
                                    <span class="component-title">${_('Notify on subtitle download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="synologynotifier_notify_onsubtitledownload" id="synologynotifier_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>${_('send a notification when subtitles are downloaded?')}</p>
                                    </span>
                                </label>
                            </div>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                           </div>
                    </fieldset>
                </div><!-- /synology notifier component-group //-->


                <div class="component-group">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-pytivo" alt="" title="${_('pyTivo')}"></span>
                        <h3><a href="${anon_url('http://pytivo.sourceforge.net/wiki/index.php/PyTivo')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">pyTivo</a></h3>
                        <p>${_('pyTivo is both an HMO and GoBack server. This notifier will load the completed downloads to your Tivo.')}</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_pytivo">
                                <span class="component-title">${_('Enable')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_pytivo" id="use_pytivo" ${('', 'checked="checked"')[bool(sickbeard.USE_PYTIVO)]}/>
                                    <p>${_('Send notifications to pyTivo?')}</p>
                                </span>
                            </label>
                            <label>
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc"><b>${_('Note')}:</b> ${_('requires the downloaded files to be accessible by pyTivo.')}</span>
                            </label>
                        </div>

                        <div id="content_use_pytivo">
                            <div class="field-pair">
                                <label for="pytivo_host">
                                    <span class="component-title">${_('pyTivo IP:Port')}</span>
                                    <input type="text" name="pytivo_host" id="pytivo_host" value="${sickbeard.PYTIVO_HOST}" class="form-control input-sm input250" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('host running pyTivo (eg. 192.168.1.1:9032)')}</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pytivo_share_name">
                                    <span class="component-title">${_('pyTivo share name')}</span>
                                    <input type="text" name="pytivo_share_name" id="pytivo_share_name" value="${sickbeard.PYTIVO_SHARE_NAME}" class="form-control input-sm input250" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('value used in pyTivo Web Configuration to name the share.')}</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pytivo_tivo_name">
                                    <span class="component-title">${_('Tivo name')}</span>
                                    <input type="text" name="pytivo_tivo_name" id="pytivo_tivo_name" value="${sickbeard.PYTIVO_TIVO_NAME}" class="form-control input-sm input250" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('(Messages &amp; Settings > Account &amp; System Information > System Information > DVR name)')}</span>
                                </label>
                            </div>
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                        </div><!-- /content_use_pytivo //-->

                    </fieldset>
                </div><!-- /component-group //-->

            </div>


            <div id="tabs-2">
                <div class="component-group">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-growl" alt="" title="${_('Growl')}"></span>
                        <h3><a href="${anon_url('http://growl.info/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Growl</a></h3>
                        <p>${_('A cross-platform unobtrusive global notification system.')}</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_growl">
                                <span class="component-title">${_('Enable')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_growl" id="use_growl" ${('', 'checked="checked"')[bool(sickbeard.USE_GROWL)]}/>
                                    <p>${_('Send Growl notifications?')}</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_growl">
                            <div class="field-pair">
                                <label for="growl_notify_onsnatch">
                                    <span class="component-title">${_('Notify on snatch')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="growl_notify_onsnatch" id="growl_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.GROWL_NOTIFY_ONSNATCH)]}/>
                                        <p>${_('send a notification when a download starts?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="growl_notify_ondownload">
                                    <span class="component-title">${_('Notify on download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="growl_notify_ondownload" id="growl_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.GROWL_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>${_('send a notification when a download finishes?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="growl_notify_onsubtitledownload">
                                    <span class="component-title">${_('Notify on subtitle download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="growl_notify_onsubtitledownload" id="growl_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.GROWL_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>${_('send a notification when subtitles are downloaded?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="growl_host">
                                    <span class="component-title">${_('Growl IP:Port')}</span>
                                    <input type="text" name="growl_host" id="growl_host" value="${sickbeard.GROWL_HOST}" class="form-control input-sm input250" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('host running Growl (eg. 192.168.1.100:23053)')}</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="growl_password">
                                    <span class="component-title">${_('Password')}</span>
                                    <input type="password" name="growl_password" id="growl_password" value="${sickbeard.GROWL_PASSWORD}" class="form-control input-sm input250" autocomplete="no" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('may leave blank if SickRage is on the same host.')}</span>
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('otherwise Growl <b>requires</b> a password to be used.')}</span>
                                </label>
                            </div>
                            <div class="testNotification" id="testGrowl-result">${_('Click below to register and test Growl, this is required for Growl notifications to work.')}</div>
                            <input  class="btn" type="button" value="${_('Register Growl')}" id="testGrowl" />
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                        </div><!-- /content_use_growl //-->

                    </fieldset>
                </div><!-- /growl component-group //-->


                <div class="component-group">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-prowl" title="${_('Prowl')}"></span>
                        <h3><a href="${anon_url('http://www.prowlapp.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Prowl</a></h3>
                        <p>${_('A Growl client for iOS.')}</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_prowl">
                                <span class="component-title">${_('Enable')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_prowl" id="use_prowl" ${('', 'checked="checked"')[bool(sickbeard.USE_PROWL)]}/>
                                    <p>${_('Send Prowl notifications?')}</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_prowl">
                            <div class="field-pair">
                                <label for="prowl_notify_onsnatch">
                                    <span class="component-title">${_('Notify on snatch')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="prowl_notify_onsnatch" id="prowl_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.PROWL_NOTIFY_ONSNATCH)]}/>
                                        <p>${_('send a notification when a download starts?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="prowl_notify_ondownload">
                                    <span class="component-title">${_('Notify on download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="prowl_notify_ondownload" id="prowl_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.PROWL_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>${_('send a notification when a download finishes?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="prowl_notify_onsubtitledownload">
                                    <span class="component-title">${_('Notify on subtitle download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="prowl_notify_onsubtitledownload" id="prowl_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>${_('send a notification when subtitles are downloaded?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                 <label for="prowl_message_title">
                                     <span class="component-title">${_('Prowl Message Title')}:</span>
                                     <input type="text" name="prowl_message_title" id="prowl_message_title" value="${sickbeard.PROWL_MESSAGE_TITLE}" class="form-control input-sm input250" autocapitalize="off" />
                                 </label>
                            </div>
                            <div class="field-pair">
                                <label for="prowl_api">
                                    <span class="component-title">${_('Global Prowl API key(s)')}:</span>
                                    <input type="text" name="prowl_api" id="prowl_api" value="${sickbeard.PROWL_API}" class="form-control input-sm input250" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('''Prowl API(s) listed here, separated by commas if applicable, will<br> receive notifications for <b>all</b> shows.
                                                                 Your Prowl API key is available at:''')}
                                                                 <a href="${anon_url('https://www.prowlapp.com/api_settings.php')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">
                                                                 https://www.prowlapp.com/api_settings.php</a><br>
                                                                 ${_('(This field may be blank except when testing.)')}</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="prowl_show">
                                    <span class="component-title">${_('Show notification list')}</span>
                                    <select name="prowl_show" id="prowl_show" class="form-control input-sm">
                                        <option value="-1">${_('-- Select a Show --')}</option>
                                    </select>
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <input type="text" name="prowl_show_list" id="prowl_show_list" class="form-control input-sm input350" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('''Configure per-show notifications here by entering Prowl API key(s), separated by commas,
                                                                 after selecting a show in the drop-down box.   Be sure to activate the 'Save for this show'
                                                                 button below after each entry.''')}</span>
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <input id="prowl_show_save" class="btn" type="button" value="${_('Save for this show')}" />
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="prowl_priority">
                                    <span class="component-title">${_('Prowl priority')}:</span>
                                    <select id="prowl_priority" name="prowl_priority" class="form-control input-sm">
                                        <option value="-2" ${('', 'selected="selected"')[sickbeard.PROWL_PRIORITY == '-2']}>${_('Very Low')}</option>
                                        <option value="-1" ${('', 'selected="selected"')[sickbeard.PROWL_PRIORITY == '-1']}>${_('Moderate')}</option>
                                        <option value="0" ${('', 'selected="selected"')[sickbeard.PROWL_PRIORITY == '0']}>${_('Normal')}</option>
                                        <option value="1" ${('', 'selected="selected"')[sickbeard.PROWL_PRIORITY == '1']}>${_('High')}</option>
                                        <option value="2" ${('', 'selected="selected"')[sickbeard.PROWL_PRIORITY == '2']}>${_('Emergency')}</option>
                                    </select>
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('priority of Prowl messages from SickRage.')}</span>
                                </label>
                            </div>
                            <div class="testNotification" id="testProwl-result">${_('Click below to test.')}</div>
                            <input  class="btn" type="button" value="Test Prowl" id="testProwl" />
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                        </div><!-- /content_use_prowl //-->

                    </fieldset>
                </div><!-- /prowl component-group //-->


                <div class="component-group">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-libnotify" title="${_('Libnotify')}"></span>
                        <h3><a href="${anon_url('http://library.gnome.org/devel/libnotify/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Libnotify</a></h3>
                        <p>${_('The standard desktop notification API for Linux/*nix systems.  This notifier will only function if the pynotify module is installed (Ubuntu/Debian package <a href="apt:python-notify">python-notify</a>).')}</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_libnotify">
                                <span class="component-title">${_('Enable')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_libnotify" id="use_libnotify" ${('', 'checked="checked"')[bool(sickbeard.USE_LIBNOTIFY)]}/>
                                    <p>${_('Send Libnotify notifications?')}</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_libnotify">
                            <div class="field-pair">
                                <label for="libnotify_notify_onsnatch">
                                    <span class="component-title">${_('Notify on snatch')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="libnotify_notify_onsnatch" id="libnotify_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.LIBNOTIFY_NOTIFY_ONSNATCH)]}/>
                                        <p>${_('send a notification when a download starts?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="libnotify_notify_ondownload">
                                    <span class="component-title">${_('Notify on download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="libnotify_notify_ondownload" id="libnotify_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.LIBNOTIFY_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>${_('send a notification when a download finishes?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="libnotify_notify_onsubtitledownload">
                                    <span class="component-title">${_('Notify on subtitle download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="libnotify_notify_onsubtitledownload" id="libnotify_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>${_('send a notification when subtitles are downloaded?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="testNotification" id="testLibnotify-result">${_('Click below to test.')}</div>
                            <input  class="btn" type="button" value="Test Libnotify" id="testLibnotify" />
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                        </div><!-- /content_use_libnotify //-->

                    </fieldset>
                </div><!-- /libnotify component-group //-->


                <div class="component-group">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-pushover" alt="" title="${_('Pushover')}"></span>
                        <h3><a href="${anon_url('https://pushover.net/apps/clone/sickrage')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Pushover</a></h3>
                        <p>${_('Pushover makes it easy to send real-time notifications to your Android and iOS devices.')}</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_pushover">
                                <span class="component-title">${_('Enable')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_pushover" id="use_pushover" ${('', 'checked="checked"')[bool(sickbeard.USE_PUSHOVER)]}/>
                                    <p>${_('Send Pushover notifications?')}</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_pushover">
                            <div class="field-pair">
                                <label for="pushover_notify_onsnatch">
                                    <span class="component-title">${_('Notify on snatch')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="pushover_notify_onsnatch" id="pushover_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.PUSHOVER_NOTIFY_ONSNATCH)]}/>
                                        <p>${_('send a notification when a download starts?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pushover_notify_ondownload">
                                    <span class="component-title">${_('Notify on download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="pushover_notify_ondownload" id="pushover_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.PUSHOVER_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>${_('send a notification when a download finishes?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pushover_notify_onsubtitledownload">
                                    <span class="component-title">${_('Notify on subtitle download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="pushover_notify_onsubtitledownload" id="pushover_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>${_('send a notification when subtitles are downloaded?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pushover_userkey">
                                    <span class="component-title">${_('Pushover key')}</span>
                                    <input type="text" name="pushover_userkey" id="pushover_userkey" value="${sickbeard.PUSHOVER_USERKEY}" class="form-control input-sm input250" autocapitalize="off" autocomplete="no" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('user key of your Pushover account')}</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pushover_apikey">
                                    <span class="component-title">${_('Pushover API key')}</span>
                                    <input type="text" name="pushover_apikey" id="pushover_apikey" value="${sickbeard.PUSHOVER_APIKEY}" class="form-control input-sm input250" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc"><a href="${anon_url('https://pushover.net/apps/clone/sickrage')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;"><b>Click here</b></a> to create a Pushover API key</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pushover_device">
                                    <span class="component-title">${_('Pushover devices')}</span>
                                    <input type="text" name="pushover_device" id="pushover_device" value="${sickbeard.PUSHOVER_DEVICE}" class="form-control input-sm input250" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('comma separated list of pushover devices you want to send notifications to')}</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pushover_sound">
                                    <span class="component-title">${_('Pushover notification sound')}</span>
                                    <select id="pushover_sound" name="pushover_sound" class="form-control input-sm">
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
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('Choose notification sound to use')}</span>
                                </label>
                            </div>
                            <div class="testNotification" id="testPushover-result">${_('Click below to test.')}</div>
                            <input  class="btn" type="button" value="Test Pushover" id="testPushover" />
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                        </div><!-- /content_use_pushover //-->

                    </fieldset>
                </div><!-- /pushover component-group //-->

                <div class="component-group">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-boxcar2" alt="" title="${_('Boxcar 2')}"></span>
                        <h3><a href="${anon_url('https://new.boxcar.io/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Boxcar 2</a></h3>
                        <p>${_('Read your messages where and when you want them!')}</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_boxcar2">
                                <span class="component-title">${_('Enable')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_boxcar2" id="use_boxcar2" ${('', 'checked="checked"')[bool(sickbeard.USE_BOXCAR2)]}/>
                                    <p>${_('Send Boxcar notifications?')}</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_boxcar2">
                            <div class="field-pair">
                                <label for="boxcar2_notify_onsnatch">
                                    <span class="component-title">${_('Notify on snatch')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="boxcar2_notify_onsnatch" id="boxcar2_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.BOXCAR2_NOTIFY_ONSNATCH)]}/>
                                        <p>${_('send a notification when a download starts?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="boxcar2_notify_ondownload">
                                    <span class="component-title">${_('Notify on download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="boxcar2_notify_ondownload" id="boxcar2_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.BOXCAR2_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>${_('send a notification when a download finishes?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="boxcar2_notify_onsubtitledownload">
                                    <span class="component-title">${_('Notify on subtitle download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="boxcar2_notify_onsubtitledownload" id="boxcar2_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>${_('send a notification when subtitles are downloaded?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="boxcar2_accesstoken">
                                    <span class="component-title">${_('Boxcar2 access token')}</span>
                                    <input type="text" name="boxcar2_accesstoken" id="boxcar2_accesstoken" value="${sickbeard.BOXCAR2_ACCESSTOKEN}" class="form-control input-sm input250" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('access token for your Boxcar account.')}</span>
                                </label>
                            </div>
                            <div class="testNotification" id="testBoxcar2-result">${_('Click below to test.')}</div>
                            <input  class="btn" type="button" value="Test Boxcar" id="testBoxcar2" />
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                        </div><!-- /content_use_boxcar2 //-->

                    </fieldset>
                </div><!-- /boxcar2 component-group //-->

                <div class="component-group">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-nma" alt="" title="${_('NMA')}"></span>
                        <h3><a href="${anon_url('http://www.notifymyandroid.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">${_('Notify My Android')}</a></h3>
                        <p>${_('Notify My Android is a Prowl-like Android App and API that offers an easy way to send notifications from your application directly to your Android device.')}</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_nma">
                                <span class="component-title">${_('Enable')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_nma" id="use_nma" ${('', 'checked="checked"')[bool(sickbeard.USE_NMA)]}/>
                                    <p>${_('Send NMA notifications?')}</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_nma">
                            <div class="field-pair">
                                <label for="nma_notify_onsnatch">
                                    <span class="component-title">${_('Notify on snatch')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="nma_notify_onsnatch" id="nma_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.NMA_NOTIFY_ONSNATCH)]}/>
                                        <p>${_('send a notification when a download starts?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="nma_notify_ondownload">
                                    <span class="component-title">${_('Notify on download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="nma_notify_ondownload" id="nma_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.NMA_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>${_('send a notification when a download finishes?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="nma_notify_onsubtitledownload">
                                    <span class="component-title">${_('Notify on subtitle download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="nma_notify_onsubtitledownload" id="nma_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.NMA_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>${_('send a notification when subtitles are downloaded?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="nma_api">
                                       <span class="component-title">${_('NMA API key')}:</span>
                                    <input type="text" name="nma_api" id="nma_api" value="${sickbeard.NMA_API}" class="form-control input-sm input350" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('(multiple keys must be separated by commas, up to a maximum of 5)')}</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="nma_priority">
                                    <span class="component-title">${_('NMA priority')}:</span>
                                       <select id="nma_priority" name="nma_priority" class="form-control input-sm">
                                        <option value="-2" ${('', 'selected="selected"')[sickbeard.NMA_PRIORITY == '-2']}>${_('Very Low')}</option>
                                        <option value="-1" ${('', 'selected="selected"')[sickbeard.NMA_PRIORITY == '-1']}>${_('Moderate')}</option>
                                        <option value="0" ${('', 'selected="selected"')[sickbeard.NMA_PRIORITY == '0']}>${_('Normal')}</option>
                                        <option value="1" ${('', 'selected="selected"')[sickbeard.NMA_PRIORITY == '1']}>${_('High')}</option>
                                        <option value="2" ${('', 'selected="selected"')[sickbeard.NMA_PRIORITY == '2']}>${_('Emergency')}</option>
                                    </select>
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('priority of NMA messages from SickRage.')}</span>
                                </label>
                            </div>
                            <div class="testNotification" id="testNMA-result">${_('Click below to test.')}</div>
                            <input  class="btn" type="button" value="Test NMA" id="testNMA" />
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                        </div><!-- /content_use_nma //-->

                    </fieldset>
                </div><!-- /nma component-group //-->

                <div class="component-group">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-pushalot" alt="" title="${_('Pushalot')}"></span>
                        <h3><a href="${anon_url('https://pushalot.com')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Pushalot</a></h3>
                        <p>${_('Pushalot is a platform for receiving custom push notifications to connected devices running Windows Phone or Windows 8.')}</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_pushalot">
                                <span class="component-title">${_('Enable')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_pushalot" id="use_pushalot" ${('', 'checked="checked"')[bool(sickbeard.USE_PUSHALOT)]}/>
                                    <p>${_('Send Pushalot notifications ?')}
                                </span>
                            </label>
                        </div>

                        <div id="content_use_pushalot">
                            <div class="field-pair">
                                <label for="pushalot_notify_onsnatch">
                                    <span class="component-title">${_('Notify on snatch')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="pushalot_notify_onsnatch" id="pushalot_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.PUSHALOT_NOTIFY_ONSNATCH)]}/>
                                        <p>${_('send a notification when a download starts?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pushalot_notify_ondownload">
                                    <span class="component-title">${_('Notify on download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="pushalot_notify_ondownload" id="pushalot_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.PUSHALOT_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>${_('send a notification when a download finishes?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pushalot_notify_onsubtitledownload">
                                    <span class="component-title">${_('Notify on subtitle download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="pushalot_notify_onsubtitledownload" id="pushalot_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>${_('send a notification when subtitles are downloaded?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pushalot_authorizationtoken">
                                    <span class="component-title">${_('Pushalot authorization token')}</span>
                                    <input type="text" name="pushalot_authorizationtoken" id="pushalot_authorizationtoken" value="${sickbeard.PUSHALOT_AUTHORIZATIONTOKEN}" class="form-control input-sm input350" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('authorization token of your Pushalot account.')}</span>
                                </label>
                            </div>
                            <div class="testNotification" id="testPushalot-result">${_('Click below to test.')}</div>
                            <input type="button" class="btn" value="Test Pushalot" id="testPushalot" />
                            <input type="submit" class="btn config_submitter" value="${_('Save Changes')}" />
                        </div><!-- /content_use_pushalot //-->

                    </fieldset>
                </div><!-- /pushalot component-group //-->

                <div class="component-group">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-pushbullet" alt="" title="${_('Pushbullet')}"></span>
                        <h3><a href="${anon_url('https://www.pushbullet.com')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Pushbullet</a></h3>
                        <p>${_('Pushbullet is a platform for receiving custom push notifications to connected devices running Android/iOS and desktop browsers such as Chrome, Firefox or Opera.')}</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_pushbullet">
                                <span class="component-title">${_('Enable')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_pushbullet" id="use_pushbullet" ${('', 'checked="checked"')[bool(sickbeard.USE_PUSHBULLET)]}/>
                                    <p>${_('Send Pushbullet notifications?')}</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_pushbullet">
                            <div class="field-pair">
                                <label for="pushbullet_notify_onsnatch">
                                    <span class="component-title">${_('Notify on snatch')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="pushbullet_notify_onsnatch" id="pushbullet_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.PUSHBULLET_NOTIFY_ONSNATCH)]}/>
                                        <p>${_('send a notification when a download starts?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pushbullet_notify_ondownload">
                                    <span class="component-title">${_('Notify on download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="pushbullet_notify_ondownload" id="pushbullet_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.PUSHBULLET_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>${_('send a notification when a download finishes?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pushbullet_notify_onsubtitledownload">
                                    <span class="component-title">${_('Notify on subtitle download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="pushbullet_notify_onsubtitledownload" id="pushbullet_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>${_('send a notification when subtitles are downloaded?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pushbullet_api">
                                    <span class="component-title">${_('Pushbullet API key')}</span>
                                    <input type="text" name="pushbullet_api" id="pushbullet_api" value="${sickbeard.PUSHBULLET_API}" class="form-control input-sm input350" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('API key of your Pushbullet account')}</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pushbullet_device_list">
                                    <span class="component-title">${_('Pushbullet devices')}</span>
                                    <select name="pushbullet_device_list" id="pushbullet_device_list" class="form-control input-sm"></select>
                                    <input type="hidden" id="pushbullet_device" value="${sickbeard.PUSHBULLET_DEVICE}">
                                    <input type="button" class="btn btn-inline" value="${_('Update device list')}" id="getPushbulletDevices" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('select device you wish to push to.')}</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pushbullet_channel_list">
                                    <span class="component-title">${_('Pushbullet channels')}</span>
                                    <select name="pushbullet_channel_list" id="pushbullet_channel_list" class="form-control input-sm"></select>
                                    <input type="hidden" id="pushbullet_channel" value="${sickbeard.PUSHBULLET_CHANNEL}">
                                </label>
                            </div>
                            <div class="testNotification" id="testPushbullet-result">${_('Click below to test.')}</div>
                            <input type="button" class="btn" value="Test Pushbullet" id="testPushbullet" />
                            <input type="submit" class="btn config_submitter" value="${_('Save Changes')}" />
                        </div><!-- /content_use_pushbullet //-->

                    </fieldset>
                </div><!-- /pushbullet component-group //-->
                <div class="component-group">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-freemobile" alt="" title="${_('Free Mobile')}"></span>
                        <h3><a href="${anon_url('http://mobile.free.fr/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Free Mobile</a></h3>
                        <p>${_('Free Mobile is a famous French cellular network provider.<br> It provides to their customer a free SMS API.')}</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_freemobile">
                                <span class="component-title">${_('Enable')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_freemobile" id="use_freemobile" ${('', 'checked="checked"')[bool(sickbeard.USE_FREEMOBILE)]}/>
                                    <p>${_('Send SMS notifications?')}</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_freemobile">
                            <div class="field-pair">
                                <label for="freemobile_notify_onsnatch">
                                    <span class="component-title">${_('Notify on snatch')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="freemobile_notify_onsnatch" id="freemobile_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.FREEMOBILE_NOTIFY_ONSNATCH)]}/>
                                        <p>${_('send a SMS when a download starts?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="freemobile_notify_ondownload">
                                    <span class="component-title">${_('Notify on download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="freemobile_notify_ondownload" id="freemobile_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.FREEMOBILE_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>${_('send a SMS when a download finishes?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="freemobile_notify_onsubtitledownload">
                                    <span class="component-title">${_('Notify on subtitle download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="freemobile_notify_onsubtitledownload" id="freemobile_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>${_('send a SMS when subtitles are downloaded?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="freemobile_id">
                                    <span class="component-title">${_('Free Mobile customer ID')}</span>
                                    <input type="text" name="freemobile_id" id="freemobile_id" value="${sickbeard.FREEMOBILE_ID}" class="form-control input-sm input250" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('It\'s your Free Mobile customer ID (8 digits)')}</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="freemobile_password">
                                    <span class="component-title">${_('Free Mobile API Key')}</span>
                                    <input type="text" name="freemobile_apikey" id="freemobile_apikey" value="${sickbeard.FREEMOBILE_APIKEY}" class="form-control input-sm input250" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('Find your API Key in your customer portal.')}</span>
                                </label>
                            </div>
                            <div class="testNotification" id="testFreeMobile-result">${_('Click below to test your settings.')}</div>
                            <input  class="btn" type="button" value="Test SMS" id="testFreeMobile" />
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                        </div><!-- /content_use_freemobile //-->

                    </fieldset>
                </div><!-- /freemobile component-group //-->
                <div class="component-group">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-telegram" alt="" title="${_('Telegram')}"></span>
                        <h3><a href="${anon_url('https://telegram.org/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">${_('Telegram')}</a></h3>
                        <p>${_('Telegram is a cloud-based instant messaging service.')}</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_telegram">
                                <span class="component-title">${_('Enable')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_telegram" id="use_telegram" ${('', 'checked="checked"')[bool(sickbeard.USE_TELEGRAM)]}/>
                                    <p>${_('Send Telegram notifications?')}</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_telegram">
                            <div class="field-pair">
                                <label for="telegram_notify_onsnatch">
                                    <span class="component-title">${_('Notify on snatch')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="telegram_notify_onsnatch" id="telegram_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.TELEGRAM_NOTIFY_ONSNATCH)]}/>
                                        <p>${_('Send a message when a download starts?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="telegram_notify_ondownload">
                                    <span class="component-title">${_('Notify on download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="telegram_notify_ondownload" id="telegram_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.TELEGRAM_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>${_('Send a message when a download finishes?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="telegram_notify_onsubtitledownload">
                                    <span class="component-title">${_('Notify on subtitle download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="telegram_notify_onsubtitledownload" id="telegram_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.TELEGRAM_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>${_('Send a message when subtitles are downloaded?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="telegram_id">
                                    <span class="component-title">${_('User/group ID')}</span>
                                    <input type="text" name="telegram_id" id="telegram_id" value="${sickbeard.TELEGRAM_ID}" class="form-control input-sm input250" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('Contact @myidbot on Telegram to get an ID')}</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="telegram_password">
                                    <span class="component-title">${_('Bot API token')}</span>
                                    <input type="text" name="telegram_apikey" id="telegram_apikey" value="${sickbeard.TELEGRAM_APIKEY}" class="form-control input-sm input250" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('Contact @BotFather on Telegram to set up one')}</span>
                                </label>
                            </div>
                            <div class="testNotification" id="testTelegram-result">${_('Click below to test your settings.')}</div>
                            <input  class="btn" type="button" value="Test Telegram" id="testTelegram" />
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                        </div><!-- /content_use_telegram //-->

                    </fieldset>
                </div><!-- /join component-group //-->
                <div class="component-group">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-join" alt="" title="${_('Join')}"></span>
                        <h3><a href="${anon_url('http://joaoapps.com/join/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">${_('Join')}</a></h3>
                        <p>${_('Join all of your devices together!')}</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_join">
                                <span class="component-title">${_('Enable')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_join" id="use_join" ${('', 'checked="checked"')[bool(sickbeard.USE_JOIN)]}/>
                                    <p>${_('Send Join notifications?')}</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_join">
                            <div class="field-pair">
                                <label for="join_notify_onsnatch">
                                    <span class="component-title">${_('Notify on snatch')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="join_notify_onsnatch" id="telegram_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.JOIN_NOTIFY_ONSNATCH)]}/>
                                        <p>${_('Send a message when a download starts?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="join_notify_ondownload">
                                    <span class="component-title">${_('Notify on download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="join_notify_ondownload" id="join_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.JOIN_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>${_('Send a message when a download finishes?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="join_notify_onsubtitledownload">
                                    <span class="component-title">${_('Notify on subtitle download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="join_notify_onsubtitledownload" id="join_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.JOIN_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>${_('Send a message when subtitles are downloaded?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="join_id">
                                    <span class="component-title">${_('Device ID')}</span>
                                    <input type="text" name="join_id" id="join_id" value="${sickbeard.JOIN_ID}" class="form-control input-sm input250" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('Per device specific id')}</span>
                                </label>
                            </div>
                            <div class="testNotification" id="testJoin-result">${_('Click below to test your settings.')}</div>
                            <input  class="btn" type="button" value="Test Join" id="testJoin" />
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                        </div><!-- /content_use_join //-->

                    </fieldset>
                </div><!-- /join component-group //-->

            </div>

            <div id="tabs-3">
                <div class="component-group">
                       <div class="component-group-desc">
                        <span class="icon-notifiers-twitter" alt="" title="${_('Twitter')}"></span>
                        <h3><a href="${anon_url('http://www.twitter.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Twitter</a></h3>
                        <p>${_('A social networking and microblogging service, enabling its users to send and read other users\' messages called tweets.')}</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_twitter">
                                <span class="component-title">${_('Enable')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_twitter" id="use_twitter" ${('', 'checked="checked"')[bool(sickbeard.USE_TWITTER)]}/>
                                    <p>${_('Should SickRage post tweets on Twitter?')}</p>
                                </span>
                            </label>
                            <label>
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc"><b>${_('Note')}:</b> ${_('you may want to use a secondary account.')}</span>
                            </label>
                        </div>

                        <div id="content_use_twitter">
                            <div class="field-pair">
                                <label for="twitter_notify_onsnatch">
                                    <span class="component-title">${_('Notify on snatch')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="twitter_notify_onsnatch" id="twitter_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.TWITTER_NOTIFY_ONSNATCH)]}/>
                                        <p>${_('send a notification when a download starts?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="twitter_notify_ondownload">
                                    <span class="component-title">${_('Notify on download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="twitter_notify_ondownload" id="twitter_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.TWITTER_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>${_('send a notification when a download finishes?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="twitter_notify_onsubtitledownload">
                                    <span class="component-title">${_('Notify on subtitle download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="twitter_notify_onsubtitledownload" id="twitter_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>${_('send a notification when subtitles are downloaded?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="twitter_usedm">
                                    <span class="component-title">${_('Send direct message')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="twitter_usedm" id="twitter_usedm" ${('', 'checked="checked"')[bool(sickbeard.TWITTER_USEDM)]}/>
                                        <p>${_('send a notification via Direct Message, not via status update')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="twitter_dmto">
                                    <span class="component-title">${_('Send DM to')}</span>
                                    <input type="text" name="twitter_dmto" id="twitter_dmto" value="${sickbeard.TWITTER_DMTO}" class="form-control input-sm input250" autocapitalize="off" />
                                </label>
                                <p>
                                    <span class="component-desc">${_('Twitter account to send Direct Messages to (must follow you)')}</span>
                                </p>
                            </div>
                            <div class="field-pair">
                                <label>
                                    <span class="component-title">${_('Step One')}</span>
                                </label>
                                <label>
                                    <span style="font-size: 11px;">Click the "Request Authorization" button.<br> This will open a new page containing an auth key.<br> <b>Note:</b> if nothing happens check your popup blocker.')}<br></span>
                                    <input class="btn" type="button" value="${_('Request Authorization')}" id="twitterStep1" />
                                </label>
                            </div>
                            <div class="field-pair">
                                <label>
                                    <span class="component-title">${_('Step Two')}</span>
                                </label>
                                <label>
                                    <span style="font-size: 11px;">${_('Enter the key Twitter gave you below, and click "Verify Key".')}<br><br></span>
                                    <input type="text" id="twitter_key" value="" class="form-control input-sm input350" autocapitalize="off" />
                                    <input class="btn btn-inline" type="button" value="Verify Key" id="twitterStep2" />
                                </label>
                            </div>
                            <!--
                            <div class="field-pair">
                                <label>
                                    <span class="component-title">${_('Step Three')}</span>
                                </label>
                            </div>
                            //-->
                            <div class="testNotification" id="testTwitter-result">${_('Click below to test.')}</div>
                            <input  class="btn" type="button" value="Test Twitter" id="testTwitter" />
                            <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                        </div><!-- /content_use_twitter //-->

                    </fieldset>
                </div><!-- /twitter component-group //-->


                <div class="component-group">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-trakt" alt="" title="${_('Trakt')}"></span>
                        <h3><a href="${anon_url('http://trakt.tv/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Trakt</a></h3>
                        <p>${_('trakt helps keep a record of what TV shows and movies you are watching. Based on your favorites, trakt recommends additional shows and movies you\'ll enjoy!')}</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_trakt">
                                <span class="component-title">${_('Enable')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_trakt" id="use_trakt" ${('', 'checked="checked"')[bool(sickbeard.USE_TRAKT)]}/>
                                    <p>${_('Send Trakt.tv notifications?')}</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_trakt">
                            <div class="field-pair">
                                <label for="trakt_username">
                                    <span class="component-title">${_('Username')}</span>
                                    <input type="text" name="trakt_username" id="trakt_username" value="${sickbeard.TRAKT_USERNAME}" class="form-control input-sm input250" autocapitalize="off" autocomplete="no" />
                                </label>
                                <p>
                                    <span class="component-desc">${_('username of your Trakt account.')}</span>
                                </p>
                            </div>
                            <input type="hidden" id="trakt_pin_url" value="${sickbeard.TRAKT_PIN_URL}">
                            <input type="button" class="btn ${('', 'hide')[bool(sickbeard.TRAKT_ACCESS_TOKEN)]}" value="${_('Get Trakt PIN')}" id="TraktGetPin" />
                            <div class="field-pair">
                                <label for="trakt_pin">
                                    <span class="component-title">${_('Trakt PIN')}</span>
                                    <input type="text" name="trakt_pin" id="trakt_pin" value="" class="form-control input-sm input250" autocapitalize="off" />
                                </label>
                                <p>
                                    <span class="component-desc">${_('PIN code to authorize SickRage to access Trakt on your behalf.')}</span>
                                </p>
                            </div>
                            <input type="button" class="btn hide" value="Authorize SickRage" id="authTrakt" />
                            <div class="field-pair">
                                <label for="trakt_timeout">
                                    <span class="component-title">${_('API Timeout')}</span>
                                    <input type="number" min="10" step="1" name="trakt_timeout" id="trakt_timeout" value="${sickbeard.TRAKT_TIMEOUT}" class="form-control input-sm input75" autocapitalize="off" />
                                </label>
                                <p>
                                    <span class="component-desc">
                                        ${_('Seconds to wait for Trakt API to respond. (Use 0 to wait forever)')}
                                    </span>
                                </p>
                            </div>
                            <div class="field-pair">
                                <label for="trakt_default_indexer">
                                    <span class="component-title">${_('Default indexer')}</span>
                                    <span class="component-desc">
                                        <select id="trakt_default_indexer" name="trakt_default_indexer" class="form-control input-sm">
                                            % for indexer in sickbeard.indexerApi().indexers:
                                            <option value="${indexer}" ${('', 'selected="selected"')[sickbeard.TRAKT_DEFAULT_INDEXER == indexer]}>${sickbeard.indexerApi().indexers[indexer]}</option>
                                            % endfor
                                        </select>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="trakt_sync">
                                    <span class="component-title">${_('Sync libraries')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" class="enabler" name="trakt_sync" id="trakt_sync" ${('', 'checked="checked"')[bool(sickbeard.TRAKT_SYNC)]}/>
                                        <p>${_('sync your SickRage show library with your trakt show library.')}</p>
                                    </span>
                                </label>
                            </div>
                            <div id="content_trakt_sync">
                                <div class="field-pair">
                                    <label for="trakt_sync_remove">
                                        <span class="component-title">${_('Remove Episodes From Collection')}</span>
                                        <span class="component-desc">
                                            <input type="checkbox" name="trakt_sync_remove" id="trakt_sync_remove" ${('', 'checked="checked"')[bool(sickbeard.TRAKT_SYNC_REMOVE)]}/>
                                            <p>${_('Remove an Episode from your Trakt Collection if it is not in your SickRage Library.')}</p>
                                        </span>
                                    </label>
                                 </div>
                            </div>
                            <div class="field-pair">
                                <label for="trakt_sync_watchlist">
                                    <span class="component-title">${_('Sync watchlist')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" class="enabler" name="trakt_sync_watchlist" id="trakt_sync_watchlist" ${('', 'checked="checked"')[bool(sickbeard.TRAKT_SYNC_WATCHLIST)]}/>
                                        <p>${_('sync your SickRage show watchlist with your trakt show watchlist (either Show and Episode).')}</p>
                                        <p>${_('Episode will be added on watch list when wanted or snatched and will be removed when downloaded ')}</p>
                                    </span>
                                </label>
                            </div>
                            <div id="content_trakt_sync_watchlist">
                                <div class="field-pair">
                                    <label for="trakt_method_add">
                                        <span class="component-title">${_('Watchlist add method')}</span>
                                           <select id="trakt_method_add" name="trakt_method_add" class="form-control input-sm">
                                            <option value="0" ${('', 'selected="selected"')[sickbeard.TRAKT_METHOD_ADD == 0]}>${_('Skip All')}</option>
                                            <option value="1" ${('', 'selected="selected"')[sickbeard.TRAKT_METHOD_ADD == 1]}>${_('Download Pilot Only')}</option>
                                            <option value="2" ${('', 'selected="selected"')[sickbeard.TRAKT_METHOD_ADD == 2]}>${_('Get whole show')}</option>
                                        </select>
                                    </label>
                                    <label>
                                        <span class="component-title">&nbsp;</span>
                                        <span class="component-desc">${_('method in which to download episodes for new shows.')}</span>
                                    </label>
                                </div>
                                <div class="field-pair">
                                    <label for="trakt_remove_watchlist">
                                        <span class="component-title">${_('Remove episode')}</span>
                                        <span class="component-desc">
                                            <input type="checkbox" name="trakt_remove_watchlist" id="trakt_remove_watchlist" ${('', 'checked="checked"')[bool(sickbeard.TRAKT_REMOVE_WATCHLIST)]}/>
                                            <p>${_('remove an episode from your watchlist after it is downloaded.')}</p>
                                        </span>
                                    </label>
                                </div>
                                <div class="field-pair">
                                    <label for="trakt_remove_serieslist">
                                        <span class="component-title">${_('Remove series')}</span>
                                        <span class="component-desc">
                                            <input type="checkbox" name="trakt_remove_serieslist" id="trakt_remove_serieslist" ${('', 'checked="checked"')[bool(sickbeard.TRAKT_REMOVE_SERIESLIST)]}/>
                                            <p>${_('remove the whole series from your watchlist after any download.')}</p>
                                        </span>
                                    </label>
                                </div>
                                <div class="field-pair">
                                    <label for="trakt_remove_show_from_sickrage">
                                        <span class="component-title">${_('Remove watched show')}:</span>
                                        <span class="component-desc">
                                            <input type="checkbox" name="trakt_remove_show_from_sickrage" id="trakt_remove_show_from_sickrage" ${('', 'checked="checked"')[bool(sickbeard.TRAKT_REMOVE_SHOW_FROM_SICKRAGE)]}/>
                                            <p>${_('remove the show from sickrage if it\'s ended and completely watched')}</p>
                                        </span>
                                    </label>
                                </div>
                                <div class="field-pair">
                                    <label for="trakt_start_paused">
                                        <span class="component-title">${_('Start paused')}</span>
                                        <span class="component-desc">
                                            <input type="checkbox" name="trakt_start_paused" id="trakt_start_paused" ${('', 'checked="checked"')[bool(sickbeard.TRAKT_START_PAUSED)]}/>
                                            <p>${_('shows grabbed from your trakt watchlist start paused.')}</p>
                                        </span>
                                    </label>
                                </div>
                            </div>
                            <div class="field-pair">
                                <label for="trakt_blacklist_name">
                                    <span class="component-title">${_('Trakt blackList name')}</span>
                                    <input type="text" name="trakt_blacklist_name" id="trakt_blacklist_name" value="${sickbeard.TRAKT_BLACKLIST_NAME}" class="form-control input-sm input150" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('Name(slug) of List on Trakt for blacklisting show on \'Add Trending Show\' & \'Add Recommended Shows\' pages')}</span>
                                </label>
                            </div>
                            <div class="testNotification" id="testTrakt-result">${_('Click below to test.')}</div>
                            <input type="button" class="btn" value="Test Trakt" id="testTrakt" />
                            <input type="submit" class="btn config_submitter" value="${_('Save Changes')}" />
                        </div><!-- /content_use_trakt //-->
                    </fieldset>
                </div><!-- /trakt component-group //-->

                <div class="component-group">
                    <div class="component-group-desc">
                        <span class="icon-notifiers-email" alt="" title="${_('Email')}"></span>
                        <h3><a href="${anon_url('http://en.wikipedia.org/wiki/Comparison_of_webmail_providers')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Email</a></h3>
                        <p>${_('Allows configuration of email notifications on a per show basis.')}</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_email">
                                <span class="component-title">${_('Enable')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_email" id="use_email" ${('', 'checked="checked"')[bool(sickbeard.USE_EMAIL)]}/>
                                    <p>${_('Send email notifications?')}</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_email">
                            <div class="field-pair">
                                <label for="email_notify_onsnatch">
                                    <span class="component-title">${_('Notify on snatch')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="email_notify_onsnatch" id="email_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.EMAIL_NOTIFY_ONSNATCH)]}/>
                                        <p>${_('send a notification when a download starts?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="email_notify_ondownload">
                                    <span class="component-title">${_('Notify on download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="email_notify_ondownload" id="email_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.EMAIL_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>${_('send a notification when a download finishes?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="email_notify_onsubtitledownload">
                                    <span class="component-title">${_('Notify on subtitle download')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="email_notify_onsubtitledownload" id="email_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>${_('send a notification when subtitles are downloaded?')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="email_host">
                                    <span class="component-title">${_('SMTP host')}</span>
                                    <input type="text" name="email_host" id="email_host" value="${sickbeard.EMAIL_HOST}" class="form-control input-sm input250" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('hostname of your SMTP email server.')}</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="email_port">
                                    <span class="component-title">${_('SMTP port')}</span>
                                    <input type="number" min"1" step="1" name="email_port" id="email_port" value="${sickbeard.EMAIL_PORT}" class="form-control input-sm input75" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('port number used to connect to your SMTP host.')}</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="email_from">
                                    <span class="component-title">${_('SMTP from')}</span>
                                    <input type="text" name="email_from" id="email_from" value="${sickbeard.EMAIL_FROM}" class="form-control input-sm input250" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('sender email address, some hosts require a real address.')}</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="email_tls">
                                    <span class="component-title">${_('Use TLS')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="email_tls" id="email_tls" ${('', 'checked="checked"')[bool(sickbeard.EMAIL_TLS)]}/>
                                        <p>${_('check to use TLS encryption.')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="email_user">
                                    <span class="component-title">${_('SMTP user')}</span>
                                    <input type="text" name="email_user" id="email_user" value="${sickbeard.EMAIL_USER}" class="form-control input-sm input250" autocapitalize="off" autocomplete="no" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('(optional) your SMTP server username.')}</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="email_password">
                                    <span class="component-title">${_('SMTP password')}</span>
                                    <input type="password" name="email_password" id="email_password" value="${sickbeard.EMAIL_PASSWORD}" class="form-control input-sm input250" autocomplete="no" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('(optional) your SMTP server password.')}</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="email_list">
                                    <span class="component-title">${_('Global email list')}</span>
                                    <input type="text" name="email_list" id="email_list" value="${sickbeard.EMAIL_LIST}" class="form-control input-sm input350" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('Email addresses listed here, separated by commas if applicable, will<br> receive notifications for <b>all</b> shows.')}<br>
                                                                 ${_('(This field may be blank except when testing.)')}</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="email_subject">
                                    <span class="component-title">${_('Email Subject')}</span>
                                    <input type="text" name="email_subject" id="email_subject" value="${sickbeard.EMAIL_SUBJECT}" class="form-control input-sm input350" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('Use a custom subject for some privacy protection?')}<br>
                                                                 ${_('(Leave blank for the default SickRage subject)')}</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="email_show">
                                    <span class="component-title">${_('Show notification list')}</span>
                                    <select name="email_show" id="email_show" class="form-control input-sm">
                                        <option value="-1">${_('-- Select a Show --')}</option>
                                    </select>
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <input type="text" name="email_show_list" id="email_show_list" class="form-control input-sm input350" autocapitalize="off" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">${_('Configure per-show notifications here by entering email address(es), separated by commas,')}
                                                                 ${_('after selecting a show in the drop-down box.  Be sure to activate the \'Save for this show\'')}
                                                                 ${_('button below after each entry.')}</span>
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <input id="email_show_save" class="btn" type="button" value="${_('Save for this show')}" />
                                </label>
                            </div>

                            <div class="testNotification" id="testEmail-result">${_('Click below to test.')}</div>
                            <input class="btn" type="button" value="Test Email" id="testEmail" />
                            <input class="btn" type="submit" class="config_submitter" value="${_('Save Changes')}" />
                        </div><!-- /content_use_email //-->
                    </fieldset>
                </div><!-- /email component-group //-->

            </div><!-- /config-components //-->
        </form>

        <br><input type="submit" class="config_submitter btn" value="${_('Save Changes')}" /><br>

    </div>
</div>

<div class="clearfix"></div>
</%block>
