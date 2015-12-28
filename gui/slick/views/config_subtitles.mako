<%inherit file="/layouts/main.mako"/>
<%!
    from sickbeard import subtitles
    import sickbeard
    from sickbeard.helpers import anon_url
%>
<%block name="scripts">
<script>
$(document).ready(function() {
    $("#subtitles_languages").tokenInput([${','.join("{\"id\": \"" + code + "\", name: \"" + subtitles.name_from_code(code) + "\"}" for code in subtitles.subtitle_code_filter())}], {
        method: "POST",
        hintText: "Write to search a language and select it",
        preventDuplicates: true,
        prePopulate: [${','.join("{\"id\": \"" + code + "\", name: \"" + subtitles.name_from_code(code) + "\"}" for code in subtitles.wanted_languages())}],
        resultsFormatter: function(item){ return "<li><img src='${srRoot}/images/subtitles/flags/" + item.id + ".png' onError='this.onerror=null;this.src=\"${srRoot}/images/flags/unknown.png\";' style='vertical-align: middle !important;' /> " + item.name + "</li>" },
        tokenFormatter: function(item)  { return "<li><img src='${srRoot}/images/subtitles/flags/" + item.id + ".png' onError='this.onerror=null;this.src=\"${srRoot}/images/flags/unknown.png\";' style='vertical-align: middle !important;' /> " + item.name + "</li>" },
    });
});
$('#config-components').tabs();
$('#subtitles_dir').fileBrowser({ title: 'Select Subtitles Download Directory' });
</script>
</%block>
<%block name="content">
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif

<div id="config">
<div id="config-content">

