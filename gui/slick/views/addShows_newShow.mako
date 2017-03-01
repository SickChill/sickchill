<%inherit file="/layouts/config.mako"/>
<%!
    import sickbeard
    from sickbeard.helpers import anon_url
%>
<%block name="scripts">
    <script type="text/javascript" src="${srRoot}/js/plotTooltip.js?${sbPID}"></script>
    <script type="text/javascript" src="${srRoot}/js/blackwhite.js?${sbPID}"></script>
</%block>

<%block name="tabs">
    <li><a href="#core-component-group1">${_('Add New Show')}</a></li>
</%block>

<%block name="saveButton"/>

<%block name="pages">
    <div id="core-component-group1" class="tab-pane active component-group">
        <div class="row">
            <div class="col-md-12">
                <div id="displayText"></div>
            </div>
        </div>
        <br/>
        <div class="row">
            <div class="col-md-12">
                <form id="addShowForm" method="post" action="${srRoot}/addShows/addNewShow" accept-charset="utf-8">
                    ${xsrf_token}
                    <fieldset class="sectionwrap">
                        <legend class="legendStep">${_('Find a show on theTVDB')}</legend>
                        <div class="row stepDiv">
                            <div class="col-md-12">
                                <input type="hidden" id="indexer_timeout" value="${sickbeard.INDEXER_TIMEOUT}" />

                                % if use_provided_info:
                                    <label>${_('Show retrieved from existing metadata')}: <a href="${anon_url(sickbeard.indexerApi(provided_indexer).config['show_url'], provided_indexer_id)}">${provided_indexer_name}</a></label>
                                    <input type="hidden" id="indexerLang" name="indexerLang" value="en" />
                                    <input type="hidden" id="whichSeries" name="whichSeries" value="${provided_indexer_id}" />
                                    <input type="hidden" id="providedIndexer" name="providedIndexer" value="${provided_indexer}" />
                                    <input type="hidden" id="providedName" value="${provided_indexer_name}" />
                                % else:
                                    <input type="text" id="nameToSearch" value="${default_show_name}" class="form-control form-control-inline input-sm input350" autocapitalize="off" />
                                    &nbsp;&nbsp;
                                    <select name="indexerLang" id="indexerLangSelect" class="form-control form-control-inline input-sm bfh-languages" data-language="${sickbeard.INDEXER_DEFAULT_LANGUAGE}" data-available="${','.join(sickbeard.indexerApi().config['valid_languages'])}">
                                    </select>
                                    <b>*</b>
                                    &nbsp;
                                    <select name="providedIndexer" id="providedIndexer" class="form-control form-control-inline input-sm">
                                        <option value="0" ${('', 'selected="selected"')[provided_indexer == 0]}>${_('All Indexers')}</option>
                                        % for indexer in indexers:
                                            <option value="${indexer}" ${('', 'selected="selected"')[provided_indexer == indexer]}>
                                                ${indexers[indexer]}
                                            </option>
                                        % endfor
                                    </select>
                                    &nbsp;
                                    <input class="btn btn-inline" type="button" id="searchName" value="${_('Search')}" />
                                    <br/><br/>
                                    <p>
                                        <b>*</b>${_('This will only affect the language of the retrieved metadata file contents and episode filenames.')}<br/>
                                        ${_('This <b>DOES NOT</b> allow SickRage to download non-english TV episodes!')}
                                    </p>
                                    <br/><br/>
                                    <div id="searchResults" style="height: 100%;"><br/></div>
                                % endif
                            </div>
                        </div>
                    </fieldset>

                    <fieldset class="sectionwrap">
                        <div class="row stepDiv">
                            <div class="col-md-12">
                                <legend class="legendStep">${_('Pick the parent folder')}</legend>
                                % if provided_show_dir:
                                    <p>${_('Pre-chosen Destination Folder')}: <b>${provided_show_dir}</b></p>
                                    <br>
                                    <input type="hidden" id="fullShowPath" name="fullShowPath" value="${provided_show_dir}" />
                                    <br>
                                % else:
                                    <%include file="/inc_rootDirs.mako"/>
                                % endif
                            </div>
                        </div>
                    </fieldset>

                    <fieldset class="sectionwrap">
                        <div class="row stepDiv">
                            <div class="col-md-12">
                                <legend class="legendStep">${_('Customize options')}</legend>
                                <%include file="/inc_addShowOptions.mako"/>
                            </div>
                        </div>
                    </fieldset>

                    % for curNextDir in other_shows:
                        <input type="hidden" name="other_shows" value="${curNextDir}" />
                    % endfor
                    <input type="hidden" name="skipShow" id="skipShow"/>
                </form>
            </div>
        </div>
        <br/>
        <div class="row">
            <div class="col-md-12">
                <div style="text-align: center;">
                    <input class="btn" type="button" id="addShowButton" value="${_('Add Show')}" disabled="disabled" />
                    % if provided_show_dir:
                        <input class="btn" type="button" id="skipShowButton" value="${_('Skip Show')}" />
                    % endif
                </div>
            </div>
        </div>
    </div>
</%block>
