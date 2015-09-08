<%inherit file="/layouts/main.mako"/>
<%!
    import os.path
    import sickbeard
    from sickbeard.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickbeard.common import Quality, qualityPresets, statusStrings, qualityPresetStrings, cpu_presets, multiEpStrings
    from sickbeard import config
    from sickbeard import metadata
    from sickbeard.metadata.generic import GenericMetadata
    from sickbeard import naming
%>

<%block name="scripts">
<script type="text/javascript" src="${sbRoot}/js/configPostProcessing.js?${sbPID}"></script>
<script type="text/javascript" src="${sbRoot}/js/config.js?${sbPID}"></script>
<script type="text/javascript">
    $('#config-components').tabs();
    $('#tv_download_dir').fileBrowser({ title: 'Select TV Download Directory' });
</script>
</%block>
<%block name="content">
<div id="content960">
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif
<div id="config">
<div id="config-content">

<form id="configForm" action="savePostProcessing" method="post">

            <div id="config-components">
                <ul>
                    <li><a href="#core-component-group1">Post-Processing</a></li>
                    <li><a href="#core-component-group2">Episode Naming</a></li>
                    <li><a href="#core-component-group3">Metadata</a></li>
                </ul>

                <div id="core-component-group1" class="component-group">

                    <div class="component-group-desc">
                        <h3>Post-Processing</h3>
                        <p>Settings that dictate how SickRage should process completed downloads.</p>
                    </div>

                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label class="nocheck" for="tv_download_dir">
                                <span class="component-title">TV Download Dir</span>
                                <input type="text" name="tv_download_dir" id="tv_download_dir" value="${sickbeard.TV_DOWNLOAD_DIR}" class="form-control input-sm input350" />
                            </label>
                            <label class="nocheck">
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc">The folder where your download client puts the completed TV downloads.</span>
                            </label>
                            <label class="nocheck">
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc"><b>NOTE:</b> Please use seperate downloading and completed folders in your download client if possible. Also, if you keep seeding torrents after they finish, please set Process Method to 'copy' instead of move to prevent errors while moving files.</span>
                            </label>
                            <label class="nocheck">
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc"><b>NOTE:</b> Use only if not using SABnzbd+ post processing.</span>
                            </label>
                            <label class="nocheck">
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc">Or if SABnzbd+ and SickRage are on different PCs.</span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label class="nocheck" for="process_method">
                                <span class="component-title">Process Episode Method:</span>
                                <span class="component-desc">
                                    <select name="process_method" id="process_method" class="form-control input-sm">
                                        <% process_method_text = {'copy': "Copy", 'move': "Move", 'hardlink': "Hard Link", 'symlink' : "Symbolic Link"} %>
                                        % for curAction in ('copy', 'move', 'hardlink', 'symlink'):
                                        <option value="${curAction}" ${('', 'selected="selected"')[sickbeard.PROCESS_METHOD == curAction]}>${process_method_text[curAction]}</option>
                                        % endfor
                                    </select>
                                </span>
                            </label>
                            <label class="nocheck">
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc">What method should be used to put file in the TV directory?</span>
                            </label>
                        </div>
                        <div class="field-pair">
                            <input type="checkbox" name="del_rar_contents" id="del_rar_contents" ${('', 'checked="checked"')[bool(sickbeard.DELRARCONTENTS)]}/>
                            <label for="del_rar_contents">
                                <span class="component-title">Delete RAR contents</span>
                                <span class="component-desc">Delete content of RAR files, even if Process Method not set to move?</span>
                            </label>
                        </div>
                        <div class="field-pair">
                            <input type="checkbox" name="skip_removed_files" id="skip_removed_files" ${('', 'checked="checked"')[bool(sickbeard.SKIP_REMOVED_FILES)]}/>
                            <label for="skip_removed_files">
                                <span class="component-title">Skip Remove Detection</span>
                                <span class="component-desc">Skip detection of removed files, so they don't get set to ignored/archived?</span>
                            </label>
                            <label class="nocheck">
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc"><b>NOTE:</b> This may mean SickRage misses renames as well</span>
                            </label>
                        </div>
                        <div class="field-pair">
                            <label class="nocheck">
                                <span class="component-title">Extra Scripts</span>
                                <input type="text" name="extra_scripts" value="${'|'.join(sickbeard.EXTRA_SCRIPTS)}" class="form-control input-sm input350" />
                            </label>
                            <label class="nocheck">
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc"><b>NOTE:</b></span>
                            </label>
                            <label class="nocheck">
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc">
                                    <ul>
                                        <li>See <a href="https://github.com/SiCKRAGETV/sickrage-issues/wiki/Post-Processing"><font color='red'><b>Wiki</b></font></a> for a script arguments description.</li>
                                        <li>Additional scripts separated by <b>|</b>.</li>
                                        <li>Scripts are called after SickRage's own post-processing.</li>
                                        <li>For any scripted languages, include the interpreter executable before the script. See the following example:</li>
                                        <ul>
                                            <li>For Windows: <pre>C:\Python27\pythonw.exe C:\Script\test.py</pre></li>
                                            <li>For Linux: <pre>python /Script/test.py</pre></li>
                                        </ul>
                                    </ul>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <input type="checkbox" name="move_associated_files" id="move_associated_files" ${('', 'checked="checked"')[bool(sickbeard.MOVE_ASSOCIATED_FILES)]}/>
                            <label for="move_associated_files">
                                <span class="component-title">Move Associated Files</span>
                                <span class="component-desc">Move srr/srt/sfv/etc files with the episode when processed?</span>
                            </label>
                        </div>
                        <div class="field-pair">
                            <label class="nocheck">
                                <span class="component-title">Sync File Extensions</span>
                                <input type="text" name="sync_files" id="sync_files" value="${sickbeard.SYNC_FILES}" class="form-control input-sm input350" />
                            </label>
                            <label class="nocheck">
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc">comma seperated list of extensions SickRage ignores when Post Processing</span>
                            </label>
                        </div>
                        <div class="field-pair">
                            <input type="checkbox" name="postpone_if_sync_files" id="postpone_if_sync_files" ${('', 'checked="checked"')[bool(sickbeard.POSTPONE_IF_SYNC_FILES)]}/>
                            <label for="postpone_if_sync_files">
                                <span class="component-title">Postpone post processing</span>
                                <span class="component-desc">if sync files are present in the TV download dir</span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <input type="checkbox" name="nfo_rename" id="nfo_rename" ${('', 'checked="checked"')[bool(sickbeard.NFO_RENAME)]}/>
                            <label for="nfo_rename">
                                <span class="component-title">Rename .nfo file</span>
                                <span class="component-desc">Rename the original .nfo file to .nfo-orig to avoid conflicts?</span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <input type="checkbox" name="rename_episodes" id="rename_episodes" ${('', 'checked="checked"')[bool(sickbeard.RENAME_EPISODES)]}/>
                            <label for="rename_episodes">
                                <span class="component-title">Rename Episodes</span>
                                <span class="component-desc">Rename episode using the Episode Naming settings?</span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <input type="checkbox" name="airdate_episodes" id="airdate_episodes" ${('', 'checked="checked"')[bool(sickbeard.AIRDATE_EPISODES)]}/>
                            <label for="airdate_episodes">
                                <span class="component-title">Change File Date</span>
                                <span class="component-desc">Set last modified filedate to the date that the episode aired?</span>
                            </label>
                            <label class="nocheck">
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc"><b>NOTE:</b> Some systems may ignore this feature.</span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <input type="checkbox" name="process_automatically" id="process_automatically" ${('', 'checked="checked"')[bool(sickbeard.PROCESS_AUTOMATICALLY)]}/>
                            <label for="process_automatically">
                                <span class="component-title">Scan and Process</span>
                                <span class="component-desc">Scan and post-process any files in your <i>TV Download Dir</i>?</span>
                            </label>
                            <label class="nocheck" for="process_automatically">
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc"><b>NOTE:</b> Do not use if you use PostProcesing external script</span>
                            </label>
                            <label class="nocheck">
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc">eg. NZBMedia w/ NZBGET, sabToSickbeard w/ SABnzbd+!</span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <input type="checkbox" name="no_delete" id="no_delete" ${('', 'checked="checked"')[bool(sickbeard.NO_DELETE)]}/>
                            <label for="no_delete">
                                <span class="component-title">Don't delete empty folders</span>
                                <span class="component-desc">Leave empty folders when Post Processing?</span>
                            </label>
                            <label class="nocheck" for="no_delete">
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc"><b>NOTE:</b> Can be overridden using manual Post Processing</span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label class="nocheck">
                                <span class="component-title">Auto Post-Processing Frequency</span>
                                <input type="text" name="autopostprocesser_frequency" id="autopostprocesser_frequency" value="${sickbeard.AUTOPOSTPROCESSER_FREQUENCY}" class="form-control input-sm input75" />
                            </label>
                            <label class="nocheck">
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc">Time in minutes to check for new files to auto post-process (eg. 10)</span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <input id="unpack" type="checkbox" name="unpack" ${('', 'checked="checked"')[bool(sickbeard.UNPACK)]} />
                            <label for="unpack">
                                <span class="component-title">Unpack</span>
                                <span class="component-desc">Unpack any TV releases in your <i>TV Download Dir</i>?</span>
                            </label>
                            <label class="nocheck" for="unpack">
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc"><b>NOTE:</b> Only working with RAR archive</span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <input id="use_failed_downloads" type="checkbox" class="enabler" name="use_failed_downloads" ${('', 'checked="checked"')[bool(sickbeard.USE_FAILED_DOWNLOADS)]}/>
                            <label for="use_failed_downloads">
                                <span class="component-title">Use Failed Downloads</span>
                                <span class="component-desc">Use Failed Download Handling?</span>
                            </label>
                            <label class="nocheck" for="use_failed_downloads">
                                <span class="component-title">&nbsp;</span>
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

                        <input type="submit" class="btn config_submitter" value="Save Changes" /><br/>

                    </fieldset>
                </div><!-- /component-group1 //-->

                <div id="core-component-group2" class="component-group">

                    <div class="component-group-desc">
                        <h3>Episode Naming</h3>
                        <p>How SickRage will name and sort your episodes.</p>
                    </div>

                    <fieldset class="component-group-list">

                        <div class="field-pair">
                            <label class="nocheck" for="name_presets">
                                <span class="component-title">Name Pattern:</span>
                                <span class="component-desc">
                                    <select id="name_presets" class="form-control input-sm">
                                        <% is_custom = True %>
                                        % for cur_preset in naming.name_presets:
                                            <% tmp = naming.test_name(cur_preset, anime_type=3) %>
                                            % if cur_preset == sickbeard.NAMING_PATTERN:
                                                <% is_custom = False %>
                                            % endif
                                            <option id="${cur_preset}" ${('', 'selected="selected"')[sickbeard.NAMING_PATTERN == cur_preset]}>${os.path.join(tmp['dir'], tmp['name'])}</option>
                                        % endfor
                                        <option id="${sickbeard.NAMING_PATTERN}" ${('', 'selected="selected"')[bool(is_custom)]}>Custom...</option>
                                    </select>
                                </span>
                            </label>
                        </div>

                        <div id="naming_custom">
                            <div class="field-pair" style="padding-top: 0;">
                                <label class="nocheck">
                                    <span class="component-title">
                                        &nbsp;
                                    </span>
                                    <span class="component-desc">
                                        <input type="text" name="naming_pattern" id="naming_pattern" value="${sickbeard.NAMING_PATTERN}" class="form-control input-sm input350" />
                                        <img src="${sbRoot}/images/legend16.png" width="16" height="16" alt="[Toggle Key]" id="show_naming_key" title="Toggle Naming Legend" class="legend" class="legend" />
                                    </span>
                                </label>
                                <label class="nocheck">
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc"><b>NOTE:</b> Dont' forget to add quality pattern. Otherwise after post-procesing the episode will have UNKNOWN quality</span>
                                 </label>
                            </div>

                            <div id="naming_key" class="nocheck" style="display: none;">
                                  <table class="Key">
                                    <thead>
                                        <tr>
                                          <th class="align-right">Meaning</th>
                                          <th>Pattern</th>
                                          <th width="60%">Result</th>
                                        </tr>
                                    </thead>
                                    <tfoot>
                                        <tr>
                                          <th colspan="3">Use lower case if you want lower case names (eg. %sn, %e.n, %q_n etc)</th>
                                        </tr>
                                    </tfoot>
                                    <tbody>
                                        <tr>
                                          <td class="align-right"><b>Show Name:</b></td>
                                          <td>%SN</td>
                                          <td>Show Name</td>
                                        </tr>
                                        <tr class="even">
                                          <td>&nbsp;</td>
                                          <td>%S.N</td>
                                          <td>Show.Name</td>
                                        </tr>
                                        <tr>
                                          <td>&nbsp;</td>
                                          <td>%S_N</td>
                                          <td>Show_Name</td>
                                        </tr>
                                        <tr class="even">
                                          <td class="align-right"><b>Season Number:</b></td>
                                          <td>%S</td>
                                          <td>2</td>
                                        </tr>
                                        <tr>
                                          <td>&nbsp;</td>
                                          <td>%0S</td>
                                          <td>02</td>
                                        </tr>
                                        <tr class="even">
                                          <td class="align-right"><b>XEM Season Number:</b></td>
                                          <td>%XMS</td>
                                          <td>2</td>
                                        </tr>
                                        <tr>
                                          <td>&nbsp;</td>
                                          <td>%0XMS</td>
                                          <td>02</td>
                                        </tr>
                                        <tr class="even">
                                          <td class="align-right"><b>Episode Number:</b></td>
                                          <td>%E</td>
                                          <td>3</td>
                                        </tr>
                                        <tr>
                                          <td>&nbsp;</td>
                                          <td>%0E</td>
                                          <td>03</td>
                                        </tr>
                                        <tr class="even">
                                          <td class="align-right"><b>XEM Episode Number:</b></td>
                                          <td>%XME</td>
                                          <td>3</td>
                                        </tr>
                                        <tr>
                                          <td>&nbsp;</td>
                                          <td>%0XME</td>
                                          <td>03</td>
                                        </tr>
                                        <tr class="even">
                                          <td class="align-right"><b>Episode Name:</b></td>
                                          <td>%EN</td>
                                          <td>Episode Name</td>
                                        </tr>
                                        <tr>
                                          <td>&nbsp;</td>
                                          <td>%E.N</td>
                                          <td>Episode.Name</td>
                                        </tr>
                                        <tr class="even">
                                          <td>&nbsp;</td>
                                          <td>%E_N</td>
                                          <td>Episode_Name</td>
                                        </tr>
                                        <tr>
                                          <td class="align-right"><b>Quality:</b></td>
                                          <td>%QN</td>
                                          <td>720p BluRay</td>
                                        </tr>
                                        <tr class="even">
                                          <td>&nbsp;</td>
                                          <td>%Q.N</td>
                                          <td>720p.BluRay</td>
                                        </tr>
                                        <tr>
                                          <td>&nbsp;</td>
                                          <td>%Q_N</td>
                                          <td>720p_BluRay</td>
                                        </tr>
                                        <tr class="even">
                                          <td class="align-right"><i class="icon-info-sign" title="Multi-EP style is ignored"></i> <b>Release Name:</b></td>
                                          <td>%RN</td>
                                          <td>Show.Name.S02E03.HDTV.XviD-RLSGROUP</td>
                                        </tr>
                                        <tr>
                                          <td class="align-right"><i class="icon-info-sign" title="'SiCKRAGE' is used in place of RLSGROUP if it could not be properly detected"></i> <b>Release Group:</b></td>
                                          <td>%RG</td>
                                          <td>RLSGROUP</td>
                                        </tr>
                                        <tr class="even">
                                          <td class="align-right"><i class="icon-info-sign" title="If episode is proper/repack add 'proper' to name."></i> <b>Release Type:</b></td>
                                          <td>%RT</td>
                                          <td>PROPER</td>
                                        </tr>
                                    </tbody>
                                  </table>
                                  <br/>
                            </div>
                        </div>

                        <div class="field-pair">
                            <label class="nocheck" for="naming_multi_ep">
                                <span class="component-title">Multi-Episode Style:</span>
                                <span class="component-desc">
                                    <select id="naming_multi_ep" name="naming_multi_ep" class="form-control input-sm">
                                    % for cur_multi_ep in sorted(multiEpStrings.iteritems(), key=lambda x: x[1]):
                                        <option value="${cur_multi_ep[0]}" ${('', 'selected="selected"')[cur_multi_ep[0] == sickbeard.NAMING_MULTI_EP]}>${cur_multi_ep[1]}</option>
                                    % endfor
                                    </select>
                                </span>
                            </label>
                        </div>

                        <div id="naming_example_div">
                            <h3>Single-EP Sample:</h3>
                            <div class="example">
                                <span class="jumbo" id="naming_example">&nbsp;</span>
                            </div>
                            <br/>
                        </div>

                        <div id="naming_example_multi_div">
                            <h3>Multi-EP sample:</h3>
                            <div class="example">
                                <span class="jumbo" id="naming_example_multi">&nbsp;</span>
                            </div>
                            <br/>
                        </div>

                        <div class="field-pair">
                            <input type="checkbox" id="naming_strip_year"  name="naming_strip_year" ${('', 'checked="checked"')[bool(sickbeard.NAMING_STRIP_YEAR)]}/>
                            <label for="naming_strip_year">
                                <span class="component-title">Strip Show Year</span>
                                <span class="component-desc">Remove the TV show's year when renaming the file?</span>
                            </label>
                            <label class="nocheck">
                                <span class="component-title">&nbsp;</span>
                                <span class="component-desc">Only applies to shows that have year inside parentheses</span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <input type="checkbox" class="enabler" id="naming_custom_abd" name="naming_custom_abd" ${('', 'checked="checked"')[bool(sickbeard.NAMING_CUSTOM_ABD)]}/>
                            <label for="naming_custom_abd">
                                <span class="component-title">Custom Air-By-Date</span>
                                <span class="component-desc">Name Air-By-Date shows differently than regular shows?</span>
                            </label>
                        </div>

                        <div id="content_naming_custom_abd">
                            <div class="field-pair">
                                <label class="nocheck" for="name_abd_presets">
                                    <span class="component-title">Name Pattern:</span>
                                    <span class="component-desc">
                                        <select id="name_abd_presets" class="form-control input-sm">
                                            <% is_abd_custom = True %>
                                            % for cur_preset in naming.name_abd_presets:
                                                <% tmp = naming.test_name(cur_preset) %>
                                                % if cur_preset == sickbeard.NAMING_ABD_PATTERN:
                                                    <% is_abd_custom = False %>
                                                % endif
                                                <option id="${cur_preset}" ${('', 'selected="selected"')[sickbeard.NAMING_ABD_PATTERN == cur_preset]}>${os.path.join(tmp['dir'], tmp['name'])}</option>
                                            % endfor
                                            <option id="${sickbeard.NAMING_ABD_PATTERN}" ${('', 'selected="selected"')[bool(is_abd_custom)]}>Custom...</option>
                                        </select>
                                    </span>
                                </label>
                            </div>

                            <div id="naming_abd_custom">
                                <div class="field-pair">
                                    <label class="nocheck">
                                        <span class="component-title">
                                            &nbsp;
                                        </span>
                                        <span class="component-desc">
                                            <input type="text" name="naming_abd_pattern" id="naming_abd_pattern" value="${sickbeard.NAMING_ABD_PATTERN}" class="form-control input-sm input350" />
                                            <img src="${sbRoot}/images/legend16.png" width="16" height="16" alt="[Toggle Key]" id="show_naming_abd_key" title="Toggle ABD Naming Legend" class="legend" />
                                        </span>
                                    </label>
                                </div>

                                <div id="naming_abd_key" class="nocheck" style="display: none;">
                                      <table class="Key">
                                        <thead>
                                            <tr>
                                              <th class="align-right">Meaning</th>
                                              <th>Pattern</th>
                                              <th width="60%">Result</th>
                                            </tr>
                                        </thead>
                                        <tfoot>
                                            <tr>
                                              <th colspan="3">Use lower case if you want lower case names (eg. %sn, %e.n, %q_n etc)</th>
                                            </tr>
                                        </tfoot>
                                        <tbody>
                                            <tr>
                                              <td class="align-right"><b>Show Name:</b></td>
                                              <td>%SN</td>
                                              <td>Show Name</td>
                                            </tr>
                                            <tr class="even">
                                              <td>&nbsp;</td>
                                              <td>%S.N</td>
                                              <td>Show.Name</td>
                                            </tr>
                                            <tr>
                                              <td>&nbsp;</td>
                                              <td>%S_N</td>
                                              <td>Show_Name</td>
                                            </tr>
                                            <tr class="even">
                                              <td class="align-right"><b>Regular Air Date:</b></td>
                                              <td>%AD</td>
                                              <td>2010 03 09</td>
                                            </tr>
                                            <tr>
                                              <td>&nbsp;</td>
                                              <td>%A.D</td>
                                              <td>2010.03.09</td>
                                            </tr>
                                            <tr class="even">
                                              <td>&nbsp;</td>
                                              <td>%A_D</td>
                                              <td>2010_03_09</td>
                                            </tr>
                                            <tr>
                                              <td>&nbsp;</td>
                                              <td>%A-D</td>
                                              <td>2010-03-09</td>
                                            </tr>
                                            <tr class="even">
                                              <td class="align-right"><b>Episode Name:</b></td>
                                              <td>%EN</td>
                                              <td>Episode Name</td>
                                            </tr>
                                            <tr>
                                              <td>&nbsp;</td>
                                              <td>%E.N</td>
                                              <td>Episode.Name</td>
                                            </tr>
                                            <tr class="even">
                                              <td>&nbsp;</td>
                                              <td>%E_N</td>
                                              <td>Episode_Name</td>
                                            </tr>
                                            <tr>
                                              <td class="align-right"><b>Quality:</b></td>
                                              <td>%QN</td>
                                              <td>720p BluRay</td>
                                            </tr>
                                            <tr class="even">
                                              <td>&nbsp;</td>
                                              <td>%Q.N</td>
                                              <td>720p.BluRay</td>
                                            </tr>
                                            <tr>
                                              <td>&nbsp;</td>
                                              <td>%Q_N</td>
                                              <td>720p_BluRay</td>
                                            </tr>
                                            <tr class="even">
                                              <td class="align-right"><b>Year:</b></td>
                                              <td>%Y</td>
                                              <td>2010</td>
                                            </tr>
                                            <tr>
                                              <td class="align-right"><b>Month:</b></td>
                                              <td>%M</td>
                                              <td>3</td>
                                            </tr>
                                            <tr class="even">
                                              <td class="align-right">&nbsp;</td>
                                              <td>%0M</td>
                                              <td>03</td>
                                            </tr>
                                            <tr>
                                              <td class="align-right"><b>Day:</b></td>
                                              <td>%D</td>
                                              <td>9</td>
                                            </tr>
                                            <tr class="even">
                                              <td class="align-right">&nbsp;</td>
                                              <td>%0D</td>
                                              <td>09</td>
                                            </tr>
                                            <tr>
                                              <td class="align-right"><i class="icon-info-sign" title="Multi-EP style is ignored"></i> <b>Release Name:</b></td>
                                              <td>%RN</td>
                                              <td>Show.Name.2010.03.09.HDTV.XviD-RLSGROUP</td>
                                            </tr>
                                            <tr class="even">
                                              <td class="align-right"><i class="icon-info-sign" title="'SiCKRAGE' is used in place of RLSGROUP if it could not be properly detected"></i> <b>Release Group:</b></td>
                                              <td>%RG</td>
                                              <td>RLSGROUP</td>
                                            </tr>
                                            <tr>
                                              <td class="align-right"><i class="icon-info-sign" title="If episode is proper/repack add 'proper' to name."></i> <b>Release Type:</b></td>
                                              <td>%RT</td>
                                              <td>PROPER</td>
                                            </tr>
                                        </tbody>
                                      </table>
                                      <br/>
                                </div>
                            </div><!-- /naming_abd_custom -->

                            <div id="naming_abd_example_div">
                                <h3>Sample:</h3>
                                <div class="example">
                                    <span class="jumbo" id="naming_abd_example">&nbsp;</span>
                                </div>
                                <br/>
                            </div>

                        </div><!-- /naming_abd_different -->

                        <div class="field-pair">
                            <input type="checkbox" class="enabler" id="naming_custom_sports" name="naming_custom_sports" ${('', 'checked="checked"')[bool(sickbeard.NAMING_CUSTOM_SPORTS)]}/>
                            <label for="naming_custom_sports">
                                <span class="component-title">Custom Sports</span>
                                <span class="component-desc">Name Sports shows differently than regular shows?</span>
                            </label>
                        </div>

                        <div id="content_naming_custom_sports">
                            <div class="field-pair">
                                <label class="nocheck" for="name_sports_presets">
                                    <span class="component-title">Name Pattern:</span>
                                    <span class="component-desc">
                                        <select id="name_sports_presets" class="form-control input-sm">
                                            <% is_sports_custom = True %>
                                            % for cur_preset in naming.name_sports_presets:
                                                <% tmp = naming.test_name(cur_preset) %>
                                                % if cur_preset == sickbeard.NAMING_SPORTS_PATTERN:
                                                    <% is_sports_custom = False %>
                                                % endif
                                                <option id="${cur_preset}" ${('', 'selected="selected"')[NAMING_SPORTS_PATTERN == cur_preset]}>${os.path.join(tmp['dir'], tmp['name'])}</option>
                                            % endfor
                                            <option id="${sickbeard.NAMING_SPORTS_PATTERN}" ${('', 'selected="selected"')[bool(is_sports_custom)]}>Custom...</option>
                                        </select>
                                    </span>
                                </label>
                            </div>

                            <div id="naming_sports_custom">
                                <div class="field-pair" style="padding-top: 0;">
                                    <label class="nocheck">
                                        <span class="component-title">
                                            &nbsp;
                                        </span>
                                        <span class="component-desc">
                                            <input type="text" name="naming_sports_pattern" id="naming_sports_pattern" value="${sickbeard.NAMING_SPORTS_PATTERN}" class="form-control input-sm input350" />
                                            <img src="${sbRoot}/images/legend16.png" width="16" height="16" alt="[Toggle Key]" id="show_naming_sports_key" title="Toggle Sports Naming Legend" class="legend" />
                                        </span>
                                    </label>
                                </div>

                                <div id="naming_sports_key" class="nocheck" style="display: none;">
                                      <table class="Key">
                                        <thead>
                                            <tr>
                                              <th class="align-right">Meaning</th>
                                              <th>Pattern</th>
                                              <th width="60%">Result</th>
                                            </tr>
                                        </thead>
                                        <tfoot>
                                            <tr>
                                              <th colspan="3">Use lower case if you want lower case names (eg. %sn, %e.n, %q_n etc)</th>
                                            </tr>
                                        </tfoot>
                                        <tbody>
                                            <tr>
                                              <td class="align-right"><b>Show Name:</b></td>
                                              <td>%SN</td>
                                              <td>Show Name</td>
                                            </tr>
                                            <tr class="even">
                                              <td>&nbsp;</td>
                                              <td>%S.N</td>
                                              <td>Show.Name</td>
                                            </tr>
                                            <tr>
                                              <td>&nbsp;</td>
                                              <td>%S_N</td>
                                              <td>Show_Name</td>
                                            </tr>
                                            <tr class="even">
                                              <td class="align-right"><b>Sports Air Date:</b></td>
                                              <td>%AD</td>
                                              <td>9 Mar 2011</td>
                                            </tr>
                                            <tr>
                                              <td>&nbsp;</td>
                                              <td>%A.D</td>
                                              <td>9.Mar.2011</td>
                                            </tr>
                                            <tr class="even">
                                              <td>&nbsp;</td>
                                              <td>%A_D</td>
                                              <td>9_Mar_2011</td>
                                            </tr>
                                            <tr>
                                              <td>&nbsp;</td>
                                              <td>%A-D</td>
                                              <td>9-Mar-2011</td>
                                            </tr>
                                            <tr class="even">
                                              <td class="align-right"><b>Episode Name:</b></td>
                                              <td>%EN</td>
                                              <td>Episode Name</td>
                                            </tr>
                                            <tr>
                                              <td>&nbsp;</td>
                                              <td>%E.N</td>
                                              <td>Episode.Name</td>
                                            </tr>
                                            <tr class="even">
                                              <td>&nbsp;</td>
                                              <td>%E_N</td>
                                              <td>Episode_Name</td>
                                            </tr>
                                            <tr>
                                              <td class="align-right"><b>Quality:</b></td>
                                              <td>%QN</td>
                                              <td>720p BluRay</td>
                                            </tr>
                                            <tr class="even">
                                              <td>&nbsp;</td>
                                              <td>%Q.N</td>
                                              <td>720p.BluRay</td>
                                            </tr>
                                            <tr>
                                              <td>&nbsp;</td>
                                              <td>%Q_N</td>
                                              <td>720p_BluRay</td>
                                            </tr>
                                            <tr class="even">
                                              <td class="align-right"><b>Year:</b></td>
                                              <td>%Y</td>
                                              <td>2010</td>
                                            </tr>
                                            <tr>
                                              <td class="align-right"><b>Month:</b></td>
                                              <td>%M</td>
                                              <td>3</td>
                                            </tr>
                                            <tr class="even">
                                              <td class="align-right">&nbsp;</td>
                                              <td>%0M</td>
                                              <td>03</td>
                                            </tr>
                                            <tr>
                                              <td class="align-right"><b>Day:</b></td>
                                              <td>%D</td>
                                              <td>9</td>
                                            </tr>
                                            <tr class="even">
                                              <td class="align-right">&nbsp;</td>
                                              <td>%0D</td>
                                              <td>09</td>
                                            </tr>
                                            <tr>
                                              <td class="align-right"><i class="icon-info-sign" title="Multi-EP style is ignored"></i> <b>Release Name:</b></td>
                                              <td>%RN</td>
                                              <td>Show.Name.9th.Mar.2011.HDTV.XviD-RLSGROUP</td>
                                            </tr>
                                            <tr class="even">
                                              <td class="align-right"><i class="icon-info-sign" title="'SiCKRAGE' is used in place of RLSGROUP if it could not be properly detected"></i> <b>Release Group:</b></td>
                                              <td>%RG</td>
                                              <td>RLSGROUP</td>
                                            </tr>
                                            <tr>
                                              <td class="align-right"><i class="icon-info-sign" title="If episode is proper/repack add 'proper' to name."></i> <b>Release Type:</b></td>
                                              <td>%RT</td>
                                              <td>PROPER</td>
                                            </tr>
                                        </tbody>
                                      </table>
                                      <br/>
                                </div>
                            </div><!-- /naming_sports_custom -->

                            <div id="naming_sports_example_div">
                                <h3>Sample:</h3>
                                <div class="example">
                                    <span class="jumbo" id="naming_sports_example">&nbsp;</span>
                                </div>
                                <br/>
                            </div>

                        </div><!-- /naming_sports_different -->

                        <!-- naming_anime_custom -->
                        <div class="field-pair">
                            <input type="checkbox" class="enabler" id="naming_custom_anime" name="naming_custom_anime" ${('', 'checked="checked"')[bool(sickbeard.NAMING_CUSTOM_ANIME)]}/>
                            <label for="naming_custom_anime">
                                <span class="component-title">Custom Anime</span>
                                <span class="component-desc">Name Anime shows differently than regular shows?</span>
                            </label>
                        </div>

                        <div id="content_naming_custom_anime">
                            <div class="field-pair">
                                <label class="nocheck" for="name_anime_presets">
                                    <span class="component-title">Name Pattern:</span>
                                    <span class="component-desc">
                                        <select id="name_anime_presets" class="form-control input-sm">
                                            <% is_anime_custom = True %>
                                            % for cur_preset in naming.name_anime_presets:
                                                <% tmp = naming.test_name(cur_preset) %>
                                                % if cur_preset == sickbeard.NAMING_ANIME_PATTERN:
                                                    <% is_anime_custom = False %>
                                                % endif
                                                <option id="${cur_preset}" ${('', 'selected="selected"')[cur_preset == sickbeard.NAMING_ANIME_PATTERN]}>${os.path.join(tmp['dir'], tmp['name'])}</option>
                                            % endfor
                                            <option id="${sickbeard.NAMING_ANIME_PATTERN}" ${('', 'selected="selected"')[bool(is_anime_custom)]}>Custom...</option>
                                        </select>
                                    </span>
                                </label>
                            </div>

                            <div id="naming_anime_custom">
                                <div class="field-pair" style="padding-top: 0;">
                                    <label class="nocheck">
                                        <span class="component-title">
                                            &nbsp;
                                        </span>
                                        <span class="component-desc">
                                            <input type="text" name="naming_anime_pattern" id="naming_anime_pattern" value="${sickbeard.NAMING_ANIME_PATTERN}" class="form-control input-sm input350" />
                                            <img src="${sbRoot}/images/legend16.png" width="16" height="16" alt="[Toggle Key]" id="show_naming_anime_key" title="Toggle Anime Naming Legend" class="legend" />
                                        </span>
                                    </label>
                                </div>

                                <div id="naming_anime_key" class="nocheck" style="display: none;">
                                      <table class="Key">
                                        <thead>
                                            <tr>
                                              <th class="align-right">Meaning</th>
                                              <th>Pattern</th>
                                              <th width="60%">Result</th>
                                            </tr>
                                        </thead>
                                        <tfoot>
                                            <tr>
                                              <th colspan="3">Use lower case if you want lower case names (eg. %sn, %e.n, %q_n etc)</th>
                                            </tr>
                                        </tfoot>
                                        <tbody>
                                            <tr>
                                              <td class="align-right"><b>Show Name:</b></td>
                                              <td>%SN</td>
                                              <td>Show Name</td>
                                            </tr>
                                            <tr class="even">
                                              <td>&nbsp;</td>
                                              <td>%S.N</td>
                                              <td>Show.Name</td>
                                            </tr>
                                            <tr>
                                              <td>&nbsp;</td>
                                              <td>%S_N</td>
                                              <td>Show_Name</td>
                                            </tr>
                                            <tr class="even">
                                              <td class="align-right"><b>Season Number:</b></td>
                                              <td>%S</td>
                                              <td>2</td>
                                            </tr>
                                            <tr>
                                              <td>&nbsp;</td>
                                              <td>%0S</td>
                                              <td>02</td>
                                            </tr>
                                            <tr class="even">
                                              <td class="align-right"><b>XEM Season Number:</b></td>
                                              <td>%XMS</td>
                                              <td>2</td>
                                            </tr>
                                            <tr>
                                              <td>&nbsp;</td>
                                              <td>%0XMS</td>
                                              <td>02</td>
                                            </tr>
                                            <tr class="even">
                                              <td class="align-right"><b>Episode Number:</b></td>
                                              <td>%E</td>
                                              <td>3</td>
                                            </tr>
                                            <tr>
                                              <td>&nbsp;</td>
                                              <td>%0E</td>
                                              <td>03</td>
                                            </tr>
                                            <tr class="even">
                                              <td class="align-right"><b>XEM Episode Number:</b></td>
                                              <td>%XME</td>
                                              <td>3</td>
                                            </tr>
                                            <tr>
                                              <td>&nbsp;</td>
                                              <td>%0XME</td>
                                              <td>03</td>
                                            </tr>
                                            <tr class="even">
                                              <td class="align-right"><b>Episode Name:</b></td>
                                              <td>%EN</td>
                                              <td>Episode Name</td>
                                            </tr>
                                            <tr>
                                              <td>&nbsp;</td>
                                              <td>%E.N</td>
                                              <td>Episode.Name</td>
                                            </tr>
                                            <tr class="even">
                                              <td>&nbsp;</td>
                                              <td>%E_N</td>
                                              <td>Episode_Name</td>
                                            </tr>
                                            <tr>
                                              <td class="align-right"><b>Quality:</b></td>
                                              <td>%QN</td>
                                              <td>720p BluRay</td>
                                            </tr>
                                            <tr class="even">
                                              <td>&nbsp;</td>
                                              <td>%Q.N</td>
                                              <td>720p.BluRay</td>
                                            </tr>
                                            <tr>
                                              <td>&nbsp;</td>
                                              <td>%Q_N</td>
                                              <td>720p_BluRay</td>
                                            </tr>
                                            <tr class="even">
                                              <td class="align-right"><i class="icon-info-sign" title="Multi-EP style is ignored"></i> <b>Release Name:</b></td>
                                              <td>%RN</td>
                                              <td>Show.Name.S02E03.HDTV.XviD-RLSGROUP</td>
                                            </tr>
                                            <tr>
                                              <td class="align-right"><i class="icon-info-sign" title="'SiCKRAGE' is used in place of RLSGROUP if it could not be properly detected"></i> <b>Release Group:</b></td>
                                              <td>%RG</td>
                                              <td>RLSGROUP</td>
                                            </tr>
                                            <tr class="even">
                                              <td class="align-right"><i class="icon-info-sign" title="If episode is proper/repack add 'proper' to name."></i> <b>Release Type:</b></td>
                                              <td>%RT</td>
                                              <td>PROPER</td>
                                            </tr>
                                        </tbody>
                                      </table>
                                      <br/>
                                </div>
                            </div><!-- /naming_anime_custom -->

                            <div class="field-pair">
                                <label class="nocheck" for="naming_anime_multi_ep">
                                    <span class="component-title">Multi-Episode Style:</span>
                                    <span class="component-desc">
                                        <select id="naming_anime_multi_ep" name="naming_anime_multi_ep" class="form-control input-sm">
                                        % for cur_multi_ep in sorted(multiEpStrings.iteritems(), key=lambda x: x[1]):
                                            <option value="${cur_multi_ep[0]}" ${('', 'selected="selected" class="selected"')[cur_multi_ep[0] == sickbeard.NAMING_ANIME_MULTI_EP]}>${cur_multi_ep[1]}</option>
                                        % endfor
                                        </select>
                                    </span>
                                </label>
                            </div>

                            <div id="naming_example_anime_div">
                                <h3>Single-EP Anime Sample:</h3>
                                <div class="example">
                                    <span class="jumbo" id="naming_example_anime">&nbsp;</span>
                                </div>
                                <br/>
                            </div>

                            <div id="naming_example_multi_anime_div">
                                <h3>Multi-EP Anime sample:</h3>
                                <div class="example">
                                    <span class="jumbo" id="naming_example_multi_anime">&nbsp;</span>
                                </div>
                                <br/>
                            </div>

                            <div class="field-pair">
                                <input type="radio" name="naming_anime" id="naming_anime" value="1" ${('', 'checked="checked"')[sickbeard.NAMING_ANIME == 1]}/>
                                <label for="naming_anime">
                                    <span class="component-title">Add Absolute Number</span>
                                    <span class="component-desc">Add the absolute number to the season/episode format?</span>
                                </label>
                                <label class="nocheck">
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">Only applies to animes. (eg. S15E45 - 310 vs S15E45)</span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <input type="radio" name="naming_anime" id="naming_anime_only" value="2" ${('', 'checked="checked"')[sickbeard.NAMING_ANIME == 2]}/>
                                <label for="naming_anime_only">
                                    <span class="component-title">Only Absolute Number</span>
                                    <span class="component-desc">Replace season/episode format with absolute number</span>
                                </label>
                                <label class="nocheck">
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">Only applies to animes.</span>
                                </label>
                            </div>

                            <div class="field-pair">
                                <input type="radio" name="naming_anime" id="naming_anime_none" value="3" ${('', 'checked="checked"')[sickbeard.NAMING_ANIME == 3]}/>
                                <label for="naming_anime_none">
                                    <span class="component-title">No Absolute Number</span>
                                    <span class="component-desc">Dont include the absolute number</span>
                                </label>
                                <label class="nocheck">
                                    <span class="component-title">&nbsp;</span>
                                    <span class="component-desc">Only applies to animes.</span>
                                </label>
                            </div>

                        </div><!-- /naming_anime_different -->

                        <div></div>
                        <input type="submit" class="btn config_submitter" value="Save Changes" /><br/>

                    </fieldset>
                </div><!-- /component-group2 //-->

                <div id="core-component-group3" class="component-group">

                    <div class="component-group-desc">
                        <h3>Metadata</h3>
                        <p>The data associated to the data. These are files associated to a TV show in the form of images and text that, when supported, will enhance the viewing experience.</p>
                    </div>

                    <fieldset class="component-group-list">
                        <div class="field-pair">
                            <label>
                                <span class="component-title">Metadata Type:</span>
                                <span class="component-desc">
                                    <% m_dict = metadata.get_metadata_generator_dict() %>
                                    <select id="metadataType" class="form-control input-sm">
                                    % for (cur_name, cur_generator) in sorted(m_dict.iteritems()):
                                        <option value="${cur_generator.get_id()}">${cur_name}</option>
                                    % endfor
                                    </select>
                                </span>
                            </label>
                            <span>Toggle the metadata options that you wish to be created. <b>Multiple targets may be used.</b></span>
                        </div>

                        % for (cur_name, cur_generator) in m_dict.iteritems():
                        <% cur_metadata_inst = sickbeard.metadata_provider_dict[cur_generator.name] %>
                        <% cur_id = cur_generator.get_id() %>
                        <div class="metadataDiv" id="${cur_id}">
                            <div class="metadata_options_wrapper">
                                <h4>Create:</h4>
                                <div class="metadata_options">
                                    <label for="${cur_id}_show_metadata"><input type="checkbox" class="metadata_checkbox" id="${cur_id}_show_metadata" ${('', 'checked="checked"')[bool(cur_metadata_inst.show_metadata)]}/>&nbsp;Show Metadata</label>
                                    <label for="${cur_id}_episode_metadata"><input type="checkbox" class="metadata_checkbox" id="${cur_id}_episode_metadata" ${('', 'checked="checked"')[bool(cur_metadata_inst.episode_metadata)]}/>&nbsp;Episode Metadata</label>
                                    <label for="${cur_id}_fanart"><input type="checkbox" class="float-left metadata_checkbox" id="${cur_id}_fanart" ${('', 'checked="checked"')[bool(cur_metadata_inst.fanart)]}/>&nbsp;Show Fanart</label>
                                    <label for="${cur_id}_poster"><input type="checkbox" class="float-left metadata_checkbox" id="${cur_id}_poster" ${('', 'checked="checked"')[bool(cur_metadata_inst.poster)]}/>&nbsp;Show Poster</label>
                                    <label for="${cur_id}_banner"><input type="checkbox" class="float-left metadata_checkbox" id="${cur_id}_banner" ${('', 'checked="checked"')[bool(cur_metadata_inst.banner)]}/>&nbsp;Show Banner</label>
                                    <label for="${cur_id}_episode_thumbnails"><input type="checkbox" class="float-left metadata_checkbox" id="${cur_id}_episode_thumbnails" ${('', 'checked="checked"')[bool(cur_metadata_inst.episode_thumbnails)]}/>&nbsp;Episode Thumbnails</label>
                                    <label for="${cur_id}_season_posters"><input type="checkbox" class="float-left metadata_checkbox" id="${cur_id}_season_posters" ${('', 'checked="checked"')[bool(cur_metadata_inst.season_posters)]}/>&nbsp;Season Posters</label>
                                    <label for="${cur_id}_season_banners"><input type="checkbox" class="float-left metadata_checkbox" id="${cur_id}_season_banners" ${('', 'checked="checked"')[bool(cur_metadata_inst.season_banners)]}/>&nbsp;Season Banners</label>
                                    <label for="${cur_id}_season_all_poster"><input type="checkbox" class="float-left metadata_checkbox" id="${cur_id}_season_all_poster" ${('', 'checked="checked"')[bool(cur_metadata_inst.season_all_poster)]}/>&nbsp;Season All Poster</label>
                                    <label for="${cur_id}_season_all_banner"><input type="checkbox" class="float-left metadata_checkbox" id="${cur_id}_season_all_banner" ${('', 'checked="checked"')[bool(cur_metadata_inst.season_all_banner)]}/>&nbsp;Season All Banner</label>
                                </div>
                            </div>
                            <div class="metadata_example_wrapper">
                                <h4>Results:</h4>
                                <div class="metadata_example">
                                    <label for="${cur_id}_show_metadata"><span id="${cur_id}_eg_show_metadata">${cur_metadata_inst.eg_show_metadata}</span></label>
                                    <label for="${cur_id}_episode_metadata"><span id="${cur_id}_eg_episode_metadata">${cur_metadata_inst.eg_episode_metadata}</span></label>
                                    <label for="${cur_id}_fanart"><span id="${cur_id}_eg_fanart">${cur_metadata_inst.eg_fanart}</span></label>
                                    <label for="${cur_id}_poster"><span id="${cur_id}_eg_poster">${cur_metadata_inst.eg_poster}</span></label>
                                    <label for="${cur_id}_banner"><span id="${cur_id}_eg_banner">${cur_metadata_inst.eg_banner}</span></label>
                                    <label for="${cur_id}_episode_thumbnails"><span id="${cur_id}_eg_episode_thumbnails">${cur_metadata_inst.eg_episode_thumbnails}</span></label>
                                    <label for="${cur_id}_season_posters"><span id="${cur_id}_eg_season_posters">${cur_metadata_inst.eg_season_posters}</span></label>
                                    <label for="${cur_id}_season_banners"><span id="${cur_id}_eg_season_banners">${cur_metadata_inst.eg_season_banners}</span></label>
                                    <label for="${cur_id}_season_all_poster"><span id="${cur_id}_eg_season_all_poster">${cur_metadata_inst.eg_season_all_poster}</span></label>
                                    <label for="${cur_id}_season_all_banner"><span id="${cur_id}_eg_season_all_banner">${cur_metadata_inst.eg_season_all_banner}</span></label>
                                </div>
                            </div>
                            <input type="hidden" name="${cur_id}_data" id="${cur_id}_data" value="${cur_metadata_inst.get_config()}" />
                        </div>
                        % endfor

                        <div class="clearfix"></div><br/>

                        <input type="submit" class="btn config_submitter" value="Save Changes" /><br/>
                    </fieldset>
                </div><!-- /component-group3 //-->

                <br/>
                <h6 class="pull-right"><b>All non-absolute folder locations are relative to <span class="path">${sickbeard.DATA_DIR}</span></b> </h6>
                <input type="submit" class="btn pull-left config_submitter button" value="Save Changes" />

        </form>
    </div>
</div>

<div class="clearfix"></div>
</%block>
