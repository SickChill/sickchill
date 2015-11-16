<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    from sickbeard import clients
%>
<%block name="scripts">
<script type="text/javascript" src="${srRoot}/js/configSearch.js?${sbPID}"></script>
<script type="text/javascript" src="${srRoot}/js/config.js?${sbPID}"></script>
<script type="text/javascript" src="${srRoot}/js/new/config_search.js"></script>
</%block>
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
                    <li><a href="#core-component-group1">Episode Search</a></li>
                    <li><a href="#core-component-group2">NZB Search</a></li>
                    <li><a href="#core-component-group3">Torrent Search</a></li>
                </ul>


                <div id="core-component-group1" class="component-group">

                    <div class="component-group-desc">
                        <h3>Episode Search</h3>
                        <p>How to manage searching with <a href="${srRoot}/config/providers">providers</a>.</p>
                    </div>

                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="randomize_providers">
                                <span class="component-title">Randomize Providers</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="randomize_providers" id="randomize_providers" class="enabler" ${('', 'checked="checked"')[bool(sickbeard.RANDOMIZE_PROVIDERS)]}/>
                                    <p>randomize the provider search order instead of going in order of placement</p>
                                </span>
                            </label>
                        </div>
                        <div class="field-pair">
                            <label for="download_propers">
                                <span class="component-title">Download propers</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="download_propers" id="download_propers" class="enabler" ${('', 'checked="checked"')[bool(sickbeard.DOWNLOAD_PROPERS)]}/>
                                    <p>replace original download with "Proper" or "Repack" if nuked</p>
                                </span>
                            </label>
                        </div>
                        <div id="content_download_propers">
                            <div class="field-pair">
                                <label for="check_propers_interval">
                                    <span class="component-title">Check propers every:</span>
                                    <span class="component-desc">
                                        <select id="check_propers_interval" name="check_propers_interval" class="form-control input-sm">
<% check_propers_interval_text = {'daily': "24 hours", '4h': "4 hours", '90m': "90 mins", '45m': "45 mins", '15m': "15 mins"} %>
% for curInterval in ('daily', '4h', '90m', '45m', '15m'):
                                            <option value="${curInterval}" ${('', 'selected="selected"')[sickbeard.CHECK_PROPERS_INTERVAL == curInterval]}>${check_propers_interval_text[curInterval]}</option>
