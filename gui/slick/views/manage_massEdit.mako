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
    endif

    anyQualities, bestQualities = common.Quality.splitQuality(initial_quality)
%>
<script type="text/javascript" src="${srRoot}/js/qualityChooser.js?${sbPID}"></script>
<script type="text/javascript" src="${srRoot}/js/massEdit.js?${sbPID}"></script>
<script type="text/javascript" src="${srRoot}/js/new/manage_massEdit.js"></script>
</%block>
<%block name="content">
<%
    if quality_value != None:
        initial_quality = int(quality_value)
    else:
        initial_quality = common.SD
    endif

    anyQualities, bestQualities = common.Quality.splitQuality(initial_quality)
%>
<form action="massEditSubmit" method="post">
<input type="hidden" name="toEdit" value="${showList}" />

<div class="optionWrapper">
    <span class="selectTitle">Root Directories <span class="separator">*</span></span><br />
    % for cur_dir in root_dir_list:
        <% cur_index = root_dir_list.index(cur_dir) %>
        <div>
            <input class="btn edit_root_dir" type="button" class="edit_root_dir" id="edit_root_dir_${cur_index}" value="Edit" />
            <input class="btn delete_root_dir" type="button" class="delete_root_dir" id="delete_root_dir_${cur_index}" value="Delete" />
            ${cur_dir} => <span id="display_new_root_dir_${cur_index}">${cur_dir}</span>
        </div>
        <input type="hidden" name="orig_root_dir_${cur_index}" value="${cur_dir}" />
        <input type="text" style="display: none" name="new_root_dir_${cur_index}" id="new_root_dir_${cur_index}" class="new_root_dir" value="${cur_dir}" />
    % endfor
</div>

<div class="optionWrapper">
<span class="selectTitle">Quality</span>
    <div class="selectChoices">
        <select id="qualityPreset" name="quality_preset" class="form-control form-control-inline input-sm">
            <option value="keep">&lt; keep &gt;</option>
            <% selected = None %>
            <option value="0" ${('', 'selected="selected"')[quality_value != None and quality_value not in common.qualityPresets]}>Custom</option>
            % for curPreset in sorted(common.qualityPresets):
            <option value="${curPreset}" ${('', 'selected="selected"')[quality_value == curPreset]}>${common.qualityPresetStrings[curPreset]}</option>
            % endfor
        </select>
    </div><br />

    <div id="customQuality">
        <div class="manageCustom pull-left">
        <h5>Allowed</h5>
            <% anyQualityList = filter(lambda x: x > common.Quality.NONE, common.Quality.qualityStrings) %>
            <select id="anyQualities" name="anyQualities" multiple="multiple" size="${len(anyQualityList)}">
            % for curQuality in sorted(anyQualityList):
            <option value="${curQuality}" ${('', 'selected="selected"')[curQuality in anyQualities]}>${common.Quality.qualityStrings[curQuality]}</option>
            % endfor
            </select>
        </div>
        <div class="manageCustom pull-left">
        <h5>Preferred</h5>
            <% bestQualityList = filter(lambda x: x >= common.Quality.SDTV, common.Quality.qualityStrings) %>
            <select id="bestQualities" name="bestQualities" multiple="multiple" size="${len(bestQualityList)}">
            % for curQuality in sorted(bestQualityList):
            <option value="${curQuality}" ${('', 'selected="selected"')[curQuality in bestQualities]}>${common.Quality.qualityStrings[curQuality]}</option>
            % endfor
            </select>
        </div>
    <br />
    </div>
</div>

<div class="optionWrapper clearfix">
<span class="selectTitle">Archive on first match</span>
    <div class="selectChoices">
        <select id="edit_archive_firstmatch" name="archive_firstmatch" class="form-control form-control-inline input-sm">
            <option value="keep" ${('', 'selected="selected"')[archive_firstmatch_value == None]}>&lt; keep &gt;</option>
            <option value="enable" ${('', 'selected="selected"')[archive_firstmatch_value == 1]}>enable</option>
            <option value="disable" ${('', 'selected="selected"')[archive_firstmatch_value == 0]}>disable</option>
        </select>
    </div>
</div>

<div class="optionWrapper clearfix">
<span class="selectTitle">Flatten Folders <span class="separator">*</span></span>
    <div class="selectChoices">
        <select id="edit_flatten_folders" name="flatten_folders" class="form-control form-control-inline input-sm">
            <option value="keep" ${('', 'selected="selected"')[flatten_folders_value == None]}>&lt; keep &gt;</option>
            <option value="enable" ${('', 'selected="selected"')[flatten_folders_value == 1]}>enable</option>
            <option value="disable" ${('', 'selected="selected"')[flatten_folders_value == 0]}>disable</option>
        </select>
    </div>
