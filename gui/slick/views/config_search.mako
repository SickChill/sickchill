<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
%>
<%block name="content">
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif

<div id="config">
    <div id="config-content">
        <form id="configForm" action="saveSearch" method="post">
            <div id="config-components">
                <ul>
                    <li><a href="#episode-search">${_('Episode Search')}</a></li>
                    <li><a href="#nzb-search">${_('NZB Search')}</a></li>
                    <li><a href="#torrent-search">${_('Torrent Search')}</a></li>
                </ul>

                <div id="episode-search" class="component-group">
                    <div class="component-group-desc">
                        <h3>${_('Episode Search')}</h3>
                        <p>${_('How to manage searching with')} <a href="${srRoot}/config/providers">providers</a>.</p>
                    </div>

                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="randomize_providers">
                                <span class="component-title">${_('Randomize Providers')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="randomize_providers" id="randomize_providers" class="enabler" ${('', 'checked="checked"')[bool(sickbeard.RANDOMIZE_PROVIDERS)]}/>
                                    <p>${_('randomize the provider search order instead of going in order of placement')}</p>
                                </span>
                            </label>
                        </div>
                        <div class="field-pair">
                            <label for="download_propers">
                                <span class="component-title">${_('Download propers')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="download_propers" id="download_propers" class="enabler" ${('', 'checked="checked"')[bool(sickbeard.DOWNLOAD_PROPERS)]}/>
                                    <p>${_('replace original download with "Proper" or "Repack" if nuked')}</p>
                                </span>
                            </label>
                        </div>
                        <div id="content_download_propers">
                            <div class="field-pair">
                                <label for="check_propers_interval">
                                    <span class="component-title">${_('Check propers every')}:</span>
                                    <span class="component-desc">
                                        <select id="check_propers_interval" name="check_propers_interval" class="form-control input-sm">
<% check_propers_interval_text = {'daily': "24 hours", '4h': "4 hours", '90m': "90 mins", '45m': "45 mins", '15m': "15 mins"} %>
% for cur_interval in ('daily', '4h', '90m', '45m', '15m'):
                                            <option value="${cur_interval}" ${('', 'selected="selected"')[sickbeard.CHECK_PROPERS_INTERVAL == cur_interval]}>${check_propers_interval_text[cur_interval]}</option>
% endfor
                                        </select>
                                    </span>
                                </label>
                            </div>
                        </div>

                        <div class="field-pair">
                            <label>
                                <span class="component-title">${_('Backlog search day(s)')}</span>
                                <span class="component-desc">
                                    <input type="number" min="1" step="1" name="backlog_days" value="${sickbeard.BACKLOG_DAYS}" class="form-control input-sm input75" autocapitalize="off" />
                                    <p>${_('number of day(s) that the "Forced Backlog Search" will cover (e.g. 7 Days)')}</p>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label>
                                <span class="component-title">${_('Backlog search frequency')}</span>
                                <span class="component-desc">
                                    <input type="number" min="720" step="60" name="backlog_frequency" value="${sickbeard.BACKLOG_FREQUENCY}" class="form-control input-sm input75" autocapitalize="off" />
                                    <p>time in minutes between searches (min.')} ${sickbeard.MIN_BACKLOG_FREQUENCY})</p>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label>
                                <span class="component-title">${_('Daily search frequency')}</span>
                                <span class="component-desc">
                                    <input type="number" min="10" step="1" name="dailysearch_frequency" value="${sickbeard.DAILYSEARCH_FREQUENCY}" class="form-control input-sm input75" autocapitalize="off" />
                                    <p>${_('time in minutes between searches (min.')} ${sickbeard.MIN_DAILYSEARCH_FREQUENCY})</p>
                                    </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label>
                                <span class="component-title">${_('Usenet retention')}</span>
                                <span class="component-desc">
                                    <input type="number" min="1" step="1" name="usenet_retention" value="${sickbeard.USENET_RETENTION}" class="form-control input-sm input75" autocapitalize="off" />
                                    <p>${_('age limit in days for usenet articles to be used (e.g. 500)')}</p>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label>
                                <span class="component-title">${_('Ignore words')}</span>
                                <span class="component-desc">
                                    <input type="text" name="ignore_words" value="${sickbeard.IGNORE_WORDS}" class="form-control input-sm input350" autocapitalize="off" />
                                    <div class="clear-left">${_('''results with one or more word from this list will be ignored<br>
                                    separate words with a comma, e.g. "word1,word2,word3"''')}
                                    </div>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label>
                                <span class="component-title">${_('Require words')}</span>
                                <span class="component-desc">
                                    <input type="text" name="require_words" value="${sickbeard.REQUIRE_WORDS}" class="form-control input-sm input350" autocapitalize="off" />
                                    <div class="clear-left">${_('''results with no word from this list will be ignored<br>
                                    separate words with a comma, e.g. "word1,word2,word3"''')}
                                    </div>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label>
                                <span class="component-title">${_('Trackers list')}</span>
                                <span class="component-desc">
                                    <input type="text" name="trackers_list" value="${sickbeard.TRACKERS_LIST}" class="form-control input-sm input350" autocapitalize="off" />
                                    <div class="clear-left">${_('''Trackers that will be added to magnets without trackers<br>
                                    separate trackers with a comma, e.g. "tracker1,tracker2,tracker3"''')}
                                    </div>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label>
                                <span class="component-title">${_('Ignore language names in subbed results')}</span>
                                <span class="component-desc">
                                    <input type="text" name="ignored_subs_list" value="${sickbeard.IGNORED_SUBS_LIST}" class="form-control input-sm input350" autocapitalize="off" />
                                    <div class="clear-left">${_('''Ignore subbed releases based on language names <br>
                                    Example: "dk" will ignore words: dksub, dksubs, dksubbed, dksubed <br>
                                    separate languages with a comma, e.g. "lang1,lang2,lang3''')}
                                    </div>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="allow_high_priority">
                                <span class="component-title">${_('Allow high priority')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="allow_high_priority" id="allow_high_priority" ${('', 'checked="checked"')[bool(sickbeard.ALLOW_HIGH_PRIORITY)]}/>
                                    <p>${_('set downloads of recently aired episodes to high priority')}</p>
                                </span>
                            </label>
                        </div>

                         <div class="field-pair">
                             <input id="use_failed_downloads" type="checkbox" class="enabler" name="use_failed_downloads" ${('', 'checked="checked"')[bool(sickbeard.USE_FAILED_DOWNLOADS)]} />
                             <label for="use_failed_downloads">
                                 <span class="component-title">${_('Use Failed Downloads')}</span>
                                 <span class="component-desc">${_('Use Failed Download Handling?')}</span>
                             </label>
                             <label class="nocheck" for="use_failed_downloads">
                                 <span class="component-title">&nbsp;</span>
                                 <span class="component-desc">${_('Will only work with snatched/downloaded episodes after enabling this')}</span>
                             </label>
                         </div>

                        <div id="content_use_failed_downloads">
                            <div class="field-pair">
                                <input id="delete_failed" type="checkbox" name="delete_failed" ${('', 'checked="checked"')[bool(sickbeard.DELETE_FAILED)]}/>
                                <label for="delete_failed">
                                    <span class="component-title">${_('Delete Failed')}</span>
                                    <span class="component-desc">${_('Delete files left over from a failed download?')}</span>
                                </label>
                                <label class="nocheck" for="delete_failed">
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc"><b>${_('Note')}:</b> ${_('This only works if Use Failed Downloads is enabled.')}</span>
                                </label>
                            </div>
                        </div>

                        <input type="submit" class="btn config_submitter" value="${_('Save Changes')}" />

                    </fieldset>
                </div><!-- /component-group1 //-->

                <div id="nzb-search" class="component-group">

                    <div class="component-group-desc">
                        <h3>${_('NZB Search')}</h3>
                        <p>${_('How to handle NZB search results.')}</p>
                        <div id="nzb_method_icon" class="add-client-icon-${sickbeard.NZB_METHOD}"></div>
                    </div>

                    <fieldset class="component-group-list">

                        <div class="field-pair">
                            <label for="use_nzbs">
                                <span class="component-title">${_('Search NZBs')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="use_nzbs" class="enabler" id="use_nzbs" ${('', 'checked="checked"')[bool(sickbeard.USE_NZBS)]}/>
                                    <p>${_('enable NZB search providers</p>')}</span>
                            </label>
                        </div>

                        <div id="content_use_nzbs">
                        <div class="field-pair">
                            <label for="nzb_method">
                                <span class="component-title">${_('Send .nzb files to')}:</span>
                                <span class="component-desc">
                                    <select name="nzb_method" id="nzb_method" class="form-control input-sm">
                                        <% nzb_method_text = {'blackhole': "Black hole", 'sabnzbd': "SABnzbd", 'nzbget': "NZBget", 'download_station': "Synology DS"} %>
                                        % for cur_action in ('sabnzbd', 'blackhole', 'nzbget', 'download_station'):
                                            <option value="${cur_action}" ${('', 'selected="selected"')[sickbeard.NZB_METHOD == cur_action]}>${nzb_method_text[cur_action]}</option>
                                        % endfor
                                    </select>
                                </span>
                            </label>
                        </div>
                        <div id="download_station_settings">
                            <div class="field-pair">
                                <label>
                                    <span class="component-title" id="host_title">${_('Torrent host:port')}</span>
                                    <span class="component-desc">
                                        <input type="text" name="syno_dsm_host" id="syno_dsm_host" value="${sickbeard.SYNOLOGY_DSM_HOST}" class="form-control input-sm input350" autocapitalize="off" />
                                        <div class="clear-left">
                                            <p>${_('URL to your Synology DS (e.g. http://localhost:5000/)')}</p>
                                        </div>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label>
                                    <span class="component-title" id="username_title">${_('Client username')}</span>
                                    <span class="component-desc">
                                        <input type="text" name="syno_dsm_user" id="syno_dsm_user" value="${sickbeard.SYNOLOGY_DSM_USERNAME}" class="form-control input-sm input200" autocapitalize="off" autocomplete="no" />
                                        <p>${_('(blank for none)')}</p>
                                    </span>
                                </label>
                            </div>
                            <div class="field-pair">
                                <label>
                                    <span class="component-title" id="password_title">${_('Client password')}</span>
                                    <span class="component-desc">
                                        <input type="password" name="syno_dsm_pass" id="syno_dsm_pass" value="${sickbeard.SYNOLOGY_DSM_PASSWORD}" class="form-control input-sm input200" autocomplete="no" autocapitalize="off" />
                                        <p>${_('(blank for none)')}</p>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title" id="directory_title">${_('Downloaded files location')}</span>
                                    <span class="component-desc">
                                        <input type="text" name="syno_dsm_path" id="syno_dsm_path" value="${sickbeard.SYNOLOGY_DSM_PATH}" class="form-control input-sm input350" autocapitalize="off" />
                                        <div class="clear-left"><p>${_('where Synology Download Station will save downloaded files (blank for client default)')}
                                            <span id="path_synology"> <b>${_('Note')}:</b> ${_('the destination has to be a shared folder for Synology DS')}</span></p>
                                        </div>
                                    </span>
                                </label>
                            </div>
                        </div>
                        <div id="blackhole_settings">
                            <div class="field-pair">
                                <label>
                                    <span class="component-title">${_('Black hole folder location')}</span>
                                    <span class="component-desc">
                                        <input type="text" name="nzb_dir" id="nzb_dir" value="${sickbeard.NZB_DIR}" class="form-control input-sm input350" autocapitalize="off" />
                                        <div class="clear-left"><p>${_('<b>.nzb</b> files are stored at this location for external software to find and use')}</p></div>
                                    </span>
                                </label>
                            </div>
                        </div>

                        <div id="sabnzbd_settings">
                            <div class="field-pair">
                                <label>
                                    <span class="component-title">${_('SABnzbd server URL')}</span>
                                    <span class="component-desc">
                                        <input type="text" id="sab_host" name="sab_host" value="${sickbeard.SAB_HOST}" class="form-control input-sm input350" autocapitalize="off" />
                                        <div class="clear-left"><p>${_('URL to your SABnzbd server (e.g. http://localhost:8080/)')}</p></div>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title">${_('SABnzbd username')}</span>
                                    <span class="component-desc">
                                        <input type="text" name="sab_username" id="sab_username" value="${sickbeard.SAB_USERNAME}" class="form-control input-sm input200" autocapitalize="off" autocomplete="no" />
                                        <p>${_('(blank for none)')}</p>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title">${_('SABnzbd password')}</span>
                                    <span class="component-desc">
                                        <input type="password" name="sab_password" id="sab_password" value="${sickbeard.SAB_PASSWORD}" class="form-control input-sm input200" autocomplete="no" autocapitalize="off" />
                                        <p>${_('(blank for none)')}</p>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title">${_('SABnzbd API key')}</span>
                                    <span class="component-desc">
                                        <input type="text" name="sab_apikey" id="sab_apikey" value="${sickbeard.SAB_APIKEY}" class="form-control input-sm input350" autocapitalize="off" />
                                        <div class="clear-left"><p>${_('locate at... SABnzbd Config -> General -> API Key')}</p></div>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title">${_('Use SABnzbd category')}</span>
                                    <span class="component-desc">
                                        <input type="text" name="sab_category" id="sab_category" value="${sickbeard.SAB_CATEGORY}" class="form-control input-sm input200" autocapitalize="off" />
                                        <p>${_('add downloads to this category (e.g. TV)')}</p>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title">${_('Use SABnzbd category (backlog episodes)')}</span>
                                    <span class="component-desc">
                                        <input type="text" name="sab_category_backlog" id="sab_category_backlog" value="${sickbeard.SAB_CATEGORY_BACKLOG}" class="form-control input-sm input200" autocapitalize="off" />
                                        <p>${_('add downloads of old episodes to this category (e.g. TV)')}</p>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title">${_('Use SABnzbd category for anime')}</span>
                                    <span class="component-desc">
                                        <input type="text" name="sab_category_anime" id="sab_category_anime" value="${sickbeard.SAB_CATEGORY_ANIME}" class="form-control input-sm input200" autocapitalize="off" />
                                        <p>${_('add anime downloads to this category (e.g. anime)')}</p>
                                    </span>
                                </label>
                            </div>


                            <div class="field-pair">
                                <label>
                                    <span class="component-title">${_('Use SABnzbd category for anime (backlog episodes)')}</span>
                                    <span class="component-desc">
                                        <input type="text" name="sab_category_anime_backlog" id="sab_category_anime_backlog" value="${sickbeard.SAB_CATEGORY_ANIME_BACKLOG}" class="form-control input-sm input200" autocapitalize="off" />
                                        <p>${_('add anime downloads of old episodes to this category (e.g. anime)')}</p>
                                    </span>
                                </label>
                            </div>

                            % if sickbeard.ALLOW_HIGH_PRIORITY is True:
                            <div class="field-pair">
                                <label for="sab_forced">
                                    <span class="component-title">${_('Use forced priority')}</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="sab_forced" class="enabler" id="sab_forced" ${('', 'checked="checked"')[bool(sickbeard.SAB_FORCED)]}/>
                                        <p>${_('enable to change priority from HIGH to FORCED')}</p></span>
                                </label>
                            </div>
                            % endif
                        </div>

                        <div id="nzbget_settings">
                            <div class="field-pair">
                                <label for="nzbget_use_https">
                                    <span class="component-title">${_('Connect using HTTPS')}</span>
                                    <span class="component-desc">
                                        <input id="nzbget_use_https" type="checkbox" class="enabler" name="nzbget_use_https" ${('', 'checked="checked"')[bool(sickbeard.NZBGET_USE_HTTPS)]}/>
                                        <p><b>${_('Note')}:</b> ${_('enable Secure control in NZBGet and set the correct Secure Port here')}</p>
                                    </span>
                                </label>

                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title">${_('NZBget host:port')}</span>
                                    <span class="component-desc">
                                        <input type="text" name="nzbget_host" id="nzbget_host" value="${sickbeard.NZBGET_HOST}" class="form-control input-sm input350" autocapitalize="off" />
                                        <p>${_('(e.g. localhost:6789)')}</p>
                                        <div class="clear-left"><p>${_('NZBget RPC host name and port number (not NZBgetweb!)')}</p></div>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title">${_('NZBget username')}</span>
                                    <span class="component-desc">
                                        <input type="text" name="nzbget_username" value="${sickbeard.NZBGET_USERNAME}" class="form-control input-sm input200" autocapitalize="off" autocomplete="no" />
                                        <p>${_('locate in nzbget.conf (default:nzbget)')}</p>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title">${_('NZBget password')}</span>
                                    <span class="component-desc">
                                        <input type="password" name="nzbget_password" id="nzbget_password" value="${sickbeard.NZBGET_PASSWORD}" class="form-control input-sm input200" autocomplete="no" autocapitalize="off" />
                                        <p>${_('locate in nzbget.conf (default:tegbzn6789)')}</p>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title">${_('Use NZBget category')}</span>
                                    <span class="component-desc">
                                        <input type="text" name="nzbget_category" id="nzbget_category" value="${sickbeard.NZBGET_CATEGORY}" class="form-control input-sm input200" autocapitalize="off" />
                                        <p>${_('send downloads marked this category (e.g. TV)')}</p>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title">${_('Use NZBget category (backlog episodes)')}</span>
                                    <span class="component-desc">
                                        <input type="text" name="nzbget_category_backlog" id="nzbget_category_backlog" value="${sickbeard.NZBGET_CATEGORY_BACKLOG}" class="form-control input-sm input200" autocapitalize="off" />
                                        <p>${_('send downloads of old episodes marked this category (e.g. TV)')}</p>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title">${_('Use NZBget category for anime')}</span>
                                    <span class="component-desc">
                                        <input type="text" name="nzbget_category_anime" id="nzbget_category_anime" value="${sickbeard.NZBGET_CATEGORY_ANIME}" class="form-control input-sm input200" autocapitalize="off" />
                                        <p>${_('send anime downloads marked this category (e.g. anime)')}</p>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title">${_('Use NZBget category for anime (backlog episodes)')}</span>
                                    <span class="component-desc">
                                        <input type="text" name="nzbget_category_anime_backlog" id="nzbget_category_anime_backlog" value="${sickbeard.NZBGET_CATEGORY_ANIME_BACKLOG}" class="form-control input-sm input200" autocapitalize="off" />
                                        <p>${_('send anime downloads of old episodes marked this category (e.g. anime)')}</p>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title">${_('NZBget priority')}</span>
                                    <span class="component-desc">
                                        <select name="nzbget_priority" id="nzbget_priority" class="form-control input-sm">
                                            <option value="-100" ${('', 'selected="selected"')[sickbeard.NZBGET_PRIORITY == -100]}>${_('Very low')}</option>
                                            <option value="-50" ${('', 'selected="selected"')[sickbeard.NZBGET_PRIORITY == -50]}>${_('Low')}</option>
                                            <option value="0" ${('', 'selected="selected"')[sickbeard.NZBGET_PRIORITY == 0]}>${_('Normal')}</option>
                                            <option value="50" ${('', 'selected="selected"')[sickbeard.NZBGET_PRIORITY == 50]}>${_('High')}</option>
                                            <option value="100" ${('', 'selected="selected"')[sickbeard.NZBGET_PRIORITY == 100]}>${_('Very high')}</option>
                                            <option value="900" ${('', 'selected="selected"')[sickbeard.NZBGET_PRIORITY == 900]}>${_('Force')}</option>
                                        </select>
                                        <span>${_('priority for daily snatches (no backlog)')}</span>
                                    </span>
                                </label>
                            </div>
                        </div>

                        <div class="testNotification" id="testSABnzbd_result">${_('Click below to test')}</div>
                        <input class="btn" type="button" value="Test SABnzbd" id="testSABnzbd" class="btn test-button"/>

                        <div class="testNotification" id="testDSM_result">${_('Click below to test')}</div>
                        <input class="btn" type="button" value="Test DSM" id="testDSM" class="btn test-button"/>

                        <input type="submit" class="btn config_submitter" value="${_('Save Changes')}" /><br>

                        </div><!-- /content_use_nzbs //-->

                    </fieldset>
                </div><!-- /component-group2 //-->

                <div id="torrent-search" class="component-group">
                    <div class="component-group-desc">
                        <h3>${_('Torrent Search')}</h3>
                        <p>${_('How to handle Torrent search results.')}</p>
                        <div id="torrent_method_icon" class="add-client-icon-${sickbeard.TORRENT_METHOD}"></div>
                    </div>

                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_torrents">
                                <span class="component-title">${_('Search torrents')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="use_torrents" class="enabler" id="use_torrents" ${('', 'checked="checked"')[bool(sickbeard.USE_TORRENTS)]}/>
                                    <p>${_('enable torrent search providers')}</p>
                                </span>
                            </label>
                        </div>

                        <div id="content_use_torrents">
                            <div class="field-pair">
                                <label for="torrent_method">
                                    <span class="component-title">${_('Send .torrent files to')}:</span>
                                    <span class="component-desc">
                                    <select name="torrent_method" id="torrent_method" class="form-control input-sm">
                                    <% torrent_method_text = {'blackhole': "Black hole", 'utorrent': "uTorrent", 'transmission': "Transmission", 'deluge': "Deluge (via WebUI)", 'deluged': "Deluge (via Daemon)", 'download_station': "Synology DS", 'rtorrent': "rTorrent", 'qbittorrent': "qbittorrent", 'mlnet': "MLDonkey"} %>
                                    % for cur_action in ('blackhole', 'utorrent', 'transmission', 'deluge', 'deluged', 'download_station', 'rtorrent', 'qbittorrent', 'mlnet'):
                                        <option value="${cur_action}" ${('', 'selected="selected"')[sickbeard.TORRENT_METHOD == cur_action]}>${torrent_method_text[cur_action]}</option>
                                    % endfor
                                    </select>
                                </label>

                                <div id="options_torrent_blackhole">
                                    <div class="field-pair">
                                        <label>
                                            <span class="component-title">${_('Black hole folder location')}</span>
                                            <span class="component-desc">
                                                <input type="text" name="torrent_dir" id="torrent_dir" value="${sickbeard.TORRENT_DIR}" class="form-control input-sm input350" autocapitalize="off" />
                                                <div class="clear-left"><p>${_('<b>.torrent</b> files are stored at this location for external software to find and use')}</p></div>
                                            </span>
                                        </label>
                                    </div>

                                    <div></div>
                                    <input type="submit" class="btn config_submitter" value="${_('Save Changes')}" /><br>
                                </div>
                            </div>

                            <div id="options_torrent_clients">
                                <div class="field-pair">
                                    <label>
                                        <span class="component-title" id="host_title">${_('Torrent host:port')}</span>
                                        <span class="component-desc">
                                            <input type="text" name="torrent_host" id="torrent_host" value="${sickbeard.TORRENT_HOST}" class="form-control input-sm input350" autocapitalize="off" />
                                            <div class="clear-left">
                                                <p id="host_desc_torrent">${_('URL to your torrent client (e.g. http://localhost:8000/)')}</p>
                                            </div>
                                        </span>
                                    </label>
                                </div>

                                <div class="field-pair" id="torrent_rpcurl_option">
                                    <label>
                                        <span class="component-title" id="rpcurl_title">${_('Torrent RPC URL')}</span>
                                        <span class="component-desc">
                                            <input type="text" name="torrent_rpcurl" id="torrent_rpcurl" value="${sickbeard.TORRENT_RPCURL}" class="form-control input-sm input350" autocapitalize="off" />
                                            <div class="clear-left">
                                                <p id="rpcurl_desc_">${_('The path without leading and trailing slashes (e.g. transmission)')}</p>
                                            </div>
                                        </span>
                                    </label>
                                </div>

                                <div class="field-pair" id="torrent_auth_type_option">
                                    <label>
                                        <span class="component-title">${_('Http Authentication')}</span>
                                        <span class="component-desc">
                                            <select name="torrent_auth_type" id="torrent_auth_type" class="form-control input-sm">
                                            <% http_authtype = {'none': "None", 'basic': "Basic", 'digest': "Digest"} %>
                                            % for authvalue, authname in http_authtype.iteritems():
                                                <option id="torrent_auth_type_value" value="${authvalue}" ${('', 'selected="selected"')[sickbeard.TORRENT_AUTH_TYPE == authvalue]}>${authname}</option>
                                            % endfor
                                            </select>
                                            <p></p>
                                        </span>
                                    </label>
                                </div>

                                <div class="field-pair" id="torrent_verify_cert_option">
                                    <label for="torrent_verify_cert">
                                        <span class="component-title">${_('Verify certificate')}</span>
                                        <span class="component-desc">
                                            <input type="checkbox" name="torrent_verify_cert" class="enabler" id="torrent_verify_cert" ${('', 'checked="checked"')[bool(sickbeard.TORRENT_VERIFY_CERT)]}/>
                                            <p id="torrent_verify_deluge">${_('disable if you get "Deluge: Authentication Error" in your log')}</p>
                                            <p id="torrent_verify_rtorrent">${_('Verify SSL certificates for HTTPS requests')}</p>
                                        </span>
                                    </label>
                                </div>

                                <div class="field-pair" id="torrent_username_option">
                                    <label>
                                        <span class="component-title" id="username_title">${_('Client username')}</span>
                                        <span class="component-desc">
                                            <input type="text" name="torrent_username" id="torrent_username" value="${sickbeard.TORRENT_USERNAME}" class="form-control input-sm input200" autocapitalize="off" autocomplete="no" />
                                            <p>${_('(blank for none)')}</p>
                                        </span>
                                    </label>
                                </div>

                                <div class="field-pair" id="torrent_password_option">
                                    <label>
                                        <span class="component-title" id="password_title">${_('Client password')}</span>
                                        <span class="component-desc">
                                            <input type="password" name="torrent_password" id="torrent_password" value="${sickbeard.TORRENT_PASSWORD}" class="form-control input-sm input200" autocomplete="no" autocapitalize="off" />
                                            <p>${_('(blank for none)')}</p>
                                        </span>
                                    </label>
                                </div>

                                <div class="field-pair" id="torrent_label_option">
                                    <label>
                                        <span class="component-title">${_('Add label to torrent')}</span>
                                        <span class="component-desc">
                                            <input type="text" name="torrent_label" id="torrent_label" value="${sickbeard.TORRENT_LABEL}" class="form-control input-sm input200" autocapitalize="off" />
                                            <span id="label_warning_deluge" style="display:none"><p>${_('(blank spaces are not allowed)')}</p>
                                                <div class="clear-left"><p>${_('note: label plugin must be enabled in Deluge clients')}</p></div>
                                            </span>
                                            <span id="label_warning_qbittorrent" style="display:none"><p>${_('(blank spaces are not allowed)')}</p>
                                                <div class="clear-left"><p>${_('note: for QBitTorrent 3.3.1 and up')}</p></div>
                                            </span>
                                        </span>
                                    </label>
                                </div>

                                <div class="field-pair" id="torrent_label_anime_option">
                                    <label>
                                        <span class="component-title">${_('Add label to torrent for anime')}</span>
                                        <span class="component-desc">
                                            <input type="text" name="torrent_label_anime" id="torrent_label_anime" value="${sickbeard.TORRENT_LABEL_ANIME}" class="form-control input-sm input200" autocapitalize="off" />
                                            <span id="label_anime_warning_deluge" style="display:none"><p>${_('(blank spaces are not allowed)')}</p>
                                                <div class="clear-left"><p>${_('note: label plugin must be enabled in Deluge clients')}</p></div>
                                            </span>
                                            <span id="label_anime_warning_qbittorrent" style="display:none"><p>${_('(blank spaces are not allowed)')}</p>
                                                <div class="clear-left"><p>${_('note: for QBitTorrent 3.3.1 and up ')}</p></div>
                                            </span>
                                        </span>
                                    </label>
                                </div>

                                <div class="field-pair" id="torrent_path_option">
                                    <label>
                                        <span class="component-title" id="directory_title">${_('Downloaded files location')}</span>
                                        <span class="component-desc">
                                            <input type="text" name="torrent_path" id="torrent_path" value="${sickbeard.TORRENT_PATH}" class="form-control input-sm input350" autocapitalize="off" />
                                            <div class="clear-left">${_('<p>where <span id="torrent_client">the torrent client</span> will save downloaded files (blank for client default)')}
                                                <span id="path_synology"> <b>${_('Note')}:</b> ${_('the destination has to be a shared folder for Synology DS</span>')}</p>
                                            </div>
                                        </span>
                                    </label>
                                </div>

                                <div class="field-pair" id="torrent_seed_time_option">
                                    <label>
                                        <span class="component-title" id="torrent_seed_time_label">${_('Minimum seeding time is')}</span>
                                        <span class="component-desc"><input type="number" step="1" name="torrent_seed_time" id="torrent_seed_time" value="${sickbeard.TORRENT_SEED_TIME}" class="form-control input-sm input100" />
                                        <p>${_('hours. (default:\'0\' passes blank to client and \'-1\' passes nothing)')}</p></span>
                                    </label>
                                </div>

                                <div class="field-pair" id="torrent_paused_option">
                                    <label>
                                        <span class="component-title">${_('Start torrent paused')}</span>
                                        <span class="component-desc">
                                            <input type="checkbox" name="torrent_paused" class="enabler" id="torrent_paused" ${('', 'checked="checked"')[bool(sickbeard.TORRENT_PAUSED)]}/>
                                            <p>${_('add .torrent to client but do <b style="font-weight:900">not</b> start downloading')}</p>
                                        </span>
                                    </label>
                                </div>

                                <div class="field-pair" id="torrent_high_bandwidth_option">
                                    <label>
                                        <span class="component-title">${_('Allow high bandwidth')}</span>
                                        <span class="component-desc">
                                            <input type="checkbox" name="torrent_high_bandwidth" class="enabler" id="torrent_high_bandwidth" ${('', 'checked="checked"')[bool(sickbeard.TORRENT_HIGH_BANDWIDTH)]}/>
                                            <p>${_('use high bandwidth allocation if priority is high')}</p>
                                        </span>
                                    </label>
                                </div>

                                <div class="testNotification" id="test_torrent_result">${_('Click below to test')}</div>
                                <input class="btn" type="button" value="Test Connection" id="test_torrent" class="btn test-button"/>
                                <input type="submit" class="btn config_submitter" value="${_('Save Changes')}" /><br>
                                </div>
                        </div><!-- /content_use_torrents //-->
                    </fieldset>
                </div><!-- /component-group3 //-->

                <br>
                <h6 class="pull-right"><b>All non-absolute folder locations are relative to <span class="path">${sickbeard.DATA_DIR}</span></b> </h6>
                <input type="submit" class="btn pull-left config_submitter button" value="${_('Save Changes')}" />

            </div><!-- /config-components //-->
        </form>
    </div>
</div>
</%block>