% endfor
                                        </select>
                                    </span>
                                </label>
                            </div>
                        </div>

                        <div class="field-pair">
                            <label>
                                <span class="component-title">Backlog search frequency</span>
                                <span class="component-desc">
                                    <input type="text" name="backlog_frequency" value="${sickbeard.BACKLOG_FREQUENCY}" class="form-control input-sm input75" />
                                    <p>time in minutes between searches (min. ${sickbeard.MIN_BACKLOG_FREQUENCY})</p>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label>
                                <span class="component-title">Daily search frequency</span>
                                <span class="component-desc">
                                    <input type="text" name="dailysearch_frequency" value="${sickbeard.DAILYSEARCH_FREQUENCY}" class="form-control input-sm input75" />
                                    <p>time in minutes between searches (min. ${sickbeard.MIN_DAILYSEARCH_FREQUENCY})</p>
                                    </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label>
                                <span class="component-title">Usenet retention</span>
                                <span class="component-desc">
                                    <input type="text" name="usenet_retention" value="${sickbeard.USENET_RETENTION}" class="form-control input-sm input75" />
                                    <p>age limit in days for usenet articles to be used (e.g. 500)</p>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label>
                                <span class="component-title">Ignore words</span>
                                <span class="component-desc">
                                    <input type="text" name="ignore_words" value="${sickbeard.IGNORE_WORDS}" class="form-control input-sm input350" />
                                    <div class="clear-left">results with one or more word from this list will be ignored<br>
                                    separate words with a comma, e.g. "word1,word2,word3"
                                    </div>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label>
                                <span class="component-title">Require words</span>
                                <span class="component-desc">
                                    <input type="text" name="require_words" value="${sickbeard.REQUIRE_WORDS}" class="form-control input-sm input350" />
                                    <div class="clear-left">results with no word from this list will be ignored<br>
                                    separate words with a comma, e.g. "word1,word2,word3"
                                    </div>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label>
                                <span class="component-title">Ignore language names in subbed results</span>
                                <span class="component-desc">
                                    <input type="text" name="ignored_subs_list" value="${sickbeard.IGNORED_SUBS_LIST}" class="form-control input-sm input350" />
                                    <div class="clear-left">Ignore subbed releases based on language names <br>
                                    Example: "dk" will ignore words: dksub, dksubs, dksubbed, dksubed <br>
                                    separate languages with a comma, e.g. "lang1,lang2,lang3
                                    </div>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="allow_high_priority">
                                <span class="component-title">Allow high priority</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="allow_high_priority" id="allow_high_priority" ${('', 'checked="checked"')[bool(sickbeard.ALLOW_HIGH_PRIORITY)]}/>
                                    <p>set downloads of recently aired episodes to high priority</p>
                                </span>
                            </label>
                        </div>

                         <div class="field-pair">
                             <input id="use_failed_downloads" type="checkbox" class="enabler" name="use_failed_downloads" ${('', 'checked="checked"')[bool(sickbeard.USE_FAILED_DOWNLOADS)]} />
                             <label for="use_failed_downloads">
                                 <span class="component-title">Use Failed Downloads</span>
                                 <span class="component-desc">Use Failed Download Handling?</span>
                             </label>
                             <label class="nocheck" for="use_failed_downloads">
                                 <span class="component-title">&nbsp;</span>
                                 <span class="component-desc">Will only work with snatched/downloaded episodes after enabling this</span>
                             </label>
                         </div>

                        <div id="content_use_failed_downloads">
                            <div class="field-pair">
                                <input id="delete_failed" type="checkbox" name="delete_failed" ${('', 'checked="checked"')[bool(sickbeard.DELETE_FAILED)]}/>
                                <label for="delete_failed">
                                    <span class="component-title">Delete Failed</span>
                                    <span class="component-desc">Delete files left over from a failed download?</span>
                                </label>
                                <label class="nocheck" for="delete_failed">
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc"><b>NOTE:</b> This only works if Use Failed Downloads is enabled.</span>
                                </label>
                            </div>
                        </div>

                        <input type="submit" class="btn config_submitter" value="Save Changes" />

                    </fieldset>
                </div><!-- /component-group1 //-->

                <div id="core-component-group2" class="component-group">

                    <div class="component-group-desc">
                        <h3>NZB Search</h3>
                        <p>How to handle NZB search results.</p>
                    </div>

                    <fieldset class="component-group-list">

                        <div class="field-pair">
                            <label for="use_nzbs">
                                <span class="component-title">Search NZBs</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="use_nzbs" class="enabler" id="use_nzbs" ${('', 'checked="checked"')[bool(sickbeard.USE_NZBS)]}/>
                                    <p>enable NZB search providers</p></span>
                            </label>
                        </div>

                        <div id="content_use_nzbs">
                        <div class="field-pair">
                            <label for="nzb_method">
                                <span class="component-title">Send .nzb files to:</span>
                                <span class="component-desc">
                                    <select name="nzb_method" id="nzb_method" class="form-control input-sm">
<% nzb_method_text = {'blackhole': "Black hole", 'sabnzbd': "SABnzbd", 'nzbget': "NZBget"} %>
% for curAction in ('sabnzbd', 'blackhole', 'nzbget'):
                                    <option value="${curAction}" ${('', 'selected="selected"')[sickbeard.NZB_METHOD == curAction]}>${nzb_method_text[curAction]}</option>
