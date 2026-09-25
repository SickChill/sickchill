<%inherit file="/layouts/config.mako" />
<%!
    import re
    from sickchill import settings
    from sickchill.oldbeard.filters import hide
    from sickchill.oldbeard.helpers import anon_url
    import sickchill
%>
<%block name="tabs">
    <li><a href="#notifier-list">${_('Notifier List')}</a></li>
    <li><a href="#notifier-settings">${_('Notifier Settings')}</a></li>
</%block>
<%block name="pages">
    <form id="configForm" action="saveNotifications" method="post">
        <div id="notifier-list" class="component-group">
            <div class="row">
                <div class="col-md-12">
                    <div class="component-group-desc">
                        <h3>${_('Notifier List')}</h3>
                    </div>
                </div>
            </div>
            <div id="notifier_enable_list" class="row">
                <div class="notifier-list-section col-md-4 col-sm-4 col-xs-12">
                    <h4 class="notifier-section-heading">${_('Home Theater / NAS')}</h4>
                    <ul id="notifier_enable_list_htpcnas" class="notifier_enable_list">
                        <li class="ui-state-default" id="notifier-enable-use_kodi">
                            <input type="checkbox" class="enabler" name="use_kodi" id="use_kodi" ${checked(settings.USE_KODI)}/>
                            <span class="icon-notifiers-kodi" title="KODI">
                            </span>
                            <label for="use_kodi">
                                KODI
                            </label>
                        </li>
                        <li class="ui-state-default" id="notifier-enable-use_plex_server">
                            <input type="checkbox" class="enabler" name="use_plex_server" id="use_plex_server" ${checked(settings.USE_PLEX_SERVER)}/>
                            <span class="icon-notifiers-plex" title="Plex Media Server">
                            </span>
                            <label for="use_plex_server">
                                Plex Media Server
                            </label>
                        </li>
                        <li class="ui-state-default" id="notifier-enable-use_plex_client">
                            <input type="checkbox" class="enabler" name="use_plex_client" id="use_plex_client" ${checked(settings.USE_PLEX_CLIENT)}/>
                            <span class="icon-notifiers-plexth" title="Plex Home Theater">
                            </span>
                            <label for="use_plex_client">
                                Plex Home Theater
                            </label>
                        </li>
                        <li class="ui-state-default" id="notifier-enable-use_emby">
                            <input type="checkbox" class="enabler" name="use_emby" id="use_emby" ${checked(settings.USE_EMBY)}/>
                            <span class="icon-notifiers-emby" title="Emby">
                            </span>
                            <label for="use_emby">
                                Emby
                            </label>
                        </li>
                        <li class="ui-state-default" id="notifier-enable-use_jellyfin">
                            <input type="checkbox" class="enabler" name="use_jellyfin" id="use_jellyfin" ${checked(settings.USE_JELLYFIN)}/>
                            <span class="icon-notifiers-jellyfin" title="Jellyfin">
                            </span>
                            <label for="use_jellyfin">
                                Jellyfin
                            </label>
                        </li>
                        <li class="ui-state-default" id="notifier-enable-use_nmj">
                            <input type="checkbox" class="enabler" name="use_nmj" id="use_nmj" ${checked(settings.USE_NMJ)}/>
                            <span class="icon-notifiers-nmj" title="NMJ">
                            </span>
                            <label for="use_nmj">
                                NMJ
                            </label>
                        </li>
                        <li class="ui-state-default" id="notifier-enable-use_nmjv2">
                            <input type="checkbox" class="enabler" name="use_nmjv2" id="use_nmjv2" ${checked(settings.USE_NMJv2)}/>
                            <span class="icon-notifiers-nmj" title="NMJv2">
                            </span>
                            <label for="use_nmjv2">
                                NMJv2
                            </label>
                        </li>
                        <li class="ui-state-default" id="notifier-enable-use_synoindex">
                            <input type="checkbox" class="enabler" name="use_synoindex" id="use_synoindex" ${checked(settings.USE_SYNOINDEX)}/>
                            <span class="icon-notifiers-syno1" title="Synology">
                            </span>
                            <label for="use_synoindex">
                                Synology
                            </label>
                        </li>
                        <li class="ui-state-default" id="notifier-enable-use_synologynotifier">
                            <input type="checkbox" class="enabler" name="use_synologynotifier" id="use_synologynotifier" ${checked(settings.USE_SYNOLOGYNOTIFIER)}/>
                            <span class="icon-notifiers-syno2" title="Synology Notifier">
                            </span>
                            <label for="use_synologynotifier">
                                Synology Notifier
                            </label>
                        </li>
                        <li class="ui-state-default" id="notifier-enable-use_pytivo">
                            <input type="checkbox" class="enabler" name="use_pytivo" id="use_pytivo" ${checked(settings.USE_PYTIVO)}/>
                            <span class="icon-notifiers-pytivo" title="pyTivo">
                            </span>
                            <label for="use_pytivo">
                                pyTivo
                            </label>
                        </li>
                    </ul>
                </div>
                <div class="notifier-list-section col-md-4 col-sm-4 col-xs-12">
                    <h4 class="notifier-section-heading">${_('Devices')}</h4>
                    <ul id="notifier_enable_list_devices" class="notifier_enable_list">
                        <li class="ui-state-default" id="notifier-enable-use_prowl">
                            <input type="checkbox" class="enabler" name="use_prowl" id="use_prowl" ${checked(settings.USE_PROWL)}/>
                            <span class="icon-notifiers-prowl" title="Prowl">
                            </span>
                            <label for="use_prowl">
                                Prowl
                            </label>
                        </li>
                        <li class="ui-state-default" id="notifier-enable-use_libnotify">
                            <input type="checkbox" class="enabler" name="use_libnotify" id="use_libnotify" ${checked(settings.USE_LIBNOTIFY)}/>
                            <span class="icon-notifiers-libnotify" title="Libnotify">
                            </span>
                            <label for="use_libnotify">
                                Libnotify
                            </label>
                        </li>
                        <li class="ui-state-default" id="notifier-enable-use_pushover">
                            <input type="checkbox" class="enabler" name="use_pushover" id="use_pushover" ${checked(settings.USE_PUSHOVER)}/>
                            <span class="icon-notifiers-pushover" title="Pushover">
                            </span>
                            <label for="use_pushover">
                                Pushover
                            </label>
                        </li>
                        <li class="ui-state-default" id="notifier-enable-use_pushbullet">
                            <input type="checkbox" class="enabler" name="use_pushbullet" id="use_pushbullet" ${checked(settings.USE_PUSHBULLET)}/>
                            <span class="icon-notifiers-pushbullet" title="Pushbullet">
                            </span>
                            <label for="use_pushbullet">
                                Pushbullet
                            </label>
                        </li>
                        <li class="ui-state-default" id="notifier-enable-use_freemobile">
                            <input type="checkbox" class="enabler" name="use_freemobile" id="use_freemobile" ${checked(settings.USE_FREEMOBILE)}/>
                            <span class="icon-notifiers-freemobile" title="Free Mobile">
                            </span>
                            <label for="use_freemobile">
                                Free Mobile
                            </label>
                        </li>
                        <li class="ui-state-default" id="notifier-enable-use_join">
                            <input type="checkbox" class="enabler" name="use_join" id="use_join" ${checked(settings.USE_JOIN)}/>
                            <span class="icon-notifiers-join" title="Join">
                            </span>
                            <label for="use_join">
                                Join
                            </label>
                        </li>
                        <li class="ui-state-default" id="notifier-enable-use_gotify">
                            <input type="checkbox" class="enabler" name="use_gotify" id="use_gotify" ${checked(settings.USE_GOTIFY)}/>
                            <span class="icon-notifiers-gotify" title="Gotify">
                            </span>
                            <label for="use_gotify">
                                Gotify
                            </label>
                        </li>
                    </ul>
                </div>
                <div class="notifier-list-section col-md-4 col-sm-4 col-xs-12">
                    <h4 class="notifier-section-heading">${_('Social')}</h4>
                    <ul id="notifier_enable_list_social" class="notifier_enable_list">
                        <li class="ui-state-default" id="notifier-enable-use_discord">
                            <input type="checkbox" class="enabler" name="use_discord" id="use_discord" ${checked(settings.USE_DISCORD)}/>
                            <span class="icon-notifiers-discord" title="Discord">
                            </span>
                            <label for="use_discord">
                                Discord
                            </label>
                        </li>
                        <li class="ui-state-default" id="notifier-enable-use_twitter">
                            <input type="checkbox" class="enabler" name="use_twitter" id="use_twitter" ${checked(settings.USE_TWITTER)}/>
                            <span class="icon-notifiers-twitter" title="X">
                            </span>
                            <label for="use_twitter">
                                X
                            </label>
                        </li>
                        <li class="ui-state-default" id="notifier-enable-use_telegram">
                            <input type="checkbox" class="enabler" name="use_telegram" id="use_telegram" ${checked(settings.USE_TELEGRAM)}/>
                            <span class="icon-notifiers-telegram" title="Telegram">
                            </span>
                            <label for="use_telegram">
                                Telegram
                            </label>
                        </li>
                        <li class="ui-state-default" id="notifier-enable-use_trakt">
                            <input type="checkbox" class="enabler" name="use_trakt" id="use_trakt" ${checked(settings.USE_TRAKT)}/>
                            <span class="icon-notifiers-trakt" title="Trakt">
                            </span>
                            <label for="use_trakt">
                                Trakt
                            </label>
                        </li>
                        <li class="ui-state-default" id="notifier-enable-use_email">
                            <input type="checkbox" class="enabler" name="use_email" id="use_email" ${checked(settings.USE_EMAIL)}/>
                            <span class="icon-notifiers-email" title="Email">
                            </span>
                            <label for="use_email">
                                Email
                            </label>
                        </li>
                        <li class="ui-state-default" id="notifier-enable-use_slack">
                            <input type="checkbox" class="enabler" name="use_slack" id="use_slack" ${checked(settings.USE_SLACK)}/>
                            <span class="icon-notifiers-slack" title="Slack">
                            </span>
                            <label for="use_slack">
                                Slack
                            </label>
                        </li>
                        <li class="ui-state-default" id="notifier-enable-use_mattermost">
                            <input type="checkbox" class="enabler" name="use_mattermost" id="use_mattermost" ${checked(settings.USE_MATTERMOST)}/>
                            <span class="icon-notifiers-matters" title="Mattermost Webhook">
                            </span>
                            <label for="use_mattermost">
                                Mattermost Webhook
                            </label>
                        </li>
                        <li class="ui-state-default" id="notifier-enable-use_mattermostbot">
                            <input type="checkbox" class="enabler" name="use_mattermostbot" id="use_mattermostbot" ${checked(settings.USE_MATTERMOSTBOT)}/>
                            <span class="icon-notifiers-matters" title="Mattermost Bot">
                            </span>
                            <label for="use_mattermostbot">
                                Mattermost Bot
                            </label>
                        </li>
                        <li class="ui-state-default" id="notifier-enable-use_rocketchat">
                            <input type="checkbox" class="enabler" name="use_rocketchat" id="use_rocketchat" ${checked(settings.USE_ROCKETCHAT)}/>
                            <span class="icon-notifiers-rocketchat" title="Rocket.Chat">
                            </span>
                            <label for="use_rocketchat">
                                Rocket.Chat
                            </label>
                        </li>
                        <li class="ui-state-default" id="notifier-enable-use_matrix">
                            <input type="checkbox" class="enabler" name="use_matrix" id="use_matrix" ${checked(settings.USE_MATRIX)}/>
                            <span class="icon-notifiers-matrix" title="Matrix">
                            </span>
                            <label for="use_matrix">
                                Matrix
                            </label>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
        <div id="notifier-settings" class="component-group">
            <div class="row">
                <div class="col-md-12">
                    <div class="component-group-desc">
                        <h3>${_('Notifier Settings')}</h3>
                    </div>
                </div>
            </div>
            <div id="notifier-settings-empty" class="alert alert-info" hidden>
                ${_('No notifiers enabled. Enable one or more on the Notifier List tab to configure them here.')}
            </div>
            <div class="notifier-settings-box" id="notifier-settings-box-use_kodi" data-notifier="use_kodi" ${hidden(settings.USE_KODI)}>
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <span class="icon-notifiers-kodi" title="KODI">
                            </span>
                            <h3>
                                <a href="${anon_url('http://kodi.tv/')}" rel="noreferrer" target="_blank">
                                    KODI
                                </a>
                            </h3>
                            <p>${_('A free and open source cross-platform media center and home entertainment system software with a 10-foot user interface designed for the living-room TV.')}</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <!-- content_use_kodi //-->
                            <div id="content_use_kodi" ${hidden(settings.USE_KODI)}>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Always on')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="kodi_always_on" id="kodi_always_on" ${checked(settings.KODI_ALWAYS_ON)}/>
                                        <label for="kodi_always_on">${_('log errors when unreachable?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on snatch')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="kodi_notify_onsnatch" id="kodi_notify_onsnatch" ${checked(settings.KODI_NOTIFY_ONSNATCH)}/>
                                        <label for="kodi_notify_onsnatch">${_('send a notification when a download starts?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="kodi_notify_ondownload" id="kodi_notify_ondownload" ${checked(settings.KODI_NOTIFY_ONDOWNLOAD)}/>
                                        <label for="kodi_notify_ondownload">${_('send a notification when a download finishes?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on subtitle download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="kodi_notify_onsubtitledownload" id="kodi_notify_onsubtitledownload" ${checked(settings.KODI_NOTIFY_ONSUBTITLEDOWNLOAD)}/>
                                        <label for="kodi_notify_onsubtitledownload">${_('send a notification when subtitles are downloaded?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Update library')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="kodi_update_library" id="kodi_update_library" ${checked(settings.KODI_UPDATE_LIBRARY)}/>
                                        <label for="kodi_update_library">${_('update KODI library when a download finishes?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Full library update')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="kodi_update_full" id="kodi_update_full" ${checked(settings.KODI_UPDATE_FULL)}/>
                                        <label for="kodi_update_full">${_('perform a full library update if update per-show fails?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Only update first host')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="kodi_update_onlyfirst" id="kodi_update_onlyfirst" ${checked(settings.KODI_UPDATE_ONLYFIRST)}/>
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
                                                <input type="text" name="kodi_host" id="kodi_host" value="${settings.KODI_HOST}" class="form-control input-sm input350" autocapitalize="off" />
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
                                        <label class="component-title">${_('Username')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" name="kodi_username" id="kodi_username" value="${settings.KODI_USERNAME}" class="form-control input-sm input250" autocapitalize="off" autocomplete="no" />
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
                                        <label class="component-title">${_('Password')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input
                                                    type="password" name="kodi_password" id="kodi_password" value="${settings.KODI_PASSWORD|hide}"
                                                    class="form-control input-sm input250" autocomplete="no" autocapitalize="off"
                                                />
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
                                        <div class="testNotification" id="testKODI-result">
                                            ${_('Click below to test.')}
                                        </div>
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
            </div>
            <div class="notifier-settings-box" id="notifier-settings-box-use_plex_server" data-notifier="use_plex_server" ${hidden(settings.USE_PLEX_SERVER)}>
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <span class="icon-notifiers-plex" title="Plex Media Server">
                            </span>
                            <h3>
                                <a href="${anon_url('http://www.plexapp.com/')}" rel="noreferrer" target="_blank">
                                    Plex Media Server
                                </a>
                            </h3>
                            <p>${_('Experience your media on a visually stunning, easy to use interface on your Mac connected to your TV. Your media library has never looked this good!')}</p>
                            <p class="plexinfo hide">${_('For sending notifications to Plex Home Theater (PHT) clients, use the KODI notifier with port<b>3005</b>.')}</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div id="content_use_plex_server" ${hidden(settings.USE_PLEX_SERVER)}>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Plex Media Server Auth Token')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" name="plex_server_token" id="plex_server_token" value="${settings.PLEX_SERVER_TOKEN}" class="form-control input-sm input350" autocapitalize="off" />
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="plex_server_token">${_('auth token used by Plex')}</label>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <span class="component-desc">
                                                    (
                                                    <a href="${anon_url('https://support.plex.tv/hc/en-us/articles/204059436-Finding-your-account-token-X-Plex-Token')}" rel="noreferrer" target="_blank">
                                                        <u>
                                                            Finding your account token
                                                        </u>
                                                    </a>
                                                    )
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
                                                <input type="text" name="plex_server_username" id="plex_server_username" value="${settings.PLEX_SERVER_USERNAME}" class="form-control input-sm input250" autocapitalize="off" autocomplete="no" />
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
                                                <input
                                                    type="password" name="plex_server_password" id="plex_server_password"
                                                    value="${settings.PLEX_SERVER_PASSWORD|hide}" class="form-control input-sm input250"
                                                    autocomplete="no" autocapitalize="off"
                                                />
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
                                        <input type="checkbox" class="enabler" name="plex_update_library" id="plex_update_library" ${checked(settings.PLEX_UPDATE_LIBRARY)}/>
                                        <label for="plex_update_library">${_('update Plex Media Server library when a download finishes')}</label>
                                    </div>
                                </div>
                                <div id="content_plex_update_library" ${hidden(settings.PLEX_UPDATE_LIBRARY)}>
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Plex Media Server IP:Port')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="text" name="plex_server_host" id="plex_server_host" value="${re.sub(r'\b,\b', ', ', settings.PLEX_SERVER_HOST or '')}" class="form-control input-sm input350" autocapitalize="off" />
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
                                            <input type="checkbox" name="plex_server_https" id="plex_server_https" ${checked(settings.PLEX_SERVER_HTTPS)}/>
                                            <label for="plex_server_https">${_('use https for plex media server requests?')}</label>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <div class="testNotification" id="testPMS-result">
                                                ${_('Click below to test Plex Media Server(s)')}
                                            </div>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input class="btn" type="button" value="${_('Test Plex Media Server')}" id="testPMS" />
                                        </div>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                    </div>
                                </div>
                            </div>
                        </fieldset>
                    </div>
                </div>
            </div>
            <div class="notifier-settings-box" id="notifier-settings-box-use_plex_client" data-notifier="use_plex_client" ${hidden(settings.USE_PLEX_CLIENT)}>
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <span class="icon-notifiers-plexth" title="Plex Home Theater">
                            </span>
                            <h3>
                                <a href="${anon_url('http://www.plexapp.com/')}" rel="noreferrer" target="_blank">
                                    Plex Home Theater
                                </a>
                            </h3>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div id="content_use_plex_client" ${hidden(settings.USE_PLEX_CLIENT)}>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on snatch')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="plex_notify_onsnatch" id="plex_notify_onsnatch" ${checked(settings.PLEX_NOTIFY_ONSNATCH)}/>
                                        <label for="plex_notify_onsnatch">${_('send a notification when a download starts?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="plex_notify_ondownload" id="plex_notify_ondownload" ${checked(settings.PLEX_NOTIFY_ONDOWNLOAD)}/>
                                        <label for="plex_notify_ondownload">${_('send a notification when a download finishes?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on subtitle download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="plex_notify_onsubtitledownload" id="plex_notify_onsubtitledownload" ${checked(settings.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD)}/>
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
                                                <input type="text" name="plex_client_host" id="plex_client_host" value="${settings.PLEX_CLIENT_HOST}" class="form-control input-sm input350" autocapitalize="off" />
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
                                                <input type="text" name="plex_client_username" id="plex_client_username" value="${settings.PLEX_CLIENT_USERNAME}" class="form-control input-sm input250" autocapitalize="off" autocomplete="no" />
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
                                                <input
                                                    type="password" name="plex_client_password" id="plex_client_password"
                                                    value="${settings.PLEX_CLIENT_PASSWORD|hide}" class="form-control input-sm input250"
                                                    autocomplete="no" autocapitalize="off"
                                                />
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
                                        <div class="testNotification" id="testPHT-result">
                                            ${_('Click below to test Plex Home Theater(s)')}
                                        </div>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <input class="btn" type="button" value="${_('Test Plex Home Theater')}" id="testPHT" />
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <label><b>${_('note')}:</b>&nbsp;${_('some Plex Home Theaters <b class="boldest">do not</b> support notifications e.g. Plexapp for Samsung TVs')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                    </div>
                                </div>
                            </div>
                            <!-- /content_use_plex_client -->
                        </fieldset>
                    </div>
                </div>
            </div>
            <div class="notifier-settings-box" id="notifier-settings-box-use_emby" data-notifier="use_emby" ${hidden(settings.USE_EMBY)}>
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <span class="icon-notifiers-emby" title="Emby">
                            </span>
                            <h3>
                                <a href="${anon_url('http://emby.media/')}" rel="noreferrer" target="_blank">
                                    Emby
                                </a>
                            </h3>
                            <p>${_('A home media server built using other popular open source technologies.')}</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div id="content_use_emby" ${hidden(settings.USE_EMBY)}>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Emby IP:Port')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" name="emby_host" id="emby_host" value="${settings.EMBY_HOST}" class="form-control input-sm input250" autocapitalize="off" />
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="emby_host">${_('host running Emby (eg. https://192.168.1.100:8920 or http://192.168.1.100:8096)')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label for="emby_apikey" class="component-title">${_('Emby API Key')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" name="emby_apikey" id="emby_apikey" value="${settings.EMBY_APIKEY}" class="form-control input-sm input250" autocapitalize="off" />
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="emby_apikey">${_('Generated from Emby > Settings > Advanced > API keys')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <div class="testNotification" id="testEMBY-result">
                                            ${_('Click below to test.')}
                                        </div>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <input class="btn" type="button" value="Test Emby" id="testEMBY" />
                                        <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                    </div>
                                </div>
                            </div>
                        </fieldset>
                    </div>
                </div>
            </div>
            <div class="notifier-settings-box" id="notifier-settings-box-use_jellyfin" data-notifier="use_jellyfin" ${hidden(settings.USE_JELLYFIN)}>
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <span class="icon-notifiers-jellyfin" title="Jellyfin">
                            </span>
                            <h3>
                                <a href="${anon_url('http://jellyfin.org/')}" rel="noreferrer" target="_blank">
                                    Jellyfin
                                </a>
                            </h3>
                            <p>${_('Jellyfin is a volunteer-built media solution that puts you in control of your media. Stream to any device from your own server, with no strings attached. Your media, your server, your way.')}</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div id="content_use_jellyfin" ${hidden(settings.USE_JELLYFIN)}>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Jellyfin Address:')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" name="jellyfin_host" id="jellyfin_host" value="${settings.JELLYFIN_HOST}" class="form-control input-sm input250" autocapitalize="off" />
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="jellyfin_host">${_('Host running Jellyfin (eg. https://jellyfin.example.com/ or http://192.168.1.100:8096)')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label for="jellyfin_apikey" class="component-title">${_('Jellyfin API Key')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="text" name="jellyfin_apikey" id="jellyfin_apikey" value="${settings.JELLYFIN_APIKEY}" class="form-control input-sm input250" autocapitalize="off" />
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <div class="testNotification" id="testJELLYFIN-result">
                                            ${_('Click below to test.')}
                                        </div>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <input class="btn" type="button" value="Test Jellyfin" id="testJELLYFIN" />
                                        <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                    </div>
                                </div>
                            </div>
                        </fieldset>
                    </div>
                </div>
            </div>
            <div class="notifier-settings-box" id="notifier-settings-box-use_nmj" data-notifier="use_nmj" ${hidden(settings.USE_NMJ)}>
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <span class="icon-notifiers-nmj" title="NMJ">
                            </span>
                            <h3>
                                <a href="${anon_url('http://www.popcornhour.com/')}" rel="noreferrer" target="_blank">
                                    NMJ
                                </a>
                            </h3>
                            <p>${_('The Networked Media Jukebox, or NMJ, is the official media jukebox interface made available for the Popcorn Hour 200-series.')}</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div id="content_use_nmj" ${hidden(settings.USE_NMJ)}>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Popcorn IP address')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" name="nmj_host" id="nmj_host" value="${settings.NMJ_HOST}" class="form-control input-sm input250" autocapitalize="off" />
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
                                                <input type="text" name="nmj_database" id="nmj_database" value="${settings.NMJ_DATABASE}" class="form-control input-sm input250" ${(' readonly="readonly"', '')[settings.NMJ_DATABASE is True]} autocapitalize="off" />
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
                                                <input type="text" name="nmj_mount" id="nmj_mount" value="${settings.NMJ_MOUNT}" class="form-control input-sm input250" ${(' readonly="readonly"', '')[settings.NMJ_MOUNT is True]} autocapitalize="off" />
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
                                        <div class="testNotification" id="testNMJ-result">
                                            ${_('Click below to test.')}
                                        </div>
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
            </div>
            <div class="notifier-settings-box" id="notifier-settings-box-use_nmjv2" data-notifier="use_nmjv2" ${hidden(settings.USE_NMJv2)}>
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <span class="icon-notifiers-nmj" title="NMJv2">
                            </span>
                            <h3>
                                <a href="${anon_url('http://www.popcornhour.com/')}" rel="noreferrer" target="_blank">
                                    NMJv2
                                </a>
                            </h3>
                            <p>${_('The Networked Media Jukebox, or NMJv2, is the official media jukebox interface made available for the Popcorn Hour 300 & 400-series.')}</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div id="content_use_nmjv2" ${hidden(settings.USE_NMJv2)}>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Popcorn IP address')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" name="nmjv2_host" id="nmjv2_host" value="${settings.NMJv2_HOST}" class="form-control input-sm input250" autocapitalize="off" />
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
                                                <input type="radio" NAME="nmjv2_dbloc" VALUE="local" id="NMJV2_DBLOC_A" ${checked(settings.NMJv2_DBLOC == 'local')}/>
                                                <label for="NMJV2_DBLOC_A">
                                                    PCH Local Media
                                                </label>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="radio" NAME="nmjv2_dbloc" VALUE="network" id="NMJV2_DBLOC_B" ${checked(settings.NMJv2_DBLOC == 'network')}/>
                                                <label for="NMJV2_DBLOC_B">
                                                    PCH Network Media
                                                </label>
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
                                                    <option value="0">
                                                        #1
                                                    </option>
                                                    <option value="1">
                                                        #2
                                                    </option>
                                                    <option value="2">
                                                        #3
                                                    </option>
                                                    <option value="3">
                                                        #4
                                                    </option>
                                                    <option value="4">
                                                        #5
                                                    </option>
                                                    <option value="5">
                                                        #6
                                                    </option>
                                                    <option value="6">
                                                        #7
                                                    </option>
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
                                                <input type="text" name="nmjv2_database" id="nmjv2_database" value="${settings.NMJv2_DATABASE}" class="form-control input-sm input250" ${(' readonly="readonly"', '')[settings.NMJv2_DATABASE is True]} autocapitalize="off" />
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
                                        <div class="testNotification" id="testNMJv2-result">
                                            Click below to test.
                                        </div>
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
            </div>
            <div class="notifier-settings-box" id="notifier-settings-box-use_synoindex" data-notifier="use_synoindex" ${hidden(settings.USE_SYNOINDEX)}>
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <span class="icon-notifiers-syno1" title="Synology">
                            </span>
                            <h3>
                                <a href="${anon_url('http://synology.com/')}" rel="noreferrer" target="_blank">
                                    Synology
                                </a>
                            </h3>
                            <p>${_('The Synology DiskStation NAS.')}</p>
                            <p>${_('Synology Indexer is the daemon running on the Synology NAS to build its media database.')}</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div class="row">
                                <div class="col-md-12">
                                    <label><b>${_('note')}:</b>&nbsp;${_('requires SickChill to be running on your Synology NAS.')}</label>
                                </div>
                            </div>
                            <div id="content_use_synoindex" ${hidden(settings.USE_SYNOINDEX)}>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                    </div>
                                </div>
                            </div>
                        </fieldset>
                    </div>
                </div>
            </div>
            <div class="notifier-settings-box" id="notifier-settings-box-use_synologynotifier" data-notifier="use_synologynotifier" ${hidden(settings.USE_SYNOLOGYNOTIFIER)}>
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <span class="icon-notifiers-syno2" title="Synology Notifier">
                            </span>
                            <h3>
                                <a href="${anon_url('http://synology.com/')}" rel="noreferrer" target="_blank">
                                    Synology Notifier
                                </a>
                            </h3>
                            <p>${_('Synology Notifier is the notification system of Synology DSM')}</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div class="row">
                                <div class="col-md-12">
                                    <label><b>${_('note')}:</b>&nbsp;${_('requires SickChill to be running on your Synology NAS (DSM 6 only).')}</label>
                                </div>
                            </div>
                            <div id="content_use_synologynotifier" ${hidden(settings.USE_SYNOLOGYNOTIFIER)}>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on snatch')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="synologynotifier_notify_onsnatch" id="synologynotifier_notify_onsnatch" ${checked(settings.SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH)}/>
                                        <label for="synologynotifier_notify_onsnatch">${_('send a notification when a download starts?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="synologynotifier_notify_ondownload" id="synologynotifier_notify_ondownload" ${checked(settings.SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD)}/>
                                        <label for="synologynotifier_notify_ondownload">${_('send a notification when a download finishes?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on subtitle download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="synologynotifier_notify_onsubtitledownload" id="synologynotifier_notify_onsubtitledownload" ${checked(settings.SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD)}/>
                                        <label for="synologynotifier_notify_onsubtitledownload">${_('send a notification when subtitles are downloaded?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                    </div>
                                </div>
                            </div>
                        </fieldset>
                    </div>
                </div>
            </div>
            <div class="notifier-settings-box" id="notifier-settings-box-use_pytivo" data-notifier="use_pytivo" ${hidden(settings.USE_PYTIVO)}>
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <span class="icon-notifiers-pytivo" title="pyTivo">
                            </span>
                            <h3>
                                <a href="${anon_url('http://pytivo.sourceforge.net/wiki/index.php/PyTivo')}" rel="noreferrer" target="_blank">
                                    pyTivo
                                </a>
                            </h3>
                            <p>${_('pyTivo is both an HMO and GoBack server. This notifier will load the completed downloads to your Tivo.')}</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div class="row">
                                <div class="col-md-12">
                                    <label><b>${_('note')}:</b>&nbsp;${_('requires the downloaded files to be accessible by pyTivo.')}</label>
                                </div>
                            </div>
                            <div id="content_use_pytivo" ${hidden(settings.USE_PYTIVO)}>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('pyTivo IP:Port')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" name="pytivo_host" id="pytivo_host" value="${settings.PYTIVO_HOST}" class="form-control input-sm input250" autocapitalize="off" />
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
                                                <input type="text" name="pytivo_share_name" id="pytivo_share_name" value="${settings.PYTIVO_SHARE_NAME}" class="form-control input-sm input250" autocapitalize="off" />
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
                                                <input type="text" name="pytivo_tivo_name" id="pytivo_tivo_name" value="${settings.PYTIVO_TIVO_NAME}" class="form-control input-sm input250" autocapitalize="off" />
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="pytivo_tivo_name">${_('(Messages &amp; Settings > Account &amp; System Information > System Information > DVR name)')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                    </div>
                                </div>
                            </div>
                        </fieldset>
                    </div>
                </div>
            </div>
            <div class="notifier-settings-box" id="notifier-settings-box-use_prowl" data-notifier="use_prowl" ${hidden(settings.USE_PROWL)}>
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <span class="icon-notifiers-prowl" title="Prowl">
                            </span>
                            <h3>
                                <a href="${anon_url('http://www.prowlapp.com/')}" rel="noreferrer" target="_blank">
                                    Prowl
                                </a>
                            </h3>
                            <p>${_('A Growl client for iOS.')}</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div id="content_use_prowl" ${hidden(settings.USE_PROWL)}>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on snatch')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="prowl_notify_onsnatch" id="prowl_notify_onsnatch" ${checked(settings.PROWL_NOTIFY_ONSNATCH)}/>
                                        <label for="prowl_notify_onsnatch">${_('send a notification when a download starts?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="prowl_notify_ondownload" id="prowl_notify_ondownload" ${checked(settings.PROWL_NOTIFY_ONDOWNLOAD)}/>
                                        <label for="prowl_notify_ondownload">${_('send a notification when a download finishes?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on subtitle download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="prowl_notify_onsubtitledownload" id="prowl_notify_onsubtitledownload" ${checked(settings.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD)}/>
                                        <label for="prowl_notify_onsubtitledownload">${_('send a notification when subtitles are downloaded?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label for="prowl_message_title" class="component-title">${_('Prowl Message Title')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="text" name="prowl_message_title" id="prowl_message_title" value="${settings.PROWL_MESSAGE_TITLE}" class="form-control input-sm input250" autocapitalize="off" />
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label for="prowl_api" class="component-title">${_('Global Prowl API key(s)')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" name="prowl_api" id="prowl_api" value="${settings.PROWL_API}" class="form-control input-sm input250" autocapitalize="off" />
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="prowl_api">${_('''Prowl API(s) listed here, separated by commas if applicable, will<br>receive notifications for <b>all</b>shows. Your Prowl API key is available at:''')}
                                                    <a href="${anon_url('https://www.prowlapp.com/api_settings.php')}" rel="noreferrer" target="_blank">https://www.prowlapp.com/api_settings.php</a><br>${_('(this field may be blank except when testing.)')}
                                                </label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label for="prowl_show" class="component-title">${_('Show notification list')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <select name="prowl_show" id="prowl_show" class="form-control input-sm input350">
                                                    <option value="-1">
                                                        ${_('-- Select a Show --')}
                                                    </option>
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
                                                    <option value="-2" ${selected(settings.PROWL_PRIORITY == '-2')}>
                                                        ${_('Very Low')}
                                                    </option>
                                                    <option value="-1" ${selected(settings.PROWL_PRIORITY == '-1')}>
                                                        ${_('Moderate')}
                                                    </option>
                                                    <option value="0" ${selected(settings.PROWL_PRIORITY == '0')}>
                                                        ${_('Normal')}
                                                    </option>
                                                    <option value="1" ${selected(settings.PROWL_PRIORITY == '1')}>
                                                        ${_('High')}
                                                    </option>
                                                    <option value="2" ${selected(settings.PROWL_PRIORITY == '2')}>
                                                        ${_('Emergency')}
                                                    </option>
                                                </select>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="prowl_priority">${_('priority of Prowl messages from SickChill.')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="testNotification" id="testProwl-result">${_('Click below to test.')}</div>
                                <div>
                                    <input  class="btn" type="button" value="Test Prowl" id="testProwl" />
                                    <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                </div>
                            </div>
                        </fieldset>
                    </div>
                </div>
            </div>
            <div class="notifier-settings-box" id="notifier-settings-box-use_libnotify" data-notifier="use_libnotify" ${hidden(settings.USE_LIBNOTIFY)}>
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <span class="icon-notifiers-libnotify" title="Libnotify">
                            </span>
                            <h3>
                                <a href="${anon_url('http://library.gnome.org/devel/libnotify/')}" rel="noreferrer" target="_blank">
                                    Libnotify
                                </a>
                            </h3>
                            <p>${_('The standard desktop notification API for Linux/*nix systems.  This notifier will only function if the pynotify module is installed (Ubuntu/Debian package <a href="apt:python-notify">python-notify</a>).')}</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div id="content_use_libnotify" ${hidden(settings.USE_LIBNOTIFY)}>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on snatch')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="libnotify_notify_onsnatch" id="libnotify_notify_onsnatch" ${checked(settings.LIBNOTIFY_NOTIFY_ONSNATCH)}/>
                                        <label for="libnotify_notify_onsnatch">${_('send a notification when a download starts?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="libnotify_notify_ondownload" id="libnotify_notify_ondownload" ${checked(settings.LIBNOTIFY_NOTIFY_ONDOWNLOAD)}/>
                                        <label for="libnotify_notify_ondownload">${_('send a notification when a download finishes?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on subtitle download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="libnotify_notify_onsubtitledownload" id="libnotify_notify_onsubtitledownload" ${checked(settings.LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD)}/>
                                        <label for="libnotify_notify_onsubtitledownload">${_('send a notification when subtitles are downloaded?')}</label>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <div class="testNotification" id="testLibnotify-result">
                                            ${_('Click below to test.')}
                                        </div>
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
            </div>
            <div class="notifier-settings-box" id="notifier-settings-box-use_pushover" data-notifier="use_pushover" ${hidden(settings.USE_PUSHOVER)}>
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <span class="icon-notifiers-pushover" title="Pushover">
                            </span>
                            <h3>
                                <a href="${anon_url('https://pushover.net/apps/clone/sickchill')}" rel="noreferrer" target="_blank">
                                    Pushover
                                </a>
                            </h3>
                            <p>${_('Pushover makes it easy to send real-time notifications to your Android and iOS devices.')}</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div id="content_use_pushover" ${hidden(settings.USE_PUSHOVER)}>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on snatch')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="pushover_notify_onsnatch" id="pushover_notify_onsnatch" ${checked(settings.PUSHOVER_NOTIFY_ONSNATCH)}/>
                                        <label for="pushover_notify_onsnatch">${_('send a notification when a download starts?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="pushover_notify_ondownload" id="pushover_notify_ondownload" ${checked(settings.PUSHOVER_NOTIFY_ONDOWNLOAD)}/>
                                        <label for="pushover_notify_ondownload">${_('send a notification when a download finishes?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on subtitle download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="pushover_notify_onsubtitledownload" id="pushover_notify_onsubtitledownload" ${checked(settings.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD)}/>
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
                                                <input type="text" name="pushover_userkey" id="pushover_userkey" value="${settings.PUSHOVER_USERKEY}" class="form-control input-sm input250" autocapitalize="off" autocomplete="no" />
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
                                                <input type="text" name="pushover_apikey" id="pushover_apikey" value="${settings.PUSHOVER_APIKEY}" class="form-control input-sm input250" autocapitalize="off" />
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="pushover_apikey">
                                                    <a href="${anon_url('https://pushover.net/apps/clone/sickchill')}" rel="noreferrer" target="_blank">
                                                        <b>
                                                            ${_('click here')}
                                                        </b>
                                                    </a>
                                                    ${_(' to create a Pushover API key')}
                                                </label>
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
                                                <input type="text" name="pushover_device" id="pushover_device" value="${settings.PUSHOVER_DEVICE}" class="form-control input-sm input250" autocapitalize="off" />
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
                                        <label for="pushover_sound" class="component-title">${_('Pushover notification sound')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <select id="pushover_sound" name="pushover_sound" class="form-control input-sm input250">
                                                    <option value="pushover" ${selected(settings.PUSHOVER_SOUND == 'pushover')}>
                                                        ${_('Pushover')}
                                                    </option>
                                                    <option value="bike" ${selected(settings.PUSHOVER_SOUND == 'bike')}>
                                                        ${_('Bike')}
                                                    </option>
                                                    <option value="bugle" ${selected(settings.PUSHOVER_SOUND == 'bugle')}>
                                                        ${_('Bugle')}
                                                    </option>
                                                    <option value="cashregister" ${selected(settings.PUSHOVER_SOUND == 'cashregister')}>
                                                        ${_('Cash Register')}
                                                    </option>
                                                    <option value="classical" ${selected(settings.PUSHOVER_SOUND == 'classical')}>
                                                        ${_('Classical')}
                                                    </option>
                                                    <option value="cosmic" ${selected(settings.PUSHOVER_SOUND == 'cosmic')}>
                                                        ${_('Cosmic')}
                                                    </option>
                                                    <option value="falling" ${selected(settings.PUSHOVER_SOUND == 'falling')}>
                                                        ${_('Falling')}
                                                    </option>
                                                    <option value="gamelan" ${selected(settings.PUSHOVER_SOUND == 'gamelan')}>
                                                        ${_('Gamelan')}
                                                    </option>
                                                    <option value="incoming" ${selected(settings.PUSHOVER_SOUND == 'incoming')}>
                                                        ${_('Incoming')}
                                                    </option>
                                                    <option value="intermission" ${selected(settings.PUSHOVER_SOUND == 'intermission')}>
                                                        ${_('Intermission')}
                                                    </option>
                                                    <option value="magic" ${selected(settings.PUSHOVER_SOUND == 'magic')}>
                                                        ${_('Magic')}
                                                    </option>
                                                    <option value="mechanical" ${selected(settings.PUSHOVER_SOUND == 'mechanical')}>
                                                        ${_('Mechanical')}
                                                    </option>
                                                    <option value="pianobar" ${selected(settings.PUSHOVER_SOUND == 'pianobar')}>
                                                        ${_('Piano Bar')}
                                                    </option>
                                                    <option value="siren" ${selected(settings.PUSHOVER_SOUND == 'siren')}>
                                                        ${_('Siren')}
                                                    </option>
                                                    <option value="spacealarm" ${selected(settings.PUSHOVER_SOUND == 'spacealarm')}>
                                                        ${_('Space Alarm')}
                                                    </option>
                                                    <option value="tugboat" ${selected(settings.PUSHOVER_SOUND == 'tugboat')}>
                                                        ${_('Tug Boat')}
                                                    </option>
                                                    <option value="alien" ${selected(settings.PUSHOVER_SOUND == 'alien')}>
                                                        ${_('Alien Alarm (long)')}
                                                    </option>
                                                    <option value="climb" ${selected(settings.PUSHOVER_SOUND == 'climb')}>
                                                        ${_('Climb (long)')}
                                                    </option>
                                                    <option value="persistent" ${selected(settings.PUSHOVER_SOUND == 'persistent')}>
                                                        ${_('Persistent (long)')}
                                                    </option>
                                                    <option value="echo" ${selected(settings.PUSHOVER_SOUND == 'echo')}>
                                                        ${_('Pushover Echo (long)')}
                                                    </option>
                                                    <option value="updown" ${selected(settings.PUSHOVER_SOUND == 'updown')}>
                                                        ${_('Up Down (long)')}
                                                    </option>
                                                    <option value="none" ${selected(settings.PUSHOVER_SOUND == 'none')}>
                                                        ${_('None (silent)')}
                                                    </option>
                                                    <option value="default" ${selected(settings.PUSHOVER_SOUND == 'default')}>
                                                        ${_('Device specific')}
                                                    </option>
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
                                        <label for="pushover_priority" class="component-title">${_('Pushover priority')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <select id="pushover_priority" name="pushover_priority" class="form-control input-sm input250">
                                                    <option value="-2" ${selected(settings.PUSHOVER_PRIORITY == '-2')}>
                                                        ${_('Very Low')}
                                                    </option>
                                                    <option value="-1" ${selected(settings.PUSHOVER_PRIORITY == '-1')}>
                                                        ${_('Moderate')}
                                                    </option>
                                                    <option value="0" ${selected(settings.PUSHOVER_PRIORITY == '0')}>
                                                        ${_('Normal')}
                                                    </option>
                                                    <option value="1" ${selected(settings.PUSHOVER_PRIORITY == '1')}>
                                                        ${_('High')}
                                                    </option>
                                                    <option value="2" ${selected(settings.PUSHOVER_PRIORITY == '2')}>
                                                        ${_('Emergency')}
                                                    </option>
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
                                        <div class="testNotification" id="testPushover-result">
                                            ${_('Click below to test.')}
                                        </div>
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
            </div>
            <div class="notifier-settings-box" id="notifier-settings-box-use_pushbullet" data-notifier="use_pushbullet" ${hidden(settings.USE_PUSHBULLET)}>
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <span class="icon-notifiers-pushbullet" title="Pushbullet">
                            </span>
                            <h3>
                                <a href="${anon_url('https://www.pushbullet.com')}" rel="noreferrer" target="_blank">
                                    Pushbullet
                                </a>
                            </h3>
                            <p>${_('Pushbullet is a platform for receiving custom push notifications to connected devices running Android/iOS and desktop browsers such as Chrome, Firefox or Opera.')}</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div id="content_use_pushbullet" ${hidden(settings.USE_PUSHBULLET)}>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on snatch')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="pushbullet_notify_onsnatch" id="pushbullet_notify_onsnatch" ${checked(settings.PUSHBULLET_NOTIFY_ONSNATCH)}/>
                                        <label for="pushbullet_notify_onsnatch">${_('send a notification when a download starts?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="pushbullet_notify_ondownload" id="pushbullet_notify_ondownload" ${checked(settings.PUSHBULLET_NOTIFY_ONDOWNLOAD)}/>
                                        <label for="pushbullet_notify_ondownload">${_('send a notification when a download finishes?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on subtitle download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="pushbullet_notify_onsubtitledownload" id="pushbullet_notify_onsubtitledownload" ${checked(settings.PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD)}/>
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
                                                <input type="text" name="pushbullet_api" id="pushbullet_api" value="${settings.PUSHBULLET_API}" class="form-control input-sm input350" autocapitalize="off" />
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
                                                <select name="pushbullet_device_list" id="pushbullet_device_list" class="form-control input-sm input250" title="Pushbullet device list">
                                                </select>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="hidden" id="pushbullet_device" value="${settings.PUSHBULLET_DEVICE}">
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
                                                <select name="pushbullet_channel_list" id="pushbullet_channel_list" class="form-control input-sm input250" title="Pushbullet channel list">
                                                </select>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="hidden" id="pushbullet_channel" value="${settings.PUSHBULLET_CHANNEL}">
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <div class="testNotification" id="testPushbullet-result">
                                            ${_('Click below to test.')}
                                        </div>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <input type="button" class="btn" value="Test Pushbullet" id="testPushbullet" />
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                    </div>
                                </div>
                            </div>
                        </fieldset>
                    </div>
                </div>
            </div>
            <div class="notifier-settings-box" id="notifier-settings-box-use_freemobile" data-notifier="use_freemobile" ${hidden(settings.USE_FREEMOBILE)}>
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <span class="icon-notifiers-freemobile" title="Free Mobile">
                            </span>
                            <h3>
                                <a href="${anon_url('http://mobile.free.fr/')}" rel="noreferrer" target="_blank">
                                    Free Mobile
                                </a>
                            </h3>
                            <p>${_('Free Mobile is a famous French cellular network provider.<br> It provides to their customer a free SMS API.')}</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div id="content_use_freemobile" ${hidden(settings.USE_FREEMOBILE)}>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on snatch')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="freemobile_notify_onsnatch" id="freemobile_notify_onsnatch" ${checked(settings.FREEMOBILE_NOTIFY_ONSNATCH)}/>
                                        <label for="freemobile_notify_onsnatch">${_('send a SMS when a download starts?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="freemobile_notify_ondownload" id="freemobile_notify_ondownload" ${checked(settings.FREEMOBILE_NOTIFY_ONDOWNLOAD)}/>
                                        <label for="freemobile_notify_ondownload">${_('send a SMS when a download finishes?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on subtitle download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="freemobile_notify_onsubtitledownload" id="freemobile_notify_onsubtitledownload" ${checked(settings.FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD)}/>
                                        <label for="freemobile_notify_onsubtitledownload">${_('send a SMS when subtitles are downloaded?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label for="freemobile_id" class="component-title">${_('Free Mobile customer ID')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" name="freemobile_id" id="freemobile_id" value="${settings.FREEMOBILE_ID}" class="form-control input-sm input250" autocapitalize="off" />
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <span class="component-desc">
                                                    ${_('it\'s your Free Mobile customer ID (8 digits)')}
                                                </span>
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
                                                <input type="text" name="freemobile_apikey" id="freemobile_apikey" value="${settings.FREEMOBILE_APIKEY}" class="form-control input-sm input250" autocapitalize="off" />
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
                                        <div class="testNotification" id="testFreeMobile-result">
                                            ${_('Click below to test your settings.')}
                                        </div>
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
            </div>
            <div class="notifier-settings-box" id="notifier-settings-box-use_join" data-notifier="use_join" ${hidden(settings.USE_JOIN)}>
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <span class="icon-notifiers-join" title="Join">
                            </span>
                            <h3>
                                <a href="${anon_url('http://joaoapps.com/join/')}" rel="noreferrer" target="_blank">
                                    ${_('Join')}
                                </a>
                            </h3>
                            <p>${_('Join all of your devices together!')}</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div id="content_use_join" ${hidden(settings.USE_JOIN)}>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on snatch')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="join_notify_onsnatch" id="join_notify_onsnatch" ${checked(settings.JOIN_NOTIFY_ONSNATCH)}/>
                                        <label for="join_notify_onsnatch">${_('send a message when a download starts?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="join_notify_ondownload" id="join_notify_ondownload" ${checked(settings.JOIN_NOTIFY_ONDOWNLOAD)}/>
                                        <label for="join_notify_ondownload">${_('send a message when a download finishes?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on subtitle download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="join_notify_onsubtitledownload" id="join_notify_onsubtitledownload" ${checked(settings.JOIN_NOTIFY_ONSUBTITLEDOWNLOAD)}/>
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
                                                <input type="text" name="join_id" id="join_id" value="${settings.JOIN_ID}" class="form-control input-sm input250" autocapitalize="off" />
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="join_id">${_('per device specific id')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('API key')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" name="join_apikey" id="join_apikey" value="${settings.JOIN_APIKEY}" class="form-control input-sm input250" autocapitalize="off" />
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="join_apikey">
                                                    <a href="${anon_url('https://joaoapps.com/join/web')}" rel="noreferrer" target="_blank">
                                                        <b>
                                                            ${_('click here')}
                                                        </b>
                                                    </a>
                                                    ${_(' to create a Join API key')}
                                                </label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <div class="testNotification" id="testJoin-result">
                                            ${_('Click below to test your settings.')}
                                        </div>
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
            </div>
            <div class="notifier-settings-box" id="notifier-settings-box-use_gotify" data-notifier="use_gotify" ${hidden(settings.USE_GOTIFY)}>
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <span class="icon-notifiers-gotify" title="Gotify">
                            </span>
                            <h3>
                                <a href="${anon_url('https://gotify.net')}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;">
                                    Gotify
                                </a>
                            </h3>
                            <p>${_('Gotify is a self-hosted push notification service.')}</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div id="content_use_gotify" ${hidden(settings.USE_GOTIFY)}>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on snatch')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="gotify_notify_onsnatch" id="gotify_notify_onsnatch" ${('', 'checked="checked"')[bool(settings.GOTIFY_NOTIFY_ONSNATCH)]}/>
                                        <label for="gotify_notify_onsnatch">${_('send a notification when a download starts?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="gotify_notify_ondownload" id="gotify_notify_ondownload" ${('', 'checked="checked"')[bool(settings.GOTIFY_NOTIFY_ONDOWNLOAD)]}/>
                                        <label for="gotify_notify_ondownload">${_('send a notification when a download finishes?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on subtitle download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="gotify_notify_onsubtitledownload" id="gotify_notify_onsubtitledownload" ${('', 'checked="checked"')[bool(settings.GOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD)]}/>
                                        <label for="gotify_notify_onsubtitledownload">${_('send a notification when subtitles are downloaded?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Gotify Host:Port')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" name="gotify_host" id="gotify_host" value="${settings.GOTIFY_HOST}" class="form-control input-sm input250" autocapitalize="off" />
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="gotify_host">${_('host running Gotify (e.g. https://gotify.example.com:8081)')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Gotify token')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" name="gotify_authorizationtoken" id="gotify_authorizationtoken" value="${settings.GOTIFY_AUTHORIZATIONTOKEN}" class="form-control input-sm input350" autocapitalize="off" />
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="gotify_authorizationtoken">${_('Authorization token of your Gotify account')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <div class="testNotification" id="testGotify-result">
                                            ${_('Click below to test.')}
                                        </div>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <input type="button" class="btn" value="Test Gotify" id="testGotify" />
                                        <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                    </div>
                                </div>
                            </div>
                        </fieldset>
                    </div>
                </div>
            </div>
            <div class="notifier-settings-box" id="notifier-settings-box-use_discord" data-notifier="use_discord" ${hidden(settings.USE_DISCORD)}>
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <span class="icon-notifiers-discord" title="Discord">
                            </span>
                            <h3>
                                <a href="${anon_url('https://discordapp.com/')}" rel="noreferrer" target="_blank">
                                    Discord
                                </a>
                            </h3>
                            <p>${_('All-in-one voice and text chat for gamers that\'s free, secure, and works on both your desktop and phone.')}</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div id="content_use_discord" ${hidden(settings.USE_DISCORD)}>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on snatch')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="discord_notify_snatch" id="discord_notify_snatch" ${checked(settings.DISCORD_NOTIFY_SNATCH)}/>
                                        <label for="discord_notify_snatch">${_('send a notification when a download starts?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="discord_notify_download" id="discord_notify_download" ${checked(settings.DISCORD_NOTIFY_DOWNLOAD)}/>
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
                                                <input type="text" name="discord_webhook" id="discord_webhook" value="${settings.DISCORD_WEBHOOK}" class="form-control input-sm input350" autocapitalize="off" />
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
                                                <input type="text" name="discord_name" id="discord_name" value="${settings.DISCORD_NAME}" class="form-control input-sm input350" autocapitalize="off" />
                                            </div>
                                            <div class="col-md-12">
                                                <label for="discord_name">${_('Blank and Save will default to SickChill.')}</label>
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
                                                <input type="text" name="discord_avatar_url" id="discord_avatar_url" value="${settings.DISCORD_AVATAR_URL}" class="form-control input-sm input350" autocapitalize="off" />
                                            </div>
                                            <div class="col-md-12">
                                                <label for="discord_avatar_url">${_('Blank will use webhook default Avatar.')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('TTS')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="discord_tts" id="discord_tts" ${checked(settings.DISCORD_TTS)}/>
                                        <label for="discord_tts">${_('Send full notification message using text-to-speech else Bot Name only')}</label>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <div class="testNotification" id="testDiscord-result">
                                            ${_('Click below to test.')}
                                        </div>
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
            </div>
            <div class="notifier-settings-box" id="notifier-settings-box-use_twitter" data-notifier="use_twitter" ${hidden(settings.USE_TWITTER)}>
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <span class="icon-notifiers-twitter" title="X">
                            </span>
                            <h3>
                                <a href="${anon_url('https://x.com/')}" rel="noreferrer" target="_blank">
                                    X
                                </a>
                            </h3>
                            <p>${_('X (formerly Twitter) is a social networking and microblogging service for short public posts and direct messages.')}</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div class="row">
                                <div class="col-md-12">
                                    <label><b>${_('note')}:</b>&nbsp;${_('you may want to use a secondary account.')}</label>
                                </div>
                            </div>
                            <div id="content_use_twitter" ${hidden(settings.USE_TWITTER)}>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on snatch')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="twitter_notify_onsnatch" id="twitter_notify_onsnatch" ${checked(settings.TWITTER_NOTIFY_ONSNATCH)}/>
                                        <label for="twitter_notify_onsnatch">${_('send a notification when a download starts?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="twitter_notify_ondownload" id="twitter_notify_ondownload" ${checked(settings.TWITTER_NOTIFY_ONDOWNLOAD)}/>
                                        <label for="twitter_notify_ondownload">${_('send a notification when a download finishes?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on subtitle download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="twitter_notify_onsubtitledownload" id="twitter_notify_onsubtitledownload" ${checked(settings.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD)}/>
                                        <label for="twitter_notify_onsubtitledownload">${_('send a notification when subtitles are downloaded?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('send direct message')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="twitter_usedm" id="twitter_usedm" ${checked(settings.TWITTER_USEDM)}/>
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
                                                <input type="text" name="twitter_dmto" id="twitter_dmto" value="${settings.TWITTER_DMTO}" class="form-control input-sm input250" autocapitalize="off" />
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
                                        <label style="font-size: 11px;">${_('Click the "Request Authorization" button.<br>This will open a new page containing an auth key.<br><b>note:</b> if nothing happens check your popup blocker.')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label for="twitter_key" class="component-title">${_('Step Two')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <span style="font-size: 11px;">
                                                    ${_('Enter the key Twitter gave you below, and click "Verify Key".')}
                                                </span>
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
                                        <input  class="btn" type="button" value="Test X" id="testTwitter" />
                                        <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                    </div>
                                </div>
                            </div>
                        </fieldset>
                    </div>
                </div>
            </div>
            <div class="notifier-settings-box" id="notifier-settings-box-use_telegram" data-notifier="use_telegram" ${hidden(settings.USE_TELEGRAM)}>
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <span class="icon-notifiers-telegram" title="Telegram">
                            </span>
                            <h3>
                                <a href="${anon_url('https://telegram.org/')}" rel="noreferrer" target="_blank">${_('Telegram')}</a>
                            </h3>
                            <p>${_('Telegram is a cloud-based instant messaging service.')}</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div id="content_use_telegram" ${hidden(settings.USE_TELEGRAM)}>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on snatch')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="telegram_notify_onsnatch" id="telegram_notify_onsnatch" ${checked(settings.TELEGRAM_NOTIFY_ONSNATCH)}/>
                                        <label for="telegram_notify_onsnatch">${_('send a message when a download starts?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="telegram_notify_ondownload" id="telegram_notify_ondownload" ${checked(settings.TELEGRAM_NOTIFY_ONDOWNLOAD)}/>
                                        <label for="telegram_notify_ondownload">${_('send a message when a download finishes?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on subtitle download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="telegram_notify_onsubtitledownload" id="telegram_notify_onsubtitledownload" ${checked(settings.TELEGRAM_NOTIFY_ONSUBTITLEDOWNLOAD)}/>
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
                                                <input type="text" name="telegram_id" id="telegram_id" value="${settings.TELEGRAM_ID}" class="form-control input-sm input250" autocapitalize="off" />
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="telegram_id">${_('contact @myidbot on Telegram to get an ID')}</label>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label>${_('Note: Don\'t forget to talk with your bot at least one time if you get a 403 error.')}</label>
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
                                                <input type="text" name="telegram_apikey" id="telegram_apikey" value="${settings.TELEGRAM_APIKEY}" class="form-control input-sm input250" autocapitalize="off" />
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
                                        <div class="testNotification" id="testTelegram-result">
                                            ${_('Click below to test your settings.')}
                                        </div>
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
            </div>
            <div class="notifier-settings-box" id="notifier-settings-box-use_trakt" data-notifier="use_trakt" ${hidden(settings.USE_TRAKT)}>
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <span class="icon-notifiers-trakt" title="Trakt">
                            </span>
                            <h3>
                                <a href="${anon_url('http://trakt.tv/')}" rel="noreferrer" target="_blank">
                                    Trakt
                                </a>
                            </h3>
                            <p>${_('Trakt helps keep a record of what TV shows and movies you are watching. Based on your favorites, Trakt recommends additional shows and movies you\'ll enjoy!')}</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div id="content_use_trakt" ${hidden(settings.USE_TRAKT)}>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Account')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <p>
                                            <strong>${_('Trakt VIP required.')}</strong>
                                            ${_('Configure Client ID, Secret, Username, and authorize (device code or legacy PIN) under')}
                                            <a href="${scRoot}/config/general/#indexer-data">${_('Config → General → Indexer / Data')}</a>.
                                        </p>
                                        % if settings.TRAKT_USERNAME:
                                            <p><em>${_('Current username')}: ${settings.TRAKT_USERNAME}</em></p>
                                        % endif
                                        ## Keep id for Test Trakt JS (field lives on Indexer / Data)
                                        <input type="hidden" id="trakt_username" value="${settings.TRAKT_USERNAME or ''}" />
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('API Timeout')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="number" min="10" step="1" name="trakt_timeout" id="trakt_timeout" value="${settings.TRAKT_TIMEOUT}" class="form-control input-sm input75" autocapitalize="off" />
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
                                            % for indexer, instance in sickchill.indexer:
                                            <option value="${indexer}" ${selected(settings.TRAKT_DEFAULT_INDEXER == indexer)}>${instance.name}</option>
                                            % endfor
                                        </select>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Sync libraries')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" class="enabler" name="trakt_sync" id="trakt_sync" ${checked(settings.TRAKT_SYNC)}/>
                                        <label for="trakt_sync">${_('sync your SickChill show library with your trakt show library.')}</label>
                                    </div>
                                </div>
                                <div id="content_trakt_sync" ${hidden(settings.TRAKT_SYNC)}>
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Remove Episodes From Collection')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="trakt_sync_remove" id="trakt_sync_remove" ${checked(settings.TRAKT_SYNC_REMOVE)}/>
                                            <label for="trakt_sync_remove">${_('remove an episode from your Trakt Collection if it is not in your SickChill Library.')}</label>
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
                                                <input type="checkbox" class="enabler" name="trakt_sync_watchlist" id="trakt_sync_watchlist" ${checked(settings.TRAKT_SYNC_WATCHLIST)}/>
                                                <label for="trakt_sync_watchlist">${_('sync your SickChill show watchlist with your trakt show watchlist (either Show and Episode).')}</label>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label>${_('episode will be added on watch list when wanted or snatched and will be removed when downloaded ')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div id="content_trakt_sync_watchlist" ${hidden(settings.TRAKT_SYNC_WATCHLIST)}>
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Watchlist add method')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <select id="trakt_method_add" name="trakt_method_add" class="form-control input-sm input250">
                                                        <option value="0" ${selected(settings.TRAKT_METHOD_ADD == 0)}>${_('Skip All')}</option>
                                                        <option value="1" ${selected(settings.TRAKT_METHOD_ADD == 1)}>${_('Download Pilot Only')}</option>
                                                        <option value="2" ${selected(settings.TRAKT_METHOD_ADD == 2)}>${_('Get whole show')}</option>
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
                                            <input type="checkbox" name="trakt_remove_watchlist" id="trakt_remove_watchlist" ${checked(settings.TRAKT_REMOVE_WATCHLIST)}/>
                                            <label for="trakt_remove_watchlist">${_('remove an episode from your watchlist after it is downloaded.')}</label>
                                        </div>
                                    </div>
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Remove series')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="trakt_remove_serieslist" id="trakt_remove_serieslist" ${checked(settings.TRAKT_REMOVE_SERIESLIST)}/>
                                            <label for="trakt_remove_serieslist">${_('remove the whole series from your watchlist after any download.')}</label>
                                        </div>
                                    </div>
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Remove watched show')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="trakt_remove_show_from_sickchill" id="trakt_remove_show_from_sickchill" ${checked(settings.TRAKT_REMOVE_SHOW_FROM_SICKCHILL)}/>
                                            <label for="trakt_remove_show_from_sickchill">${_('remove the show from sickchill if it\'s ended and completely watched')}</label>
                                        </div>
                                    </div>
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Start paused')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="trakt_start_paused" id="trakt_start_paused" ${checked(settings.TRAKT_START_PAUSED)}/>
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
                                                <input type="text" name="trakt_blacklist_name" id="trakt_blacklist_name" value="${settings.TRAKT_BLACKLIST_NAME}" class="form-control input-sm input250" autocapitalize="off" />
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="trakt_blacklist_name">${_('name (slug) of list on Trakt for blacklisting shows (legacy Trakt list features)')}</label>
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
                                        <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                    </div>
                                </div>
                            </div>
                        </fieldset>
                    </div>
                </div>
            </div>
            <div class="notifier-settings-box" id="notifier-settings-box-use_email" data-notifier="use_email" ${hidden(settings.USE_EMAIL)}>
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <span class="icon-notifiers-email" title="Email">
                            </span>
                            <h3>
                                <a href="${anon_url('http://en.wikipedia.org/wiki/Comparison_of_webmail_providers')}" rel="noreferrer" target="_blank">
                                    Email
                                </a>
                            </h3>
                            <p>${_('Allows configuration of email notifications on a per show basis.')}</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div id="content_use_email" ${hidden(settings.USE_EMAIL)}>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on snatch')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="email_notify_onsnatch" id="email_notify_onsnatch" ${checked(settings.EMAIL_NOTIFY_ONSNATCH)}/>
                                        <label for="email_notify_onsnatch">${_('send a notification when a download starts?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="email_notify_ondownload" id="email_notify_ondownload" ${checked(settings.EMAIL_NOTIFY_ONDOWNLOAD)}/>
                                        <label for="email_notify_ondownload">${_('send a notification when a download finishes?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on postprocess')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="email_notify_onpostprocess" id="email_notify_onpostprocess" ${checked(settings.EMAIL_NOTIFY_ONPOSTPROCESS)}/>
                                        <label for="email_notify_onpostprocess">${_('send a notification when a postprocessing finishes?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on subtitle download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="email_notify_onsubtitledownload" id="email_notify_onsubtitledownload" ${checked(settings.EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD)}/>
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
                                                <input type="text" name="email_host" id="email_host" value="${settings.EMAIL_HOST}" class="form-control input-sm input250" autocapitalize="off" />
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
                                                <input type="number" min="1" step="1" name="email_port" id="email_port" value="${settings.EMAIL_PORT}" class="form-control input-sm input75" autocapitalize="off" />
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
                                                <input type="text" name="email_from" id="email_from" value="${settings.EMAIL_FROM | h}" class="form-control input-sm input250" autocapitalize="off" />
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
                                        <input type="checkbox" name="email_tls" id="email_tls" ${checked(settings.EMAIL_TLS)}/>
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
                                                <input type="text" name="email_user" id="email_user" value="${settings.EMAIL_USER}" class="form-control input-sm input250" autocapitalize="off" autocomplete="no" />
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
                                                <input
                                                    type="password" name="email_password" id="email_password" value="${settings.EMAIL_PASSWORD|hide}"
                                                    class="form-control input-sm input250" autocomplete="no" autocapitalize="off"
                                                />
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
                                                <input type="text" name="email_list" id="email_list" value="${settings.EMAIL_LIST}" class="form-control input-sm input350" autocapitalize="off" />
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="email_list">${_('email addresses listed here, separated by commas if applicable, will <br>receive notifications for <b>all</b>shows.')}<br>${_('(This field may be blank except when testing.)')}</label>
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
                                                <input type="text" name="email_subject" id="email_subject" value="${settings.EMAIL_SUBJECT}" class="form-control input-sm input350" autocapitalize="off" />
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="email_subject">${_('use a custom subject for some privacy protection?')}<br>${_('(leave blank for the default SickChill subject)')}</label>
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
                                                <input id="email_show_save" class="btn" type="button" value="${_('Save for this show')}" />
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
                                        <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                    </div>
                                </div>
                            </div>
                        </fieldset>
                    </div>
                </div>
            </div>
            <div class="notifier-settings-box" id="notifier-settings-box-use_slack" data-notifier="use_slack" ${hidden(settings.USE_SLACK)}>
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <span class="icon-notifiers-slack" title="Slack">
                            </span>
                            <h3>
                                <a href="${anon_url('http://www.slack.com/')}" rel="noreferrer" target="_blank">
                                    Slack
                                </a>
                            </h3>
                            <p>${_('Slack brings all your communication together in one place. It\'s real-time messaging, archiving and search for modern teams.')}</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div id="content_use_slack" ${hidden(settings.USE_SLACK)}>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on snatch')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="slack_notify_snatch" id="slack_notify_snatch" ${checked(settings.SLACK_NOTIFY_SNATCH)}/>
                                        <label for="slack_notify_snatch">${_('send a notification when a download starts?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="slack_notify_download" id="slack_notify_download" ${checked(settings.SLACK_NOTIFY_DOWNLOAD)}/>
                                        <label for="slack_notify_download">${_('send a notification when a download finishes?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on subtitle download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="slack_notify_subtitledownload" id="slack_notify_subtitledownload" ${checked(settings.SLACK_NOTIFY_SUBTITLEDOWNLOAD)}/>
                                        <label for="slack_notify_subtitledownload">${_('send a notification when subtitles are downloaded?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label for="slack_webhook" class="component-title">${_('Slack Incoming Webhook')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="text" name="slack_webhook" id="slack_webhook" value="${settings.SLACK_WEBHOOK}" class="form-control input-sm input350" autocapitalize="off" />
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label for="slack_icon_emoji" class="component-title">${_('Slack Icon Emoji')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="text" name="slack_icon_emoji" id="slack_icon_emoji" value="${settings.SLACK_ICON_EMOJI}" class="form-control input-sm input350" autocapitalize="off" />
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
            </div>
            <div class="notifier-settings-box" id="notifier-settings-box-use_mattermost" data-notifier="use_mattermost" ${hidden(settings.USE_MATTERMOST)}>
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <span class="icon-notifiers-matters" title="Mattermost Webhook">
                            </span>
                            <h3>
                                <a href="${anon_url('http://www.mattermost.com/')}" rel="noreferrer" target="_blank">
                                    Mattermost Webhook
                                </a>
                            </h3>
                            <p>${_('Secure collaboration for technical teams. Give operational and engineering teams the workspace they need to collaborate securely and effectively.')}</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div id="content_use_mattermost" ${hidden(settings.USE_MATTERMOST)}>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on snatch')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="mattermost_notify_snatch" id="mattermost_notify_snatch" ${checked(settings.MATTERMOST_NOTIFY_SNATCH)}/>
                                        <label for="mattermost_notify_snatch">${_('send a notification when a download starts?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="mattermost_notify_download" id="mattermost_notify_download" ${checked(settings.MATTERMOST_NOTIFY_DOWNLOAD)}/>
                                        <label for="mattermost_notify_download">${_('send a notification when a download finishes?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on subtitle download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="mattermost_notify_subtitledownload" id="mattermost_notify_subtitledownload" ${checked(settings.MATTERMOST_NOTIFY_SUBTITLEDOWNLOAD)}/>
                                        <label for="mattermost_notify_subtitledownload">${_('send a notification when subtitles are downloaded?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label for="mattermost_webhook" class="component-title">${_('Mattermost Incoming Webhook')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="text" name="mattermost_webhook" id="mattermost_webhook" value="${settings.MATTERMOST_WEBHOOK}" class="form-control input-sm input350" autocapitalize="off" />
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label for="mattermost_username" class="component-title">${_('Mattermost Username')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="text" name="mattermost_username" id="mattermost_username" value="${settings.MATTERMOST_USERNAME}" class="form-control input-sm input350" autocapitalize="off" />
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label for="mattermost_icon_emoji" class="component-title">${_('Mattermost Icon Emoji')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="text" name="mattermost_icon_emoji" id="mattermost_icon_emoji" value="${settings.MATTERMOST_ICON_EMOJI}" class="form-control input-sm input350" autocapitalize="off" />
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <div class="testNotification" id="testMattermost-result">
                                            ${_('Click below to test.')}
                                        </div>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <input  class="btn" type="button" value="Test Mattermost" id="testMattermost" />
                                        <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                    </div>
                                </div>
                            </div>
                        </fieldset>
                    </div>
                </div>
            </div>
            <div class="notifier-settings-box" id="notifier-settings-box-use_mattermostbot" data-notifier="use_mattermostbot" ${hidden(settings.USE_MATTERMOSTBOT)}>
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <span class="icon-notifiers-matters" title="Mattermost Bot">
                            </span>
                            <h3>
                                <a href="${anon_url('http://www.mattermost.com/')}" rel="noreferrer" target="_blank">
                                    Mattermost Bot
                                </a>
                            </h3>
                            <p>${_('Secure collaboration for technical teams. Give operational and engineering teams the workspace they need to collaborate securely and effectively.')}</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div id="content_use_mattermostbot" ${hidden(settings.USE_MATTERMOSTBOT)}>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on snatch')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="mattermostbot_notify_snatch" id="mattermostbot_notify_snatch" ${checked(settings.MATTERMOSTBOT_NOTIFY_SNATCH)}/>
                                        <label for="mattermostbot_notify_snatch">${_('send a notification when a download starts?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="mattermostbot_notify_download" id="mattermostbot_notify_download" ${checked(settings.MATTERMOSTBOT_NOTIFY_DOWNLOAD)}/>
                                        <label for="mattermostbot_notify_download">${_('send a notification when a download finishes?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on subtitle download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="mattermostbot_notify_subtitledownload" id="mattermostbot_notify_subtitledownload" ${checked(settings.MATTERMOSTBOT_NOTIFY_SUBTITLEDOWNLOAD)}/>
                                        <label for="mattermostbot_notify_subtitledownload">${_('send a notification when subtitles are downloaded?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label for="mattermostbot_url" class="component-title">${_('Mattermost Base URL')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="text" name="mattermostbot_url" id="mattermostbot_url" value="${settings.MATTERMOSTBOT_URL}" class="form-control input-sm input350" autocapitalize="off" />
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label for="mattermostbot_author" class="component-title">${_('Mattermost Author Name')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="text" name="mattermostbot_author" id="mattermostbot_author" value="${settings.MATTERMOSTBOT_AUTHOR}" class="form-control input-sm input350" autocapitalize="off" />
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label for="mattermostbot_token" class="component-title">${_('Mattermost Bot Token')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="text" name="mattermostbot_token" id="mattermostbot_token" value="${settings.MATTERMOSTBOT_TOKEN}" class="form-control input-sm input350" autocapitalize="off" />
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label for="mattermostbot_channel" class="component-title">${_('Mattermost Bot Channel ID')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="text" name="mattermostbot_channel" id="mattermostbot_channel" value="${settings.MATTERMOSTBOT_CHANNEL}" class="form-control input-sm input350" autocapitalize="off" />
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label for="mattermostbot_icon_emoji" class="component-title">${_('Mattermost Bot Icon Emoji')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="text" name="mattermostbot_icon_emoji" id="mattermostbot_icon_emoji" value="${settings.MATTERMOSTBOT_ICON_EMOJI}" class="form-control input-sm input350" autocapitalize="off" />
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <div class="testNotification" id="testMattermostBot-result">${_('Click below to test.')}</div>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <input  class="btn" type="button" value="Test Mattermost Bot" id="testMattermostBot" />
                                        <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                    </div>
                                </div>
                            </div>
                        </fieldset>
                    </div>
                </div>
            </div>
            <div class="notifier-settings-box" id="notifier-settings-box-use_rocketchat" data-notifier="use_rocketchat" ${hidden(settings.USE_ROCKETCHAT)}>
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <span class="icon-notifiers-rocketchat" title="Rocket.Chat">
                            </span>
                            <h3>
                                <a href="${anon_url('http://rocket.chat/')}" rel="noreferrer" target="_blank">
                                    Rocket.Chat
                                </a>
                            </h3>
                            <p>${_('Rocket.Chat is free, unlimited and open source chat software solution.')}</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div id="content_use_rocketchat" ${hidden(settings.USE_ROCKETCHAT)}>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on snatch')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="rocketchat_notify_snatch" id="rocketchat_notify_snatch" ${checked(settings.ROCKETCHAT_NOTIFY_SNATCH)}/>
                                        <label for="rocketchat_notify_snatch">${_('send a notification when a download starts?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="rocketchat_notify_download" id="rocketchat_notify_download" ${checked(settings.ROCKETCHAT_NOTIFY_DOWNLOAD)}/>
                                        <label for="rocketchat_notify_download">${_('send a notification when a download finishes?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on subtitle download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="rocketchat_notify_subtitledownload" id="rocketchat_notify_subtitledownload" ${checked(settings.ROCKETCHAT_NOTIFY_SUBTITLEDOWNLOAD)}/>
                                        <label for="rocketchat_notify_subtitledownload">${_('send a notification when subtitles are downloaded?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label for="rocketchat_webhook" class="component-title">${_('Rocket.Chat Incoming Webhook')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="text" name="rocketchat_webhook" id="rocketchat_webhook" value="${settings.ROCKETCHAT_WEBHOOK}" class="form-control input-sm input350" autocapitalize="off" />
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label for="rocketchat_icon_emoji" class="component-title">${_('Rocket.Chat Icon Emoji')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="text" name="rocketchat_icon_emoji" id="rocketchat_icon_emoji" value="${settings.ROCKETCHAT_ICON_EMOJI}" class="form-control input-sm input350" autocapitalize="off" />
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <div class="testNotification" id="testRocketChat-result">
                                            ${_('Click below to test.')}
                                        </div>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <input class="btn" type="button" value="Test Rocket.Chat" id="testRocketChat" />
                                        <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                    </div>
                                </div>
                            </div>
                        </fieldset>
                    </div>
                </div>
            </div>
            <div class="notifier-settings-box" id="notifier-settings-box-use_matrix" data-notifier="use_matrix" ${hidden(settings.USE_MATRIX)}>
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <span class="icon-notifiers-matrix" title="Matrix">
                            </span>
                            <h3>
                                <a href="${anon_url('http://www.matrix.org/')}" rel="noreferrer" target="_blank">
                                    Matrix
                                </a>
                            </h3>
                            <p>${_('Matrix is an open fabric for communication that anyone can participate in.')}</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div id="content_use_matrix" ${hidden(settings.USE_MATRIX)}>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on snatch')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="matrix_notify_snatch" id="matrix_notify_snatch" ${checked(settings.MATRIX_NOTIFY_SNATCH)}/>
                                        <label for="matrix_notify_snatch">${_('send a notification when a download starts?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="matrix_notify_download" id="matrix_notify_download" ${checked(settings.MATRIX_NOTIFY_DOWNLOAD)}/>
                                        <label for="matrix_notify_download">${_('send a notification when a download finishes?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Notify on subtitle download')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" name="matrix_notify_subtitledownload" id="matrix_notify_subtitledownload" ${checked(settings.MATRIX_NOTIFY_SUBTITLEDOWNLOAD)}/>
                                        <label for="matrix_notify_subtitledownload">${_('send a notification when subtitles are downloaded?')}</label>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('matrix User Auth Token')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" name="matrix_api_token" id="matrix_api_token" value="${settings.MATRIX_API_TOKEN}" class="form-control input-sm input350" autocapitalize="off" />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('matrix server address')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" name="matrix_server" id="matrix_server" value="${settings.MATRIX_SERVER}" class="form-control input-sm input350" autocapitalize="off" />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('matrix server room')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" name="matrix_room" id="matrix_room" value="${settings.MATRIX_ROOM}" class="form-control input-sm input350" autocapitalize="off" />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <div class="testNotification" id="testMatrix-result">
                                            ${_('Click below to test.')}
                                        </div>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <input  class="btn" type="button" value="Test Matrix" id="testMatrix" />
                                        <input type="submit" class="config_submitter btn" value="${_('Save Changes')}" />
                                    </div>
                                </div>
                            </div>
                        </fieldset>
                    </div>
                </div>
            </div>
        </div>
    </form>
</%block>
<%block name="scripts">
    <script>
    (function () {
    function syncNotifierSettingsVisibility() {
    let any = false;
    $('.notifier-settings-box').each(function () {
    const id = $(this).data('notifier');
    const on = $('#' + id).is(':checked');
    $(this).toggle(on);
    if (on) any = true;
    });
    $('#notifier-settings-empty').toggle(!any);
    }
    $(document).on('change', '#notifier-list .enabler', function () {
    const id = this.id;
    const on = this.checked;
    $('#content_' + id).toggle(on);
    $('#notifier-settings-box-' + id).toggle(on);
    syncNotifierSettingsVisibility();
    });
    $(function () {
    syncNotifierSettingsVisibility();
    });
    })();
    </script>
</%block>
