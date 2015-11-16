<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    from sickbeard import common
    from sickbeard.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickbeard.common import Quality, qualityPresets, qualityPresetStrings, statusStrings
    from sickrage.helper import exceptions
%>

<%block name="scripts">
<%
    if quality_value != None:
        initial_quality = int(quality_value)
    else:
        initial_quality = common.SD

    anyQualities, bestQualities = common.Quality.splitQuality(initial_quality)
%>
<script type="text/javascript" src="${srRoot}/js/qualityChooser.js?${sbPID}"></script>
<script type="text/javascript" src="${srRoot}/js/massEdit.js?${sbPID}"></script>
<script type="text/javascript" src="${srRoot}/js/new/manage_massEdit.js"></script>
</%block>

<%block name="content">

<div id="config">

    <div id="config-content">
        <form action="massEditSubmit" method="post">
            <input type="hidden" name="toEdit" value="${showList}" />

            <div id="config-components">
                <ul>
                    <li><a href="#core-component-group1">Main</a></li>
                </ul>

                <div id="core-component-group1">
                    <div class="component-group">
                        <h3>Main Settings</h3>

                        ==> <u>Changing any settings marked with (<span class="separator">*</span>) will force a refresh of the selected shows.</u><br>
                        <br>

                        <fieldset class="component-group-list">

                        <div class="field-pair">
                            <label for="shows">
                                <span class="component-title">Selected Shows</span>
                                <span class="component-desc">
                                    % for curName in sorted(showNames):
                                    <span style="font-size: 14px;">${curName}</span><br>
                                    % endfor
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="edit_root_dir_0">
                                <span class="component-title">Root Directories (<span class="separator">*</span>)</span>
                                <span class="component-desc">
                                    <table class="sickbeardTable" cellspacing="1" cellpadding="0" border="0">
                                        <thead>
                                            <tr>
                                                <th class="nowrap tablesorter-header">Current</th>
                                                <th class="nowrap tablesorter-header">New</th>
                                                <th class="nowrap tablesorter-header" style="width: 140px;">-</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                        % for cur_dir in root_dir_list:
                                            <% cur_index = root_dir_list.index(cur_dir) %>
                                            <tr class="listing-default">
                                                <td align="center">${cur_dir}</td>
                                                <td align="center" id="display_new_root_dir_${cur_index}">${cur_dir}</td>
                                                <td>
                                                    <a href="#" class="btn edit_root_dir" class="edit_root_dir" id="edit_root_dir_${cur_index}">Edit</a>
                                                    <a href="#" class="btn delete_root_dir" class="delete_root_dir" id="delete_root_dir_${cur_index}">Delete</a>
                                                    <input type="hidden" name="orig_root_dir_${cur_index}" value="${cur_dir}" />
                                                    <input type="text" style="display: none" name="new_root_dir_${cur_index}" id="new_root_dir_${cur_index}" class="new_root_dir" value="${cur_dir}" />
                                                </td>
                                            </tr>
                                        % endfor
                                        </tbody>
                                    </table>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="qualityPreset">
                                <span class="component-title">Preferred Quality</span>
                                <span class="component-desc">
                                    <%
                                        if quality_value != None:
                                            initial_quality = int(quality_value)
                                        else:
                                            initial_quality = common.SD
                                        endif

                                        anyQualities, bestQualities = common.Quality.splitQuality(initial_quality)
                                    %>
                                    <select id="qualityPreset" name="quality_preset" class="form-control form-control-inline input-sm">
                                        <option value="keep">&lt; Keep &gt;</option>
                                        <% selected = None %>
                                        <option value="0" ${('', 'selected="selected"')[quality_value != None and quality_value not in common.qualityPresets]}>Custom</option>
                                        % for curPreset in sorted(common.qualityPresets):
                                        <option value="${curPreset}" ${('', 'selected="selected"')[quality_value == curPreset]}>${common.qualityPresetStrings[curPreset]}</option>
                                        % endfor
                                    </select>

                                    <div id="customQuality" style="padding-left: 0px;">
                                        <div style="padding-right: 40px; text-align: left; float: left;">
                                            <h5>Allowed</h5>
                                            <% anyQualityList = filter(lambda x: x > common.Quality.NONE, common.Quality.qualityStrings) %>
                                            <select id="anyQualities" name="anyQualities" multiple="multiple" size="${len(anyQualityList)}" class="form-control form-control-inline input-sm">
                                                % for curQuality in sorted(anyQualityList):
                                                <option value="${curQuality}" ${('', 'selected="selected"')[curQuality in anyQualities]}>${common.Quality.qualityStrings[curQuality]}</option>
                                                % endfor
                                            </select>
                                        </div>

                                        <div style="text-align: left; float: left;">
                                            <h5>Preferred</h5>
                                            <% bestQualityList = filter(lambda x: x >= common.Quality.SDTV, common.Quality.qualityStrings) %>
                                            <select id="bestQualities" name="bestQualities" multiple="multiple" size="${len(bestQualityList)}" class="form-control form-control-inline input-sm">
                                                % for curQuality in sorted(bestQualityList):
                                                <option value="${curQuality}" ${('', 'selected="selected"')[curQuality in bestQualities]}>${common.Quality.qualityStrings[curQuality]}</option>
                                                % endfor
                                            </select>
                                        </div>
                                    </div>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="edit_archive_firstmatch">
                                <span class="component-title">Archive on first match</span>
                                <span class="component-desc">
                                    <select id="edit_archive_firstmatch" name="archive_firstmatch" class="form-control form-control-inline input-sm">
                                        <option value="keep" ${('', 'selected="selected"')[archive_firstmatch_value == None]}>&lt; Keep &gt;</option>
                                        <option value="enable" ${('', 'selected="selected"')[archive_firstmatch_value == 1]}>Yes</option>
                                        <option value="disable" ${('', 'selected="selected"')[archive_firstmatch_value == 0]}>No</option>
                                    </select><br>
                                    Archive episode after the first best match is found from your archive quality list.
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="edit_flatten_folders">
                                <span class="component-title">Season folders (<span class="separator">*</span>)</span>
                                <span class="component-desc">
                                    <select id="" name="flatten_folders" class="form-control form-control-inline input-sm">
                                        <option value="keep" ${('', 'selected="selected"')[flatten_folders_value == None]}>&lt; Keep &gt;</option>
                                        <option value="enable" ${('', 'selected="selected"')[flatten_folders_value == 0]}>Yes</option>
                                        <option value="disable" ${('', 'selected="selected"')[flatten_folders_value == 1]}>No</option>
                                    </select><br>
                                    Group episodes by season folder (set to "No" to store in a single folder).
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="edit_paused">
                                <span class="component-title">Paused</span>
                                <span class="component-desc">
                                    <select id="edit_paused" name="paused" class="form-control form-control-inline input-sm">
                                        <option value="keep" ${('', 'selected="selected"')[paused_value == None]}>&lt; Keep &gt;</option>
                                        <option value="enable" ${('', 'selected="selected"')[paused_value == 1]}>Yes</option>
                                        <option value="disable" ${('', 'selected="selected"')[paused_value == 0]}>No</option>
                                    </select><br/ >
                                    Pause these shows (SickRage will not download episodes).
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="edit_default_ep_status">
                                <span class="component-title">Default Episode Status</span>
                                <span class="component-desc">
                                    <select id="edit_default_ep_status" name="default_ep_status" class="form-control form-control-inline input-sm">
                                        <option value="keep">&lt; Keep &gt;</option>
                                        % for curStatus in [WANTED, SKIPPED, IGNORED]:
                                        <option value="${curStatus}" ${('', 'selected="selected"')[curStatus == default_ep_status_value]}>${statusStrings[curStatus]}</option>
                                        % endfor
                                    </select><br>
                                    This will set the status for future episodes.
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="edit_scene">
                                <span class="component-title">Scene Numbering</span>
                                <span class="component-desc">
                                    <select id="edit_scene" name="scene" class="form-control form-control-inline input-sm">
                                        <option value="keep" ${('', 'selected="selected"')[scene_value == None]}>&lt; Keep &gt;</option>
                                        <option value="enable" ${('', 'selected="selected"')[scene_value == 1]}>Yes</option>
                                        <option value="disable" ${('', 'selected="selected"')[scene_value == 0]}>No</option>
                                    </select><br>
                                    Search by scene numbering (set to "No" to search by indexer numbering).
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="edit_anime">
                                <span class="component-title">Anime</span>
                                <span class="component-desc">
                                    <select id="edit_anime" name="anime" class="form-control form-control-inline input-sm">
                                        <option value="keep" ${('', 'selected="selected"')[anime_value == None]}>&lt; Keep &gt;</option>
                                        <option value="enable" ${('', 'selected="selected"')[anime_value == 1]}>Yes</option>
                                        <option value="disable" ${('', 'selected="selected"')[anime_value == 0]}>No</option>
                                    </select><br>
                                    Set if these shows are Anime and episodes are released as Show.265 rather than Show.S02E03
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="edit_sports">
                                <span class="component-title">Sports</span>
                                <span class="component-desc">
                                    <select id="edit_sports" name="sports" class="form-control form-control-inline input-sm">
                                        <option value="keep" ${('', 'selected="selected"')[sports_value == None]}>&lt; Keep &gt;</option>
                                        <option value="enable" ${('', 'selected="selected"')[sports_value == 1]}>Yes</option>
                                        <option value="disable" ${('', 'selected="selected"')[sports_value == 0]}>No</option>
                                    </select><br>
                                    Set if these shows are sporting or MMA events released as Show.03.02.2010 rather than Show.S02E03.<br>
                                    <span style="color:red">In case of an air date conflict between regular and special episodes, the later will be ignored.</span>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="edit_air_by_date">
                                <span class="component-title">Air by date</span>
                                <span class="component-desc">
                                    <select id="edit_air_by_date" name="air_by_date" class="form-control form-control-inline input-sm">
                                        <option value="keep" ${('', 'selected="selected"')[air_by_date_value == None]}>&lt; Keep &gt;</option>
                                        <option value="enable" ${('', 'selected="selected"')[air_by_date_value == 1]}>Yes</option>
                                        <option value="disable" ${('', 'selected="selected"')[air_by_date_value == 0]}>No</option>
                                    </select><br>
                                    Set if these shows are released as Show.03.02.2010 rather than Show.S02E03.<br>
                                    <span style="color:red">In case of an air date conflict between regular and special episodes, the later will be ignored.</span>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="edit_subtitles">
                                <span class="component-title">Subtitles</span>
                                <span class="component-desc">
                                    <select id="edit_subtitles" name="subtitles" class="form-control form-control-inline input-sm">
                                        <option value="keep" ${('', 'selected="selected"')[subtitles_value == None]}>&lt; Keep &gt;</option>
                                        <option value="enable" ${('', 'selected="selected"')[subtitles_value == 1]}>Yes</option>
                                        <option value="disable" ${('', 'selected="selected"')[subtitles_value == 0]}>No</option>
                                    </select><br>
                                    Search for subtitles.
                                </span>
                            </label>
                        </div>

                        </fieldset>
                    </div>
                </div>

            </div>

            <input id="submit" type="submit" value="Save Changes" class="btn pull-left config_submitter button">
        </form>
    </div>
</div>

</%block>