<form id="configForm" action="saveSubtitles" method="post">

            <div id="config-components">
                <ul>
                    <li><a href="#subtitles-search">Subtitles Search</a></li>
                    <li><a href="#subtitles-plugin">Subtitles Plugin</a></li>
                    <li><a href="#plugin-settings">Plugin Settings</a></li>
                </ul>

                <div id="subtitles-search" class="component-group">

                    <div class="component-group-desc">
                        <h3>Subtitles Search</h3>
                        <p>Settings that dictate how SickRage handles subtitles search results.</p>
                    </div>

                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label for="use_subtitles" class="clearfix">
                                <span class="component-title">Search Subtitles</span>
                                <span class="component-desc">
                                    <input type="checkbox" class="enabler" ${('', ' checked="checked"')[bool(sickbeard.USE_SUBTITLES)]} id="use_subtitles" name="use_subtitles">
                                </span>
                            </label>
                        </div>
                        <div id="content_use_subtitles">
                                <div class="field-pair">
                                    <label>
                                        <span class="component-title">Subtitle Languages</span>
                                        <span class="component-desc"><input type="text" id="subtitles_languages" name="subtitles_languages" autocapitalize="off" /></span>
                                    </label>
                                </div>
                                <div class="field-pair">
                                    <label>
                                        <span class="component-title">Subtitle Directory</span>
                                        <input type="text" value="${sickbeard.SUBTITLES_DIR}" id="subtitles_dir" name="subtitles_dir" class="form-control input-sm input350">
                                    </label>
                                    <label>
                                            <span class="component-title">&nbsp;</span>
                                            <span class="component-desc">The directory where SickRage should store your <i>Subtitles</i> files.</span>
                                      </label>
                                    <label>
                                            <span class="component-title">&nbsp;</span>
                                            <span class="component-desc"><b>NOTE:</b> Leave empty if you want store subtitle in episode path.</span>
                                      </label>
                                </div>
                                <div class="field-pair">
                                    <label>
                                        <span class="component-title">Subtitle Find Frequency</span>
                                        <input type="number" name="subtitles_finder_frequency" value="${sickbeard.SUBTITLES_FINDER_FREQUENCY}" hours="1" min="1" step="1" class="form-control input-sm input75" />
                                        <span class="component-desc">time in hours between scans (default: 1)</span>
                                    </label>
                                </div>
                                <div class="field-pair">
                                    <label for="subtitles_perfect_match" class="clearfix">
                                        <span class="component-title">Perfect matches</span>
                                        <span class="component-desc">
                                            <input type="checkbox" class="enabler" ${('', ' checked="checked"')[bool(sickbeard.SUBTITLES_PERFECT_MATCH)]} id="subtitles_perfect_match" name="subtitles_perfect_match">
                                            <p>Only download subtitles that match: release group, video codec, audio codec and resolution</p>
                                            <p>If disabled you may get out of sync subtitles</p>
                                        </span>
                                    </label>
                                </div>
                                <div class="field-pair">
                                    <label class="clearfix" for="subtitles_history">
                                        <span class="component-title">Subtitles History</span>
                                        <span class="component-desc">
                                            <input type="checkbox" name="subtitles_history" id="subtitles_history" ${('', 'checked="checked"')[bool(sickbeard.SUBTITLES_HISTORY)]}/>
                                            <p>Log downloaded Subtitle on History page?</p>
                                        </span>
                                    </label>
                                </div>
                                <div class="field-pair">
                                    <label class="clearfix" for="subtitles_multi">
                                        <span class="component-title">Subtitles Multi-Language</span>
                                        <span class="component-desc">
                                            <input type="checkbox" name="subtitles_multi" id="subtitles_multi" ${('', 'checked="checked"')[bool(sickbeard.SUBTITLES_MULTI)]}/>
                                            <p>Append language codes to subtitle filenames?</p>
                                        </span>
                                    </label>
                                    <label>
                                        <span class="component-title">&nbsp;</span>
                                        <span class="component-desc"><b>NOTE:</b> This option is required if you use multiple subtitle languages.</span>
                                    </label>
                                </div>
                                <div class="field-pair">
                                    <label class="clearfix" for="subtitles_download_in_pp">
                                        <span class="component-title">Subtitles in Post-Process folder</span>
                                        <span class="component-desc">
                                            <input type="checkbox" name="subtitles_download_in_pp" id="subtitles_download_in_pp" ${('', 'checked="checked"')[bool(sickbeard.SUBTITLES_DOWNLOAD_IN_PP)]}/>
                                            <p>Download subtitles in post-process folder</p>
                                            <p>Useful if you only want the episode to be post-processed when it has subtitles associated</p>
                                            <p>You might also want to enable the post-process setting 'Postpone if no subtitle'</p>
                                        </span>
                                    </label>
                                </div>
                                <div class="field-pair">
                                    <label class="clearfix" for="embedded_subtitles_all">
                                        <span class="component-title">Embedded Subtitles</span>
                                        <span class="component-desc">
                                            <input type="checkbox" name="embedded_subtitles_all" id="embedded_subtitles_all" ${('', 'checked="checked"')[bool(sickbeard.EMBEDDED_SUBTITLES_ALL)]}/>
                                            <p>Ignore subtitles embedded inside video file?</p>
                                            <p><b>Warning: </b>this will ignore <u>all</u> embedded subtitles for every video file!</p>
                                        </span>
                                    </label>
                                </div>
                                <div class="field-pair">
                                    <label class="clearfix" for="subtitles_hearing_impaired">
                                        <span class="component-title">Hearing Impaired Subtitles</span>
                                        <span class="component-desc">
                                            <input type="checkbox" name="subtitles_hearing_impaired" id="subtitles_hearing_impaired" ${('', 'checked="checked"')[bool(sickbeard.SUBTITLES_HEARING_IMPAIRED)]}/>
                                            <p>Download hearing impaired style subtitles?</p>
                                        </span>
                                    </label>
                                </div>
                                <div class="field-pair">
                                        <label>
                                        <span class="component-title">Extra Scripts</span>
                                           <input type="text" name="subtitles_extra_scripts" value="${'|'.join(sickbeard.SUBTITLES_EXTRA_SCRIPTS)}" class="form-control input-sm input350" autocapitalize="off" />
                                        </label>
                                        <label>
                                        <span class="component-desc">
                                            <ul>
                                                    <li>See <a href="https://github.com/SickRage/SickRage/wiki/Subtitle%20Scripts"><font color='red'><b>Wiki</b></font></a> for a script arguments description.</li>
                                                    <li>Additional scripts separated by <b>|</b>.</li>
                                                    <li>Scripts are called after each episode has searched and downloaded subtitles.</li>
                                                    <li>For any scripted languages, include the interpreter executable before the script. See the following example:</li>
                                                    <ul>
                                                        <li>For Windows: <pre>C:\Python27\pythonw.exe C:\Script\test.py</pre></li>
                                                        <li>For Linux: <pre>python /Script/test.py</pre></li>
                                                    </ul>
                                            </ul>
                                        </span>
                                        </label>
                                </div>
                        </div>
                        <br><input type="submit" class="btn config_submitter" value="Save Changes" /><br>
                    </fieldset>
                </div><!-- /component-group1 //-->

                <div id="subtitles-plugin" class="component-group">

                    <div class="component-group-desc">
                        <h3>Subtitle Plugins</h3>
                        <p>Check off and drag the plugins into the order you want them to be used.</p>
                        <p class="note">At least one plugin is required.</p>
                        <p class="note"><span style="font-size: 16px;">*</span> Web-scraping plugin</p>
                    </div>

                    <fieldset class="component-group-list" style="margin-left: 50px; margin-top:36px">
                        <ul id="service_order_list">
                        % for curService in sickbeard.subtitles.sorted_service_list():
                            <li class="ui-state-default" id="${curService['name']}">
                                <input type="checkbox" id="enable_${curService['name']}" class="service_enabler" ${('', 'checked="checked"')[curService['enabled'] is True]}/>
                                <a href="${anon_url(curService['url'])}" class="imgLink" target="_new">
                                    <img src="${srRoot}/images/subtitles/${curService['image']}" alt="${curService['url']}" title="${curService['url']}" width="16" height="16" style="vertical-align:middle;"/>
                                </a>
                            <span style="vertical-align:middle;">${curService['name'].capitalize()}</span>
                            <span class="ui-icon ui-icon-arrowthick-2-n-s pull-right" style="vertical-align:middle;"></span>
                          </li>
                        % endfor
                        </ul>
                        <input type="hidden" name="service_order" id="service_order" value="${' '.join(['%s:%d' % (x['name'], x['enabled']) for x in sickbeard.subtitles.sorted_service_list()])}"/>

                        <br><input type="submit" class="btn config_submitter" value="Save Changes" /><br>
                    </fieldset>
                </div><!-- /component-group2 //-->
                <div id="plugin-settings" class="component-group">
                    <div class="component-group-desc">
                        <h3>Subtitle Settings</h3>
                        <p>Set user and password for each provider</p>
                    </div><!-- /component-group-desc //-->

                    <fieldset class="component-group-list" style="margin-left: 50px; margin-top:36px">
                        <%
                            providerLoginDict = {
                                'legendastv': {'user': sickbeard.LEGENDASTV_USER, 'pass': sickbeard.LEGENDASTV_PASS},
                                'addic7ed': {'user': sickbeard.ADDIC7ED_USER, 'pass': sickbeard.ADDIC7ED_PASS},
                                'opensubtitles': {'user': sickbeard.OPENSUBTITLES_USER, 'pass': sickbeard.OPENSUBTITLES_PASS}}
                        %>
                        % for curService in sickbeard.subtitles.sorted_service_list():
                            % if curService['name'] not in providerLoginDict.keys():
                                <% continue %>
                            % endif
                            ##<div class="field-pair${(' hidden', '')[curService['enabled']]}"> ## Need js to show/hide on save
                            <div class="field-pair">
                                <label class="nocheck" for="${curService['name']}_user">
                                    <span class="component-title">${curService['name'].capitalize()} User Name</span>
                                    <span class="component-desc">
                                        <input type="text" name="${curService['name']}_user" id="${curService['name']}_user" value="${providerLoginDict[curService['name']]['user']}" class="form-control input-sm input300" autocapitalize="off" autocomplete="no" />
                                    </span>
                                </label>
                                <label class="nocheck" for="${curService['name']}_pass">
                                    <span class="component-title">${curService['name'].capitalize()} Password</span>
                                    <span class="component-desc">
                                        <input type="password" name="${curService['name']}_pass" id="${curService['name']}_pass" value="${providerLoginDict[curService['name']]['pass']}" class="form-control input-sm input300" autocomplete="no" autocapitalize="off" />
                                    </span>
                                </label>
                            </div>
                        % endfor
                        <br><input type="submit" class="btn config_submitter" value="Save Changes" /><br>
                    </fieldset>
                </div><!-- /component-group3 //-->
                <br><input type="submit" class="btn config_submitter" value="Save Changes" /><br>
            </div><!-- /config-components //-->

</form>
</div>
</div>

<div class="clearfix"></div>
</%block>
