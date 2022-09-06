<%
    from sickchill import settings
    from sickchill.oldbeard.common import SKIPPED, WANTED, IGNORED
    from sickchill.oldbeard.common import Quality, statusStrings
%>
    <div class="field-pair row">
        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
            <span class="component-title">${_('Preferred Quality')}</span>
        </div>
        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
            <% anyQualities, bestQualities = Quality.splitQuality(settings.QUALITY_DEFAULT) %>
            <%include file="/inc_qualityChooser.mako"/>
        </div>
    </div>
    <br>

    % if settings.USE_SUBTITLES:
        <div class="field-pair row">
            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                <span class="component-title">${_('Subtitles')}</span>
            </div>
            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                <input type="checkbox" name="subtitles" id="subtitles" ${('', 'checked="checked"')[bool(settings.SUBTITLES_DEFAULT)]} />
                <label for="subtitles">${_('Download subtitles for this show?')}</label>
            </div>
            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                <span class="component-title">${_('Use SC Metadata')}</span>
            </div>
            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                <input type="checkbox" id="subtitles_sr_metadata" name="subtitles_sr_metadata"  />
                <label for="subtitles_sr_metadata">${_('use SickChill metadata when searching for subtitle, <br />this will override the autodiscovered metadata')}</label>
            </div>
        </div>
        <br>
    % endif

    <div class="field-pair row">
        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
            <span class="component-title">${_('Status for previously aired episodes')}</span>
        </div>
        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
            <select name="defaultStatus" id="statusSelect" class="form-control form-control-inline input-sm" title="defaultStatus">
                % for curStatus in [SKIPPED, WANTED, IGNORED]:
                    <option value="${curStatus}" ${('', 'selected="selected"')[settings.STATUS_DEFAULT == curStatus]}>${statusStrings[curStatus]}</option>
                % endfor
            </select>
        </div>
    </div>
    <br>

    <div class="field-pair row">
        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
            <span class="component-title">${_('Status for all future episodes')}</span>
        </div>
        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
            <select name="defaultStatusAfter" id="statusSelectAfter" class="form-control form-control-inline input-sm">
                % for curStatus in [SKIPPED, WANTED, IGNORED]:
                    <option value="${curStatus}" ${('', 'selected="selected"')[settings.STATUS_DEFAULT_AFTER == curStatus]}>${statusStrings[curStatus]}</option>
                % endfor
            </select>
        </div>
    </div>
    <br>

    <div class="field-pair row">
        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
            <span class="component-title">${_('Season Folders')}</span>
        </div>
        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
            <input type="checkbox" name="season_folders" id="season_folders" ${('', 'checked="checked"')[bool(settings.SEASON_FOLDERS_DEFAULT)]}/>
            <label for="season_folders">${_('Group episodes by season folder?')}</label>
        </div>
    </div>
    <br>

    % if enable_anime_options:
        <div class="field-pair row">
            <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                <span class="component-title">${_('Anime')}</span>
            </div>
            <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                <input type="checkbox" name="anime" id="anime" ${('', 'checked="checked"')[bool(settings.ANIME_DEFAULT)]} />
                <label for="anime">${_('Is this show an Anime?')}</label>
            </div>
        </div>
        <br>
    % endif

    <div class="field-pair row">
        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
            <span class="component-title">${_('Scene Numbering')}</span>
        </div>
        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
            <input type="checkbox" name="scene" id="scene" ${('', 'checked="checked"')[bool(settings.SCENE_DEFAULT)]} />
            <label for="scene">${_('Is this show scene numbered?')}</label>
        </div>
    </div>
    <br>
    <div class="field-pair row">
        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
            <span class="component-title">
                <input class="btn btn-inline" type="button" id="saveDefaultsButton" value="${_('Save as default')}" disabled="disabled" />
            </span>
        </div>
        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
            <label>${_('Use current values as the defaults')}</label>
        </div>
    </div>

    % if enable_anime_options:
        <% import sickchill.oldbeard.blackandwhitelist %>
        <%include file="/inc_blackwhitelist.mako"/>
    % else:
        <input type="hidden" name="anime" id="anime" value="0" />
    % endif
