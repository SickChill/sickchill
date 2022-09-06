<%inherit file="/layouts/main.mako"/>
<%!
    from sickchill import settings
    from sickchill.oldbeard import common
    from sickchill.oldbeard.common import SKIPPED, WANTED, IGNORED
    from sickchill.oldbeard.common import statusStrings
    from sickchill import indexer as show_indexer
%>

<%block name="metas">
    <meta data-var="show.is_anime" data-content="${show.is_anime}">
</%block>
<%block name='css'>
    <link rel="stylesheet" type="text/css" href="${static_url('css/imageSelector.css')}" />
</%block>
<%block name="scripts">
    % if show.is_anime:
        <script type="text/javascript" src="${static_url('js/blackwhite.js')}"></script>
    % endif
    <script type="text/javascript" src="${static_url('js/imageSelector.js')}"></script>
</%block>

<%block name="content">
    <div class="image-selector-dialog" style="display:none">
        <div class="image-provider-container">
            <select id="images-provider" name="provider" data-default="${show.indexer}">
                <option value="-1">Upload</option>
                <option value="${show_indexer.FANART}">Fanart</option>
                <option value="${show_indexer.TMDB}">TMDB</option>
                % for index, indexer in show_indexer:
                <option value="${index}" ${('', 'selected="selected"')[show.indexer == index]}>
                    ${indexer.name}
                </option>
                % endfor
            </select>
        </div>
        <div class="upload" hidden>
            <input type="file" id="upload-image-input" accept="image/*" multiple/>
        </div>
        <div class="error ui-state-error" hidden></div>
        <div class="images ui-dialog-scrollable-child"></div>
    </div>

    <div id="config">
        <div class="row">
            <div class="col-md-12">
                % if not header is UNDEFINED:
                    <h1 class="header">${header}</h1>
                % else:
                    <h1 class="title">${title}</h1>
                % endif
            </div>
        </div>
        <div class="row">
            <div class="col-md-12">
                <form action="editShow" method="post" accept-charset="utf-8">

                    <div id="config-components">
                        <!-- Tabs -->
                        <ul>
                            <li><a href="#main">${_('Main')}</a></li>
                            <li><a href="#format">${_('Format')}</a></li>
                            <li><a href="#advanced">${_('Advanced')}</a></li>
                            <li><a href="#customize">${_('Customize')}</a></li>
                        </ul>

                        <!-- Main -->
                        <div id="main">
                            <div class="row">
                                <div class="col-md-12">
                                    <h3>${_('Main Settings')}</h3>
                                </div>
                            </div>
                            <fieldset class="component-group-list">

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('Show Location')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="hidden" name="show" id="showID" value="${show.indexerid}"/>
                                        <input type="text" name="location" id="location" value="${show._location}"
                                               class="form-control input-sm input350"
                                               autocapitalize="off" title="Location"/>
                                    </div>
                                </div>

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('Preferred Quality')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <% anyQualities, bestQualities = common.Quality.splitQuality(int(show.quality)) %>
                                        <%include file="/inc_qualityChooser.mako"/>
                                    </div>
                                </div>

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('Default Episode Status')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <select name="defaultEpStatus" id="defaultEpStatusSelect" class="form-control input-sm input100" title="defaultEpStatus">
                                                    % for curStatus in [WANTED, SKIPPED, IGNORED]:
                                                        <option value="${curStatus}" ${('', 'selected="selected"')[curStatus == show.default_ep_status]}>${statusStrings[curStatus]}</option>
                                                    % endfor
                                                </select>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="defaultEpStatus">${_('this will set the status for future episodes.')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('Info Language')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <select name="indexerLang" id="indexerLangSelect"
                                                        class="form-control input-sm input150 bfh-languages"
                                                        data-language="${show.lang}"
                                                        data-available="${','.join(show_indexer.languages())}" title="indexerLang">
                                                </select>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="indexerLang">${_('this only applies to episode file names and the contents of metadata files.')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('Subtitles')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" class="enabler" id="subtitles" name="subtitles" ${('', 'checked="checked"')[show.subtitles == 1 and settings.USE_SUBTITLES is True]} ${('disabled="disabled"', '')[bool(settings.USE_SUBTITLES)]}/>
                                        <label for="subtitles">${_('search for subtitles')}</label>
                                    </div>
                                </div>
                                <div id="content_subtitles">
                                    <div class="field-pair row">
                                        <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                            <span class="component-title">${_('Use SC Metadata')}</span>
                                        </div>
                                        <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                            <input type="checkbox" id="subtitles_sr_metadata" name="subtitles_sr_metadata" ${('', 'checked="checked"')[show.subtitles_sr_metadata == 1 ]} />
                                            <label for="subtitles_sr_metadata">${_('use SickChill metadata when searching for subtitle, this will override the autodiscovered metadata')}</label>
                                        </div>
                                    </div>
                                </div>

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('Paused')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" id="paused" name="paused" ${('', 'checked="checked"')[show.paused == 1]}  title="paused"/>
                                        <label for="paused">${_('pause this show (SickChill will not download episodes)')}</label>
                                    </div>
                                </div>

                            </fieldset>
                        </div>

                        <!-- Format -->
                        <div id="format">
                            <div class="row">
                                <div class="col-md-12">
                                    <h3>${_('Format Settings')}</h3>
                                </div>
                            </div>
                            <fieldset class="component-group-list">

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('Air by date')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="checkbox" id="airbydate" name="air_by_date" ${('', 'checked="checked"')[show.air_by_date == 1]} />
                                                <label for="airbydate">${_('check if the show is released as Show.03.02.2010 rather than Show.S02E03.')}</label>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="airbydate" style="color:red">${_('in case of an air date conflict between regular and special episodes, the later will be ignored.')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('Anime')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="checkbox" id="anime"
                                                       name="anime" ${('', 'checked="checked"')[show.is_anime == 1]}>
                                                <label for="anime">${_('check if the show is Anime and episodes are released as Show.265 rather than Show.S02E03')}</label>
                                            </div>
                                        </div>
                                        % if show.is_anime:
                                            <div class="row">
                                                <div class="col-md-12">
                                                    <%include file="/inc_blackwhitelist.mako"/>
                                                </div>
                                            </div>
                                        % endif
                                    </div>
                                </div>

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('Sports')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="checkbox" id="sports" name="sports" ${('', 'checked="checked"')[show.sports == 1]}/>
                                                <label>${_('check if the show is a sporting or MMA event released as Show.03.02.2010 rather than Show.S02E03')}</label>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="sports" style="color:red">${_('in case of an air date conflict between regular and special episodes, the later will be ignored.')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('Season folders')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" id="season_folders" name="season_folders" ${('', 'checked="checked"')[show.season_folders == 1 or settings.NAMING_FORCE_FOLDERS]} ${('', 'disabled="disabled"')[bool(settings.NAMING_FORCE_FOLDERS)]} title="season_folders"/>
                                        <label for="season_folders">${_('group episodes by season folder (uncheck to store in a single folder)')}</label>
                                    </div>
                                </div>

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('Scene Numbering')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="checkbox" id="scene" name="scene" ${('', 'checked="checked"')[show.scene == 1]} />
                                        <label for="scene">${_('search by scene numbering (uncheck to search by indexer numbering)')}</label>
                                    </div>
                                </div>

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('DVD Order')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="checkbox" id="dvdorder" name="dvdorder" ${('', 'checked="checked"')[show.dvdorder == 1]} />
                                                <label>${_('use the DVD order instead of the air order')}</label>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="dvdorder">${_('a "Force Full Update" is necessary, and if you have existing episodes you need to sort them manually.')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                            </fieldset>

                        </div>

                        <!-- Advanced -->
                        <div id="advanced">
                            <div class="row">
                                <div class="col-md-12">
                                    <h3>${_('Advanced Settings')}</h3>
                                </div>
                            </div>

                            <fieldset class="component-group-list">

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('Ignored Words')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" id="rls_ignore_words"
                                                       name="rls_ignore_words" value="${show.rls_ignore_words}"
                                                       class="form-control input-sm input350" autocapitalize="off"/>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="rls_ignore_words">${_('comma-separated <i>e.g. "word1,word2,word3</i>"')}</label>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label>${_('search results with one or more words from this list will be ignored.')}</label>
                                                <label><b>${_('note')}:</b> ${_('this option adds to the globally ignored words!')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('Preferred Words')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" id="rls_prefer_words" name="rls_prefer_words"
                                                       value="${show.rls_prefer_words}" autocapitalize="off"
                                                       class="form-control input-sm input350"/>
                                                <br/>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="rls_prefer_words">${_('comma-separated <i>e.g. "word1,word2,word3</i>"')}</label>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label>${_('search results with these words will be preferred in this order.')}</label>
                                                <label><b>${_('note')}:</b> ${_('this option overrides the globally preferred words!')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>


                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('Required Words')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" id="rls_require_words" name="rls_require_words"
                                                       value="${show.rls_require_words}" autocapitalize="off"
                                                       class="form-control input-sm input350"/>
                                                <br/>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label for="rls_require_words">${_('comma-separated <i>e.g. "word1,word2,word3</i>"')}</label>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label>${_('search results with no words from this list will be ignored.')}</label>
                                                <label><b>${_('note')}:</b> ${_('this option overrides the globally required words, and globally ignored words!')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('Scene Exception')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="text" id="SceneName" class="form-control input-sm input250" autocapitalize="off"/>
                                                <select id="SceneSeason" class="form-control input-sm" style="width: 95px">
                                                    % for season in range(0, len(seasonResults) + 1):
                                                        %if season == 0:
                                                            <% season = -1 %>
                                                        %endif
                                                        <option data-season="${season}">${_('Show') if season == -1 else _('Season ') + str(season)}</option>
                                                    %endfor
                                                </select>
                                                <input class="btn btn-inline" type="button" value="${_('Add')}" id="addSceneName"/>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <input type="hidden" id="exceptions" name="exceptions_list"/>
                                                <select id="exceptions_list" multiple
                                                        style="height:200px;" class="form-control input350 exceptions_list" title="exceptions_list">
                                                    % for season in range(0, len(seasonResults) + 1):
                                                        %if season == 0:
                                                            <% season = -1 %>
                                                        %endif
                                                        <optgroup data-season="${season}" label="${_('Show') if season == -1 else _('Season ') + str(season)}">
                                                            %if season in scene_exceptions:
                                                                %for exception in scene_exceptions[season]:
                                                                    <option ${'disabled' if exception["custom"] == False else ''} value="${exception["show_name"]}">
                                                                        ${exception["show_name"]}
                                                                    </option>
                                                                %endfor
                                                            % else:
                                                            <option class="empty" disabled>${_('None')}</option>
                                                        %endif
                                                        </optgroup>
                                                    % endfor
                                                </select>
                                                <div>
                                                    <input id="removeSceneName" value="${_('Remove')}" class="btn float-left" type="button" style="margin-top: 10px;"/>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label>${_('this will affect episode search on NZB and torrent providers.')}</label>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label>${_('this list appends to the original show name.')}</label>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-12">
                                                <label>${_('disabled entries come from a central file on github,<br/> if you think something is wrong please make an issue <a href="//github.com/sickchill/sickchill.github.io/issues">here</a>.')}</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                            </fieldset>
                        </div>

                        <!-- Customize -->
                        <div id="customize">
                            <div class="row">
                                <div class="col-md-12">
                                    <h3>${_('Customize Settings')}</h3>
                                </div>
                            </div>

                            <fieldset class="component-group-list">

                                <!-- Name -->
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('Name')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <input type="text" name="custom_name" id="custom_name" placeholder="${show.show_name}" value="${show.custom_name}"
                                               list="scene_exceptions"
                                               class="form-control input-sm input350"
                                               autocapitalize="off" title="Name"/>
                                    </div>

                                    %if -1 in scene_exceptions:
                                    <datalist id="scene_exceptions">
                                       %for exception in scene_exceptions[-1]:
                                        <option>${exception["show_name"]}</option>
                                        %endfor
                                    </datalist>
                                    %endif
                                </div>

                                <!-- Poster -->
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('Poster')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <div class="poster-container">
                                                    <input type="hidden" name="poster"/>
                                                    <img src="${static_url(show.show_image_url('poster'))}"
                                                         data-image-type="poster"
                                                         class="custom-image tvshowImg" alt="${_('Poster for')} ${show.name}"
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <!-- Banner -->
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('Banner')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <div class="banner-container">
                                                    <input type="hidden" name="banner"/>
                                                    <img src="${static_url(show.show_image_url('banner'))}"
                                                         data-image-type="banner"
                                                         class="custom-image banner" alt="${_('Banner for')} ${show.name}"
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <!-- Fanart -->
                                <div class="field-pair row">
                                    <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
                                        <span class="component-title">${_('Background')}</span>
                                    </div>
                                    <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
                                        <div class="row">
                                            <div class="col-md-12">
                                                <div class="fanart-container">
                                                    <input type="hidden" name="fanart"/>
                                                    <img src="${static_url(show.show_image_url('fanart'))}"
                                                         data-image-type="fanart"
                                                         class="custom-image tvshowImg" alt="${_('Fanart for')} ${show.name}"
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </fieldset>
                        </div>
                    </div>

                    <br/>
                    <div class="row">
                        <div class="col-lg-2 col-md-2 col-sm-2 col-xs-12">
                            <input type="submit" id="submit" class="btn pull-left config_submitter button" value="${_('Save Changes')}"/>
                        </div>
                    </div>

                </form>
            </div>
        </div>
    </div>

</%block>
