<%
    import sickbeard
    from sickbeard.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickbeard.common import Quality, qualityPresets, qualityPresetStrings, statusStrings
    from sickbeard import subtitles
%>
        % if sickbeard.USE_SUBTITLES:
        <br><div class="field-pair">
            <label for="subtitles" class="clearfix">
                <span class="component-title">Subtitles</span>
                <span class="component-desc">
                     <input type="checkbox" name="subtitles" id="subtitles" ${('', 'checked="checked"')[bool(sickbeard.SUBTITLES_DEFAULT)]} />
                    <p>Download subtitles for this show?</p>
                </span>
            </label>
        </div>
        % endif

        <div class="field-pair">
            <label for="statusSelect">
                <span class="component-title">Status for previously aired episodes</span>
                <span class="component-desc">
                    <select name="defaultStatus" id="statusSelect" class="form-control form-control-inline input-sm">
                    % for curStatus in [SKIPPED, WANTED, ARCHIVED, IGNORED]:
                        <option value="${curStatus}" ${('', 'selected="selected"')[sickbeard.STATUS_DEFAULT == curStatus]}>${statusStrings[curStatus]}</option>
                    % endfor
                    </select>
                </span>
            </label>
        </div>
        <div class="field-pair">
            <label for="statusSelectAfter">
                <span class="component-title">Status for all future episodes</span>
                <span class="component-desc">
                    <select name="defaultStatusAfter" id="statusSelectAfter" class="form-control form-control-inline input-sm">
                    % for curStatus in [SKIPPED, WANTED, ARCHIVED, IGNORED]:
                        <option value="${curStatus}" ${('', 'selected="selected"')[sickbeard.STATUS_DEFAULT_AFTER == curStatus]}>${statusStrings[curStatus]}</option>
                    % endfor
                    </select>
                </span>
            </label>
        </div>
        <div class="field-pair alt">
            <label for="flatten_folders" class="clearfix">
                <span class="component-title">Flatten Folders</span>
                <span class="component-desc">
                    <input class="cb" type="checkbox" name="flatten_folders" id="flatten_folders" ${('', 'checked="checked"')[bool(sickbeard.FLATTEN_FOLDERS_DEFAULT)]}/>
                    <p>Disregard sub-folders?</p>
                </span>
            </label>
        </div>

% if enable_anime_options:
        <div class="field-pair alt">
            <label for="anime" class="clearfix">
                <span class="component-title">Anime</span>
                <span class="component-desc">
                    <input type="checkbox" name="anime" id="anime" ${('', 'checked="checked"')[bool(sickbeard.ANIME_DEFAULT)]} />
                    <p>Is this show an Anime?<p>
                </span>
            </label>
        </div>
% endif

        <div class="field-pair alt">
            <label for="scene" class="clearfix">
                <span class="component-title">Scene Numbering</span>
                <span class="component-desc">
                    <input type="checkbox" name="scene" id="scene" ${('', 'checked="checked"')[bool(sickbeard.SCENE_DEFAULT)]} />
                    <p>Is this show scene numbered?</p>
                </span>
            </label>
        </div>

        <% qualities = Quality.splitQuality(sickbeard.QUALITY_DEFAULT) %>
        <% anyQualities = qualities[0] %>
        <% bestQualities = qualities[1] %>
        <%include file="/inc_qualityChooser.mako"/>

        <br>
        <div class="field-pair alt">
            <label for="saveDefaultsButton" class="nocheck clearfix">
                <span class="component-title"><input class="btn btn-inline" type="button" id="saveDefaultsButton" value="Save Defaults" disabled="disabled" /></span>
                <span class="component-desc">
                    <p>Use current values as the defaults</p>
                </span>
            </label>
        </div><br>

% if enable_anime_options:
    <% import sickbeard.blackandwhitelist %>
    <%include file="/inc_blackwhitelist.mako"/>
% else:
        <input type="hidden" name="anime" id="anime" value="0" />
% endif
