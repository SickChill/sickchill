<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    from sickbeard import common
    from sickbeard.common import SKIPPED, WANTED, IGNORED
    from sickbeard.common import statusStrings
%>

<%block name="metas">
<meta data-var="show.is_anime" data-content="${show.is_anime}">
</%block>

<%block name="scripts">
    <script type="text/javascript" src="${srRoot}/js/qualityChooser.js?${sbPID}"></script>
    <script type="text/javascript" src="${srRoot}/js/editShow.js"></script>
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
                <li><a href="#core-component-group1">${_('Main')}</a></li>
                <li><a href="#core-component-group2">${_('Format')}</a></li>
                <li><a href="#core-component-group3">${_('Advanced')}</a></li>
            </ul>

            <div id="core-component-group1">
                <div class="component-group">
                    <h3>${_('Main Settings')}</h3>
                    <fieldset class="component-group-list">

                        <div class="field-pair">
                            <label for="location">
                                <span class="component-title">${_('Show Location')}</span>
                                <span class="component-desc">
                                    <input type="hidden" name="show" value="${show.indexerid}" />
                                    <input type="text" name="location" id="location" value="${show._location}" class="form-control form-control-inline input-sm input350" autocapitalize="off" />
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="quality_preset">
                                <span class="component-title">${_('Preferred Quality')}</span>
                                <span class="component-desc">
                                    <% allowed_qualities, preferred_qualities = common.Quality.splitQuality(int(show.quality)) %>
                                    <%include file="/inc_qualityChooser.mako"/>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="default_ep_statusSelect">
                                <span class="component-title">${_('Default Episode Status')}</span>
                                <span class="component-desc">
                                    <select name="default_ep_status" id="default_ep_statusSelect" class="form-control form-control-inline input-sm">
                                        % for cur_status in [WANTED, SKIPPED, IGNORED]:
                                        <option value="${cur_status}" ${('', 'selected="selected"')[cur_status == show.default_ep_status]}>${statusStrings[cur_status]}</option>
                                        % endfor
                                    </select>
                                    <div class="clear-left"><p>${_('This will set the status for future episodes.')}</p></div>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="indexer_lang_select">
                                <span class="component-title">${_('Info Language')}</span>
                                <span class="component-desc">
                                    <select name="indexer_lang" id="indexer_lang_select" class="form-control form-control-inline input-sm bfh-languages" data-language="${show.lang}" data-available="${','.join(sickbeard.indexerApi().config['valid_languages'])}"></select>
                                    <div class="clear-left"><p>${_('This only applies to episode filenames and the contents of metadata files.')}</p></div>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="subtitles">
                                <span class="component-title">${_('Subtitles')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" id="subtitles" name="subtitles" ${('', 'checked="checked"')[show.subtitles == 1 and sickbeard.USE_SUBTITLES is True]} ${('disabled="disabled"', '')[bool(sickbeard.USE_SUBTITLES)]}/> search for subtitles
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="paused">
                                <span class="component-title">${_('Paused')}</span>
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
                    <h3>${_('Format Settings')}</h3>
                    <fieldset class="component-group-list">

                        <div class="field-pair">
                            <label for="airbydate">
                                <span class="component-title">${_('Air by date')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" id="airbydate" name="air_by_date" ${('', 'checked="checked"')[show.air_by_date == 1]} /> ${_('check if the show is released as Show.03.02.2010 rather than Show.S02E03.')}<br>
                                    <span style="color:red">${_('In case of an air date conflict between regular and special episodes, the later will be ignored.')}</span>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="anime">
                                <span class="component-title">${_('Anime')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" id="anime" name="anime" ${('', 'checked="checked"')[show.is_anime == 1]}> ${_('check if the show is Anime and episodes are released as Show.265 rather than Show.S02E03')}<br>
                                    % if show.is_anime:
                                        <%include file="/inc_blackwhitelist.mako"/>
                                    % endif
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="sports">
                                <span class="component-title">${_('Sports')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" id="sports" name="sports" ${('', 'checked="checked"')[show.sports == 1]}/> ${_('check if the show is a sporting or MMA event released as Show.03.02.2010 rather than Show.S02E03')}<br>
                                    <span style="color:red">${_('In case of an air date conflict between regular and special episodes, the later will be ignored.')}</span>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="season_folders">
                                <span class="component-title">${_('Season folders')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" id="season_folders" name="flatten_folders" ${('checked="checked"', '')[show.flatten_folders == 1 and not sickbeard.NAMING_FORCE_FOLDERS]} ${('', 'disabled="disabled"')[bool(sickbeard.NAMING_FORCE_FOLDERS)]}/> ${_('group episodes by season folder (uncheck to store in a single folder)')}
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="scene">
                                <span class="component-title">${_('Scene Numbering')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" id="scene" name="scene" ${('', 'checked="checked"')[show.scene == 1]} /> ${_('search by scene numbering (uncheck to search by indexer numbering)')}
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="dvdorder">
                                <span class="component-title">${_('DVD Order')}</span>
                                <span class="component-desc">
                                    <input type="checkbox" id="dvdorder" name="dvdorder" ${('', 'checked="checked"')[show.dvdorder == 1]} /> ${_('use the DVD order instead of the air order')}<br>
                                    <div class="clear-left"><p>${_('A "Force Full Update" is necessary, and if you have existing episodes you need to sort them manually.')}</p></div>
                                </span>
                            </label>
                        </div>

                    </fieldset>
                </div>
            </div>

            <div id="core-component-group3">
                <div class="component-group">
                    <h3>${_('Advanced Settings')}</h3>
                    <fieldset class="component-group-list">

                        <div class="field-pair">
                            <label for="rls_ignore_words">
                                <span class="component-title">${_('Ignored Words')}</span>
                                <span class="component-desc">
                                    <input type="text" id="rls_ignore_words" name="rls_ignore_words" id="rls_ignore_words" value="${show.rls_ignore_words}" class="form-control form-control-inline input-sm input350" autocapitalize="off" /><br>
                                    <div class="clear-left">
                                        <p>${_('comma-separated <i>e.g. "word1,word2,word3"')}</i></>
                                        <p>${_('Search results with one or more words from this list will be ignored.')}</p>
                                    </div>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="rls_require_words">
                                <span class="component-title">${_('Required Words')}</span>
                                <span class="component-desc">
                                    <input type="text" id="rls_require_words" name="rls_require_words" id="rls_require_words" value="${show.rls_require_words}" class="form-control form-control-inline input-sm input350" autocapitalize="off" /><br>
                                    <div class="clear-left">
                                        <p>comma-separated <i>${_('e.g. "word1,word2,word3"')}</i></p>
                                        <p>${_('Search results with no words from this list will be ignored.')}</p>
                                    </div>
                                </span>
                            </label>
                        </div>

                        <div class="field-pair">
                            <label for="SceneName">
                                <span class="component-title">${_('Scene Exception')}</span>
                                <span class="component-desc">
                                    <input type="text" id="SceneName" class="form-control form-control-inline input-sm input200" autocapitalize="off" /><input class="btn btn-inline" type="button" value="Add" id="addSceneName" /><br><br>
                                    <div class="pull-left">
                                        <select id="exceptions_list" name="exceptions_list" multiple="multiple" style="min-width:200px;height:99px;">
                                        % for cur_exception in show.exceptions:
                                            <option value="${cur_exception}">${cur_exception}</option>
                                        % endfor
                                        </select>
                                        <div><input id="removeSceneName" value="${_('Remove')}" class="btn float-left" type="button" style="margin-top: 10px;"/></div>
                                    </div>
                                    <div class="clear-left"><p>${_('This will affect episode search on NZB and torrent providers. This list appends to the original show name.')}</p></div>
                                </span>
                            </label>
                        </div>

                    </fieldset>
                </div>
            </div>

        </div>

        <br>
        <input id="submit" type="submit" value="${_('Save Changes')}" class="btn pull-left config_submitter button">
        </form>
    </div>
</div>

</%block>
