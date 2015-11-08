<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    import re
    from sickbeard.helpers import anon_url
    from sickbeard.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickbeard.common import Quality, qualityPresets, statusStrings, qualityPresetStrings, cpu_presets, multiEpStrings
%>

<%block name="scripts">
<script type="text/javascript" src="${srRoot}/js/configNotifications.js?${sbPID}"></script>
<script type="text/javascript" src="${srRoot}/js/config.js?${sbPID}"></script>
<script type="text/javascript" src="${srRoot}/js/new/config_notifications.js"></script>
</%block>
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
                    <li><a href="#tabs-1">Home Theater / NAS</a></li>
                    <li><a href="#tabs-2">Devices</a></li>
                    <li><a href="#tabs-3">Social</a></li>
                </ul>

                <div id="tabs-1">
                <div class="component-group">

                    <div class="component-group-desc">
                        <img class="notifier-icon" src="${srRoot}/images/notifiers/kodi.png" alt="" title="KODI" />
                        <h3><a href="${anon_url('http://kodi.tv/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">KODI</a></h3>
                        <p>A free and open source cross-platform media center and home entertainment system software with a 10-foot user interface designed for the living-room TV.</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label class="clearfix" for="use_kodi">
                                <span class="component-title">Enable</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_kodi" id="use_kodi" ${('', 'checked="checked"')[bool(sickbeard.USE_KODI)]}/>
                                    <p>should SickRage send KODI commands ?<p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_kodi">
                            <div class="field-pair">
                                <label for="kodi_always_on">
                                    <span class="component-title">Always on</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="kodi_always_on" id="kodi_always_on" ${('', 'checked="checked"')[bool(sickbeard.KODI_ALWAYS_ON)]}/>
                                        <p>log errors when unreachable ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="kodi_notify_onsnatch">
                                    <span class="component-title">Notify on snatch</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="kodi_notify_onsnatch" id="kodi_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.KODI_NOTIFY_ONSNATCH)]}/>
                                        <p>send a notification when a download starts ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="kodi_notify_ondownload">
                                    <span class="component-title">Notify on download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="kodi_notify_ondownload" id="kodi_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.KODI_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>send a notification when a download finishes ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="kodi_notify_onsubtitledownload">
                                    <span class="component-title">Notify on subtitle download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="kodi_notify_onsubtitledownload" id="kodi_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.KODI_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>send a notification when subtitles are downloaded ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="kodi_update_library">
                                    <span class="component-title">Update library</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="kodi_update_library" id="kodi_update_library" ${('', 'checked="checked"')[bool(sickbeard.KODI_UPDATE_LIBRARY)]}/>
                                        <p>update KODI library when a download finishes ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="kodi_update_full">
                                    <span class="component-title">Full library update</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="kodi_update_full" id="kodi_update_full" ${('', 'checked="checked"')[bool(sickbeard.KODI_UPDATE_FULL)]}/>
                                        <p>perform a full library update if update per-show fails ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="kodi_update_onlyfirst">
                                    <span class="component-title">Only update first host</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="kodi_update_onlyfirst" id="kodi_update_onlyfirst" ${('', 'checked="checked"')[bool(sickbeard.KODI_UPDATE_ONLYFIRST)]}/>
                                        <p>only send library updates to the first active host ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="kodi_host">
                                    <span class="component-title">KODI IP:Port</span>
                                    <input type="text" name="kodi_host" id="kodi_host" value="${sickbeard.KODI_HOST}" class="form-control input-sm input350" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">host running KODI (eg. 192.168.1.100:8080)</span>
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">(multiple host strings must be separated by commas)</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="kodi_username">
                                    <span class="component-title">KODI username</span>
                                    <input type="text" name="kodi_username" id="kodi_username" value="${sickbeard.KODI_USERNAME}" class="form-control input-sm input250" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">username for your KODI server (blank for none)</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="kodi_password">
                                    <span class="component-title">KODI password</span>
                                    <input type="password" name="kodi_password" id="kodi_password" value="${sickbeard.KODI_PASSWORD}" class="form-control input-sm input250" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">password for your KODI server (blank for none)</span>
                                </label>
                            </div>
                            <div class="testNotification" id="testKODI-result">Click below to test.</div>
                            <input  class="btn" type="button" value="Test KODI" id="testKODI" />
                            <input type="submit" class="config_submitter btn" value="Save Changes" />
                        </div><!-- /content_use_kodi //-->

                    </fieldset>

                </div><!-- /kodi component-group //-->


                <div class="component-group">
                    <div class="component-group-desc">
                        <img class="notifier-icon" src="${srRoot}/images/notifiers/plex.png" alt="" title="Plex Media Server" />
                        <h3><a href="${anon_url('http://www.plexapp.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Plex Media Server</a></h3>
                        <p>Experience your media on a visually stunning, easy to use interface on your Mac connected to your TV. Your media library has never looked this good!</p>
                        <p class="plexinfo hide">For sending notifications to Plex Home Theater (PHT) clients, use the KODI notifier with port <b>3005</b>.</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_plex">
                                <span class="component-title">Enable</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_plex" id="use_plex" ${('', 'checked="checked"')[bool(sickbeard.USE_PLEX)]}/>
                                    <p>should SickRage send Plex commands ?</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_plex">
                            <div class="field-pair">
                                <label for="plex_server_token">
                                    <span class="component-title">Plex Media Server Auth Token</span>
                                    <input type="text" name="plex_server_token" id="plex_server_token" value="${sickbeard.PLEX_SERVER_TOKEN}" class="form-control input-sm input250" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">Auth Token used by plex</span>
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">(<a href="${anon_url('https://support.plex.tv/hc/en-us/articles/204059436-Finding-your-account-token-X-Plex-Token')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;"><u>Finding your account token</u></a>)</span>
                                </label>
                            </div>
                            <div class="component-group" style="padding: 0; min-height: 130px">
                                <div class="field-pair">
                                    <label for="plex_username">
                                        <span class="component-title">Server Username</span>
                                        <span class="component-desc">
                                            <input type="text" name="plex_username" id="plex_username" value="${sickbeard.PLEX_USERNAME}" class="form-control input-sm input250" />
                                            <p>blank = no authentication</p>
                                        </span>
                                    </label>
                                </div>
                                <div class="field-pair">
                                    <label for="plex_password">
                                        <span class="component-title">Server/client password</span>
                                        <span class="component-desc">
                                            <input type="password" name="plex_password" id="plex_password" value="${'*' * len(sickbeard.PLEX_PASSWORD)}" class="form-control input-sm input250" />
                                            <p>blank = no authentication</p>
                                        </span>
                                    </label>
                                </div>
                            </div>

                            <div class="component-group" style="padding: 0; min-height: 50px">
                                <div class="field-pair">
                                    <label for="plex_update_library">
                                        <span class="component-title">Update server library</span>
                                        <span class="component-desc">
                                            <input type="checkbox" class="enabler" name="plex_update_library" id="plex_update_library" ${('', 'checked="checked"')[bool(sickbeard.PLEX_UPDATE_LIBRARY)]}/>
                                            <p>update Plex Media Server library when a download finishes</p>
                                        </span>
                                    </label>
                                </div>
                                <div id="content_plex_update_library">
                                    <div class="field-pair">
                                        <label for="plex_server_host">
                                            <span class="component-title">Plex Media Server IP:Port</span>
                                            <span class="component-desc">
                                                <input type="text" name="plex_server_host" id="plex_server_host" value="${re.sub(r'\b,\b', ', ', sickbeard.PLEX_SERVER_HOST)}" class="form-control input-sm input350" />
                                                <div class="clear-left">
                                                    <p>one or more hosts running Plex Media Server<br>(eg. 192.168.1.1:32400, 192.168.1.2:32400)</p>
                                                </div>
                                            </span>
                                        </label>
                                    </div>

                                    <div class="field-pair">
                                        <div class="testNotification" id="testPMS-result">Click below to test Plex server(s)</div>
                                        <input class="btn" type="button" value="Test Plex Server" id="testPMS" />
                                        <input type="submit" class="config_submitter btn" value="Save Changes" />
                                        <div class="clear-left">&nbsp;</div>
                                    </div>
                                </div>
                            </div>
                        </div><!-- /content_use_plex -->
                    </fieldset>
                </div><!-- /plex media server component-group -->

                <div class="component-group">
                    <div class="component-group-desc">
                        <img class="notifier-icon" src="${srRoot}/images/notifiers/plex.png" alt="" title="Plex Media Client" />
                        <h3><a href="${anon_url('http://www.plexapp.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Plex Media Client</a></h3>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_plex_client">
                                <span class="component-title">Enable</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_plex" id="use_plex_client" ${('', 'checked="checked"')[bool(sickbeard.USE_PLEX_CLIENT)]}/>
                                    <p>should SickRage send Plex commands ?</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_plex_client">
                            <div class="field-pair">
                                <label for="plex_notify_onsnatch">
                                    <span class="component-title">Notify on snatch</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="plex_notify_onsnatch" id="plex_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.PLEX_NOTIFY_ONSNATCH)]}/>
                                        <p>send a notification when a download starts ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="plex_notify_ondownload">
                                    <span class="component-title">Notify on download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="plex_notify_ondownload" id="plex_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.PLEX_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>send a notification when a download finishes ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="plex_notify_onsubtitledownload">
                                    <span class="component-title">Notify on subtitle download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="plex_notify_onsubtitledownload" id="plex_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>send a notification when subtitles are downloaded ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="plex_host">
                                    <span class="component-title">Plex Client IP:Port</span>
                                    <span class="component-desc">
                                        <input type="text" name="plex_host" id="plex_host" value="${sickbeard.PLEX_HOST}" class="form-control input-sm input350" />
                                        <div class="clear-left">
                                            <p>one or more hosts running Plex client<br>(eg. 192.168.1.100:3000, 192.168.1.101:3000)</p>
                                        </div>
                                    </span>
                                </label>
                            </div>
                            <div class="component-group" style="padding: 0; min-height: 130px">
                                <div class="field-pair">
                                    <label for="plex_username">
                                        <span class="component-title">Server Username</span>
                                        <span class="component-desc">
                                            <input type="text" name="plex_client_username" id="plex_client_username" value="${sickbeard.PLEX_CLIENT_USERNAME}" class="form-control input-sm input250" />
                                            <p>blank = no authentication</p>
                                        </span>
                                    </label>
                                </div>
                                <div class="field-pair">
                                    <label for="plex_client_password">
                                        <span class="component-title">Client Password</span>
                                        <span class="component-desc">
                                            <input type="password" name="plex_client_password" id="plex_client_password" value="${'*' * len(sickbeard.PLEX_CLIENT_PASSWORD)}" class="form-control input-sm input250" />
                                            <p>blank = no authentication</p>
                                        </span>
                                    </label>
                                </div>
                            </div>

                            <div class="field-pair">
                                <div class="testNotification" id="testPMC-result">Click below to test Plex client(s)</div>
                                <input class="btn" type="button" value="Test Plex Client" id="testPMC" />
                                <input type="submit" class="config_submitter btn" value="Save Changes" />
                                <div class=clear-left><p>Note: some Plex clients <b class="boldest">do not</b> support notifications e.g. Plexapp for Samsung TVs</p></div>
                            </div>
                        </div><!-- /content_use_plex_client -->
                    </fieldset>
                </div><!-- /plex client component-group -->


                 <div class="component-group">
                     <div class="component-group-desc">
                        <img class="notifier-icon" src="${srRoot}/images/notifiers/emby.png" alt="" title="Emby" />
                        <h3><a href="${anon_url('http://emby.media/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Emby</a></h3>
                        <p>A home media server built using other popular open source technologies.</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_emby">
                                <span class="component-title">Enable</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_emby" id="use_emby" ${('', 'checked="checked"')[bool(sickbeard.USE_EMBY)]} />
                                    <p>should SickRage send update commands to Emby?<p>
                                </span>
                            </label>
                        </div>
                        <div id="content_use_emby">
                            <div class="field-pair">
                                <label for="emby_host">
                                    <span class="component-title">Emby IP:Port</span>
                                    <input type="text" name="emby_host" id="emby_host" value="${sickbeard.EMBY_HOST}" class="form-control input-sm input250" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">host running Emby (eg. 192.168.1.100:8096)</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="emby_apikey">
                                    <span class="component-title">Emby API Key</span>
                                    <input type="text" name="emby_apikey" id="emby_apikey" value="${sickbeard.EMBY_APIKEY}" class="form-control input-sm input250" />
                                </label>
                            </div>
                            <div class="testNotification" id="testEMBY-result">Click below to test.</div>
                                <input  class="btn" type="button" value="Test Emby" id="testEMBY" />
                                <input type="submit" class="config_submitter btn" value="Save Changes" />
                            </div>
                        <!-- /content_use_emby //-->
                    </fieldset>
                </div><!-- /emby component-group //-->


                <div class="component-group">
                    <div class="component-group-desc">
                        <img class="notifier-icon" src="${srRoot}/images/notifiers/nmj.png" alt="" title="Networked Media Jukebox" />
                        <h3><a href="${anon_url('http://www.popcornhour.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">NMJ</a></h3>
                        <p>The Networked Media Jukebox, or NMJ, is the official media jukebox interface made available for the Popcorn Hour 200-series.</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_nmj">
                                <span class="component-title">Enable</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_nmj" id="use_nmj" ${('', 'checked="checked"')[bool(sickbeard.USE_NMJ)]}/>
                                    <p>should SickRage send update commands to NMJ ?</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_nmj">
                            <div class="field-pair">
                                <label for="nmj_host">
                                    <span class="component-title">Popcorn IP address</span>
                                    <input type="text" name="nmj_host" id="nmj_host" value="${sickbeard.NMJ_HOST}" class="form-control input-sm input250" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">IP address of Popcorn 200-series (eg. 192.168.1.100)</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label>
                                    <span class="component-title">Get settings</span>
                                    <input class="btn btn-inline" type="button" value="Get Settings" id="settingsNMJ" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">the Popcorn Hour device must be powered on and NMJ running.</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="nmj_database">
                                    <span class="component-title">NMJ database</span>
                                    <input type="text" name="nmj_database" id="nmj_database" value="${sickbeard.NMJ_DATABASE}" class="form-control input-sm input250" ${(' readonly="readonly"', '')[sickbeard.NMJ_DATABASE == True]}/>
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">automatically filled via the 'Get Settings' button.</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="nmj_mount">
                                    <span class="component-title">NMJ mount url</span>
                                    <input type="text" name="nmj_mount" id="nmj_mount" value="${sickbeard.NMJ_MOUNT}" class="form-control input-sm input250" ${(' readonly="readonly"', '')[sickbeard.NMJ_MOUNT == True]}/>
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">automatically filled via the 'Get Settings' button.</span>
                                </label>
                            </div>
                            <div class="testNotification" id="testNMJ-result">Click below to test.</div>
                            <input class="btn" type="button" value="Test NMJ" id="testNMJ" />
                            <input type="submit" class="config_submitter btn" value="Save Changes" />
                        </div><!-- /content_use_nmj //-->

                    </fieldset>
                </div><!-- /nmj component-group //-->

                <div class="component-group">
                    <div class="component-group-desc">
                        <img class="notifier-icon" src="${srRoot}/images/notifiers/nmj.png" alt="" title="Networked Media Jukebox v2"/>
                        <h3><a href="${anon_url('http://www.popcornhour.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">NMJv2</a></h3>
                        <p>The Networked Media Jukebox, or NMJv2, is the official media jukebox interface made available for the Popcorn Hour 300 & 400-series.</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_nmjv2">
                                <span class="component-title">Enable</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_nmjv2" id="use_nmjv2" ${('', 'checked="checked"')[bool(sickbeard.USE_NMJv2)]}/>
                                    <p>should SickRage send update commands to NMJv2 ?</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_nmjv2">
                            <div class="field-pair">
                                <label for="nmjv2_host">
                                    <span class="component-title">Popcorn IP address</span>
                                    <input type="text" name="nmjv2_host" id="nmjv2_host" value="${sickbeard.NMJv2_HOST}" class="form-control input-sm input250" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">IP address of Popcorn 300/400-series (eg. 192.168.1.100)</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <span class="component-title">Database location</span>
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
                                    <span class="component-title">Database instance</span>
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
                                    <span class="component-desc">adjust this value if the wrong database is selected.</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="settingsNMJv2">
                                    <span class="component-title">Find database</span>
                                    <input type="button" class="btn btn-inline" value="Find Database" id="settingsNMJv2" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">the Popcorn Hour device must be powered on.</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="nmjv2_database">
                                    <span class="component-title">NMJv2 database</span>
                                    <input type="text" name="nmjv2_database" id="nmjv2_database" value="${sickbeard.NMJv2_DATABASE}" class="form-control input-sm input250" ${(' readonly="readonly"', '')[sickbeard.NMJv2_DATABASE == True]}/>
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">automatically filled via the 'Find Database' buttons.</span>
                                </label>
                            </div>
                        <div class="testNotification" id="testNMJv2-result">Click below to test.</div>
                        <input class="btn" type="button" value="Test NMJv2" id="testNMJv2" />
                        <input type="submit" class="config_submitter btn" value="Save Changes" />
                        </div><!-- /content_use_nmjv2 //-->

                    </fieldset>
                </div><!-- /nmjv2 component-group //-->


                <div class="component-group">
                    <div class="component-group-desc">
                        <img class="notifier-icon" src="${srRoot}/images/notifiers/synoindex.png" alt="" title="Synology" />
                        <h3><a href="${anon_url('http://synology.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Synology</a></h3>
                        <p>The Synology DiskStation NAS.</p>
                        <p>Synology Indexer is the daemon running on the Synology NAS to build its media database.</p>
                    </div>

                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_synoindex">
                                <span class="component-title">Enable</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_synoindex" id="use_synoindex" ${('', 'checked="checked"')[bool(sickbeard.USE_SYNOINDEX)]}/>
                                    <p>should SickRage send Synology notifications ?</p>
                                </span>
                            </label>
                            <label>
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc"><b>Note:</b> requires SickRage to be running on your Synology NAS.</span>
                            </label>
                        </div>

                        <div id="content_use_synoindex">
                            <input type="submit" class="config_submitter btn" value="Save Changes" />
                        </div><!-- /content_use_synoindex //-->

                    </fieldset>
                </div><!-- /synoindex component-group //-->


                <div class="component-group">
                    <div class="component-group-desc">
                        <img class="notifier-icon" src="${srRoot}/images/notifiers/synologynotifier.png" alt="" title="Synology Indexer" />
                        <h3><a href="${anon_url('http://synology.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Synology Notifier</a></h3>
                        <p>Synology Notifier is the notification system of Synology DSM</p>
                    </div>

                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_synologynotifier">
                                <span class="component-title">Enable</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_synologynotifier" id="use_synologynotifier" ${('', 'checked="checked"')[bool(sickbeard.USE_SYNOLOGYNOTIFIER)]}/>
                                    <p>should SickRage send notifications to the Synology Notifier ?</p>
                                </span>
                            </label>
                            <label>
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc"><b>Note:</b> requires SickRage to be running on your Synology DSM.</span>
                            </label>
                           </div>
                        <div id="content_use_synologynotifier">
                            <div class="field-pair">
                                <label for="synologynotifier_notify_onsnatch">
                                    <span class="component-title">Notify on snatch</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="synologynotifier_notify_onsnatch" id="synologynotifier_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH)]}/>
                                        <p>send a notification when a download starts ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="synologynotifier_notify_ondownload">
                                    <span class="component-title">Notify on download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="synologynotifier_notify_ondownload" id="synologynotifier_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>send a notification when a download finishes ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="synologynotifier_notify_onsubtitledownload">
                                    <span class="component-title">Notify on subtitle download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="synologynotifier_notify_onsubtitledownload" id="synologynotifier_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>send a notification when subtitles are downloaded ?</p>
                                    </span>
                                </label>
                            </div>
                            <input type="submit" class="config_submitter btn" value="Save Changes" />
                           </div>
                    </fieldset>
                </div><!-- /synology notifier component-group //-->


                <div class="component-group">
                    <div class="component-group-desc">
                        <img class="notifier-icon" src="${srRoot}/images/notifiers/pytivo.png" alt="" title="pyTivo" />
                        <h3><a href="${anon_url('http://pytivo.sourceforge.net/wiki/index.php/PyTivo')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">pyTivo</a></h3>
                        <p>pyTivo is both an HMO and GoBack server. This notifier will load the completed downloads to your Tivo.</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_pytivo">
                                <span class="component-title">Enable</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_pytivo" id="use_pytivo" ${('', 'checked="checked"')[bool(sickbeard.USE_PYTIVO)]}/>
                                    <p>should SickRage send notifications to pyTivo ?</p>
                                </span>
                            </label>
                            <label>
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc"><b>Note:</b> requires the downloaded files to be accessible by pyTivo.</span>
                            </label>
                        </div>

                        <div id="content_use_pytivo">
                            <div class="field-pair">
                                <label for="pytivo_host">
                                    <span class="component-title">pyTivo IP:Port</span>
                                    <input type="text" name="pytivo_host" id="pytivo_host" value="${sickbeard.PYTIVO_HOST}" class="form-control input-sm input250" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">host running pyTivo (eg. 192.168.1.1:9032)</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pytivo_share_name">
                                    <span class="component-title">pyTivo share name</span>
                                    <input type="text" name="pytivo_share_name" id="pytivo_share_name" value="${sickbeard.PYTIVO_SHARE_NAME}" class="form-control input-sm input250" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">value used in pyTivo Web Configuration to name the share.</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pytivo_tivo_name">
                                    <span class="component-title">Tivo name</span>
                                    <input type="text" name="pytivo_tivo_name" id="pytivo_tivo_name" value="${sickbeard.PYTIVO_TIVO_NAME}" class="form-control input-sm input250" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">(Messages &amp; Settings > Account &amp; System Information > System Information > DVR name)</span>
                                </label>
                            </div>
                            <input type="submit" class="config_submitter btn" value="Save Changes" />
                        </div><!-- /content_use_pytivo //-->

                    </fieldset>
                </div><!-- /component-group //-->

            </div>


            <div id="tabs-2">
                <div class="component-group">
                    <div class="component-group-desc">
                        <img class="notifier-icon" src="${srRoot}/images/notifiers/growl.png" alt="" title="Growl" />
                        <h3><a href="${anon_url('http://growl.info/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Growl</a></h3>
                        <p>A cross-platform unobtrusive global notification system.</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_growl">
                                <span class="component-title">Enable</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_growl" id="use_growl" ${('', 'checked="checked"')[bool(sickbeard.USE_GROWL)]}/>
                                    <p>should SickRage send Growl notifications ?</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_growl">
                            <div class="field-pair">
                                <label for="growl_notify_onsnatch">
                                    <span class="component-title">Notify on snatch</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="growl_notify_onsnatch" id="growl_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.GROWL_NOTIFY_ONSNATCH)]}/>
                                        <p>send a notification when a download starts ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="growl_notify_ondownload">
                                    <span class="component-title">Notify on download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="growl_notify_ondownload" id="growl_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.GROWL_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>send a notification when a download finishes ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="growl_notify_onsubtitledownload">
                                    <span class="component-title">Notify on subtitle download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="growl_notify_onsubtitledownload" id="growl_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.GROWL_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>send a notification when subtitles are downloaded ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="growl_host">
                                    <span class="component-title">Growl IP:Port</span>
                                    <input type="text" name="growl_host" id="growl_host" value="${sickbeard.GROWL_HOST}" class="form-control input-sm input250" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">host running Growl (eg. 192.168.1.100:23053)</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="growl_password">
                                    <span class="component-title">Growl password</span>
                                    <input type="password" name="growl_password" id="growl_password" value="${sickbeard.GROWL_PASSWORD}" class="form-control input-sm input250" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">may leave blank if SickRage is on the same host.</span>
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">otherwise Growl <b>requires</b> a password to be used.</span>
                                </label>
                            </div>
                            <div class="testNotification" id="testGrowl-result">Click below to register and test Growl, this is required for Growl notifications to work.</div>
                            <input  class="btn" type="button" value="Register Growl" id="testGrowl" />
                            <input type="submit" class="config_submitter btn" value="Save Changes" />
                        </div><!-- /content_use_growl //-->

                    </fieldset>
                </div><!-- /growl component-group //-->


                <div class="component-group">
                    <div class="component-group-desc">
                        <img class="notifier-icon" src="${srRoot}/images/notifiers/prowl.png" alt="Prowl" title="Prowl" />
                        <h3><a href="${anon_url('http://www.prowlapp.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Prowl</a></h3>
                        <p>A Growl client for iOS.</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_prowl">
                                <span class="component-title">Enable</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_prowl" id="use_prowl" ${('', 'checked="checked"')[bool(sickbeard.USE_PROWL)]}/>
                                    <p>should SickRage send Prowl notifications ?</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_prowl">
                            <div class="field-pair">
                                <label for="prowl_notify_onsnatch">
                                    <span class="component-title">Notify on snatch</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="prowl_notify_onsnatch" id="prowl_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.PROWL_NOTIFY_ONSNATCH)]}/>
                                        <p>send a notification when a download starts ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="prowl_notify_ondownload">
                                    <span class="component-title">Notify on download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="prowl_notify_ondownload" id="prowl_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.PROWL_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>send a notification when a download finishes ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="prowl_notify_onsubtitledownload">
                                    <span class="component-title">Notify on subtitle download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="prowl_notify_onsubtitledownload" id="prowl_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>send a notification when subtitles are downloaded ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="prowl_api">
                                    <span class="component-title">Prowl API key:</span>
                                    <input type="text" name="prowl_api" id="prowl_api" value="${sickbeard.PROWL_API}" class="form-control input-sm input250" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">get your key at: <a href="${anon_url('https://www.prowlapp.com/api_settings.php')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">https://www.prowlapp.com/api_settings.php</a></span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="prowl_priority">
                                    <span class="component-title">Prowl priority:</span>
                                    <select id="prowl_priority" name="prowl_priority" class="form-control input-sm">
                                        <option value="-2" ${('', 'selected="selected"')[sickbeard.PROWL_PRIORITY == '-2']}>Very Low</option>
                                        <option value="-1" ${('', 'selected="selected"')[sickbeard.PROWL_PRIORITY == '-1']}>Moderate</option>
                                        <option value="0" ${('', 'selected="selected"')[sickbeard.PROWL_PRIORITY == '0']}>Normal</option>
                                        <option value="1" ${('', 'selected="selected"')[sickbeard.PROWL_PRIORITY == '1']}>High</option>
                                        <option value="2" ${('', 'selected="selected"')[sickbeard.PROWL_PRIORITY == '2']}>Emergency</option>
                                    </select>
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">priority of Prowl messages from SickRage.</span>
                                </label>
                            </div>
                            <div class="testNotification" id="testProwl-result">Click below to test.</div>
                            <input  class="btn" type="button" value="Test Prowl" id="testProwl" />
                            <input type="submit" class="config_submitter btn" value="Save Changes" />
                        </div><!-- /content_use_prowl //-->

                    </fieldset>
                </div><!-- /prowl component-group //-->


                <div class="component-group">
                    <div class="component-group-desc">
                        <img class="notifier-icon" src="${srRoot}/images/notifiers/libnotify.png" alt="" title="Libnotify" />
                        <h3><a href="${anon_url('http://library.gnome.org/devel/libnotify/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Libnotify</a></h3>
                        <p>The standard desktop notification API for Linux/*nix systems.  This notifier will only function if the pynotify module is installed (Ubuntu/Debian package <a href="apt:python-notify">python-notify</a>).</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_libnotify">
                                <span class="component-title">Enable</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_libnotify" id="use_libnotify" ${('', 'checked="checked"')[bool(sickbeard.USE_LIBNOTIFY)]}/>
                                    <p>should SickRage send Libnotify notifications ?</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_libnotify">
                            <div class="field-pair">
                                <label for="libnotify_notify_onsnatch">
                                    <span class="component-title">Notify on snatch</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="libnotify_notify_onsnatch" id="libnotify_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.LIBNOTIFY_NOTIFY_ONSNATCH)]}/>
                                        <p>send a notification when a download starts ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="libnotify_notify_ondownload">
                                    <span class="component-title">Notify on download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="libnotify_notify_ondownload" id="libnotify_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.LIBNOTIFY_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>send a notification when a download finishes ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="libnotify_notify_onsubtitledownload">
                                    <span class="component-title">Notify on subtitle download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="libnotify_notify_onsubtitledownload" id="libnotify_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>send a notification when subtitles are downloaded ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="testNotification" id="testLibnotify-result">Click below to test.</div>
                            <input  class="btn" type="button" value="Test Libnotify" id="testLibnotify" />
                            <input type="submit" class="config_submitter btn" value="Save Changes" />
                        </div><!-- /content_use_libnotify //-->

                    </fieldset>
                </div><!-- /libnotify component-group //-->


                <div class="component-group">
                    <div class="component-group-desc">
                        <img class="notifier-icon" src="${srRoot}/images/notifiers/pushover.png" alt="" title="Pushover" />
                        <h3><a href="${anon_url('https://pushover.net/apps/clone/sickrage')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Pushover</a></h3>
                        <p>Pushover makes it easy to send real-time notifications to your Android and iOS devices.</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_pushover">
                                <span class="component-title">Enable</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_pushover" id="use_pushover" ${('', 'checked="checked"')[bool(sickbeard.USE_PUSHOVER)]}/>
                                    <p>should SickRage send Pushover notifications ?</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_pushover">
                            <div class="field-pair">
                                <label for="pushover_notify_onsnatch">
                                    <span class="component-title">Notify on snatch</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="pushover_notify_onsnatch" id="pushover_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.PUSHOVER_NOTIFY_ONSNATCH)]}/>
                                        <p>send a notification when a download starts ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pushover_notify_ondownload">
                                    <span class="component-title">Notify on download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="pushover_notify_ondownload" id="pushover_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.PUSHOVER_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>send a notification when a download finishes ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pushover_notify_onsubtitledownload">
                                    <span class="component-title">Notify on subtitle download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="pushover_notify_onsubtitledownload" id="pushover_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>send a notification when subtitles are downloaded ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pushover_userkey">
                                    <span class="component-title">Pushover key</span>
                                    <input type="text" name="pushover_userkey" id="pushover_userkey" value="${sickbeard.PUSHOVER_USERKEY}" class="form-control input-sm input250" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">user key of your Pushover account</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pushover_apikey">
                                    <span class="component-title">Pushover API key</span>
                                    <input type="text" name="pushover_apikey" id="pushover_apikey" value="${sickbeard.PUSHOVER_APIKEY}" class="form-control input-sm input250" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc"><a href="${anon_url('https://pushover.net/apps/clone/sickrage')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;"><b>Click here</b></a> to create a Pushover API key</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pushover_device">
                                    <span class="component-title">Pushover devices</span>
                                    <input type="text" name="pushover_device" id="pushover_device" value="${sickbeard.PUSHOVER_DEVICE}" class="form-control input-sm input250" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">comma separated list of pushover devices you want to send notifications to</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pushover_sound">
                                    <span class="component-title">Pushover notification sound</span>
                                    <select id="pushover_sound" name="pushover_sound" class="form-control input-sm">
                                        <option value="pushover" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'pushover']}>Pushover</option>
                                        <option value="bike" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'bike']}>Bike</option>
                                        <option value="bugle" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'bugle']}>Bugle</option>
                                        <option value="cashregister" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'cashregister']}>Cash Register</option>
                                        <option value="classical" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'classical']}>Classical</option>
                                        <option value="cosmic" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'cosmic']}>Cosmic</option>
                                        <option value="falling" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'falling']}>Falling</option>
                                        <option value="gamelan" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'gamelan']}>Gamelan</option>
                                        <option value="incoming" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'incoming']}> Incoming</option>
                                        <option value="intermission" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'intermission']}>Intermission</option>
                                        <option value="magic" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'magic']}>Magic</option>
                                        <option value="mechanical" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'mechanical']}>Mechanical</option>
                                        <option value="pianobar" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'pianobar']}>Piano Bar</option>
                                        <option value="siren" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'siren']}>Siren</option>
                                        <option value="spacealarm" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'spacealarm']}>Space Alarm</option>
                                        <option value="tugboat" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'tugboat']}>Tug Boat</option>
                                        <option value="alien" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'alien']}>Alien Alarm (long)</option>
                                        <option value="climb" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'climb']}>Climb (long)</option>
                                        <option value="persistent" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'persistent']}>Persistent (long)</option>
                                        <option value="echo" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'echo']}>Pushover Echo (long)</option>
                                        <option value="updown" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'updown']}>Up Down (long)</option>
                                        <option value="none" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'none']}>None (silent)</option>
                                        <option value="default" ${('', 'selected="selected"')[sickbeard.PUSHOVER_SOUND == 'default']}>Device specific</option>
                                    </select>
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">Choose notification sound to use</span>
                                </label>
                            </div>
                            <div class="testNotification" id="testPushover-result">Click below to test.</div>
                            <input  class="btn" type="button" value="Test Pushover" id="testPushover" />
                            <input type="submit" class="config_submitter btn" value="Save Changes" />
                        </div><!-- /content_use_pushover //-->

                    </fieldset>
                </div><!-- /pushover component-group //-->

                <div class="component-group">
                    <div class="component-group-desc">
                        <img class="notifier-icon" src="${srRoot}/images/notifiers/boxcar.png" alt="" title="Boxcar" />
                        <h3><a href="${anon_url('http://boxcar.io/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Boxcar</a></h3>
                        <p>Universal push notification for iOS. Read your messages where and when you want them! A subscription will be sent if needed.</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_boxcar">
                                <span class="component-title">Enable</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_boxcar" id="use_boxcar" ${('', 'checked="checked"')[bool(sickbeard.USE_BOXCAR)]}/>
                                    <p>should SickRage send Boxcar notifications ?</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_boxcar">
                            <div class="field-pair">
                                <label for="boxcar_notify_onsnatch">
                                    <span class="component-title">Notify on snatch</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="boxcar_notify_onsnatch" id="boxcar_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.BOXCAR_NOTIFY_ONSNATCH)]}/>
                                        <p>send a notification when a download starts ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="boxcar_notify_ondownload">
                                    <span class="component-title">Notify on download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="boxcar_notify_ondownload" id="boxcar_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.BOXCAR_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>send a notification when a download finishes ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="boxcar_notify_onsubtitledownload">
                                    <span class="component-title">Notify on subtitle download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="boxcar_notify_onsubtitledownload" id="boxcar_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.BOXCAR_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>send a notification when subtitles are downloaded ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="boxcar_username">
                                    <span class="component-title">Boxcar username</span>
                                    <input type="text" name="boxcar_username" id="boxcar_username" value="${sickbeard.BOXCAR_USERNAME}" class="form-control input-sm input250" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">username of your Boxcar account</span>
                                </label>
                            </div>
                            <div class="testNotification" id="testBoxcar-result">Click below to test.</div>
                            <input  class="btn" type="button" value="Test Boxcar" id="testBoxcar" />
                            <input type="submit" class="config_submitter btn" value="Save Changes" />
                        </div><!-- /content_use_boxcar //-->

                    </fieldset>
                </div><!-- /boxcar component-group //-->

                <div class="component-group">
                    <div class="component-group-desc">
                        <img class="notifier-icon" src="${srRoot}/images/notifiers/boxcar2.png" alt="" title="Boxcar2"/>
                        <h3><a href="${anon_url('https://new.boxcar.io/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Boxcar2</a></h3>
                        <p>Read your messages where and when you want them!</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_boxcar2">
                                <span class="component-title">Enable</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_boxcar2" id="use_boxcar2" ${('', 'checked="checked"')[bool(sickbeard.USE_BOXCAR2)]}/>
                                    <p>should SickRage send Boxcar2 notifications ?</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_boxcar2">
                            <div class="field-pair">
                                <label for="boxcar2_notify_onsnatch">
                                    <span class="component-title">Notify on snatch</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="boxcar2_notify_onsnatch" id="boxcar2_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.BOXCAR2_NOTIFY_ONSNATCH)]}/>
                                        <p>send a notification when a download starts ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="boxcar2_notify_ondownload">
                                    <span class="component-title">Notify on download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="boxcar2_notify_ondownload" id="boxcar2_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.BOXCAR2_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>send a notification when a download finishes ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="boxcar2_notify_onsubtitledownload">
                                    <span class="component-title">Notify on subtitle download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="boxcar2_notify_onsubtitledownload" id="boxcar2_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>send a notification when subtitles are downloaded ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="boxcar2_accesstoken">
                                    <span class="component-title">Boxcar2 access token</span>
                                    <input type="text" name="boxcar2_accesstoken" id="boxcar2_accesstoken" value="${sickbeard.BOXCAR2_ACCESSTOKEN}" class="form-control input-sm input250" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">access token for your Boxcar2 account.</span>
                                </label>
                            </div>
                            <div class="testNotification" id="testBoxcar2-result">Click below to test.</div>
                            <input  class="btn" type="button" value="Test Boxcar2" id="testBoxcar2" />
                            <input type="submit" class="config_submitter btn" value="Save Changes" />
                        </div><!-- /content_use_boxcar2 //-->

                    </fieldset>
                </div><!-- /boxcar2 component-group //-->

                <div class="component-group">
                    <div class="component-group-desc">
                        <img class="notifier-icon" src="${srRoot}/images/notifiers/nma.png" alt="" title="NMA"/>
                        <h3><a href="${anon_url('http://nma.usk.bz')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Notify My Android</a></h3>
                        <p>Notify My Android is a Prowl-like Android App and API that offers an easy way to send notifications from your application directly to your Android device.</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_nma">
                                <span class="component-title">Enable</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_nma" id="use_nma" ${('', 'checked="checked"')[bool(sickbeard.USE_NMA)]}/>
                                    <p>should SickRage send NMA notifications ?</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_nma">
                            <div class="field-pair">
                                <label for="nma_notify_onsnatch">
                                    <span class="component-title">Notify on snatch</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="nma_notify_onsnatch" id="nma_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.NMA_NOTIFY_ONSNATCH)]}/>
                                        <p>send a notification when a download starts ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="nma_notify_ondownload">
                                    <span class="component-title">Notify on download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="nma_notify_ondownload" id="nma_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.NMA_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>send a notification when a download finishes ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="nma_notify_onsubtitledownload">
                                    <span class="component-title">Notify on subtitle download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="nma_notify_onsubtitledownload" id="nma_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.NMA_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>send a notification when subtitles are downloaded ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="nma_api">
                                       <span class="component-title">NMA API key:</span>
                                    <input type="text" name="nma_api" id="nma_api" value="${sickbeard.NMA_API}" class="form-control input-sm input350" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">(multiple keys must be seperated by commas, up to a maximum of 5)</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="nma_priority">
                                    <span class="component-title">NMA priority:</span>
                                       <select id="nma_priority" name="nma_priority" class="form-control input-sm">
                                        <option value="-2" ${('', 'selected="selected"')[sickbeard.NMA_PRIORITY == '-2']}>Very Low</option>
                                        <option value="-1" ${('', 'selected="selected"')[sickbeard.NMA_PRIORITY == '-1']}>Moderate</option>
                                        <option value="0" ${('', 'selected="selected"')[sickbeard.NMA_PRIORITY == '0']}>Normal</option>
                                        <option value="1" ${('', 'selected="selected"')[sickbeard.NMA_PRIORITY == '1']}>High</option>
                                        <option value="2" ${('', 'selected="selected"')[sickbeard.NMA_PRIORITY == '2']}>Emergency</option>
                                    </select>
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">priority of NMA messages from SickRage.</span>
                                </label>
                            </div>
                            <div class="testNotification" id="testNMA-result">Click below to test.</div>
                            <input  class="btn" type="button" value="Test NMA" id="testNMA" />
                            <input type="submit" class="config_submitter btn" value="Save Changes" />
                        </div><!-- /content_use_nma //-->

                    </fieldset>
                </div><!-- /nma component-group //-->

                <div class="component-group">
                    <div class="component-group-desc">
                        <img class="notifier-icon" src="${srRoot}/images/notifiers/pushalot.png" alt="" title="Pushalot" />
                        <h3><a href="${anon_url('https://pushalot.com')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Pushalot</a></h3>
                        <p>Pushalot is a platform for receiving custom push notifications to connected devices running Windows Phone or Windows 8.</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_pushalot">
                                <span class="component-title">Enable</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_pushalot" id="use_pushalot" ${('', 'checked="checked"')[bool(sickbeard.USE_PUSHALOT)]}/>
                                    <p>should SickRage send Pushalot notifications ?
                                </span>
                            </label>
                        </div>

                        <div id="content_use_pushalot">
                            <div class="field-pair">
                                <label for="pushalot_notify_onsnatch">
                                    <span class="component-title">Notify on snatch</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="pushalot_notify_onsnatch" id="pushalot_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.PUSHALOT_NOTIFY_ONSNATCH)]}/>
                                        <p>send a notification when a download starts ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pushalot_notify_ondownload">
                                    <span class="component-title">Notify on download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="pushalot_notify_ondownload" id="pushalot_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.PUSHALOT_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>send a notification when a download finishes ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pushalot_notify_onsubtitledownload">
                                    <span class="component-title">Notify on subtitle download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="pushalot_notify_onsubtitledownload" id="pushalot_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>send a notification when subtitles are downloaded ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pushalot_authorizationtoken">
                                    <span class="component-title">Pushalot authorization token</span>
                                    <input type="text" name="pushalot_authorizationtoken" id="pushalot_authorizationtoken" value="${sickbeard.PUSHALOT_AUTHORIZATIONTOKEN}" class="form-control input-sm input350" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">authorization token of your Pushalot account.</span>
                                </label>
                            </div>
                            <div class="testNotification" id="testPushalot-result">Click below to test.</div>
                            <input type="button" class="btn" value="Test Pushalot" id="testPushalot" />
                            <input type="submit" class="btn config_submitter" value="Save Changes" />
                        </div><!-- /content_use_pushalot //-->

                    </fieldset>
                </div><!-- /pushalot component-group //-->

                <div class="component-group">
                    <div class="component-group-desc">
                        <img class="notifier-icon" src="${srRoot}/images/notifiers/pushbullet.png" alt="" title="Pushbullet" />
                        <h3><a href="${anon_url('https://www.pushbullet.com')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Pushbullet</a></h3>
                        <p>Pushbullet is a platform for receiving custom push notifications to connected devices running Android and desktop Chrome browsers.</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_pushbullet">
                                <span class="component-title">Enable</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_pushbullet" id="use_pushbullet" ${('', 'checked="checked"')[bool(sickbeard.USE_PUSHBULLET)]}/>
                                    <p>should SickRage send Pushbullet notifications ?</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_pushbullet">
                            <div class="field-pair">
                                <label for="pushbullet_notify_onsnatch">
                                    <span class="component-title">Notify on snatch</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="pushbullet_notify_onsnatch" id="pushbullet_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.PUSHBULLET_NOTIFY_ONSNATCH)]}/>
                                        <p>send a notification when a download starts ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pushbullet_notify_ondownload">
                                    <span class="component-title">Notify on download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="pushbullet_notify_ondownload" id="pushbullet_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.PUSHBULLET_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>send a notification when a download finishes ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pushbullet_notify_onsubtitledownload">
                                    <span class="component-title">Notify on subtitle download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="pushbullet_notify_onsubtitledownload" id="pushbullet_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>send a notification when subtitles are downloaded ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pushbullet_api">
                                    <span class="component-title">Pushbullet API key</span>
                                    <input type="text" name="pushbullet_api" id="pushbullet_api" value="${sickbeard.PUSHBULLET_API}" class="form-control input-sm input350" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">API key of your Pushbullet account</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="pushbullet_device_list">
                                    <span class="component-title">Pushbullet devices</span>
                                    <select name="pushbullet_device_list" id="pushbullet_device_list" class="form-control input-sm"></select>
                                    <input type="hidden" id="pushbullet_device" value="${sickbeard.PUSHBULLET_DEVICE}">
                                    <input type="button" class="btn btn-inline" value="Update device list" id="getPushbulletDevices" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">select device you wish to push to.</span>
                                </label>
                            </div>
                            <div class="testNotification" id="testPushbullet-result">Click below to test.</div>
                            <input type="button" class="btn" value="Test Pushbullet" id="testPushbullet" />
                            <input type="submit" class="btn config_submitter" value="Save Changes" />
                        </div><!-- /content_use_pushbullet //-->

                    </fieldset>
                </div><!-- /pushbullet component-group //-->
                <div class="component-group">
                    <div class="component-group-desc">
                        <img class="notifier-icon" src="${srRoot}/images/notifiers/freemobile.png" alt="" title="Free Mobile" />
                        <h3><a href="${anon_url('http://mobile.free.fr/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Free Mobile</a></h3>
                        <p>Free Mobile is a famous French cellular network provider.<br> It provides to their customer a free SMS API.</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_freemobile">
                                <span class="component-title">Enable</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_freemobile" id="use_freemobile" ${('', 'checked="checked"')[bool(sickbeard.USE_FREEMOBILE)]}/>
                                    <p>should SickRage send SMS notifications ?</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_freemobile">
                            <div class="field-pair">
                                <label for="freemobile_notify_onsnatch">
                                    <span class="component-title">Notify on snatch</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="freemobile_notify_onsnatch" id="freemobile_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.FREEMOBILE_NOTIFY_ONSNATCH)]}/>
                                        <p>send a SMS when a download starts ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="freemobile_notify_ondownload">
                                    <span class="component-title">Notify on download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="freemobile_notify_ondownload" id="freemobile_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.FREEMOBILE_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>send a SMS when a download finishes ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="freemobile_notify_onsubtitledownload">
                                    <span class="component-title">Notify on subtitle download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="freemobile_notify_onsubtitledownload" id="freemobile_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>send a SMS when subtitles are downloaded ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="freemobile_id">
                                    <span class="component-title">Free Mobile customer ID</span>
                                    <input type="text" name="freemobile_id" id="freemobile_id" value="${sickbeard.FREEMOBILE_ID}" class="form-control input-sm input250" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">It's your Free Mobile customer ID (8 digits)</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="freemobile_password">
                                    <span class="component-title">Free Mobile API Key</span>
                                    <input type="text" name="freemobile_apikey" id="freemobile_apikey" value="${sickbeard.FREEMOBILE_APIKEY}" class="form-control input-sm input250" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">Find your API Key in your customer portal.</span>
                                </label>
                            </div>
                            <div class="testNotification" id="testFreeMobile-result">Click below to test your settings.</div>
                            <input  class="btn" type="button" value="Test SMS" id="testFreeMobile" />
                            <input type="submit" class="config_submitter btn" value="Save Changes" />
                        </div><!-- /content_use_freemobile //-->

                    </fieldset>
                </div><!-- /freemobile component-group //-->

            </div>

            <div id="tabs-3">
                <div class="component-group">
                       <div class="component-group-desc">
                        <img class="notifier-icon" src="${srRoot}/images/notifiers/twitter.png" alt="" title="Twitter"/>
                        <h3><a href="${anon_url('http://www.twitter.com/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Twitter</a></h3>
                        <p>A social networking and microblogging service, enabling its users to send and read other users' messages called tweets.</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_twitter">
                                <span class="component-title">Enable</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_twitter" id="use_twitter" ${('', 'checked="checked"')[bool(sickbeard.USE_TWITTER)]}/>
                                    <p>should SickRage post tweets on Twitter ?</p>
                                </span>
                            </label>
                            <label>
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc"><b>Note:</b> you may want to use a secondary account.</span>
                            </label>
                        </div>

                        <div id="content_use_twitter">
                            <div class="field-pair">
                                <label for="twitter_notify_onsnatch">
                                    <span class="component-title">Notify on snatch</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="twitter_notify_onsnatch" id="twitter_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.TWITTER_NOTIFY_ONSNATCH)]}/>
                                        <p>send a notification when a download starts ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="twitter_notify_ondownload">
                                    <span class="component-title">Notify on download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="twitter_notify_ondownload" id="twitter_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.TWITTER_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>send a notification when a download finishes ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="twitter_notify_onsubtitledownload">
                                    <span class="component-title">Notify on subtitle download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="twitter_notify_onsubtitledownload" id="twitter_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>send a notification when subtitles are downloaded ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="twitter_usedm">
                                    <span class="component-title">Send direct message</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="twitter_usedm" id="twitter_usedm" ${('', 'checked="checked"')[bool(sickbeard.TWITTER_USEDM)]}/>
                                        <p>send a notification via Direct Message, not via status update</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="twitter_dmto">
                                    <span class="component-title">Send DM to</span>
                                    <input type="text" name="twitter_dmto" id="twitter_dmto" value="${sickbeard.TWITTER_DMTO}" class="form-control input-sm input250" />
                                </label>
                                <p>
                                    <span class="component-desc">Twitter account to send Direct Messages to (must follow you)</span>
                                </p>
                            </div>
                            <div class="field-pair">
                                <label>
                                    <span class="component-title">Step One</span>
                                </label>
                                <label>
                                    <span style="font-size: 11px;">Click the "Request Authorization" button.<br> This will open a new page containing an auth key.<br> <b>Note:</b> if nothing happens check your popup blocker.<br></span>
                                    <input class="btn" type="button" value="Request Authorization" id="twitterStep1" />
                                </label>
                            </div>
                            <div class="field-pair">
                                <label>
                                    <span class="component-title">Step Two</span>
                                </label>
                                <label>
                                    <span style="font-size: 11px;">Enter the key Twitter gave you below, and click "Verify Key".<br><br></span>
                                    <input type="text" id="twitter_key" value="" class="form-control input-sm input350" />
                                    <input class="btn btn-inline" type="button" value="Verify Key" id="twitterStep2" />
                                </label>
                            </div>
                            <!--
                            <div class="field-pair">
                                <label>
                                    <span class="component-title">Step Three</span>
                                </label>
                            </div>
                            //-->
                            <div class="testNotification" id="testTwitter-result">Click below to test.</div>
                            <input  class="btn" type="button" value="Test Twitter" id="testTwitter" />
                            <input type="submit" class="config_submitter btn" value="Save Changes" />
                        </div><!-- /content_use_twitter //-->

                    </fieldset>
                </div><!-- /twitter component-group //-->


                <div class="component-group">
                    <div class="component-group-desc">
                        <img class="notifier-icon" src="${srRoot}/images/notifiers/trakt.png" alt="" title="Trakt"/>
                        <h3><a href="${anon_url('http://trakt.tv/')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Trakt</a></h3>
                        <p>trakt helps keep a record of what TV shows and movies you are watching. Based on your favorites, trakt recommends additional shows and movies you'll enjoy!</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_trakt">
                                <span class="component-title">Enable</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_trakt" id="use_trakt" ${('', 'checked="checked"')[bool(sickbeard.USE_TRAKT)]}/>
                                    <p>should SickRage send Trakt.tv notifications ?</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_trakt">
                            <div class="field-pair">
                                <label for="trakt_username">
                                    <span class="component-title">Trakt username</span>
                                    <input type="text" name="trakt_username" id="trakt_username" value="${sickbeard.TRAKT_USERNAME}" class="form-control input-sm input250" />
                                </label>
                                <p>
                                    <span class="component-desc">username of your Trakt account.</span>
                                </p>
                            </div>
                            <input type="hidden" id="trakt_pin_url" value="${sickbeard.TRAKT_PIN_URL}">
                            <input type="button" class="btn ${('', 'hide')[bool(sickbeard.TRAKT_ACCESS_TOKEN)]}" value="Get Trakt PIN" id="TraktGetPin" />
                            <div class="field-pair">
                                <label for="trakt_pin">
                                    <span class="component-title">Trakt PIN</span>
                                    <input type="text" name="trakt_pin" id="trakt_pin" value="" class="form-control input-sm input250" />
                                </label>
                                <p>
                                    <span class="component-desc">PIN code to authorize SickRage to access Trakt on your behalf.</span>
                                </p>
                            </div>
                            <input type="button" class="btn hide" value="Authorize SickRage" id="authTrakt" />
                            <div class="field-pair">
                                <label for="trakt_timeout">
                                    <span class="component-title">API Timeout</span>
                                    <input type="text" name="trakt_timeout" id="trakt_timeout" value="${sickbeard.TRAKT_TIMEOUT}" class="form-control input-sm input75" />
                                </label>
                                <p>
                                    <span class="component-desc">
                                        Seconds to wait for Trakt API to respond. (Use 0 to wait forever)
                                    </span>
                                </p>
                            </div>
                            <div class="field-pair">
                                <label for="trakt_default_indexer">
                                    <span class="component-title">Default indexer</span>
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
                                    <span class="component-title">Sync libraries</span>
                                    <span class="component-desc">
                                        <input type="checkbox" class="enabler" name="trakt_sync" id="trakt_sync" ${('', 'checked="checked"')[bool(sickbeard.TRAKT_SYNC)]}/>
                                        <p>sync your SickRage show library with your trakt show library.</p>
                                    </span>
                                </label>
                            </div>
                            <div id="content_trakt_sync">
                                <div class="field-pair">
                                    <label for="trakt_sync_remove">
                                        <span class="component-title">Remove Episodes From Collection</span>
                                        <span class="component-desc">
                                            <input type="checkbox" name="trakt_sync_remove" id="trakt_sync_remove" ${('', 'checked="checked"')[bool(sickbeard.TRAKT_SYNC_REMOVE)]}/>
                                            <p>Remove an Episode from your Trakt Collection if it is not in your SickRage Library.</p>
                                        </span>
                                    </label>
                                 </div>
                            </div>
                            <div class="field-pair">
                                <label for="trakt_sync_watchlist">
                                    <span class="component-title">Sync watchlist</span>
                                    <span class="component-desc">
                                        <input type="checkbox" class="enabler" name="trakt_sync_watchlist" id="trakt_sync_watchlist" ${('', 'checked="checked"')[bool(sickbeard.TRAKT_SYNC_WATCHLIST)]}/>
                                        <p>sync your SickRage show watchlist with your trakt show watchlist (either Show and Episode).</p>
                                        <p>Episode will be added on watch list when wanted or snatched and will be removed when downloaded </p>
                                    </span>
                                </label>
                            </div>
                            <div id="content_trakt_sync_watchlist">
                                <div class="field-pair">
                                    <label for="trakt_method_add">
                                        <span class="component-title">Watchlist add method</span>
                                           <select id="trakt_method_add" name="trakt_method_add" class="form-control input-sm">
                                            <option value="0" ${('', 'selected="selected"')[sickbeard.TRAKT_METHOD_ADD == 0]}>Skip All</option>
                                            <option value="1" ${('', 'selected="selected"')[sickbeard.TRAKT_METHOD_ADD == 1]}>Download Pilot Only</option>
                                            <option value="2" ${('', 'selected="selected"')[sickbeard.TRAKT_METHOD_ADD == 2]}>Get whole show</option>
                                        </select>
                                    </label>
                                    <label>
                                        <span class="component-title">&nbsp;</span>
                                        <span class="component-desc">method in which to download episodes for new show's.</span>
                                    </label>
                                </div>
                                <div class="field-pair">
                                    <label for="trakt_remove_watchlist">
                                        <span class="component-title">Remove episode</span>
                                        <span class="component-desc">
                                            <input type="checkbox" name="trakt_remove_watchlist" id="trakt_remove_watchlist" ${('', 'checked="checked"')[bool(sickbeard.TRAKT_REMOVE_WATCHLIST)]}/>
                                            <p>remove an episode from your watchlist after it is downloaded.</p>
                                        </span>
                                    </label>
                                </div>
                                <div class="field-pair">
                                    <label for="trakt_remove_serieslist">
                                        <span class="component-title">Remove series</span>
                                        <span class="component-desc">
                                            <input type="checkbox" name="trakt_remove_serieslist" id="trakt_remove_serieslist" ${('', 'checked="checked"')[bool(sickbeard.TRAKT_REMOVE_SERIESLIST)]}/>
                                            <p>remove the whole series from your watchlist after any download.</p>
                                        </span>
                                    </label>
                                </div>
                                <div class="field-pair">
                                    <label for="trakt_remove_show_from_sickrage">
                                        <span class="component-title">Remove watched show:</span>
                                        <span class="component-desc">
                                            <input type="checkbox" name="trakt_remove_show_from_sickrage" id="trakt_remove_show_from_sickrage" ${('', 'checked="checked"')[bool(sickbeard.TRAKT_REMOVE_SHOW_FROM_SICKRAGE)]}/>
                                            <p>remove the show from sickrage if it's ended and completely watched</p>
                                        </span>
                                    </label>
                                </div>
                                <div class="field-pair">
                                    <label for="trakt_start_paused">
                                        <span class="component-title">Start paused</span>
                                        <span class="component-desc">
                                            <input type="checkbox" name="trakt_start_paused" id="trakt_start_paused" ${('', 'checked="checked"')[bool(sickbeard.TRAKT_START_PAUSED)]}/>
                                            <p>show's grabbed from your trakt watchlist start paused.</p>
                                        </span>
                                    </label>
                                </div>
                            </div>
                            <div class="field-pair">
                                <label for="trakt_blacklist_name">
                                    <span class="component-title">Trakt blackList name</span>
                                    <input type="text" name="trakt_blacklist_name" id="trakt_blacklist_name" value="${sickbeard.TRAKT_BLACKLIST_NAME}" class="form-control input-sm input150" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">Name(slug) of List on Trakt for blacklisting show on 'Add Trending Show' & 'Add Recommended Shows' pages</span>
                                </label>
                            </div>
                            <div class="testNotification" id="testTrakt-result">Click below to test.</div>
                            <input type="button" class="btn" value="Test Trakt" id="testTrakt" />
                            <input type="submit" class="btn config_submitter" value="Save Changes" />
                        </div><!-- /content_use_trakt //-->
                    </fieldset>
                </div><!-- /trakt component-group //-->

                <div class="component-group">
                    <div class="component-group-desc">
                        <img class="notifier-icon" src="${srRoot}/images/notifiers/email.png" alt="" title="Email" />
                        <h3><a href="${anon_url('http://en.wikipedia.org/wiki/Comparison_of_webmail_providers')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">Email</a></h3>
                        <p>Allows configuration of email notifications on a per show basis.</p>
                    </div>
                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_email">
                                <span class="component-title">Enable</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" name="use_email" id="use_email" ${('', 'checked="checked"')[bool(sickbeard.USE_EMAIL)]}/>
                                    <p>should SickRage send email notifications ?</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_email">
                            <div class="field-pair">
                                <label for="email_notify_onsnatch">
                                    <span class="component-title">Notify on snatch</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="email_notify_onsnatch" id="email_notify_onsnatch" ${('', 'checked="checked"')[bool(sickbeard.EMAIL_NOTIFY_ONSNATCH)]}/>
                                        <p>send a notification when a download starts ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="email_notify_ondownload">
                                    <span class="component-title">Notify on download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="email_notify_ondownload" id="email_notify_ondownload" ${('', 'checked="checked"')[bool(sickbeard.EMAIL_NOTIFY_ONDOWNLOAD)]}/>
                                        <p>send a notification when a download finishes ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="email_notify_onsubtitledownload">
                                    <span class="component-title">Notify on subtitle download</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="email_notify_onsubtitledownload" id="email_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(sickbeard.EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <p>send a notification when subtitles are downloaded ?</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="email_host">
                                    <span class="component-title">SMTP host</span>
                                    <input type="text" name="email_host" id="email_host" value="${sickbeard.EMAIL_HOST}" class="form-control input-sm input250" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">hostname of your SMTP email server.</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="email_port">
                                    <span class="component-title">SMTP port</span>
                                    <input type="text" name="email_port" id="email_port" value="${sickbeard.EMAIL_PORT}" class="form-control input-sm input75" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">port number used to connect to your SMTP host.</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="email_from">
                                    <span class="component-title">SMTP from</span>
                                    <input type="text" name="email_from" id="email_from" value="${sickbeard.EMAIL_FROM}" class="form-control input-sm input250" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">sender email address, some hosts require a real address.</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="email_tls">
                                    <span class="component-title">Use TLS</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="email_tls" id="email_tls" ${('', 'checked="checked"')[bool(sickbeard.EMAIL_TLS)]}/>
                                        <p>check to use TLS encryption.</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="email_user">
                                    <span class="component-title">SMTP user</span>
                                    <input type="text" name="email_user" id="email_user" value="${sickbeard.EMAIL_USER}" class="form-control input-sm input250" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">(optional) your SMTP server username.</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="email_password">
                                    <span class="component-title">SMTP password</span>
                                    <input type="password" name="email_password" id="email_password" value="${sickbeard.EMAIL_PASSWORD}" class="form-control input-sm input250" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">(optional) your SMTP server password.</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="email_list">
                                    <span class="component-title">Global email list</span>
                                    <input type="text" name="email_list" id="email_list" value="${sickbeard.EMAIL_LIST}" class="form-control input-sm input350" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">all emails here receive notifications for <b>all</b> shows.</span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="email_show">
                                    <span class="component-title">Show notification list</span>
                                    <select name="email_show" id="email_show" class="form-control input-sm">
                                        <option value="-1">-- Select a Show --</option>
                                    </select>
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <input type="text" name="email_show_list" id="email_show_list" class="form-control input-sm input350" />
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">configure per show notifications here.</span>
                                </label>
                                <label>
                                    <span class="component-title">&nbsp;</span>
                                    <input id="email_show_save" class="btn" type="button" value="Save for this show" />
                                </label>
                            </div>

                            <div class="testNotification" id="testEmail-result">Click below to test.</div>
                            <input class="btn" type="button" value="Test Email" id="testEmail" />
                            <input class="btn" type="submit" class="config_submitter" value="Save Changes" />
                        </div><!-- /content_use_email //-->
                    </fieldset>
                </div><!-- /email component-group //-->

            </div><!-- /config-components //-->
        </form>

        <br><input type="submit" class="config_submitter btn" value="Save Changes" /><br>

    </div>
</div>

<div class="clearfix"></div>
</%block>