</div>

<div class="optionWrapper">
    <span class="selectTitle">Paused</span>
    <div class="selectChoices">
        <select id="edit_paused" name="paused" class="form-control form-control-inline input-sm">
            <option value="keep" ${('', 'selected="selected"')[paused_value == None]}>&lt; keep &gt;</option>
            <option value="enable" ${('', 'selected="selected"')[paused_value == 1]}>enable</option>
            <option value="disable" ${('', 'selected="selected"')[paused_value == 0]}>disable</option>
        </select>
    </div><br />
</div>

<div class="optionWrapper">
    <span class="selectTitle">Default Episode Status:</span>
    <div class="selectChoices">
      <select id="edit_default_ep_status" name="default_ep_status" class="form-control form-control-inline input-sm">
          <option value="keep">&lt; keep &gt;</option>
          % for curStatus in [WANTED, SKIPPED, IGNORED]:
          <option value="${curStatus}" ${('', 'selected="selected"')[curStatus == default_ep_status_value]}>${statusStrings[curStatus]}</option>
          % endfor
      </select>
    </div><br />
</div>

<div class="optionWrapper">
    <span class="selectTitle">Scene Numbering</span>
    <div class="selectChoices">
        <select id="edit_scene" name="scene" class="form-control form-control-inline input-sm">
            <option value="keep" ${('', 'selected="selected"')[scene_value == None]}>&lt; keep &gt;</option>
            <option value="enable" ${('', 'selected="selected"')[scene_value == 1]}>enable</option>
            <option value="disable" ${('', 'selected="selected"')[scene_value == 0]}>disable</option>
        </select>
    </div><br />
</div>

<div class="optionWrapper">
    <span class="selectTitle">Anime</span>
    <div class="selectChoices">
        <select id="edit_anime" name="anime" class="form-control form-control-inline input-sm">
            <option value="keep" ${('', 'selected="selected"')[anime_value == None]}>&lt; keep &gt;</option>
            <option value="enable" ${('', 'selected="selected"')[anime_value == 1]}>enable</option>
            <option value="disable" ${('', 'selected="selected"')[anime_value == 0]}>disable</option>
        </select>
    </div><br />
</div>

<div class="optionWrapper">
    <span class="selectTitle">Sports</span>
    <div class="selectChoices">
        <select id="edit_sports" name="sports" class="form-control form-control-inline input-sm">
            <option value="keep" ${('', 'selected="selected"')[sports_value == None]}>&lt; keep &gt;</option>
            <option value="enable" ${('', 'selected="selected"')[sports_value == 1]}>enable</option>
            <option value="disable" ${('', 'selected="selected"')[sports_value == 0]}>disable</option>
        </select>
    </div><br />
</div>

<div class="optionWrapper">
    <span class="selectTitle">Air-By-Date</span>
    <div class="selectChoices">
        <select id="edit_air_by_date" name="air_by_date" class="form-control form-control-inline input-sm">
            <option value="keep" ${('', 'selected="selected"')[air_by_date_value == None]}>&lt; keep &gt;</option>
            <option value="enable" ${('', 'selected="selected"')[air_by_date_value == 1]}>enable</option>
            <option value="disable" ${('', 'selected="selected"')[air_by_date_value == 0]}>disable</option>
        </select>
    </div><br />
</div>

<div class="optionWrapper">
<span class="selectTitle">Subtitles<span class="separator"></span></span>
    <div class="selectChoices">
        <select id="edit_subtitles" name="subtitles" class="form-control form-control-inline input-sm">
            <option value="keep" ${('', 'selected="selected"')[subtitles_value == None]}>&lt; keep &gt;</option>
            <option value="enable" ${('', 'selected="selected"')[subtitles_value == 1]}>enable</option>
            <option value="disable" ${('', 'selected="selected"')[subtitles_value == 0]}>disable</option>
        </select>
    </div><br />
</div>

<div class="optionWrapper">
    <br /><span class="separator" style="font-size: 1.2em; font-weight: 700;">*</span>
    Changing these settings will cause the selected shows to be refreshed.
</div>

<div class="optionWrapper" style="text-align: center;">
    <input type="submit" value="Submit" class="btn" /><br />
</div>

</form>
<br />
</%block>