% endfor
                                    </select>
                                </span>
                            </label>
                        </div>

                        <div id="blackhole_settings">
                            <div class="field-pair">
                                <label>
                                    <span class="component-title">Black hole folder location</span>
                                    <span class="component-desc">
                                        <input type="text" name="nzb_dir" id="nzb_dir" value="${sickbeard.NZB_DIR}" class="form-control input-sm input350" />
                                        <div class="clear-left"><p><b>.nzb</b> files are stored at this location for external software to find and use</p></div>
                                    </span>
                                </label>
                            </div>
                        </div>

                        <div id="sabnzbd_settings">
                            <div class="field-pair">
                                <label>
                                    <span class="component-title">SABnzbd server URL</span>
                                    <span class="component-desc">
                                        <input type="text" id="sab_host" name="sab_host" value="${sickbeard.SAB_HOST}" class="form-control input-sm input350" />
                                        <div class="clear-left"><p>URL to your SABnzbd server (e.g. http://localhost:8080/)</p></div>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title">SABnzbd username</span>
                                    <span class="component-desc">
                                        <input type="text" name="sab_username" id="sab_username" value="${sickbeard.SAB_USERNAME}" class="form-control input-sm input200" />
                                        <p>(blank for none)</p>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title">SABnzbd password</span>
                                    <span class="component-desc">
                                        <input type="password" name="sab_password" id="sab_password" value="${sickbeard.SAB_PASSWORD}" class="form-control input-sm input200" />
                                        <p>(blank for none)</p>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title">SABnzbd API key</span>
                                    <span class="component-desc">
                                        <input type="text" name="sab_apikey" id="sab_apikey" value="${sickbeard.SAB_APIKEY}" class="form-control input-sm input350" />
                                        <div class="clear-left"><p>locate at... SABnzbd Config -> General -> API Key</p></div>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title">Use SABnzbd category</span>
                                    <span class="component-desc">
                                        <input type="text" name="sab_category" id="sab_category" value="${sickbeard.SAB_CATEGORY}" class="form-control input-sm input200" />
                                        <p>add downloads to this category (e.g. TV)</p>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title">Use SABnzbd category (backlog episodes)</span>
                                    <span class="component-desc">
                                        <input type="text" name="sab_category_backlog" id="sab_category_backlog" value="${sickbeard.SAB_CATEGORY_BACKLOG}" class="form-control input-sm input200" />
                                        <p>add downloads of old episodes to this category (e.g. TV)</p>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title">Use SABnzbd category for anime</span>
                                    <span class="component-desc">
                                        <input type="text" name="sab_category_anime" id="sab_category_anime" value="${sickbeard.SAB_CATEGORY_ANIME}" class="form-control input-sm input200" />
                                        <p>add anime downloads to this category (e.g. anime)</p>
                                    </span>
                                </label>
                            </div>


                            <div class="field-pair">
                                <label>
                                    <span class="component-title">Use SABnzbd category for anime (backlog episodes)</span>
                                    <span class="component-desc">
                                        <input type="text" name="sab_category_anime_backlog" id="sab_category_anime_backlog" value="${sickbeard.SAB_CATEGORY_ANIME_BACKLOG}" class="form-control input-sm input200" />
                                        <p>add anime downloads of old episodes to this category (e.g. anime)</p>
                                    </span>
                                </label>
                            </div>

                            % if sickbeard.ALLOW_HIGH_PRIORITY == True:
                            <div class="field-pair">
                                <label for="sab_forced">
                                    <span class="component-title">Use forced priority</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="sab_forced" class="enabler" id="sab_forced" ${('', 'selected="selected"')[bool(sickbeard.SAB_FORCED)]}/>
                                        <p>enable to change priority from HIGH to FORCED</p></span>
                                </label>
                            </div>
                            % endif
                        </div>

                        <div id="nzbget_settings">
                            <div class="field-pair">
                                <label for="nzbget_use_https">
                                    <span class="component-title">Connect using HTTPS</span>
                                    <span class="component-desc">
                                        <input id="nzbget_use_https" type="checkbox" class="enabler" name="nzbget_use_https" ${('', 'selected="selected"')[bool(sickbeard.NZBGET_USE_HTTPS)]}/>
                                        <p><b>note:</b> enable Secure control in NZBGet and set the correct Secure Port here</p>
                                    </span>
                                </label>

                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title">NZBget host:port</span>
                                    <span class="component-desc">
                                        <input type="text" name="nzbget_host" id="nzbget_host" value="${sickbeard.NZBGET_HOST}" class="form-control input-sm input350" />
                                        <p>(e.g. localhost:6789)</p>
                                        <div class="clear-left"><p>NZBget RPC host name and port number (not NZBgetweb!)</p></div>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title">NZBget username</span>
                                    <span class="component-desc">
                                        <input type="text" name="nzbget_username" value="${sickbeard.NZBGET_USERNAME}" class="form-control input-sm input200" />
                                        <p>locate in nzbget.conf (default:nzbget)</p>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title">NZBget password</span>
                                    <span class="component-desc">
                                        <input type="password" name="nzbget_password" id="nzbget_password" value="${sickbeard.NZBGET_PASSWORD}" class="form-control input-sm input200" />
                                        <p>locate in nzbget.conf (default:tegbzn6789)</p>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title">Use NZBget category</span>
                                    <span class="component-desc">
                                        <input type="text" name="nzbget_category" id="nzbget_category" value="${sickbeard.NZBGET_CATEGORY}" class="form-control input-sm input200" />
                                        <p>send downloads marked this category (e.g. TV)</p>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title">Use NZBget category (backlog episodes)</span>
                                    <span class="component-desc">
                                        <input type="text" name="nzbget_category_backlog" id="nzbget_category_backlog" value="${sickbeard.NZBGET_CATEGORY_BACKLOG}" class="form-control input-sm input200" />
                                        <p>send downloads of old episodes marked this category (e.g. TV)</p>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title">Use NZBget category for anime</span>
                                    <span class="component-desc">
                                        <input type="text" name="nzbget_category_anime" id="nzbget_category_anime" value="${sickbeard.NZBGET_CATEGORY_ANIME}" class="form-control input-sm input200" />
                                        <p>send anime downloads marked this category (e.g. anime)</p>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title">Use NZBget category for anime (backlog episodes)</span>
                                    <span class="component-desc">
                                        <input type="text" name="nzbget_category_anime_backlog" id="nzbget_category_anime_backlog" value="${sickbeard.NZBGET_CATEGORY_ANIME_BACKLOG}" class="form-control input-sm input200" />
                                        <p>send anime downloads of old episodes marked this category (e.g. anime)</p>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <label>
                                    <span class="component-title">NZBget priority</span>
                                    <span class="component-desc">
                                        <select name="nzbget_priority" id="nzbget_priority" class="form-control input-sm">
                                            <option value="-100" ${('', 'selected="selected"')[sickbeard.NZBGET_PRIORITY == -100]}>Very low</option>
                                            <option value="-50" ${('', 'selected="selected"')[sickbeard.NZBGET_PRIORITY == -50]}>Low</option>
                                            <option value="0" ${('', 'selected="selected"')[sickbeard.NZBGET_PRIORITY == 0]}>Normal</option>
                                            <option value="50" ${('', 'selected="selected"')[sickbeard.NZBGET_PRIORITY == 50]}>High</option>
                                            <option value="100" ${('', 'selected="selected"')[sickbeard.NZBGET_PRIORITY == 100]}>Very high</option>
                                            <option value="900" ${('', 'selected="selected"')[sickbeard.NZBGET_PRIORITY == 900]}>Force</option>
                                        </select>
                                        <span>priority for daily snatches (no backlog)</span>
                                    </span>
                                </label>
                            </div>
                        </div>

                        <div class="testNotification" id="testSABnzbd_result">Click below to test</div>
                        <input class="btn" type="button" value="Test SABnzbd" id="testSABnzbd" class="btn test-button"/>
                        <input type="submit" class="btn config_submitter" value="Save Changes" /><br>

                        </div><!-- /content_use_nzbs //-->

                    </fieldset>
                </div><!-- /component-group2 //-->

                <div id="core-component-group3" class="component-group">

                    <div class="component-group-desc">
                        <h3>Torrent Search</h3>
                        <p>How to handle Torrent search results.</p>
                    </div>

                    <fieldset class="component-group-list">

                        <div class="field-pair">

                            <label for="use_torrents">
                                <span class="component-title">Search torrents</span>
                                <span class="component-desc">
                                    <input type="checkbox" name="use_torrents" class="enabler" id="use_torrents" ${('', 'checked="checked"')[bool(sickbeard.USE_TORRENTS)]}/>
                                    <p>enable torrent search providers</p>
                                </span>
                            </label>
                        </div>

                    <div id="content_use_torrents">
                        <div class="field-pair">
                            <label for="torrent_method">
                                <span class="component-title">Send .torrent files to:</span>
                                <span class="component-desc">
                                <select name="torrent_method" id="torrent_method" class="form-control input-sm">
<% torrent_method_text = {'blackhole': "Black hole", 'utorrent': "uTorrent", 'transmission': "Transmission", 'deluge': "Deluge (via WebUI)", 'deluged': "Deluge (via Daemon)", 'download_station': "Synology DS", 'rtorrent': "rTorrent", 'qbittorrent': "qbittorrent", 'mlnet': "MLDonkey"} %>
% for curAction in ('blackhole', 'utorrent', 'transmission', 'deluge', 'deluged', 'download_station', 'rtorrent', 'qbittorrent', 'mlnet'):
                                <option value="${curAction}" ${('', 'selected="selected"')[sickbeard.TORRENT_METHOD == curAction]}>${torrent_method_text[curAction]}</option>
% endfor
                                </select>
                            </label>

                        <div id="options_torrent_blackhole">
                            <div class="field-pair">
                                <label>
                                    <span class="component-title">Black hole folder location</span>
                                    <span class="component-desc">
                                        <input type="text" name="torrent_dir" id="torrent_dir" value="${sickbeard.TORRENT_DIR}" class="form-control input-sm input350" />
                                        <div class="clear-left"><p><b>.torrent</b> files are stored at this location for external software to find and use</p></div>
                                    </span>
                                </label>
                            </div>

                            <div></div>
                            <input type="submit" class="btn config_submitter" value="Save Changes" /><br>
                            </div>
                        </div>

                        <div id="options_torrent_clients">
                            <div class="field-pair">
                                <label>
                                    <span class="component-title" id="host_title">Torrent host:port</span>
                                    <span class="component-desc">
                                        <input type="text" name="torrent_host" id="torrent_host" value="${sickbeard.TORRENT_HOST}" class="form-control input-sm input350" />
                                        <div class="clear-left">
                                            <p id="host_desc_torrent">URL to your torrent client (e.g. http://localhost:8000/)</p>
                                        </div>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair" id="torrent_rpcurl_option">
                                <label>
                                    <span class="component-title" id="rpcurl_title">Torrent RPC URL</span>
                                    <span class="component-desc">
                                        <input type="text" name="torrent_rpcurl" id="torrent_rpcurl" value="${sickbeard.TORRENT_RPCURL}" class="form-control input-sm input350"/>
                                        <div class="clear-left">
                                            <p id="rpcurl_desc_">The path without leading and trailing slashes (e.g. transmission)</p>
                                        </div>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair" id="torrent_auth_type_option">
                                <label>
                                    <span class="component-title">Http Authentication</span>
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
                                    <span class="component-title">Verify certificate</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="torrent_verify_cert" class="enabler" id="torrent_verify_cert" ${('', 'checked="checked"')[bool(sickbeard.TORRENT_VERIFY_CERT)]}/>
                                        <p id="torrent_verify_deluge">disable if you get "Deluge: Authentication Error" in your log</p>
                                        <p id="torrent_verify_rtorrent">Verify SSL certificates for HTTPS requests</p>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair" id="torrent_username_option">
                                <label>
                                    <span class="component-title" id="username_title">Client username</span>
                                    <span class="component-desc">
                                        <input type="text" name="torrent_username" id="torrent_username" value="${sickbeard.TORRENT_USERNAME}" class="form-control input-sm input200" />
                                        <p>(blank for none)</p>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair" id="torrent_password_option">
                                <label>
                                    <span class="component-title" id="password_title">Client password</span>
                                    <span class="component-desc">
                                        <input type="password" name="torrent_password" id="torrent_password" value="${sickbeard.TORRENT_PASSWORD}" class="form-control input-sm input200" />
                                        <p>(blank for none)</p>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair" id="torrent_label_option">
                                <label>
                                    <span class="component-title">Add label to torrent</span>
                                    <span class="component-desc">
                                        <input type="text" name="torrent_label" id="torrent_label" value="${sickbeard.TORRENT_LABEL}" class="form-control input-sm input200" />
                                        <span id="label_warning_deluge" style="display:none"><p>(blank spaces are not allowed)</p>
                                            <div class="clear-left"><p>note: label plugin must be enabled in Deluge clients</p></div>
                                        </span>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair" id="torrent_label_anime_option">
                                <label>
                                    <span class="component-title">Add label to torrent for anime</span>
                                    <span class="component-desc">
                                        <input type="text" name="torrent_label_anime" id="torrent_label_anime" value="${sickbeard.TORRENT_LABEL_ANIME}" class="form-control input-sm input200" />
                                        <span id="label_anime_warning_deluge" style="display:none"><p>(blank spaces are not allowed)</p>
                                            <div class="clear-left"><p>note: label plugin must be enabled in Deluge clients</p></div>
                                        </span>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair" id="torrent_path_option">
                                <label>
                                    <span class="component-title" id="directory_title">Downloaded files location</span>
                                    <span class="component-desc">
                                        <input type="text" name="torrent_path" id="torrent_path" value="${sickbeard.TORRENT_PATH}" class="form-control input-sm input350" />
                                        <div class="clear-left"><p>where <span id="torrent_client">the torrent client</span> will save downloaded files (blank for client default)
                                            <span id="path_synology"> <b>note:</b> the destination has to be a shared folder for Synology DS</span></p>
                                        </div>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair" id="torrent_seed_time_option">
                                <label>
                                    <span class="component-title" id="torrent_seed_time_label">Minimum seeding time is</span>
                                    <span class="component-desc"><input type="number" step="1" name="torrent_seed_time" id="torrent_seed_time" value="${sickbeard.TORRENT_SEED_TIME}" class="form-control input-sm input100" />
                                    <p>hours. (default:'0' passes blank to client and '-1' passes nothing)</p></span>
                                </label>
                            </div>

                            <div class="field-pair" id="torrent_paused_option">
                                <label>
                                    <span class="component-title">Start torrent paused</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="torrent_paused" class="enabler" id="torrent_paused" ${('', 'checked="checked"')[bool(sickbeard.TORRENT_PAUSED)]}/>
                                        <p>add .torrent to client but do <b style="font-weight:900">not</b> start downloading</p>
                                    </span>
                                </label>
                            </div>

                            <div class="field-pair" id="torrent_high_bandwidth_option">
                                <label>
                                    <span class="component-title">Allow high bandwidth</span>
                                    <span class="component-desc">
                                        <input type="checkbox" name="torrent_high_bandwidth" class="enabler" id="torrent_high_bandwidth" ${('', 'checked="checked"')[bool(sickbeard.TORRENT_HIGH_BANDWIDTH)]}/>
                                        <p>use high bandwidth allocation if priority is high</p>
                                    </span>
                                </label>
                            </div>

                            <div class="testNotification" id="test_torrent_result">Click below to test</div>
                            <input class="btn" type="button" value="Test Connection" id="test_torrent" class="btn test-button"/>
                            <input type="submit" class="btn config_submitter" value="Save Changes" /><br>
                            </div>
                    </div><!-- /content_use_torrents //-->
                    </fieldset>
                </div><!-- /component-group3 //-->

                <br>
                <h6 class="pull-right"><b>All non-absolute folder locations are relative to <span class="path">${sickbeard.DATA_DIR}</span></b> </h6>
                <input type="submit" class="btn pull-left config_submitter button" value="Save Changes" />

            </div><!-- /config-components //-->

        </form>
    </div>
</div>

<div></div>
</%block>
