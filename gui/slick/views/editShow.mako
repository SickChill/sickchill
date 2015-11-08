<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    import adba
    from sickbeard import common
    from sickbeard.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickbeard.common import statusStrings
    from sickrage.helper import exceptions
    from sickbeard import scene_exceptions
%>

<%block name="metas">
<meta data-var="show.is_anime" data-content="${show.is_anime}">
</%block>

<%block name="scripts">
    <script type="text/javascript" src="${srRoot}/js/qualityChooser.js?${sbPID}"></script>
    <script type="text/javascript" src="${srRoot}/js/lib/bootstrap-formhelpers.min-2.3.0.js?${sbPID}"></script>
    <script type="text/javascript" src="${srRoot}/js/new/editShow.js"></script>
% if show.is_anime:
    <script type="text/javascript" src="${srRoot}/js/blackwhite.js?${sbPID}"></script>
% endif
</%block>

<%block name="content">
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif

<div id="config">

    <div id="config-content">
        <form action="editShow" method="post">

        <div id="config-components">
            <ul>
                <li><a href="#core-component-group1">Main</a></li>
                <li><a href="#core-component-group2">Format</a></li>
                <li><a href="#core-component-group3">Advanced</a></li>
            </ul>

            <div id="core-component-group1">
                <div class="component-group">
                    <h3>Main Settings</h3>
                    <fieldset class="component-group-list">
                        
                        <div class="field-pair">
                            <label for="location">
                                <span class="component-title">Show Location</span>
                                <span class="component-desc">
                                    <input type="hidden" name="show" value="${show.indexerid}" />
                                    <input type="text" name="location" id="location" value="${show._location}" class="form-control form-control-inline input-sm input350" />
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="qualityPreset">
                                <span class="component-title">Preferred Quality</span>
                                <span class="component-desc">
                                    <%
                                        qualities = common.Quality.splitQuality(int(show.quality))
                                        anyQualities = qualities[0]
                                        bestQualities = qualities[1]
                                    %>
                                    <%include file="/inc_qualityChooser.mako"/>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="">
                                <span class="component-title">Archive on first match</span>
                                <span class="component-desc">
                                    <input type="checkbox" id="archive_firstmatch" name="archive_firstmatch" ${('', 'checked="checked"')[show.archive_firstmatch == 1]} /> archive episode after the first best match is found from your archive quality list
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="defaultEpStatusSelect">
                                <span class="component-title">Default Episode Status</span>
                                <span class="component-desc">
                                    <select name="defaultEpStatus" id="defaultEpStatusSelect" class="form-control form-control-inline input-sm">
                                        % for curStatus in [WANTED, SKIPPED, IGNORED]:
                                        <option value="${curStatus}" ${('', 'selected="selected"')[curStatus == show.default_ep_status]}>${statusStrings[curStatus]}</option>
                                        % endfor
                                    </select>
                                    <div class="clear-left"><p>This will set the status for future episodes.</p></div>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="indexerLangSelect">
                                <span class="component-title">Info Language</span>
                                <span class="component-desc">
                                    <select name="indexerLang" id="indexerLangSelect" class="form-control form-control-inline input-sm bfh-languages" data-language="${show.lang}" data-available="${','.join(sickbeard.indexerApi().config['valid_languages'])}"></select>
                                    <div class="clear-left"><p>This only applies to episode filenames and the contents of metadata files.</p></div>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="subtitles">
                                <span class="component-title">Subtitles</span>
                                <span class="component-desc">
                                    <input type="checkbox" id="subtitles" name="subtitles" ${('', 'checked="checked"')[show.subtitles == 1 and sickbeard.USE_SUBTITLES == True]} ${('disabled="disabled"', '')[bool(sickbeard.USE_SUBTITLES)]}/> search for subtitles
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="paused">
                                <span class="component-title">Paused</span>
                                <span class="component-desc">
                                    <input type="checkbox" id="paused" name="paused" ${('', 'checked="checked"')[show.paused == 1]} /> pause this show (SickRage will not download episodes)
                                </span>
                            </label>
                        </div>

                    </fieldset>
                </div>
            </div>

            <div id="core-component-group2">
                <div class="component-group">
                    <h3>Format Settings</h3>
                    <fieldset class="component-group-list">

                        <div class="field-pair">
                            <label for="airbydate">
                                <span class="component-title">Air by date</span>
                                <span class="component-desc">
                                    <input type="checkbox" id="airbydate" name="air_by_date" ${('', 'checked="checked"')[show.air_by_date == 1]} /> check if the show is released as Show.03.02.2010 rather than Show.S02E03.<br>
                                    <span style="color:red">In case of an air date conflict between regular and special episodes, the later will be ignored.</span>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="anime">
                                <span class="component-title">Anime</span>
                                <span class="component-desc">
                                    <input type="checkbox" id="anime" name="anime" ${('', 'checked="checked"')[show.is_anime == 1]}> check if the show is Anime and episodes are released as Show.265 rather than Show.S02E03<br>
                                    % if show.is_anime:
                                        <%include file="/inc_blackwhitelist.mako"/>
                                    % endif
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="sports">
                                <span class="component-title">Sports</span>
                                <span class="component-desc">
                                    <input type="checkbox" id="sports" name="sports" ${('', 'checked="checked"')[show.sports == 1]}/> check if the show is a sporting or MMA event released as Show.03.02.2010 rather than Show.S02E03<br>
                                    <span style="color:red">In case of an air date conflict between regular and special episodes, the later will be ignored.</span>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="season_folders">
                                <span class="component-title">Season folders</span>
                                <span class="component-desc">
                                    <input type="checkbox" id="season_folders" name="flatten_folders" ${('checked="checked"', '')[show.flatten_folders == 1 and not sickbeard.NAMING_FORCE_FOLDERS]} ${('', 'disabled="disabled"')[bool(sickbeard.NAMING_FORCE_FOLDERS)]}/> group episodes by season folder (uncheck to store in a single folder)
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="scene">
                                <span class="component-title">Scene Numbering</span>
                                <span class="component-desc">
                                    <input type="checkbox" id="scene" name="scene" ${('', 'checked="checked"')[show.scene == 1]} /> search by scene numbering (uncheck to search by indexer numbering)
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="dvdorder">
                                <span class="component-title">DVD Order</span>
                                <span class="component-desc">
                                    <input type="checkbox" id="dvdorder" name="dvdorder" ${('', 'checked="checked"')[show.dvdorder == 1]} /> use the DVD order instead of the air order<br>
                                    <div class="clear-left"><p>A "Force Full Update" is necessary, and if you have existing episodes you need to sort them manually.</p></div>
                                </span>
                            </label>
                        </div>

                    </fieldset>
                </div>
            </div>

            <div id="core-component-group3">
                <div class="component-group">
                    <h3>Advanced Settings</h3>
                    <fieldset class="component-group-list">

                        <div class="field-pair">
                            <label for="rls_ignore_words">
                                <span class="component-title">Ignored Words</span>
                                <span class="component-desc">
                                    <input type="text" id="rls_ignore_words" name="rls_ignore_words" id="rls_ignore_words" value="${show.rls_ignore_words}" class="form-control form-control-inline input-sm input350" /><br>
                                    <div class="clear-left">
                                        <p>comma-separated <i>e.g. "word1,word2,word3"</i></>
                                        <p>Search results with one or more words from this list will be ignored.</p>
                                    </div>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="rls_require_words">
                                <span class="component-title">Required Words</span>
                                <span class="component-desc">
                                    <input type="text" id="rls_require_words" name="rls_require_words" id="rls_require_words" value="${show.rls_require_words}" class="form-control form-control-inline input-sm input350" /><br>
                                    <div class="clear-left">
                                        <p>comma-separated <i>e.g. "word1,word2,word3"</i></p>
                                        <p>Search results with no words from this list will be ignored.</p>
                                    </div>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="SceneName">
                                <span class="component-title">Scene Exception</span>
                                <span class="component-desc">
                                    <input type="text" id="SceneName" class="form-control form-control-inline input-sm input200" /><input class="btn btn-inline" type="button" value="Add" id="addSceneName" /><br><br>
                                    <div class="pull-left">
                                        <select id="exceptions_list" name="exceptions_list" multiple="multiple" style="min-width:200px;height:99px;">
                                        % for cur_exception in show.exceptions:
                                            <option value="${cur_exception}">${cur_exception}</option>
                                        % endfor
                                        </select>
                                        <div><input id="removeSceneName" value="Remove" class="btn float-left" type="button" style="margin-top: 10px;"/></div>
                                    </div>
                                    <div class="clear-left"><p>This will affect episode search on NZB and torrent providers. This list overrides the original name; it doesn't append to it.</p></div>
                                </span>
                            </label>
                        </div>

                    </fieldset>
                </div>
            </div>
        
        </div>

        <br>
        <input id="submit" type="submit" value="Save Changes" class="btn pull-left config_submitter button">
        </form>
    </div>
</div>

</%block>
