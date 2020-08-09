<%inherit file="/layouts/config.mako"/>
<%!
    from sickchill.oldbeard import common
%>

<%block name="tabs">
    <li><a href="#main">${_('Main')}</a></li>
</%block>

<%block name="pages">
    <form id="configForm" action="massEditSubmit" method="post" accept-charset="utf-8">
        <input type="hidden" name="toEdit" value="${showList}" />

        <div id="main">

            <div class="row">
                <div class="col-md-12">
                    <h3>${_('Main Settings')}</h3>

                    <label>==>&nbsp;${_('Changing any settings marked with (<span class="separator">*</span>) will force a refresh of the selected shows.')}</label><br>
                    <br>
                </div>
            </div>

            <fieldset class="component-group-list">

                <div class="field-pair row">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <span class="component-title">${_('Selected Shows')}</span>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="row">
                            <div class="col-md-12">
                                <span style="font-size: 14px;">${', '.join(sorted(showNames))}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="field-pair row">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <span class="component-title">${_('Root Directories')} (<span class="separator">*</span>)</span>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="row">
                            <div class="col-md-12">
                                <table class="sickchillTable">
                                    <thead>
                                        <tr>
                                            <th class="nowrap tablesorter-header">${_('Current')}</th>
                                            <th class="nowrap tablesorter-header">${_('New')}</th>
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
                                                    <a href="#" class="btn edit_root_dir" class="edit_root_dir" id="edit_root_dir_${cur_index}">${_('Edit')}</a>
                                                    <a href="#" class="btn delete_root_dir" class="delete_root_dir" id="delete_root_dir_${cur_index}">${_('Delete')}</a>
                                                    <input type="hidden" name="orig_root_dir_${cur_index}" value="${cur_dir}" />
                                                    <input type="text" style="display: none" name="new_root_dir_${cur_index}" id="new_root_dir_${cur_index}" class="new_root_dir" value="${cur_dir}" autocapitalize="off" />
                                                </td>
                                            </tr>
                                        % endfor
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="field-pair row">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <span class="component-title">${_('Preferred Quality')}</span>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="row">
                            <div class="col-md-12">
                                <%
                                    if quality_value is not None:
                                        initial_quality = int(quality_value)
                                    else:
                                        initial_quality = common.SD

                                    anyQualities, bestQualities = common.Quality.splitQuality(initial_quality)
                                %>
                                <div class="row">
                                    <div class="col-lg-4 col-md-4 col-sm-4 col-xs-12">
                                        <select id="qualityPreset" name="quality_preset" class="form-control form-control-inline input-sm" title="Quality Preset">
                                            <option value="keep">&lt; ${_('Keep')} &gt;</option>
                                            <% selected = None %>
                                            <option value="0" ${('', 'selected="selected"')[quality_value is not None and quality_value not in common.qualityPresets]}>${_('Custom')}</option>
                                            % for curPreset in sorted(common.qualityPresets):
                                                <option value="${curPreset}" ${('', 'selected="selected"')[quality_value == curPreset]}>${common.qualityPresetStrings[curPreset]}</option>
                                            % endfor
                                        </select>
                                    </div>
                                    <div class="col-lg-8 col-md-8 col-sm-8 col-xs-12">
                                        <div id="customQuality" style="padding-left: 0;">
                                            <div style="padding-right: 40px; text-align: left; float: left;">
                                                <h5>${_('Allowed')}</h5>
                                                <% anyQualityList = [x for x in common.Quality.qualityStrings if x > common.Quality.NONE] %>
                                                <select id="anyQualities" name="anyQualities" multiple="multiple" size="${len(anyQualityList)}" class="form-control form-control-inline input-sm">
                                                    % for curQuality in sorted(anyQualityList):
                                                        <option value="${curQuality}" ${('', 'selected="selected"')[curQuality in anyQualities]}>${common.Quality.qualityStrings[curQuality]}</option>
                                                    % endfor
                                                </select>
                                            </div>

                                            <div style="text-align: left; float: left;">
                                                <h5>${_('Preferred')}</h5>
                                                <% bestQualityList = [x for x in common.Quality.qualityStrings if x >= common.Quality.SDTV] %>
                                                <select id="bestQualities" name="bestQualities" multiple="multiple" size="${len(bestQualityList)}" class="form-control form-control-inline input-sm">
                                                    % for curQuality in sorted(bestQualityList):
                                                        <option value="${curQuality}" ${('', 'selected="selected"')[curQuality in bestQualities]}>${common.Quality.qualityStrings[curQuality]}</option>
                                                    % endfor
                                                </select>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="field-pair row">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <span class="component-title">Season folders (<span class="separator">*</span>)</span>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <select id="season_folders" name="season_folders" class="form-control form-control-inline input-sm">
                            <option value="keep" ${('', 'selected="selected"')[season_folders_value is None]}>&lt; ${_('Keep')} &gt;</option>
                            <option value="enable" ${('', 'selected="selected"')[season_folders_value == 1]}>${_('Yes')}</option>
                            <option value="disable" ${('', 'selected="selected"')[season_folders_value == 0]}>${_('No')}</option>
                        </select>
                        <label for="season_folders">${_('Group episodes by season folder (set to "No" to store in a single folder).')}</label>
                    </div>
                </div>

                <div class="field-pair row">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <span class="component-title">${_('Paused')}</span>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <select id="edit_paused" name="paused" class="form-control form-control-inline input-sm">
                            <option value="keep" ${('', 'selected="selected"')[paused_value is None]}>&lt; ${_('Keep')} &gt;</option>
                            <option value="enable" ${('', 'selected="selected"')[paused_value == 1]}>${_('Yes')}</option>
                            <option value="disable" ${('', 'selected="selected"')[paused_value == 0]}>${_('No')}</option>
                        </select>
                        <label for="edit_paused">${_('Pause these shows (SickChill will not download episodes).')}</label>
                    </div>
                </div>

                <div class="field-pair row">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <span class="component-title">${_('Default Episode Status')}</span>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <select id="edit_default_ep_status" name="default_ep_status" class="form-control form-control-inline input-sm">
                            <option value="keep">&lt; Keep &gt;</option>
                            % for curStatus in [common.WANTED, common.SKIPPED, common.IGNORED]:
                                <option value="${curStatus}" ${('', 'selected="selected"')[curStatus == default_ep_status_value]}>${common.statusStrings[curStatus]}</option>
                            % endfor
                        </select>
                        <label for="edit_default_ep_status">${_('This will set the status for future episodes.')}</label>
                    </div>
                </div>

                <div class="field-pair row">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <span class="component-title">${_('Scene Numbering')}</span>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <select id="edit_scene" name="scene" class="form-control form-control-inline input-sm">
                            <option value="keep" ${('', 'selected="selected"')[scene_value is None]}>&lt; ${_('Keep')} &gt;</option>
                            <option value="enable" ${('', 'selected="selected"')[scene_value == 1]}>${_('Yes')}</option>
                            <option value="disable" ${('', 'selected="selected"')[scene_value == 0]}>${_('No')}</option>
                        </select>
                        <label for="edit_scene">${_('Search by scene numbering (set to "No" to search by indexer numbering).')}</label>
                    </div>
                </div>

                <div class="field-pair row">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <span class="component-title">${_('Anime')}</span>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <select id="edit_anime" name="anime" class="form-control form-control-inline input-sm">
                            <option value="keep" ${('', 'selected="selected"')[anime_value is None]}>&lt; ${_('Keep')} &gt;</option>
                            <option value="enable" ${('', 'selected="selected"')[anime_value == 1]}>${_('Yes')}</option>
                            <option value="disable" ${('', 'selected="selected"')[anime_value == 0]}>${_('No')}</option>
                        </select><br>
                        <label for="edit_anime">${_('Set if these shows are Anime and episodes are released as Show.265 rather than Show.S02E03')}</label>
                    </div>
                </div>

                <div class="field-pair row">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <span class="component-title">${_('Sports')}</span>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="row">
                            <div class="col-md-12">
                                <select id="edit_sports" name="sports" class="form-control form-control-inline input-sm">
                                    <option value="keep" ${('', 'selected="selected"')[sports_value is None]}>&lt; ${_('Keep')} &gt;</option>
                                    <option value="enable" ${('', 'selected="selected"')[sports_value == 1]}>${_('Yes')}</option>
                                    <option value="disable" ${('', 'selected="selected"')[sports_value == 0]}>${_('No')}</option>
                                </select>
                                <label for="edit_sports">${_('Set if these shows are sporting or MMA events released as Show.03.02.2010 rather than Show.S02E03.')}</label>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-12">
                                <span style="color:red">${_('In case of an air date conflict between regular and special episodes, the later will be ignored.')}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="field-pair row">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <span class="component-title">${_('Air by date')}</span>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <div class="row">
                            <div class="col-md-12">
                                <select id="edit_air_by_date" name="air_by_date" class="form-control form-control-inline input-sm">
                                    <option value="keep" ${('', 'selected="selected"')[air_by_date_value is None]}>&lt; ${_('Keep')} &gt;</option>
                                    <option value="enable" ${('', 'selected="selected"')[air_by_date_value == 1]}>${_('Yes')}</option>
                                    <option value="disable" ${('', 'selected="selected"')[air_by_date_value == 0]}>${_('No')}</option>
                                </select>
                                <label for="edit_air_by_date">${_('Set if these shows are released as Show.03.02.2010 rather than Show.S02E03.')}</label>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-12">
                                <span style="color:red">${_('In case of an air date conflict between regular and special episodes, the later will be ignored.')}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="field-pair row">
                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                        <span class="component-title">${_('Subtitles')}</span>
                    </div>
                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                        <select id="edit_subtitles" name="subtitles" class="form-control form-control-inline input-sm">
                            <option value="keep" ${('', 'selected="selected"')[subtitles_value is None]}>&lt; ${_('Keep')} &gt;</option>
                            <option value="enable" ${('', 'selected="selected"')[subtitles_value == 1]}>${_('Yes')}</option>
                            <option value="disable" ${('', 'selected="selected"')[subtitles_value == 0]}>${_('No')}</option>
                        </select><br>
                        <label for="edit_subtitles">${_('Search for subtitles.')}</label>
                    </div>
                </div>

            </fieldset>
        </div>
    </form>
</%block>
