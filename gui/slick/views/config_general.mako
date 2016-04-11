<%inherit file="/layouts/main.mako"/>
<%!
    import os
    import datetime
    import sickbeard
    from sickbeard.common import SKIPPED, ARCHIVED, IGNORED, statusStrings, cpu_presets
    from sickbeard.sbdatetime import sbdatetime, date_presets, time_presets
    from sickbeard.helpers import anon_url
%>
<%block name="scripts">
<script type="text/javascript" src="${srRoot}/js/rootDirs.js?${sbPID}"></script>
</%block>
<%block name="content">
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif

<div id="config">
    <div id="config-content">

        <form id="configForm" action="saveGeneral" method="post">
            <div id="config-components">

                <ul>
                    <li><a href="#misc">${_('Misc')}</a></li>
                    <li><a href="#interface">${_('Interface')}</a></li>
                    <li><a href="#advanced-settings">${_('Advanced Settings')}</a></li>
                </ul>

                <div id="misc">
                <div class="component-group">

                    <div class="component-group-desc">
                        <h3>${_('Misc')}</h3>
                        <p>${_('Startup options. Indexer options. Log and show file locations.')}</p>
                        <p><b>${_('Some options may require a manual restart to take effect.')}</b></p>
                    </div>

                    <fieldset class="component-group-list">

                        <div class="field-pair">
                            <label for="indexerDefaultLang">
                                <span class="component-title">${_('Default Indexer Language')}</span>
                                <span class="component-desc">
                                    <select name="indexerDefaultLang" id="indexerDefaultLang" class="form-control form-control-inline input-sm bfh-languages" data-language=${sickbeard.INDEXER_DEFAULT_LANGUAGE} data-available="${','.join(sickbeard.indexerApi().config['valid_languages'])}"></select>
                                    <span>${_('for adding shows and metadata providers')}</span>
                                </span>
                            </label>
                        </div>
                        <div class="field-pair">
                            <label for="launch_browser">
                                <span class="component-title">${_('Launch browser')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="launch_browser" id="launch_browser" ${('', 'checked="checked"')[bool(sickbeard.LAUNCH_BROWSER)]}/>
                                    <p>${_('open the SickRage home page on startup')}</p>
                                </span>
                            </label>
                        </div>
                        <div class="field-pair">
                            <label for="default_page">
                                <span class="component-title">${_('Initial page')}</span>
                                <span class="component-desc">
                                    <select id="default_page" name="default_page" class="form-control input-sm">
                                        <option value="home" ${('', 'selected="selected"')[sickbeard.DEFAULT_PAGE == 'home']}>${_('Shows')}</option>
                                        <option value="schedule" ${('', 'selected="selected"')[sickbeard.DEFAULT_PAGE == 'schedule']}>${_('Schedule')}</option>
                                        <option value="history" ${('', 'selected="selected"')[sickbeard.DEFAULT_PAGE == 'history']}>${_('History')}</option>
                                        <option value="news" ${('', 'selected="selected"')[sickbeard.DEFAULT_PAGE == 'news']}>${_('News')}</option>
                                        <option value="IRC" ${('', 'selected="selected"')[sickbeard.DEFAULT_PAGE == 'IRC']}>${_('IRC')}</option>
                                    </select>
                                    <span>${_('when launching SickRage interface')}</span>
                                </span>
                            </label>
                        </div>
                        <div class="field-pair">
                            <label for="showupdate_hour">
                                <span class="component-title">${_('Choose hour to update shows')}</span>
                                <span class="component-desc">
                                    <input type="number" min="0" max="23" step="1" name="showupdate_hour" id="showupdate_hour" value="${sickbeard.SHOWUPDATE_HOUR}" class="form-control input-sm input75" autocapitalize="off" />
                                    <p>${_('with information such as next air dates, show ended, etc. Use 15 for 3pm, 4 for 4am etc.')}</p>
                                    <p>${_('Note: minutes are randomized each time SickRage is started')}</p>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <span class="component-title">${_('Send to trash for actions')}</span>
                            <span class="component-desc">
                                <label for="trash_remove_show" class="nextline-block">
                                    <input type="checkbox" name="trash_remove_show" id="trash_remove_show" ${('', 'checked="checked"')[bool(sickbeard.TRASH_REMOVE_SHOW)]}/>
                                    <p>${_('when using show "Remove" and delete files')}</p>
                                </label>
                                <label for="trash_rotate_logs" class="nextline-block">
                                    <input type="checkbox" name="trash_rotate_logs" id="trash_rotate_logs" ${('', 'checked="checked"')[bool(sickbeard.TRASH_ROTATE_LOGS)]}/>
                                    <p>${_('on scheduled deletes of the oldest log files')}</p>
                                </label>
                                <div class="clear-left"><p>${_('selected actions use trash (recycle bin) instead of the default permanent delete')}</p></div>
                            </span>
                        </div>

                        <div class="field-pair">
                            <label for="log_dir">
                                <span class="component-title">${_('Log file folder location')}</span>
                                <span class="component-desc">
                                    <input type="text" name="log_dir" id="log_dir" value="${sickbeard.ACTUAL_LOG_DIR}" class="form-control input-sm input350" autocapitalize="off" />
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="log_nr">
                                <span class="component-title">${_('Number of Log files saved')}</span>
                                <span class="component-desc">
                                    <input type="number" min="1" step="1" name="log_nr" id="log_nr" value="${sickbeard.LOG_NR}" class="form-control input-sm input75" autocapitalize="off" />
                                    <p>${_('number of log files saved when rotating logs (default: 5) (REQUIRES RESTART)')}</p>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="log_size">
                                <span class="component-title">Size of Log files saved')}</span>
                                <span class="component-desc">
                                    <input type="number" min="0.5" step="0.1" name="log_size" id="log_size" value="${sickbeard.LOG_SIZE}" class="form-control input-sm input75" autocapitalize="off" />
                                    <p>${_('maximum size in MB of the log file (default: 1MB) (REQUIRES RESTART)')}</p>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="indexer_default">
                                <span class="component-title">${_('Use initial indexer set to')}</span>
                                <span class="component-desc">
                                    <select id="indexer_default" name="indexer_default" class="form-control input-sm">
                                        <option value="0" ${('', 'selected="selected"')[sickbeard.INDEXER_DEFAULT == 0]}>All Indexers</option>
                                        % for indexer in sickbeard.indexerApi().indexers:
                                        <option value="${indexer}" ${('', 'selected="selected"')[sickbeard.INDEXER_DEFAULT == indexer]}>${sickbeard.indexerApi().indexers[indexer]}</option>
                                        % endfor
                                    </select>
                                    <span>${_('as the default selection when adding new shows')}</span>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="indexer_timeout">
                                <span class="component-title">${_('Timeout show indexer at')}</span>
                                <span class="component-desc">
                                    <input type="number" min="10" step="1" name="indexer_timeout" id="indexer_timeout" value="${sickbeard.INDEXER_TIMEOUT}" class="form-control input-sm input75" autocapitalize="off" />
                                    <p>${_('seconds of inactivity when finding new shows (default:20)')}</p>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label>
                                <span class="component-title">${_('Show root directories')}</span>
                                <span class="component-desc">
                                    <p>${_('where the files of shows are located')}</p>
                                    <%include file="/inc_rootDirs.mako"/>
                                </span>
                            </label>
                        </div>

                        <input type="submit" class="btn config_submitter" value="${_('Save Changes')}" />
                    </fieldset>
                </div>
                <div class="component-group">

                    <div class="component-group-desc">
                        <h3>${_('Updates')}</h3>
                        <p>${_('Options for software updates.')}</p>
                    </div>
                    <fieldset class="component-group-list">

                        <div class="field-pair">
                            <label for="version_notify">
                                <span class="component-title">${_('Check software updates')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="version_notify" id="version_notify" ${('', 'checked="checked"')[bool(sickbeard.VERSION_NOTIFY)]}/>
                                    <p>${_('''and display notifications when updates are available.
                                    Checks are run on startup and at the frequency set below*''')}</p>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="auto_update">
                                <span class="component-title">${_('Automatically update')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="auto_update" id="auto_update" ${('', 'checked="checked"')[bool(sickbeard.AUTO_UPDATE)]}/>
                                    <p>${_('''fetch and install software updates.
                                    Updates are run on startup and in the background at the frequency set below*''')}</p>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label>
                                <span class="component-title">${_('Check the server every*')}</span>
                                <span class="component-desc">
                                    <input type="number" min="1" step="1" name="update_frequency" id="update_frequency" value="${sickbeard.UPDATE_FREQUENCY}" class="form-control input-sm input75" autocapitalize="off" />
                                    <p>${_('hours for software updates (default:1)')}</p>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="notify_on_update">
                                <span class="component-title">${_('Notify on software update')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="notify_on_update" id="notify_on_update" ${('', 'checked="checked"')[bool(sickbeard.NOTIFY_ON_UPDATE)]}/>
                                    <p>${_('send a message to all enabled notifiers when SickRage has been updated')}</p>
                                </span>
                            </label>
                        </div>

                        <input type="submit" class="btn config_submitter" value="${_('Save Changes')}" />
                    </fieldset>

                </div>
                </div><!-- /component-group1 //-->


                <div id="interface">
                <div class="component-group">

                    <div class="component-group-desc">
                        <h3>User Interface</h3>
                        <p>Options for visual appearance.</p>
                    </div>

                    <fieldset class="component-group-list">

                        <div class="field-pair">
                            <label for="gui_language">
                                <span class="component-title">${_('Interface Language')}:</span>
                                <span class="component-desc">
                                    <select id="gui_language" name="gui_language" class="form-control input-sm">
                                        <option value="" ${('', 'selected="selected"')[sickbeard.GUI_LANG == ""]}>${_('System Language')}</option>
                                        % for lang in [language for language in os.listdir('locale') if '_' in language]:
                                            <option value="${lang}" ${('', 'selected="selected"')[sickbeard.GUI_LANG == lang]}>${lang}</option>
                                        % endfor
                                    </select>
                                    <span class="red-text">${_('for appearance to take effect, save then refresh your browser')}</span>
                                </span>
                            </label>
                        </div>
                        <div class="field-pair">
                            <label for="theme_name">
                                <span class="component-title">${_('Display theme')}:</span>
                                <span class="component-desc">
                                    <select id="theme_name" name="theme_name" class="form-control input-sm">
                                        <option value="dark" ${('', 'selected="selected"')[sickbeard.THEME_NAME == 'dark']}>Dark</option>
                                        <option value="light" ${('', 'selected="selected"')[sickbeard.THEME_NAME == 'light']}>Light</option>
                                    </select>
                                    <span class="red-text">${_('for appearance to take effect, save then refresh your browser')}</span>
                                </span>
                            </label>
                        </div>
                        <div class="field-pair">
                            <label for="display_all_seasons">
                                <span class="component-title">${_('Show all seasons')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="display_all_seasons" id="display_all_seasons" ${('', 'checked="checked"')[bool(sickbeard.DISPLAY_ALL_SEASONS)]}>
                                    <p>${_('on the show summary page')}</p>
                                </span>
                            </label>
                        </div>
                        <div class="field-pair">
                            <label for="sort_article">
                                <span class="component-title">${_('Sort with "The", "A", "An"')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="sort_article" id="sort_article" ${('', 'checked="checked"')[bool(sickbeard.SORT_ARTICLE)]}/>
                                    <p>${_('include articles ("The", "A", "An") when sorting show lists')}</p>
                                </span>
                            </label>
                        </div>
                        <div class="field-pair">
                            <label for="coming_eps_missed_range">
                                <span class="component-title">${_('Missed episodes range')}</span>
                                <span class="component-desc">
                                    <input type="number" step="1" min="7" name="coming_eps_missed_range" id="coming_eps_missed_range" value="${sickbeard.COMING_EPS_MISSED_RANGE}" class="form-control input-sm input75" />
                                    <p>${_('Set the range in days of the missed episodes in the Schedule page')}</p>
                                </span>
                            </label>
                        </div>
                        <div class="field-pair">
                            <label for="fuzzy_dating">
                                <span class="component-title">${_('Display fuzzy dates')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="fuzzy_dating" id="fuzzy_dating" class="viewIf datePresets" ${('', 'checked="checked"')[bool(sickbeard.FUZZY_DATING)]}/>
                                    <p>${_('move absolute dates into tooltips and display e.g. "Last Thu", "On Tue"')}</p>
                                </span>
                            </label>
                        </div>
                        <div class="field-pair show_if_fuzzy_dating ${(' metadataDiv', '')[not bool(sickbeard.FUZZY_DATING)]}">
                            <label for="trim_zero">
                                <span class="component-title">${_('Trim zero padding')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="trim_zero" id="trim_zero" ${('', 'checked="checked"')[bool(sickbeard.TRIM_ZERO)]}/>
                                    <p>${_('remove the leading number "0" shown on hour of day, and date of month')}</p>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="date_presets">
                                <span class="component-title">${_('Date style')}:</span>
                                <span class="component-desc">
                                    <select class="form-control input-sm ${(' metadataDiv', '')[bool(sickbeard.FUZZY_DATING)]}" id="date_presets${('_na', '')[bool(sickbeard.FUZZY_DATING)]}" name="date_preset${('_na', '')[bool(sickbeard.FUZZY_DATING)]}">
                                        % for cur_preset in date_presets:
                                            <option value="${cur_preset}" ${('', 'selected="selected"')[sickbeard.DATE_PRESET == cur_preset or ("%x" == sickbeard.DATE_PRESET and cur_preset == '%a, %b %d, %Y')]}>${datetime.datetime(datetime.datetime.now().year, 12, 31, 14, 30, 47).strftime(cur_preset)}</option>
                                        % endfor
                                    </select>
                                    <select class="form-control input-sm ${(' metadataDiv', '')[not bool(sickbeard.FUZZY_DATING)]}" id="date_presets${(' metadataDiv', '')[not bool(sickbeard.FUZZY_DATING)]}" name="date_preset${('_na', '')[not bool(sickbeard.FUZZY_DATING)]}">
                                        <option value="%x" ${('', 'selected="selected"')[sickbeard.DATE_PRESET == '%x']}>${_('Use System Default')}</option>
                                        % for cur_preset in date_presets:
                                            <option value="${cur_preset}" ${('', 'selected="selected"')[sickbeard.DATE_PRESET == cur_preset]}>${datetime.datetime(datetime.datetime.now().year, 12, 31, 14, 30, 47).strftime(cur_preset)}</option>
                                        % endfor
                                    </select>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="time_presets">
                                <span class="component-title">${_('Time style')}:</span>
                                <span class="component-desc">
                                    <select id="time_presets" name="time_preset" class="form-control input-sm">
                                         % for cur_preset in time_presets:
                                            <option value="${cur_preset}" ${('', 'selected="selected"')[sickbeard.TIME_PRESET_W_SECONDS == cur_preset]}>${sbdatetime.now().sbftime(show_seconds=True, t_preset=cur_preset)}</option>
                                         % endfor
                                    </select>
                                    <span><b>note:</b>${_(' seconds are only shown on the History page')}</span>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <span class="component-title">${_('Timezone')}:</span>
                            <span class="component-desc">
                                <label for="local" class="space-right">
                                    <input type="radio" name="timezone_display" id="local" value="local" ${('', 'checked="checked"')[sickbeard.TIMEZONE_DISPLAY == "local"]} />${_('Local')}
                                </label>
                                <label for="network">
                                    <input type="radio" name="timezone_display" id="network" value="network" ${('', 'checked="checked"')[sickbeard.TIMEZONE_DISPLAY == "network"]} />${_('Network')}
                                </label>
                                <div class="clear-left">
                                <p>${_('display dates and times in either your timezone or the shows network timezone')}</p>
                                </div>
                                <div class="clear-left">
                                <p>${_(' <b>Note:</b> Use local timezone to start searching for episodes minutes after show ends (depends on your dailysearch frequency)')}</p>
                                </div>
                            </span>
                        </div>

                        <div class="field-pair">
                            <label for="download_url">
                                <span class="component-title">${_('Download url')}</span>
                                <input type="text" name="download_url" id="download_url" value="${sickbeard.DOWNLOAD_URL}" size="35" autocapitalize="off" />
                            </label>
                            <label>
                                <span class="component-title">&nbsp;</span>
                            <span class="component-desc">${_('URL where the shows can be downloaded.')}</span>
                            </label>
                        </div>


                        <input type="submit" class="btn config_submitter" value="${_('Save Changes')}" />

                    </fieldset>

                </div><!-- /User interface component-group -->

                <div class="component-group">

                    <div class="component-group-desc">
                        <h3>${_('Web Interface')}</h3>
                        <p>${_('It is recommended that you enable a username and password to secure SickRage from being tampered with remotely.')}</p>
                        <p><b>${_('These options require a manual restart to take effect.')}</b></p>
                    </div>

                    <fieldset class="component-group-list">

                        <div class="field-pair">
                            <label for="api_key">
                                <span class="component-title">${_('API key')}</span>
                                <span class="component-desc">
                                    <input type="text" name="api_key" id="api_key" value="${sickbeard.API_KEY}" class="form-control input-sm input300" readonly="readonly" autocapitalize="off" />
                                    <input class="btn btn-inline" type="button" id="generate_new_apikey" value="Generate">
                                    <div class="clear-left">
                                        <p>${_('used to give 3rd party programs limited access to SickRage')}</p>
                                        <p>${_('you can try all the features of the API')} <a href="${srRoot}/apibuilder/">${_('here')}</a></p>
                                    </div>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="web_log">
                                <span class="component-title">${_('HTTP logs')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="web_log" id="web_log" ${('', 'checked="checked"')[bool(sickbeard.WEB_LOG)]}/>
                                    <p>${_('enable logs from the internal Tornado web server')}</p>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="web_username">
                                <span class="component-title">${_('HTTP username')}</span>
                                <span class="component-desc">
                                    <input type="text" name="web_username" id="web_username" value="${sickbeard.WEB_USERNAME}" class="form-control input-sm input300" autocapitalize="off" autocomplete="no" />
                                    <p>${_('set blank for no login')}</p>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="web_password">
                                <span class="component-title">${_('HTTP password')}</span>
                                <span class="component-desc">
                                    <input type="password" name="web_password" id="web_password" value="${sickbeard.WEB_PASSWORD}" class="form-control input-sm input300" autocomplete="no" autocapitalize="off" />
                                    <p>blank = ${_('no authentication')}</span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="web_port">
                                <span class="component-title">${_('HTTP port')}</span>
                                <span class="component-desc">
                                    <input type="number" min="1" step="1" name="web_port" id="web_port" value="${sickbeard.WEB_PORT}" class="form-control input-sm input100" autocapitalize="off" />
                                    <p>${_('web port to browse and access SickRage (default:8081)')}</p>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="notify_on_login">
                                <span class="component-title">${_('Notify on login')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="notify_on_login" class="enabler" id="notify_on_login" ${('', 'checked="checked"')[bool(sickbeard.NOTIFY_ON_LOGIN)]}/>
                                    <p>${_('enable to be notified when a new login happens in webserver')}</p>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="web_ipv6">
                                <span class="component-title">${_('Listen on IPv6')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="web_ipv6" id="web_ipv6" ${('', 'checked="checked"')[bool(sickbeard.WEB_IPV6)]}/>
                                    <p>${_('attempt binding to any available IPv6 address')}</p>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="enable_https">
                                <span class="component-title">${_('Enable HTTPS')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="enable_https" class="enabler" id="enable_https" ${('', 'checked="checked"')[bool(sickbeard.ENABLE_HTTPS)]}/>
                                    <p>${_('enable access to the web interface using a HTTPS address')}</p>
                                </span>
                            </label>
                        </div>
                        <div id="content_enable_https">
                            <div class="field-pair">
                                <label for="https_cert">
                                    <span class="component-title">${_('HTTPS certificate')}</span>
                                    <span class="component-desc">
                                        <input type="text" name="https_cert" id="https_cert" value="${sickbeard.HTTPS_CERT}" class="form-control input-sm input300" autocapitalize="off" />
                                        <div class="clear-left"><p>${_('file name or path to HTTPS certificate')}</p></div>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label for="https_key">
                                    <span class="component-title">${_('HTTPS key')}</span>
                                    <span class="component-desc">
                                        <input type="text" name="https_key" id="https_key" value="${sickbeard.HTTPS_KEY}" class="form-control input-sm input300" autocapitalize="off" />
                                        <div class="clear-left"><p>${_('file name or path to HTTPS key')}</p></div>
                                    </span>
                                </label>
                            </div>
                        </div>

                        <div class="field-pair">
                            <label for="handle_reverse_proxy">
                                <span class="component-title">${_('Reverse proxy headers')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="handle_reverse_proxy" id="handle_reverse_proxy" ${('', 'checked="checked"')[bool(sickbeard.HANDLE_REVERSE_PROXY)]}/>
                                    <p>${_('accept the following reverse proxy headers (advanced)...<br>(X-Forwarded-For, X-Forwarded-Host, and X-Forwarded-Proto)')}</p>
                                </span>
                            </label>
                        </div>

                        <input type="submit" class="btn config_submitter" value="${_('Save Changes')}" />

                    </fieldset>

                </div><!-- /component-group2 //-->
                </div>


                <div id="advanced-settings" class="component-group">

                <div class="component-group">

                    <div class="component-group-desc">
                        <h3>Advanced Settings</h3>
                    </div>

                    <fieldset class="component-group-list">

                        <div class="field-pair">
                            <label>
                                <span class="component-title">${_('CPU throttling')}:</span>
                                <span class="component-desc">
                                    <select id="cpu_presets" name="cpu_preset" class="form-control input-sm">
                                    % for cur_preset in cpu_presets:
                                        <option value="${cur_preset}" ${('', 'selected="selected"')[sickbeard.CPU_PRESET == cur_preset]}>${cur_preset.capitalize()}</option>
                                    % endfor
                                    </select>
                                    <span>${_('Normal (default). High is lower and Low is higher CPU use')}</span>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label>
                                <span class="component-title">${_('Anonymous redirect')}</span>
                                <span class="component-desc">
                                    <input type="text" name="anon_redirect" value="${sickbeard.ANON_REDIRECT}" class="form-control input-sm input300" autocapitalize="off" />
                                    <div class="clear-left"><p>${_('backlink protection via anonymizer service, must end in "?"')}</p></div>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="debug">
                                <span class="component-title">${_('Enable debug')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="debug" id="debug" ${('', 'checked="checked"')[bool(sickbeard.DEBUG)]}/>
                                    <p>${_('Enable debug logs')}<p>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="ssl_verify">
                                <span class="component-title">${_('Verify SSL Certs')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="ssl_verify" id="ssl_verify" ${('', 'checked="checked"')[bool(sickbeard.SSL_VERIFY)]}/>
                                        <p>${_('Verify SSL Certificates (Disable this for broken SSL installs (Like QNAP))')}<p>
                                    </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="no_restart">
                                <span class="component-title">${_('No Restart')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="no_restart" id="no_restart" ${('', 'checked="checked"')[bool(sickbeard.NO_RESTART)]}/>
                                    <p>${_('''Only shutdown when restarting SR.
                                    Only select this when you have external software restarting SR automatically when it stops (like FireDaemon)''')}</p>
                                </span>

                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="encryption_version">
                                <span class="component-title">${_('Encrypt passwords')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="encryption_version" id="encryption_version" ${('', 'checked="checked"')[bool(sickbeard.ENCRYPTION_VERSION)]}/>
                                    <p>${_('in the <code>config.ini</code> file.')}
                                    ${_('<b>Warning:</b> Passwords must only contain')} <a target="_blank" href="${anon_url('http://en.wikipedia.org/wiki/ASCII#ASCII_printable_characters')}">${_('ASCII characters')}</a></p>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="calendar_unprotected">
                                <span class="component-title">${_('Unprotected calendar')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="calendar_unprotected" id="calendar_unprotected" ${('', 'checked="checked"')[bool(sickbeard.CALENDAR_UNPROTECTED)]}/>
                                    <p>${_('''allow subscribing to the calendar without user and password.
                                    Some services like Google Calendar only work this way''')}</p>
                                </span>

                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="calendar_icons">
                                <span class="component-title">${_('Google Calendar Icons')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="calendar_icons" id="calendar_icons" ${('', 'checked="checked"')[bool(sickbeard.CALENDAR_ICONS)]}/>
                                    <p>${_('show an icon next to exported calendar events in Google Calendar.')}</p>
                                </span>

                            </label>
                        </div>

                        <div class="field-pair">
                            <label>
                                <span class="component-title">${_('Proxy host')}</span>
                                <span class="component-desc">
                                    <input type="text" name="proxy_setting" value="${sickbeard.PROXY_SETTING}" class="form-control input-sm input300" autocapitalize="off" />
                                    <div class="clear-left"><p>${_('blank to disable or proxy to use when connecting to providers')}</p></div>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="proxy_indexers">
                                <span class="component-title">${_('Use proxy for indexers')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="proxy_indexers" id="proxy_indexers" ${('', 'checked="checked"')[bool(sickbeard.PROXY_INDEXERS)]}/>
                                    <p>${_('use proxy host for connecting to indexers (thetvdb)')}</p>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="skip_removed_files">
                                <span class="component-title">${_('Skip Remove Detection')}</span>
                                <span class="component-desc">
                                <input type="checkbox" name="skip_removed_files" id="skip_removed_files" ${('', 'checked="checked"')[bool(sickbeard.SKIP_REMOVED_FILES)]}/>
                                <p>${_('Skip detection of removed files. If disabled the episode will be set to the default deleted status')}</p>
                                 </span>
                                <div class="clear-left">
                                <span class="component-desc"><b>${_('Note')}:</b> ${_('This may mean SickRage misses renames as well')}</span>
                                </div>
                        </div>

                        <div class="field-pair">
                            <label for="ep_default_deleted_status">
                                <span class="component-title">${_('Default deleted episode status')}:</span>
                                    <span class="component-desc">
% if not sickbeard.SKIP_REMOVED_FILES:
                                        <select name="ep_default_deleted_status" id="ep_default_deleted_status" class="form-control input-sm">
                                        % for defStatus in [SKIPPED, IGNORED, ARCHIVED]:
                                            <option value="${defStatus}" ${('', 'selected="selected"')[int(sickbeard.EP_DEFAULT_DELETED_STATUS) == defStatus]}>${statusStrings[defStatus]}</option>
                                        % endfor
                                        </select>
% else:
                                        <select name="ep_default_deleted_status" id="ep_default_deleted_status" class="form-control input-sm" disabled="disabled">
                                        % for defStatus in [SKIPPED, IGNORED]:
                                            <option value="${defStatus}" ${('', 'selected="selected"')[sickbeard.EP_DEFAULT_DELETED_STATUS == defStatus]}>${statusStrings[defStatus]}</option>
                                        % endfor
                                        </select>
                                        <input type="hidden" name="ep_default_deleted_status" value="${sickbeard.EP_DEFAULT_DELETED_STATUS}" />
% endif
                                    <span>${_('Define the status to be set for media file that has been deleted.')}</span>
                                    <div class="clear-left">
                                    <p> <b>${_('Note')}:</b> ${_('Archived option will keep previous downloaded quality')}</p>
                                    <p>${_('Example: Downloaded (1080p WEB-DL) ==> Archived (1080p WEB-DL)')}</p>
                                    </div>
                                </span>
                            </label>
                        </div>

                        <input type="submit" class="btn config_submitter" value="${_('Save Changes')}" />
                    </fieldset>
                </div>

                <div class="component-group">

                    <div class="component-group-desc">
                        <h3>GitHub</h3>
                        <p>${_('Options for github related features.')}</p>
                    </div>
                    <fieldset class="component-group-list">

                        <div class="field-pair">
                            <label>
                                <span class="component-title">${_('Branch version')}:</span>
                                <span class="component-desc">
                                    <select id="branchVersion" class="form-control form-control-inline input-sm pull-left">
                                    <% gh_branch = sickbeard.versionCheckScheduler.action.list_remote_branches() %>
                                    % if gh_branch:
                                        % for cur_branch in gh_branch:
                                            % if sickbeard.GIT_USERNAME and sickbeard.GIT_PASSWORD and sickbeard.DEVELOPER == 1:
                                                <option value="${cur_branch}" ${('', 'selected="selected"')[sickbeard.BRANCH == cur_branch]}>${cur_branch}</option>
                                            % elif sickbeard.GIT_USERNAME and sickbeard.GIT_PASSWORD and cur_branch in ['master', 'develop']:
                                                <option value="${cur_branch}" ${('', 'selected="selected"')[sickbeard.BRANCH == cur_branch]}>${cur_branch}</option>
                                            % elif cur_branch == 'master':
                                                <option value="${cur_branch}" ${('', 'selected="selected"')[sickbeard.BRANCH == cur_branch]}>${cur_branch}</option>
                                            % endif
                                        % endfor
                                    % endif
                                    </select>
                                    % if not gh_branch:
                                       <input class="btn btn-inline" style="margin-left: 6px;" type="button" id="branchCheckout" value="Checkout Branch" disabled>
                                    % else:
                                       <input class="btn btn-inline" style="margin-left: 6px;" type="button" id="branchCheckout" value="Checkout Branch">
                                    % endif
                                    % if not gh_branch:
                                       <div class="clear-left" style="color:#FF0000"><p>${_('Error: No branches found.')}</p></div>
                                    % else:
                                       <div class="clear-left"><p>${_('select branch to use (restart required)')}</p></div>
                                    % endif
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="git_username">
                                <span class="component-title">${_('GitHub username')}</span>
                                <span class="component-desc">
                                    <input type="text" name="git_username" id="git_username" value="${sickbeard.GIT_USERNAME}" class="form-control input-sm input300" autocapitalize="off" autocomplete="no" />
                                    <div class="clear-left"><p>${_('*** (REQUIRED FOR SUBMITTING ISSUES) ***')}</p></div>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="git_password">
                                <span class="component-title">${_('GitHub password')}</span>
                                <span class="component-desc">
                                    <input type="password" name="git_password" id="git_password" value="${sickbeard.GIT_PASSWORD}" class="form-control input-sm input300" autocomplete="no" autocapitalize="off" />
                                    <div class="clear-left"><p>${_('*** (REQUIRED FOR SUBMITTING ISSUES) ***')}</p></div>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="git_remote">
                                <span class="component-title">${_('GitHub remote for branch')}</span>
                                <span class="component-desc">
                                    <input type="text" name="git_remote" id="git_remote" value="${sickbeard.GIT_REMOTE}" class="form-control input-sm input300" autocapitalize="off" />
                                    <div class="clear-left"><p>${_('default:origin. Access repo configured remotes (save then refresh browser)')}</p></div>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label>
                                <span class="component-title">${_('Git executable path')}</span>
                                <span class="component-desc">
                                    <input type="text" name="git_path" value="${sickbeard.GIT_PATH}" class="form-control input-sm input300" autocapitalize="off" />
                                    <div class="clear-left"><p>${_('only needed if OS is unable to locate git from env')}</p></div>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair" hidden>
                            <label for="git_reset">
                                <span class="component-title">${_('Git reset')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="git_reset" id="git_reset" ${('', 'checked="checked"')[bool(sickbeard.GIT_RESET)]}/>
                                    <p>${_('removes untracked files and performs a hard reset on git branch automatically to help resolve update issues')}</p>
                                </span>
                            </label>
                        </div>
                        <input type="submit" class="btn config_submitter" value="${_('Save Changes')}" />
                    </fieldset>

                </div>

                </div><!-- /component-group3 //-->

                <br>
                <h6 class="pull-right"><b>${_('All non-absolute folder locations are relative to ')}<span class="path">${sickbeard.DATA_DIR}</span></b> </h6>
                <input type="submit" class="btn pull-left config_submitter button" value="${_('Save Changes')}" />

            </div><!-- /config-components -->

        </form>
    </div>
</div>

<div></div>
</%block>
