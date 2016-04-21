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
	            <form action="editShow" method="post">

		            <div id="config-components">
			            <!-- Tabs -->
			            <ul>
				            <li><a href="#core-component-group1">${_('Main')}</a></li>
				            <li><a href="#core-component-group2">${_('Format')}</a></li>
				            <li><a href="#core-component-group3">${_('Advanced')}</a></li>
			            </ul>

			            <!-- Main -->
			            <div id="core-component-group1">
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
                                        <input type="hidden" name="show" value="${show.indexerid}"/>
                                        <input type="text" name="location" id="location" value="${show._location}"
                                               class="form-control form-control-inline input-sm input350"
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
		                                <select name="defaultEpStatus" id="defaultEpStatusSelect" class="form-control form-control-inline input-sm" title="defaultEpStatus">
                                            % for curStatus in [WANTED, SKIPPED, IGNORED]:
				                                <option value="${curStatus}" ${('', 'selected="selected"')[curStatus == show.default_ep_status]}>${statusStrings[curStatus]}</option>
                                            % endfor
		                                </select>
		                                <label for="defaultEpStatus">${_('This will set the status for future episodes.')}</label>
	                                </div>
                                </div>

                                <div class="field-pair row">
	                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
		                                <span class="component-title">${_('Info Language')}</span>
	                                </div>
	                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
		                                <select name="indexerLang" id="indexerLangSelect"
		                                        class="form-control form-control-inline input-sm bfh-languages"
		                                        data-language="${show.lang}"
		                                        data-available="${','.join(sickbeard.indexerApi().config['valid_languages'])}" title="indexerLang">
                                        </select>
                                        <label for="indexerLang">${_('This only applies to episode filenames and the contents of metadata files.')}</label>
	                                </div>
                                </div>

                                <div class="field-pair row">
	                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
		                                <span class="component-title">${_('Subtitles')}</span>
	                                </div>
	                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
		                                <input type="checkbox" id="subtitles" name="subtitles" ${('', 'checked="checked"')[show.subtitles == 1 and sickbeard.USE_SUBTITLES is True]} ${('disabled="disabled"', '')[bool(sickbeard.USE_SUBTITLES)]}/>
                                        <label for="subtitles">${_('search for subtitles')}</label>
	                                </div>
                                </div>

                                <div class="field-pair row">
	                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
		                                <span class="component-title">${_('Paused')}</span>
	                                </div>
	                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
		                                <input type="checkbox" id="paused" name="paused" ${('', 'checked="checked"')[show.paused == 1]}  title="paused"/>
                                        <label for="paused">${_('pause this show (SickRage will not download episodes)')}</label>
	                                </div>
                                </div>

                            </fieldset>
                        </div>

			            <!-- Format -->
			            <div id="core-component-group2">
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
                                                ${_('check if the show is released as Show.03.02.2010 rather than Show.S02E03.')}
			                                </div>
		                                </div>
		                                <div class="row">
			                                <div class="col-md-12">
				                                <label for="airbydate" style="color:red">${_('In case of an air date conflict between regular and special episodes, the later will be ignored.')}</label>
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
	                                            <input type="checkbox" id="sports" name="sports" ${('', 'checked="checked"')[show.sports == 1]}/> ${_('check if the show is a sporting or MMA event released as Show.03.02.2010 rather than Show.S02E03')}
                                            </div>
                                        </div>
		                                <div class="row">
			                                <div class="col-md-12">
				                                <label for="sports" style="color:red">${_('In case of an air date conflict between regular and special episodes, the later will be ignored.')}</label>
                                            </div>
                                        </div>
	                                </div>
                                </div>

                                <div class="field-pair row">
	                                <div class="col-lg-3 col-md-4 col-sm-5 col-xs-12">
		                                <span class="component-title">${_('Season folders')}</span>
	                                </div>
	                                <div class="col-lg-9 col-md-8 col-sm-7 col-xs-12 component-desc">
		                                <input type="checkbox" id="season_folders" name="flatten_folders" ${('checked="checked"', '')[show.flatten_folders == 1 and not sickbeard.NAMING_FORCE_FOLDERS]} ${('', 'disabled="disabled"')[bool(sickbeard.NAMING_FORCE_FOLDERS)]} title="season_folders"/>
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
	                                            <input type="checkbox" id="dvdorder" name="dvdorder" ${('', 'checked="checked"')[show.dvdorder == 1]} /> ${_('use the DVD order instead of the air order')}
                                            </div>
                                        </div>
		                                <div class="row">
			                                <div class="col-md-12">
				                                <label for="dvdorder">${_('A "Force Full Update" is necessary, and if you have existing episodes you need to sort them manually.')}</label>
                                            </div>
                                        </div>
	                                </div>
                                </div>

                            </fieldset>

			            </div>

			            <!-- Advanced -->
			            <div id="core-component-group3">
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
	                                            <input type="text" id="rls_ignore_words" name="rls_ignore_words"
	                                                   id="rls_ignore_words" value="${show.rls_ignore_words}"
	                                                   class="form-control form-control-inline input-sm input350"
	                                                   autocapitalize="off"/><br>
	                                            <label for="rls_ignore_words">${_('comma-separated <i>e.g. "word1,word2,word3</i>"')}</label>
                                            </div>
                                        </div>
		                                <div class="row">
			                                <div class="col-md-12">
				                                <label>${_('Search results with one or more words from this list will be ignored.')}</label>
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
	                                                   id="rls_require_words" value="${show.rls_require_words}"
	                                                   class="form-control form-control-inline input-sm input350"
	                                                   autocapitalize="off"/>
                                                <br/>
	                                            <label for="rls_require_words">comma-separated&nbsp;<i>${_('e.g. "word1,word2,word3"')}</i></label>
                                            </div>
                                        </div>
		                                <div class="row">
			                                <div class="col-md-12">
				                                <label>${_('Search results with no words from this list will be ignored.')}</label>
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
	                                            <input type="text" id="SceneName"
	                                                   class="form-control form-control-inline input-sm input200" autocapitalize="off"/>
	                                            <input class="btn btn-inline" type="button" value="${_('Add')}" id="addSceneName"/>
                                            </div>
                                        </div>
		                                <div class="row">
			                                <div class="col-md-12">
				                                <select id="exceptions_list" name="exceptions_list" multiple="multiple"
				                                        style="min-width:200px;height:99px;" title="exceptions_list">
                                                    % for cur_exception in show.exceptions:
						                                <option value="${cur_exception}">${cur_exception}</option>
                                                    % endfor
				                                </select>
				                                <div>
					                                <input id="removeSceneName" value="${_('Remove')}" class="btn float-left" type="button" style="margin-top: 10px;"/>
				                                </div>
			                                </div>
		                                </div>
		                                <div class="row">
			                                <div class="col-md-12">
				                                <p>${_('This will affect episode search on NZB and torrent providers. This list appends to the original show name.')}</p>
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
		                    <input type="submit" class="btn pull-left config_submitter button" value="${_('Save Changes')}"/>
	                    </div>
                    </div>

	            </form>
            </div>
        </div>
	</div>

</%block>
