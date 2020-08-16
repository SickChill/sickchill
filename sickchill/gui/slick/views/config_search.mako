<%inherit file="/layouts/config.mako"/>
<%!
    from sickchill import settings
    from sickchill.oldbeard.filters import hide
    from sickchill.oldbeard.clients import getClientListDict
%>

<%block name="tabs">
    <li><a href="#episode-search">${_('Episode Search')}</a></li>
    <li><a href="#nzb-search">${_('NZB Search')}</a></li>
    <li><a href="#torrent-search">${_('Torrent Search')}</a></li>
</%block>

<%block name="pages">
    <form id="configForm" action="saveSearch" method="post">

        <div id="config-components">

            <!-- Episode search -->
            <div id="episode-search" class="component-group">

                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <h3>${_('Episode Search')}</h3>
                            <p>${_('How to manage searching with')} <a href="${scRoot}/config/providers">providers</a>.</p>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">

                        <fieldset class="component-group-list">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Randomize Providers')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="randomize_providers" id="randomize_providers"
                                           class="enabler" ${('', 'checked="checked"')[bool(settings.RANDOMIZE_PROVIDERS)]}/>
                                    <label for="randomize_providers">${_('randomize the provider search order instead of going in order of placement')}</label>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Download propers')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="download_propers" id="download_propers"
                                           class="enabler" ${('', 'checked="checked"')[bool(settings.DOWNLOAD_PROPERS)]}/>
                                    <label for="download_propers">${_('replace original download with "Proper" or "Repack" if nuked')}</label>
                                </div>
                            </div>

                            <div id="content_download_propers">

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Check propers every')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <select id="check_propers_interval" name="check_propers_interval" class="form-control input-sm input150">
                                            <% check_propers_interval_text = {'daily': _('24 hours'), '4h': _('4 hours'), '90m': _('90 mins'), '45m': _('45 mins'), '15m': _('15 mins')} %>
                                            % for curInterval in check_propers_interval_text:
                                                <option value="${curInterval}" ${('', 'selected="selected"')[settings.CHECK_PROPERS_INTERVAL == curInterval]}>${check_propers_interval_text[curInterval]}</option>
                                            % endfor
                                        </select>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Backlog search day(s)')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="number" min="1" step="1" name="backlog_days"
                                                   value="${settings.BACKLOG_DAYS}" class="form-control input-sm input75"
                                                   autocapitalize="off" id="backlog_days"/>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="backlog_days">${_('number of day(s) that the "Forced Backlog Search" will cover (e.g. 7 Days)')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Backlog search frequency')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="number" min="720" step="60" name="backlog_frequency"
                                                   value="${settings.BACKLOG_FREQUENCY}" class="form-control input-sm input75"
                                                   id="backlog_frequency" autocapitalize="off"/>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="backlog_frequency">${_('time in minutes between searches (min.')} ${settings.MIN_BACKLOG_FREQUENCY})</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Daily search frequency')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="number" min="10" step="1" name="dailysearch_frequency"
                                                   id="dailysearch_frequency" value="${settings.DAILYSEARCH_FREQUENCY}"
                                                   class="form-control input-sm input75" autocapitalize="off"/>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="dailysearch_frequency">${_('time in minutes between searches (min.')} ${settings.MIN_DAILYSEARCH_FREQUENCY})</label>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Ignore words')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="ignore_words" value="${settings.IGNORE_WORDS}"
                                                   id="ignore_words" class="form-control input-sm input350" autocapitalize="off"/>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="ignore_words">${_('''results with one or more word from this list will be ignored<br>separate words with a comma, e.g. "word1,word2,word3"''')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Prefer words')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="prefer_words" value="${settings.PREFER_WORDS}"
                                                   id="prefer_words" class="form-control input-sm input350" autocapitalize="off"/>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="prefer_words">${_('''search results with these words will be preferred in this order<br>separate words with a comma, e.g. "word1,word2,word3"''')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Require words')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="require_words" value="${settings.REQUIRE_WORDS}"
                                                   id="require_words" class="form-control input-sm input350" autocapitalize="off"/>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="require_words">${_('''results with no word from this list will be ignored<br>separate words with a comma, e.g. "word1,word2,word3"''')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Ignore language names in subbed results')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="text" name="ignored_subs_list" value="${settings.IGNORED_SUBS_LIST}"
                                                   class="form-control input-sm input350" autocapitalize="off"/>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label for="ignored_subs_list">${_('''ignore subbed releases based on language names <br>
                            Example: "dk" will ignore words: dksub, dksubs, dksubbed, dksubed <br>
                            separate languages with a comma, e.g. "lang1,lang2,lang3''')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Allow high priority')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="allow_high_priority"
                                           id="allow_high_priority" ${('', 'checked="checked"')[bool(settings.ALLOW_HIGH_PRIORITY)]}/>
                                    <label for="allow_high_priority">${_('set downloads of recently aired episodes to high priority')}</label>
                                </div>
                            </div>
                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Allow downloading HEVC x265 releases')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="quality_allow_hevc"
                                           id="quality_allow_hevc" ${('', 'checked="checked"')[bool(settings.QUALITY_ALLOW_HEVC)]}/>
                                    <label for="quality_allow_hevc">${_('whether we should download HEVC x265 releases')}</label>
                                </div>
                            </div>
                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Use Failed Downloads')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input id="use_failed_downloads" type="checkbox" class="enabler"
                                                   name="use_failed_downloads" ${('', 'checked="checked"')[bool(settings.USE_FAILED_DOWNLOADS)]} />
                                            <label for="use_failed_downloads">${_('use Failed Download Handling?')}</label>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <label>${_('will only work with snatched/downloaded episodes after enabling this')}</label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div id="content_use_failed_downloads">

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Delete Failed')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input id="delete_failed" type="checkbox"
                                                       name="delete_failed" ${('', 'checked="checked"')[bool(settings.DELETE_FAILED)]}/>
                                                <label for="delete_failed">${_('delete files left over from a failed download?')}</label>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label><b>${_('note')}:</b> ${_('this only works if Use Failed Downloads is enabled.')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                            </div>

                            <div id="content_backlog_missing_only">

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Backlog search for missing only')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input id="backlog_missing_only" type="checkbox"
                                                       name="backlog_missing_only" ${('', 'checked="checked"')[bool(settings.BACKLOG_MISSING_ONLY)]}/>
                                                <label for="backlog_missing_only">${_('restrict backlog searches to missing episodes only?')}</label>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label><b>${_('note')}:</b> ${_('if enabled, this ignores episodes that are not preferred qualities')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                            </div>

                        </fieldset>
                    </div>
                </div>
            </div>

            <!-- Nzb search -->
            <div id="nzb-search" class="component-group">
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <h3>${_('NZB Search')}</h3>
                            <p>${_('How to handle NZB search results.')}</p>
                            <div id="nzb_method_icon" class="add-client-icon-${settings.NZB_METHOD}"></div>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">

                        <fieldset class="component-group-list">

                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Search NZBs')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="use_nzbs" class="enabler"
                                           id="use_nzbs" ${('', 'checked="checked"')[bool(settings.USE_NZBS)]}/>
                                    <label for="use_nzbs">${_('enable NZB search providers')}</label>
                                </div>
                            </div>

                            <div id="content_use_nzbs">
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Usenet retention')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="number" min="1" step="1" name="usenet_retention"
                                                       value="${settings.USENET_RETENTION}" class="form-control input-sm input75"
                                                       id="usenet_retention" autocapitalize="off"/>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="usenet_retention">${_('age limit in days for usenet articles to be used (e.g. 500)')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Send .nzb files to')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <select name="nzb_method" id="nzb_method" class="form-control input-sm input150" title="nzb_method">
                                            <% nzb_method_text = {'blackhole': "Black hole", 'sabnzbd': "SABnzbd", 'nzbget': "NZBget", 'download_station': "Synology DS"} %>
                                            % for curAction in ('blackhole', 'sabnzbd', 'nzbget', 'download_station'):
                                                <option value="${curAction}" ${('', 'selected="selected"')[settings.NZB_METHOD == curAction]}>${nzb_method_text[curAction]}</option>
                                            % endfor
                                        </select>
                                    </div>
                                </div>
                                <div id="sabnzbd_settings">

                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('SABnzbd server URL')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="text" id="sab_host" name="sab_host" value="${settings.SAB_HOST}"
                                                           class="form-control input-sm input350" autocapitalize="off"/>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="sab_host">${_('URL to your SABnzbd server (e.g. http://localhost:8080/)')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('SABnzbd username')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="text" name="sab_username" id="sab_username"
                                                           value="${settings.SAB_USERNAME}" class="form-control input-sm input200"
                                                           autocapitalize="off" autocomplete="no"/>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="sab_username">${_('(blank for none)')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('SABnzbd password')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input
                                                        type="password" name="sab_password" id="sab_password" value="${settings.SAB_PASSWORD|hide}"
                                                        class="form-control input-sm input200" autocomplete="no" autocapitalize="off"
                                                    />
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="sab_password">${_('(blank for none)')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('SABnzbd API key')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input
                                                        type="password" name="sab_apikey" id="sab_apikey" value="${settings.SAB_APIKEY|hide}"
                                                        class="form-control input-sm input350" autocapitalize="off"
                                                    />
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="sab_apikey">${_('locate at... SABnzbd Config -> General -> API Key')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Use SABnzbd category')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="text" name="sab_category" id="sab_category"
                                                           value="${settings.SAB_CATEGORY}" class="form-control input-sm input200"
                                                           autocapitalize="off"/>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="sab_category">${_('add downloads to this category (e.g. TV)')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Use SABnzbd category (backlog episodes)')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="text" name="sab_category_backlog" id="sab_category_backlog"
                                                           value="${settings.SAB_CATEGORY_BACKLOG}"
                                                           class="form-control input-sm input200" autocapitalize="off"/>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="sab_category_backlog">${_('add downloads of old episodes to this category (e.g. TV)')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Use SABnzbd category for anime')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="text" name="sab_category_anime" id="sab_category_anime"
                                                           value="${settings.SAB_CATEGORY_ANIME}"
                                                           class="form-control input-sm input200" autocapitalize="off"/>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="sab_category_anime">${_('add anime downloads to this category (e.g. anime)')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>


                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Use SABnzbd category for anime (backlog episodes)')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="text" name="sab_category_anime_backlog"
                                                           id="sab_category_anime_backlog"
                                                           value="${settings.SAB_CATEGORY_ANIME_BACKLOG}"
                                                           class="form-control input-sm input200" autocapitalize="off"/>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="sab_category_anime_backlog">${_('add anime downloads of old episodes to this category (e.g. anime)')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    % if settings.ALLOW_HIGH_PRIORITY is True:
                                        <div class="field-pair row">
                                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                                <label class="component-title">${_('Use forced priority')}</label>
                                            </div>
                                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                                <input type="checkbox" name="sab_forced" class="enabler"
                                                       id="sab_forced" ${('', 'checked="checked"')[bool(settings.SAB_FORCED)]}/>
                                                <label for="sab_forced">${_('enable to change priority from HIGH to FORCED')}</label>
                                            </div>
                                        </div>
                                    % endif
                                </div>

                                <div id="blackhole_settings">
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Black hole folder location')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="text" name="nzb_dir" id="nzb_dir" value="${settings.NZB_DIR}"
                                                           class="form-control input-sm input350" autocapitalize="off"/>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="nzb_dir">${_('<b>.nzb</b> files are stored at this location for external software to find and use')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div id="nzbget_settings">

                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Connect using HTTPS')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input id="nzbget_use_https" type="checkbox" class="enabler"
                                                           name="nzbget_use_https" ${('', 'checked="checked"')[bool(settings.NZBGET_USE_HTTPS)]}/>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="nzbget_use_https"><b>${_('note')}:</b> ${_('enable Secure control in NZBGet and set the correct Secure Port here')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('NZBget host:port')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="text" name="nzbget_host" id="nzbget_host"
                                                           value="${settings.NZBGET_HOST}" class="form-control input-sm input350"
                                                           autocapitalize="off"/>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="nzbget_host">${_('(e.g. localhost:6789)')}</label>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label>${_('NZBget RPC host name and port number (not NZBgetweb!)')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('NZBget username')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="text" name="nzbget_username" value="${settings.NZBGET_USERNAME}"
                                                           class="form-control input-sm input200" autocapitalize="off"
                                                           id="nzbget_username" autocomplete="no"/>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="nzbget_username">${_('locate in nzbget.conf (default:nzbget)')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('NZBget password')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input
                                                        type="password" name="nzbget_password" id="nzbget_password" value="${settings.NZBGET_PASSWORD|hide}"
                                                        class="form-control input-sm input200" autocomplete="no" autocapitalize="off"
                                                    />
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="nzbget_password">${_('locate in nzbget.conf (default:tegbzn6789)')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Use NZBget category')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="text" name="nzbget_category" id="nzbget_category"
                                                           value="${settings.NZBGET_CATEGORY}"
                                                           class="form-control input-sm input200" autocapitalize="off"/>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="nzbget_category">${_('send downloads marked this category (e.g. TV)')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Use NZBget category (backlog episodes)')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="text" name="nzbget_category_backlog" id="nzbget_category_backlog"
                                                           value="${settings.NZBGET_CATEGORY_BACKLOG}"
                                                           class="form-control input-sm input200" autocapitalize="off"/>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="nzbget_category_backlog">${_('send downloads of old episodes marked this category (e.g. TV)')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Use NZBget category for anime')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="text" name="nzbget_category_anime" id="nzbget_category_anime"
                                                           value="${settings.NZBGET_CATEGORY_ANIME}"
                                                           class="form-control input-sm input200" autocapitalize="off"/>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="nzbget_category_anime">${_('send anime downloads marked this category (e.g. anime)')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Use NZBget category for anime (backlog episodes)')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="text" name="nzbget_category_anime_backlog"
                                                           id="nzbget_category_anime_backlog"
                                                           value="${settings.NZBGET_CATEGORY_ANIME_BACKLOG}"
                                                           class="form-control input-sm input200" autocapitalize="off"/>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="nzbget_category_anime_backlog">${_('send anime downloads of old episodes marked this category (e.g. anime)')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('NZBget priority')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <select name="nzbget_priority" id="nzbget_priority" class="form-control input-sm input200">
                                                        <option value="-100" ${('', 'selected="selected"')[settings.NZBGET_PRIORITY == -100]}>${_('Very low')}</option>
                                                        <option value="-50" ${('', 'selected="selected"')[settings.NZBGET_PRIORITY == -50]}>${_('Low')}</option>
                                                        <option value="0" ${('', 'selected="selected"')[settings.NZBGET_PRIORITY == 0]}>${_('Normal')}</option>
                                                        <option value="50" ${('', 'selected="selected"')[settings.NZBGET_PRIORITY == 50]}>${_('High')}</option>
                                                        <option value="100" ${('', 'selected="selected"')[settings.NZBGET_PRIORITY == 100]}>${_('Very high')}</option>
                                                        <option value="900" ${('', 'selected="selected"')[settings.NZBGET_PRIORITY == 900]}>${_('Force')}</option>
                                                    </select>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="nzbget_priority">${_('priority for daily snatches (no backlog)')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div id="download_station_settings">

                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title" id="host_title">${_('Torrent host:port')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="text" name="syno_dsm_host" id="syno_dsm_host"
                                                           value="${settings.SYNOLOGY_DSM_HOST}"
                                                           class="form-control input-sm input350" autocapitalize="off"/>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="syno_dsm_host">${_('URL to your Synology DSM (e.g. http://localhost:5000/)')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title" id="username_title">${_('Client username')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="text" name="syno_dsm_user" id="syno_dsm_user"
                                                           value="${settings.SYNOLOGY_DSM_USERNAME}"
                                                           class="form-control input-sm input200" autocapitalize="off"
                                                           autocomplete="no"/>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="syno_dsm_user">${_('(blank for none)')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title" id="password_title">${_('Client password')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input
                                                        type="password" name="syno_dsm_pass" id="syno_dsm_pass" value="${settings.SYNOLOGY_DSM_PASSWORD|hide}"
                                                        class="form-control input-sm input200" autocomplete="no" autocapitalize="off"
                                                    />
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="syno_dsm_pass">${_('(blank for none)')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title" id="directory_title">${_('Downloaded files location')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="text" name="syno_dsm_path" id="syno_dsm_path"
                                                           value="${settings.SYNOLOGY_DSM_PATH}"
                                                           class="form-control input-sm input350" autocapitalize="off"/>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="syno_dsm_path">${_('where Synology Download Station will save downloaded files (blank for client default)')}</label>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <span id="path_synology"> <b>${_('note')}:</b> ${_('the destination has to be a shared folder for Synology DS')}</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div class="row">
                                    <div class="col-md-12">
                                        <div class="testNotification" id="testSABnzbd_result">${_('Click below to test')}</div>
                                        <div class="testNotification" id="testDSM_result">${_('Click below to test')}</div>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-12">
                                        <input class="btn test-button" type="button" value="Test SABnzbd" id="testSABnzbd"/>
                                        <input type="button" value="Test DSM" id="testDSM" class="btn test-button"/>
                                        <input type="submit" class="btn config_submitter" value="${_('Save Changes')}"/>
                                    </div>
                                </div>


                            </div><!-- /content_use_nzbs //-->

                        </fieldset>
                    </div>
                </div>
            </div>

            <!-- Torrent search -->
            <div id="torrent-search" class="component-group">
                <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-4 col-xs-12">
                        <div class="component-group-desc">
                            <h3>${_('Torrent Search')}</h3>
                            <p>${_('How to handle Torrent search results.')}</p>
                            <div id="torrent_method_icon" class="add-client-icon-${settings.TORRENT_METHOD}"></div>
                        </div>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-8 col-xs-12">
                        <fieldset class="component-group-list">
                            <div class="field-pair row">
                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                    <label class="component-title">${_('Search torrents')}</label>
                                </div>
                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                    <input type="checkbox" name="use_torrents" class="enabler"
                                           id="use_torrents" ${('', 'checked="checked"')[bool(settings.USE_TORRENTS)]}/>
                                    <label for="use_torrents">${_('enable torrent search providers')}</label>
                                </div>
                            </div>
                            <div id="content_use_torrents">
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Trackers list')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" name="trackers_list" value="${settings.TRACKERS_LIST}"
                                                       class="form-control input-sm input350" autocapitalize="off"/>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="trackers_list">
                                                    ${_('''trackers that will be added to magnets without trackers<br>separate trackers with a comma, e.g. "tracker1,tracker2,tracker3"''')}
                                                </label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <label class="component-title">${_('Send torrents to')}</label>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <select name="torrent_method" id="torrent_method" class="form-control input-sm input200" title="torrent_method">
                                            % for curAction, curTitle in getClientListDict().items():
                                                <option value="${curAction}" ${('', 'selected="selected"')[settings.TORRENT_METHOD == curAction]}>${curTitle}</option>
                                            % endfor
                                        </select>
                                    </div>
                                </div>
                                <div id="options_torrent_blackhole">
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Black hole folder location')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="text" name="torrent_dir" id="torrent_dir"
                                                           value="${settings.TORRENT_DIR}"
                                                           class="form-control input-sm input350" autocapitalize="off"/>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="torrent_dir">${_('<b>.torrent</b> files are stored at this location for external software to find and use')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-12">
                                            <input type="submit" class="btn config_submitter" value="${_('Save Changes')}"/>
                                        </div>
                                    </div>
                                </div>
                                <div id="options_torrent_clients">
                                    <div class="field-pair row" id="torrent_host_option">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title" id="host_title">${_('Torrent host:port')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="text" name="torrent_host" id="torrent_host" value="${settings.TORRENT_HOST}"
                                                           class="form-control input-sm input350" autocapitalize="off"/>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="torrent_host" id="host_desc_torrent">${_('URL to your torrent client (e.g. http://localhost:8000/)')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="field-pair row" id="torrent_rpcurl_option">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title" id="rpcurl_title">${_('Torrent RPC URL')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="text" name="torrent_rpcurl" id="torrent_rpcurl"
                                                           value="${settings.TORRENT_RPCURL}"
                                                           class="form-control input-sm input350" autocapitalize="off"/>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="torrent_rpcurl" id="rpcurl_desc_">${_('the path without leading and trailing slashes (e.g. transmission)')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="field-pair row" id="torrent_auth_type_option">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Http Authentication')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <select name="torrent_auth_type" id="torrent_auth_type" class="form-control input-sm input150" title="torrent_auth_type">
                                                <% http_authtype = {'none': "None", 'basic': "Basic", 'digest': "Digest"} %>
                                                % for authvalue, authname in http_authtype.items():
                                                    <option id="torrent_auth_type_value"
                                                            value="${authvalue}" ${('', 'selected="selected"')[settings.TORRENT_AUTH_TYPE == authvalue]}>${authname}</option>
                                                % endfor
                                            </select>
                                        </div>
                                    </div>
                                    <div class="field-pair row" id="torrent_verify_cert_option">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Verify certificate')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" name="torrent_verify_cert" class="enabler"
                                                   id="torrent_verify_cert" ${('', 'checked="checked"')[bool(settings.TORRENT_VERIFY_CERT)]}/>
                                            <label for="torrent_verify_cert"></label>
                                        </div>
                                    </div>
                                    <div class="field-pair row" id="torrent_username_option">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title" id="username_title">${_('Client username')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="text" name="torrent_username" id="torrent_username"
                                                           value="${settings.TORRENT_USERNAME}"
                                                           class="form-control input-sm input200" autocapitalize="off"
                                                           autocomplete="no"/>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="torrent_username">${_('(blank for none)')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="field-pair row" id="torrent_password_option">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title" id="password_title">${_('Client password')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input
                                                        type="password" name="torrent_password" id="torrent_password" value="${settings.TORRENT_PASSWORD|hide}"
                                                        class="form-control input-sm input200" autocomplete="no" autocapitalize="off"/>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="torrent_password">${_('(blank for none)')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div id="torrent_label_option">
                                        <div class="field-pair row">
                                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                                <label class="component-title">${_('Add label to torrent')}</label>
                                            </div>
                                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                                <div class="row">
                                                    <div class="col-md-12">
                                                        <input type="text" name="torrent_label" id="torrent_label"
                                                               value="${settings.TORRENT_LABEL}"
                                                               class="form-control input-sm input200" autocapitalize="off"/>
                                                    </div>
                                                </div>
                                                <div class="row">
                                                    <div class="col-md-12">
                                                        <span id="label_warning_deluge" style="display:none">
                                                            <label for="torrent_label">${_('(blank spaces are not allowed)')}</label>
                                                            <label><b>${_('note')}:</b> ${_('label plugin must be enabled in Deluge clients')}</label>
                                                        </span>
                                                        <span id="label_warning_qbittorrent" style="display:none">
                                                            <label for="torrent_label">${_('(blank spaces are not allowed)')}</label>
                                                            <label><b>${_('note')}:</b> ${_('for QBitTorrent 3.3.1 and up')}</label>
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="field-pair row">
                                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                                <label class="component-title">${_('Add label to torrent for anime')}</label>
                                            </div>
                                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                                <div class="row">
                                                    <div class="col-md-12">
                                                        <input type="text" name="torrent_label_anime" id="torrent_label_anime"
                                                               value="${settings.TORRENT_LABEL_ANIME}"
                                                               class="form-control input-sm input200" autocapitalize="off"/>
                                                    </div>
                                                </div>
                                                <div class="row">
                                                    <div class="col-md-12">
                                                        <span id="label_anime_warning_deluge" style="display:none">
                                                            <label for="torrent_label_anime">${_('(blank spaces are not allowed)')}</label>
                                                            <label><b>${_('note')}:</b> ${_('label plugin must be enabled in Deluge clients')}</label>
                                                        </span>
                                                        <span id="label_anime_warning_qbittorrent" style="display:none">
                                                            <label for="torrent_label_anime">${_('(blank spaces are not allowed)')}</label>
                                                            <label><b>${_('note')}:</b> ${_('for QBitTorrent 3.3.1 and up ')}</label>
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="field-pair row" id="torrent_path_option">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title" id="directory_title">${_('Downloaded files location')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="text" name="torrent_path" id="torrent_path" value="${settings.TORRENT_PATH}"
                                                           class="form-control input-sm input350" autocapitalize="off"/>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="torrent_path">
                                                        ${_('where <span id="torrent_client">the torrent client</span> will save downloaded files (blank for client default)')}
                                                    </label>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label id="path_synology"><b>${_('note')}:</b> ${_('the destination has to be a shared folder for Synology DS</span>')}</label>
                                                </div>
                                            </div>
                                        </div>
                                        <div id="torrent_path_incomplete_option">
                                            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                                <label class="component-title" id="directory_title">${_('Incomplete files location')}</label>
                                            </div>
                                            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                                <div class="row">
                                                    <div class="col-md-12">
                                                        <input type="text" name="torrent_path_incomplete" id="torrent_path_incomplete"
                                                               value="${settings.TORRENT_PATH_INCOMPLETE}"
                                                               class="form-control input-sm input350" autocapitalize="off"/>
                                                    </div>
                                                </div>
                                                <div class="row">
                                                    <div class="col-md-12">
                                                        <label for="torrent_path_incomplete">
                                                            ${_('where incomplete downloads will be saved until they are completed (blank for client default)')}
                                                        </label>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="field-pair row" id="torrent_seed_time_option">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title" id="torrent_seed_time_label">${_('Minimum seeding time')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="number" step="1" name="torrent_seed_time" id="torrent_seed_time"
                                                           value="${settings.TORRENT_SEED_TIME}" class="form-control input-sm input100"/>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="torrent_seed_time">${_('time in hours')}</label>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <label for="torrent_seed_time">${_('(default:\'0\' passes blank to client and \'-1\' passes nothing)')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="field-pair row" id="torrent_paused_option">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Start torrent paused')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="checkbox" name="torrent_paused" class="enabler"
                                                           id="torrent_paused" ${('', 'checked="checked"')[bool(settings.TORRENT_PAUSED)]}/>
                                                    <label for="torrent_paused">${_('add torrent to client but do <b style="font-weight:900">not</b> start downloading')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="field-pair row" id="torrent_high_bandwidth_option">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <label class="component-title">${_('Allow high bandwidth')}</label>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <input type="checkbox" name="torrent_high_bandwidth" class="enabler"
                                                           id="torrent_high_bandwidth" ${('', 'checked="checked"')[bool(settings.TORRENT_HIGH_BANDWIDTH)]}/>
                                                    <label for="torrent_high_bandwidth">${_('use high bandwidth allocation if priority is high')}</label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="row">
                                        <div class="col-md-12">
                                            <div class="testNotification" id="test_torrent_result">${_('Click below to test')}</div>
                                        </div>
                                    </div>

                                    <div class="row">
                                        <div class="col-md-12">
                                            <input class="btn test-button" type="button" value="${_('Test Connection')}" id="test_torrent"/>
                                            <input type="submit" class="btn config_submitter" value="${_('Save Changes')}"/>
                                        </div>
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
